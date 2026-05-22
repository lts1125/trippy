"""
/api/chat 路由
"""
import asyncio
import json
import re
from fastapi import APIRouter
from src.models.schemas import ChatRequest, ChatResponse
from src.services.intent import parse_request
from src.services.prompts import build_prompt
from src.services.minimax import MiniMaxService
from typing import Optional
from src.services.amap import AmapService

router = APIRouter(prefix="/api", tags=["chat"])
mm = MiniMaxService()
amap = AmapService()


def parse_json_response(content: str) -> dict:
    """
    从 MiniMax 返回中提取 JSON。
    策略：先剥离 markdown 代码块，然后尝试解析。如果失败，尝试从文本中提取 JSON 子串。
    """
    original = content.strip()

    # 扩展 1：剥离 markdown 代码块（支持 ```json 和 ```，以及多行情况）
    content = original
    fence_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', content, re.DOTALL)
    if fence_match:
        content = fence_match.group(1).strip()
    elif content.startswith('```'):
        lines = content.split('\n')
        if len(lines) > 1:
            # 去掉首行 ```json 和尾行 ```（如果有）
            if lines[-1].strip() == '```':
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            content = '\n'.join(lines).strip()

    # 扩展 2：直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 扩展 3：尝试从文本中提取第一个 JSON 对象/数组
    json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
    if json_match:
        try:
            candidate = json_match.group(1)
            # 尝试找到匹配的括号
            for end in range(len(candidate), 0, -1):
                try:
                    return json.loads(candidate[:end])
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

    # 扩展 4：尝试解析 reply 字段内的 JSON
    try:
        wrapper = json.loads(content)
        reply_str = wrapper.get('reply', '')
        if reply_str and isinstance(reply_str, str):
            inner = json.loads(reply_str)
            print(f'[parse_json_response] extracted inner JSON from reply field, cards: {len(inner.get("cards", []))}')
            return inner
    except Exception:
        pass

    print(f'[parse_json_response] all parse attempts failed, falling back to raw text. first 200 chars: {original[:200]!r}')
    return {'reply': original[:800], 'cards': []}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    处理用户消息，返回 AI 回复和结果卡片。

    Food 模式特殊处理：
    1. 用 Amap 搜索真实商户数据
    2. 将真实数据注入 Prompt 给 MiniMax 生成卡片
    """
    # 1. 意图识别
    params = parse_request(req.message)
    if req.mode:
        params["mode"] = req.mode

    mode = params.get("mode", "guide")
    location = params.get("location") or params.get("destination") or ""
    cuisine = params.get("cuisine") or ""

    # 保存 Amap 搜索结果，供后续 route enrich 使用
    attraction_results: list[dict] = []
    food_results: list[dict] = []

    # ── 美食模式：先用 Amap 搜索真实商户 ───────────────────
    if mode == "food" and amap.key:
        cuisine = params.get("cuisine") or ""
        city = _resolve_destination(req.message) or ""
        if city:
            keywords = city + (" " + cuisine if cuisine else "") + " 美食"
            amap_results = await asyncio.to_thread(
                amap.search_restaurants,
                keywords=keywords,
                city=None,
                offset=5,
            )
            if amap_results:
                amap_context = _build_amap_context(amap_results)
                params["_amap_data"] = amap_context

    # ── 攻略模式：搜索真实景点 ───────────────────
    if mode == "guide" and amap.key:
        destination = _resolve_destination(req.message) or ""
        if destination:
            attraction_results = await asyncio.to_thread(
                amap.search_attractions,
                keywords=destination,
                city=None,
                offset=8,
            )
            if attraction_results:
                attraction_context = _build_attraction_context(attraction_results)
                params["_amap_data"] = attraction_context

    # ── 行程模式：搜索真实景点 + 餐饮 ───────────────
    if mode == "trip" and amap.key:
        destination = _resolve_destination(req.message) or ""
        if destination:
            attraction_task = asyncio.to_thread(
                amap.search_attractions,
                keywords=destination,
                city=None,
                offset=6,
            )
            food_task = asyncio.to_thread(
                amap.search_restaurants,
                keywords=destination + " 美食",
                city=None,
                offset=4,
            )
            attraction_results, food_results = await asyncio.gather(attraction_task, food_task)
            ctx = _build_attraction_context(attraction_results) if attraction_results else ""
            ctx += ("\n\n" + _build_amap_context(food_results)) if food_results else ""
            if ctx:
                params["_amap_data"] = ctx

    # 2. 构建 Prompt
    messages, user_msg = build_prompt(params, req.history)

    # 3. 调用 MiniMax
    raw_response = mm.chat(
        messages,
        mode=mode,
        destination=params.get("destination", ""),
    )

    print(f"[chat] mode={mode}, raw_response[:100]: {repr(raw_response[:100])}")

    # 4. 解析 JSON 响应
    parsed = parse_json_response(raw_response)
    print(f"[chat] parsed keys: {list(parsed.keys())}, cards count: {len(parsed.get('cards', []))}")

    reply = parsed.get("reply", "")
    raw_cards = parsed.get("cards", [])

    # ── 行程/攻略模式：Markdown 模式 ─────────────────────
    # 当 JSON 解析失败或内容超长，说明 AI 返回了 Markdown 格式
    # 此时切换到 Markdown 回显，并补充真实交通路线
    is_trip_or_guide = mode in ("trip", "guide")
    is_markdown_mode = (
        is_trip_or_guide
        and raw_cards == []
        and len(raw_response) > 500
    )

    if is_markdown_mode and amap.key:
        print("[chat] Markdown mode detected, injecting real route info")
        attraction_map = _build_attraction_map(attraction_results) if attraction_results else {}
        if attraction_map:
            try:
                reply = await _inject_routes_into_markdown(reply, attraction_map, amap)
            except Exception as e:
                print(f"[chat] _inject_routes_into_markdown error: {e}")
        cards = []

    # ── 传统 JSON 卡片模式 ───────────────────
    elif raw_cards:
        # 补充真实交通路线（用真实景点坐标做名称匹配）
        attraction_map = _build_attraction_map(attraction_results) if attraction_results else {}
        if amap.key:
            try:
                raw_cards = await _enrich_routes(raw_cards, amap, attraction_map)
            except Exception as e:
                print(f"[chat] _enrich_routes error: {e}")

        # 类型安全转换
        cards = []
        for card in raw_cards:
            card_type = card.get("type")
            if card_type == "food":
                cards.append({"type": "food", "data": card.get("data", {})})
            elif card_type == "trip":
                try:
                    validated = {"type": "trip", "data": card.get("data", {})}
                    from src.models.schemas import TripCard
                    TripCard(**validated)
                    cards.append(validated)
                except Exception as e:
                    print(f"[card validation trip error] {e}")
            elif card_type == "guide":
                cards.append({"type": "guide", "data": card.get("data", {})})
    else:
        cards = []

    return ChatResponse(reply=reply, cards=cards)


def _build_attraction_context(places: list[dict]) -> str:
    """
    将 Amap 景点搜索结果格式化为文本，注入到 prompt 中。
    """
    if not places:
        return ""

    lines = ["【以下是从高德地图搜索到的真实景点信息】"]
    for i, p in enumerate(places, 1):
        name = p.get("name", "")
        addr = p.get("address", "")
        loc = p.get("location", "")  # "经度,纬度"
        typ = p.get("type", "")
        tel = p.get("tel", "")
        line = f"{i}. {name}"
        if addr and addr not in ("NULL", "undefined", ""):
            line += f"，地址：{addr}"
        if loc and loc not in ("NULL", "undefined", ""):
            line += f"，坐标：{loc}"
        if typ:
            line += f"，类型：{typ}"
        if tel:
            line += f"，电话：{tel}"
        lines.append(line)

    lines.append("【请基于以上真实景点信息生成行程/攻略。每个景点请使用上述坐标数据，后续将根据坐标自动计算交通方案。】")
    return "\n".join(lines)


def _build_amap_context(places: list[dict]) -> str:
    """
    将 Amap 搜索结果格式化为文本，注入到 prompt 中。
    """
    if not places:
        return ""

    lines = ["【以下是从高德地图搜索到的真实商户信息】"]
    for i, p in enumerate(places, 1):
        name = p.get("name", "")
        addr = p.get("address", "")
        tel = p.get("tel", "")
        rating = p.get("biz_ext", {}).get("rating", "")
        cost = p.get("biz_ext", {}).get("cost", "")
        line = f"{i}. {name}"
        if addr and addr not in ("NULL", "undefined", ""):
            line += f"，地址：{addr}"
        if cost:
            line += f"，人均：约{cost}元"
        if rating:
            line += f"，评分：{rating}分"
        if tel:
            line += f"，电话：{tel}"
        lines.append(line)

    lines.append("【请基于以上真实商户信息生成推荐回复。如果商户信息为空则说「暂时没找到合适的店」】")
    return "\n".join(lines)


def _resolve_destination(message: str) -> Optional[str]:
    """
    从用户消息中提取目的地（城市/地点）名称。
    策略：找"去""在""到"等介词后的词，支持任意城市名。
    """
    patterns = [
        r'去\s*([\u4e00-\uffff]{2,8})(?:\s|$|，|。|！|？)',
        r'在\s*([\u4e00-\uffff]{2,8})(?:\s|$|，|。|！|？)',
        r'到\s*([\u4e00-\uffff]{2,8})(?:\s|$|，|。|！|？)',
        r'\[([\u4e00-\uffff]{2,8})\]',
    ]
    for p in patterns:
        m = re.search(p, message)
        if m:
            return m.group(1)
    return None


def _build_attraction_map(places: list[dict]) -> dict[str, dict]:
    """
    从 Amap 搜索结果构建景点名称→信息映射表，
    支持精确匹配和包含匹配（景点名可能带城市前缀）。
    Returns: {normalized_name: {"location": "lng,lat", "address": "...", "name": "..."}}
    """
    attraction_map = {}
    for p in places:
        name = p.get("name", "")
        loc = p.get("location", "")
        addr = p.get("address", "")
        if not name or not loc:
            continue
        # 精确 key
        attraction_map[name] = {"location": loc, "address": addr, "name": name}
        # 去掉城市前缀后的 key（如 "杭州西湖" -> "西湖"）
        for city_prefix in ["杭州", "上海", "北京", "成都", "重庆", "广州", "深圳", "厦门", "苏州", "南京", "西安", "青岛", "大连"]:
            if name.startswith(city_prefix) and len(name) > len(city_prefix):
                short = name[len(city_prefix):]
                if short not in attraction_map:
                    attraction_map[short] = {"location": loc, "address": addr, "name": name}
    return attraction_map


async def _inject_routes_into_markdown(reply: str, attraction_map: dict[str, dict], amap: AmapService) -> str:
    """
    在 Markdown 格式的行程/攻略中，遍历相邻的景点对，用真实坐标计算最优交通方式并插入（并发）。
    """
    if not attraction_map:
        return reply

    lines = reply.split("\n")
    spot_names_in_order: list[tuple[int, str]] = []  # (line_idx, matched_map_key)

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 匹配常见行程列表格式：► / • / - / 1. / ①
        m = re.match(r'^[▶•\-\*]\s*(.+)$', stripped) or re.match(r'^\d+[．、.](.+)$', stripped)
        if m:
            spot_name = m.group(1).strip()
            matched = _match_spot_name(spot_name, attraction_map)
            if matched:
                spot_names_in_order.append((i, matched))

    # 并发查询所有相邻景点对的路线
    route_tasks = []
    for k in range(len(spot_names_in_order) - 1):
        idx1, name1 = spot_names_in_order[k]
        idx2, name2 = spot_names_in_order[k + 1]
        loc1 = attraction_map[name1]["location"]
        loc2 = attraction_map[name2]["location"]
        route_tasks.append((idx2, loc1, loc2))

    if route_tasks:
        results = await asyncio.gather(*[
            asyncio.to_thread(_get_route_between_spots, loc1, loc2, amap) for _, loc1, loc2 in route_tasks
        ])
        # 从后往前插入避免行号偏移
        for (idx2, _, _), route_info in zip(reversed(route_tasks), reversed(results)):
            if route_info:
                transport_desc = _format_transport_line(route_info)
                lines.insert(idx2 + 1, transport_desc)

    return "\n".join(lines)


def _match_spot_name(spot_name: str, attraction_map: dict[str, dict]) -> Optional[str]:
    """
    在 attraction_map 中查找与 spot_name 最匹配的景点名。
    优先精确匹配，其次去城市前缀匹配，最后包含匹配。
    """
    if spot_name in attraction_map:
        return spot_name
    # 去掉城市前缀后匹配
    for city_prefix in ["杭州", "上海", "北京", "成都", "重庆", "广州", "深圳", "厦门", "苏州", "南京", "西安", "青岛", "大连"]:
        if spot_name.startswith(city_prefix):
            short = spot_name[len(city_prefix):]
            if short in attraction_map:
                return short
    # 包含匹配
    for key in attraction_map:
        if key in spot_name or spot_name in key:
            return key
    return None


def _format_transport_line(route_info: dict) -> str:
    """将路线信息格式化为一行 Markdown"""
    strategy = route_info.get("strategy", "")
    duration = route_info.get("duration", "")
    distance = route_info.get("distance", "")
    route_str = route_info.get("route", "")
    if route_str:
        return f"  └─ {strategy} · {duration} · {route_str}"
    return f"  └─ {strategy} · {duration}（{distance}）"


def _get_route_between_spots(from_loc: str, to_loc: str, amap: AmapService) -> Optional[dict]:
    """
    调用 Amap 路线 API 获取两坐标间的交通方案。
    from_loc / to_loc: "lng,lat" 格式
    Returns: {"type": "地铁/驾车", "duration": "25分钟", "distance": "8公里", "route": "具体路线"}
    """
    # 优先公交，其次驾车
    for mode in ("transit", "driving"):
        result = amap.get_route(from_loc, to_loc, mode=mode)
        if result:
            return result
    return None


async def _enrich_routes(cards: list[dict], amap: AmapService, attraction_map: dict[str, dict]) -> list[dict]:
    """
    行程/攻略卡片生成后，对每个相邻 spot leg：
    1. 用景点名在 attraction_map 中查找真实坐标（支持名称模糊匹配）
    2. 注入坐标到每个 spot（供前端地图渲染）
    3. 调用高德路线 API 计算最优交通方式（并发）
    4. 用真实路线信息替换 transport 字段
    """
    route_tasks = []  # [(card, day_idx, spot_idx, from_loc, to_loc), ...]

    for card in cards:
        card_type = card.get("type")
        if card_type not in ("trip", "guide"):
            continue

        data = card.get("data", {})

        if card_type == "trip":
            itinerary = data.get("itinerary", [])
            for day_idx, day in enumerate(itinerary):
                spots = day.get("spots", [])
                prev_loc = None
                for spot_idx, spot in enumerate(spots):
                    # 注入坐标
                    spot_loc = _resolve_spot_location(spot, attraction_map)
                    if spot_loc:
                        spot["location"] = spot_loc
                    if spot_idx > 0 and prev_loc and spot_loc:
                        route_tasks.append((card, day_idx, spot_idx, prev_loc, spot_loc))
                    prev_loc = spot_loc or prev_loc

        elif card_type == "guide":
            spots = data.get("spots", [])
            for spot in spots:
                spot_loc = _resolve_spot_location(spot, attraction_map)
                if spot_loc:
                    spot["location"] = spot_loc

    # 并发查询所有路线
    if route_tasks:
        async def _fetch_route(from_loc, to_loc):
            return await asyncio.to_thread(_get_route_between_spots, from_loc, to_loc, amap)

        results = await asyncio.gather(*[
            _fetch_route(from_loc, to_loc) for _, _, _, from_loc, to_loc in route_tasks
        ])

        # 回填结果
        for (card, day_idx, spot_idx, _, _), route_info in zip(route_tasks, results):
            if route_info:
                day = card["data"]["itinerary"][day_idx]
                spot = day["spots"][spot_idx]
                spot["transport"] = {
                    "type": route_info.get("strategy", ""),
                    "route": route_info.get("route", f"{route_info.get('duration', '')} {route_info.get('distance', '')}"),
                    "detail": route_info.get("first_advice", ""),
                }

    return cards


def _resolve_spot_location(spot: dict, attraction_map: dict[str, dict]) -> Optional[str]:
    """
    解析 spot 的坐标：
    1. 优先用 spot 自带的 location 字段（AI 按坐标注入的）
    2. 否则用景点名在 attraction_map 中模糊匹配查找
    """
    loc = spot.get("location")
    if loc and loc not in ("估算", "", None):
        return loc
    # 用景点名匹配
    name = spot.get("name", "")
    matched_name = _match_spot_name(name, attraction_map)
    if matched_name:
        return attraction_map[matched_name]["location"]
    return None
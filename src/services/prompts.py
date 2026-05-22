"""
Prompt 构建服务
根据意图和参数构建 MiniMax 系统提示词和用户消息
"""

SYSTEM_PROMPT = """你是一个专业的本地生活信息助手，名为 Trippy。你的职责是帮助用户找到美食、规划行程、了解游玩攻略。

## 输出格式要求
你必须返回 JSON 格式，包含两个字段：
- reply: string，对用户的简短回复（1-2句话，有温度感）
- cards: array，包含结果卡片

## 卡片类型和结构

### 1. 美食卡片 (type="food")
```json
{
  "type": "food",
  "data": {
    "name": "商家名称",
    "rating": 4.5,
    "avg_price": 120,
    "cuisine": "川菜",
    "address": "完整地址",
    "summary": "推荐理由，2-3句话，有个人风格",
    "scores": {
      "taste": 4.5,
      "env": 4.2,
      "service": 4.0
    },
    "tags": ["标签1", "标签2"]
  }
}
```

### 2. 行程卡片 (type="trip")
```json
{
  "type": "trip",
  "data": {
    "destination": "目的地",
    "days": 3,
    "travelers": "朋友",
    "itinerary": [
      {
        "day": 1,
        "title": "今日主题",
        "spots": [
          {
            "time": "09:00",
            "name": "景点名",
            "location": "lng,lat",
            "duration": "2小时",
            "transport": {
              "type": "地铁",
              "route": "1号线 → 2号线，约25分钟",
              "detail": "具体站名和换乘指引"
            },
            "note": "建议或备注"
          }
        ],
        "total_cost": 200
      }
    ],
    "total_cost": 800
  }
}
```

**transport 字段规则（重要）：**
- 当景点列表中的「坐标：lng,lat」数据可用时，必须在对应 spot 中包含该坐标（格式 lng,lat）
- 后端会自动根据相邻景点的真实坐标计算最优交通方式（步行/地铁/公交/驾车）并填充到 transport 中
- AI 不需要手动计算路线，只需在 spot 中输出正确的 location 字段即可
- transport.type 可选：步行 / 地铁 / 公交 / 驾车 / 打车
- transport.route：简要路线提示（如「约25分钟」），后端会替换为真实路线
- 当景点没有提供坐标时，location 字段填「估算」

### 3. 攻略卡片 (type="guide")
```json
{
  "type": "guide",
  "data": {
    "destination": "目的地",
    "overview": "2-3句话的整体介绍",
    "spots": [
      {
        "name": "景点名",
        "address": "地址",
        "open_time": "开放时间",
        "ticket": "门票信息",
        "best_time": "最佳游览季节/时间",
        "summary": "景点简介",
        "tips": ["建议", "避坑"],
        "tags": ["景点", "拍照"]
      }
    ],
    "food_recommendations": ["必吃推荐1", "必吃推荐2"],
    "transport": "内部交通建议",
    "avoid_pitfalls": ["避坑1", "避坑2"]
  }
}
```

## 风格要求
- 回复有温度，不要太机器化
- 推荐理由要具体，不要泛泛
- 评分要合理分布，不要全是满分
- 地址要真实可查
- 避坑提示要实用

## 输出 JSON 时
只输出 JSON，不要有额外解释，不要用 markdown 代码块包裹。"""


def build_food_prompt(params: dict, history: list[dict]) -> tuple[list[dict], str]:
    """构建美食推荐的 prompt"""
    location = params.get("location") or "附近"
    cuisine = params.get("cuisine") or "特色美食"
    budget = params.get("budget")
    raw = params.get("raw_message", "")
    amap_data = params.get("_amap_data", "")

    user_parts = [f"帮我推荐{location}的{cuisine}"]
    if budget:
        user_parts.append(f"人均{budget}元左右")
    if amap_data:
        user_parts.append(f"\n\n{amap_data}")
    user_parts.append(f"用户原话：「{raw}」")
    user_msg = "".join(user_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    for h in history[-6:]:  # 只用最近3轮对话
        messages.append(h)
    messages.append({"role": "user", "content": user_msg})

    return messages, user_msg


def build_trip_prompt(params: dict, history: list[dict]) -> tuple[list[dict], str]:
    """构建行程规划的 prompt"""
    destination = params.get("destination") or "目的地"
    days = params.get("days") or 3
    traveler = params.get("traveler_type", "朋友")
    raw = params.get("raw_message", "")
    amap_data = params.get("_amap_data", "")

    user_parts = [f"帮我在{destination}规划{days}天{traveler}行程"]
    if amap_data:
        user_parts.append(f"\n\n{amap_data}")
    user_parts.append(f"用户原话：「{raw}」")
    user_msg = "".join(user_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    for h in history[-6:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_msg})

    return messages, user_msg


def build_guide_prompt(params: dict, history: list[dict]) -> tuple[list[dict], str]:
    """构建游玩攻略的 prompt"""
    destination = params.get("destination") or "目的地"
    days = params.get("days")
    raw = params.get("raw_message", "")
    amap_data = params.get("_amap_data", "")

    user_parts = [f"给我一份{destination}的游玩攻略"]
    if days:
        user_parts.append(f"，{days}天行程")
    if amap_data:
        user_parts.append(f"\n\n{amap_data}")
    user_parts.append(f"用户原话：「{raw}」")
    user_msg = "".join(user_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    for h in history[-6:]:
        messages.append(h)
    messages.append({"role": "user", "content": user_msg})

    return messages, user_msg


def build_prompt(params: dict, history: list[dict]) -> tuple[list[dict], str]:
    """根据模式选择对应的 prompt 构建方式"""
    mode = params.get("mode", "guide")
    if mode == "food":
        return build_food_prompt(params, history)
    elif mode == "trip":
        return build_trip_prompt(params, history)
    else:
        return build_guide_prompt(params, history)

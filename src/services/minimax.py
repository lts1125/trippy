"""
MiniMax API 调用服务
"""
import httpx
import json
from typing import Any, Optional
from src.config import config


# 真实目的地数据
DEST_DATA = {
    "西安": {
        "overview": "十三朝古都，中华文明发源地。兵马俑、古城墙、大雁塔诉说着千年历史，小吃美食让人流连忘返。",
        "spots": [
            {"name": "秦始皇兵马俑", "address": "西安市临潼区秦陵北路", "open_time": "08:30-18:00", "ticket": "120元", "best_time": "四季皆宜", "summary": "世界第八大奇迹，建议预约讲解", "tips": ["提前公众号预约", "建议请讲解员"]},
            {"name": "西安城墙", "address": "西安市碑林区南大街", "open_time": "08:00-22:00", "ticket": "54元", "best_time": "傍晚", "summary": "中国现存最完整的古代城垣，骑车一圈约2小时", "tips": ["推荐骑自行车游览", "傍晚去可以看到日落"]},
            {"name": "大雁塔", "address": "西安市雁塔区慈恩寺", "open_time": "09:00-17:00", "ticket": "50元", "best_time": "春秋", "summary": "玄奘法师取经归来藏经处，唐代建筑标志", "tips": ["晚上有音乐喷泉表演"]},
            {"name": "大唐不夜城", "address": "西安市雁塔区大唐不夜城", "open_time": "全天", "ticket": "免费", "best_time": "晚上", "summary": "仿唐商业街，夜景绝美，适合拍照", "tips": ["建议晚上去", "穿汉服拍照效果更佳"]},
            {"name": "回民街", "address": "西安市莲湖区北院门", "open_time": "全天", "ticket": "免费", "best_time": "傍晚", "summary": "西安小吃一条街，肉夹馍、羊肉泡馍、凉皮应有尽有", "tips": ["小吃价格比外面贵，适量即可", "回民店注意尊重习俗"]},
        ],
        "food_recommendations": ["肉夹馍", "羊肉泡馍", "凉皮", "biangbiang面", "贾三灌汤包"],
        "avoid_pitfalls": ["旺季提前预约门票", "回民街注意清真禁忌", "城墙骑行注意安全"],
        "transport": "地铁覆盖完善，推荐办一张长安通卡"
    },
    "重庆": {
        "overview": "山城雾都，火锅天堂。立体城市风貌、魔幻夜景、麻辣美食是重庆的标签。",
        "spots": [
            {"name": "解放碑", "address": "重庆市渝中区解放碑商圈", "open_time": "全天", "ticket": "免费", "best_time": "任何时候", "summary": "重庆地标，周边是商业中心", "tips": ["附近有很多小吃"]},
            {"name": "洪崖洞", "address": "重庆市渝中区嘉陵江滨江路", "open_time": "全天", "ticket": "免费", "best_time": "晚上", "summary": "吊脚楼建筑群，夜晚灯光亮起时像千与千寻", "tips": ["人流很多注意安全", "节假日提前去"]},
            {"name": "长江索道", "address": "重庆市南岸区南滨路", "open_time": "07:30-22:00", "ticket": "单程20元", "best_time": "傍晚", "summary": "重庆独特交通工具，横跨长江看两岸风光", "tips": ["公众号提前购票", "排队2小时起"]},
            {"name": "武隆天生三桥", "address": "重庆市武隆区仙女山镇", "open_time": "08:30-16:30", "ticket": "125元", "best_time": "春秋", "summary": "《变形金刚》取景地，天坑壮观", "tips": ["跟团更方便", "穿舒适的鞋"]},
        ],
        "food_recommendations": ["重庆火锅", "小面", "酸辣粉", "抄手", "串串香"],
        "avoid_pitfalls": ["火锅不要吃太辣微辣就行", "长江索道提前网上买票", "导航在重庆容易失灵"],
        "transport": "轻轨是主要出行方式，很多地方打车比公交快"
    },
    "成都": {
        "overview": "天府之国，休闲之都。熊猫、火锅、茶馆是成都的标签，生活节奏悠闲。",
        "spots": [
            {"name": "大熊猫繁育研究基地", "address": "成都市成华区外北熊猫大道1375号", "open_time": "07:30-18:00", "ticket": "58元", "best_time": "上午", "summary": "看大熊猫最佳地点，建议早上去", "tips": ["早上去熊猫更活跃", "需要3-4小时"]},
            {"name": "宽窄巷子", "address": "成都市青羊区长顺街附近", "open_time": "全天", "ticket": "免费", "best_time": "傍晚", "summary": "清朝古街道，保留了老成都风情", "tips": ["人很多", "买点伴手礼不错"]},
            {"name": "锦里", "address": "成都市武侯区武侯祠大街231号", "open_time": "全天", "ticket": "免费", "best_time": "晚上", "summary": "仿古商业街，夜晚红灯笼很美", "tips": ["小吃多", "比宽窄巷子更商业化"]},
            {"name": "都江堰", "address": "成都市都江堰市公园路", "open_time": "08:00-18:00", "ticket": "90元", "best_time": "四季", "summary": "古代水利工程，世界文化遗产", "tips": ["请讲解", "可以玩半天"]},
        ],
        "food_recommendations": ["火锅", "串串", "担担面", "龙抄手", "赖汤圆", "兔头"],
        "avoid_pitfalls": ["火锅微微辣就好", "熊猫基地早上去", "宽窄巷子别买贵的东西"],
        "transport": "地铁覆盖好，天府通卡很方便"
    },
    "厦门": {
        "overview": "海上花园，文艺清新。鼓浪屿、厦门大学、海滩构成了这座海滨城市的名片。",
        "spots": [
            {"name": "鼓浪屿", "address": "厦门市思明区鼓浪屿", "open_time": "全天", "ticket": "免费（上岛需船票35元）", "best_time": "春秋", "summary": "世界遗产，钢琴之岛，漫步在老建筑间很有情调", "tips": ["提前买船票", "不要周末去", "建议住一晚"]},
            {"name": "厦门大学", "address": "厦门市思明区思明南路422号", "open_time": "需预约", "ticket": "免费", "best_time": "任何时候", "summary": "中国最美大学之一，芙蓉隧道很有名", "tips": ["必须预约", "带身份证"]},
            {"name": "曾厝垵", "address": "厦门市思明区环岛南路", "open_time": "全天", "ticket": "免费", "best_time": "傍晚", "summary": "文艺小渔村，小吃和民宿很多", "tips": ["小吃一般", "住一晚体验更好"]},
            {"name": "南普陀寺", "address": "厦门市思明区思明南路515号", "open_time": "08:00-17:30", "ticket": "免费", "best_time": "早上", "summary": "厦门著名佛教寺庙，香火旺盛", "tips": ["吃一碗素面", "爬山看厦门全景"]},
        ],
        "food_recommendations": ["沙茶面", "姜母鸭", "海蛎煎", "土笋冻", "花生汤"],
        "avoid_pitfalls": ["鼓浪屿船票提前买", "旺季酒店价格翻倍", "不要在曾厝垵吃海鲜"],
        "transport": "公交+打车比较方便，环岛路适合租电动车"
    },
    "杭州": {
        "overview": "人间天堂，西湖美景。茶园、古镇、互联网城市气质让杭州兼具古典与现代。",
        "spots": [
            {"name": "西湖", "address": "杭州市西湖区西湖风景名胜区", "open_time": "全天", "ticket": "免费", "best_time": "四季", "summary": "世界文化遗产，十景各异，建议租自行车环湖", "tips": ["苏堤春晓、断桥残雪必去", "绕湖一圈约2小时"]},
            {"name": "灵隐寺", "address": "杭州市西湖区灵隐路1号", "open_time": "07:00-18:00", "ticket": "75元（入园）", "best_time": "清晨", "summary": "千年古刹，香火旺盛，景色幽深", "tips": ["请香要花钱", "可以爬北高峰"]},
            {"name": "宋城", "address": "杭州市西湖区之江路148号", "open_time": "09:00-21:00", "ticket": "320元（含演出）", "best_time": "下午+晚上", "summary": "大型宋文化主题公园，《宋城千古情》演出很震撼", "tips": ["演出票要提前订", "不建议夏天去"]},
            {"name": "龙井村", "address": "杭州市西湖区龙井路69号", "open_time": "全天", "ticket": "免费", "best_time": "春季", "summary": "茶山环绕，品茶休闲的好地方", "tips": ["买茶要小心", "农家乐很惬意"]},
        ],
        "food_recommendations": ["东坡肉", "龙井虾仁", "叫化鸡", "片儿川", "葱包烩"],
        "avoid_pitfalls": ["西湖尽量别骑多人自行车", "灵隐寺山路注意安全", "龙井茶别买太贵的"],
        "transport": "地铁覆盖主城区，西湖边骑车最舒服"
    },
}


class MiniMaxService:
    """MiniMax ChatCompletion 调用封装"""

    def __init__(self):
        self.api_key = config.MINIMAX_API_KEY
        self.base_url = config.MINIMAX_BASE_URL
        self.model = config.MINIMAX_MODEL

    def chat(
        self,
        messages: list[dict],
        mode: str = "guide",
        destination: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        发送对话请求到 MiniMax，返回 content 字符串。
        如果未配置 API_KEY，返回模拟数据。
        """
        if not self.api_key or self.api_key in ("***", "your_api_key_here", ""):
            return self._mock_response(messages, mode, destination)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            # Anthropic compatible: content is array, find text block
            content_blocks = data.get("content", [])
            for block in content_blocks:
                if block.get("type") == "text":
                    return block["text"]
            # Fallback: return thinking or first block as text
            if content_blocks:
                b = content_blocks[0]
                if b.get("type") == "thinking":
                    return b.get("thinking", "")[:500]  # truncate thinking
                return str(b)
            return ""

    def _mock_response(self, messages: list[dict], mode: str = "guide", destination: str = "") -> str:
        """
        未配置 API Key 时，返回结构化 JSON 模拟数据。
        智能解析真实目的地，返回真实数据。
        """
        last_msg = messages[-1]["content"] if messages else ""

        # 从消息中检测真实目的地
        found_dest = destination
        if not found_dest:
            for dest in DEST_DATA.keys():
                if dest in last_msg:
                    found_dest = dest
                    break

        # 检测模式（优先用传入的 mode）
        active_mode = mode

        # ── 美食模式 ─────────────────────────────────────
        if active_mode == "food":
            # 简单食物 mock
            return json.dumps({
                "reply": f"好的，这是我在{found_dest or '本地'}找到的餐厅推荐：",
                "cards": [
                    {
                        "type": "food",
                        "data": {
                            "name": "老城厢酒家",
                            "rating": 4.5,
                            "avg_price": 120,
                            "cuisine": "本地菜",
                            "address": f"{found_dest or '市中心'}区中山路128号",
                            "summary": "本地人常去的老字号，价格实惠，味道正宗，适合朋友聚餐。",
                            "scores": {"taste": 4.6, "env": 4.2, "service": 4.3},
                            "tags": ["老字号", "本地菜", "高性价比"]
                        }
                    },
                    {
                        "type": "food",
                        "data": {
                            "name": "味道工厂",
                            "rating": 4.3,
                            "avg_price": 85,
                            "cuisine": "融合菜",
                            "address": f"{found_dest or '市中心'}区解放路56号",
                            "summary": "创意融合菜，环境好，适合约会或者商务宴请。",
                            "scores": {"taste": 4.2, "env": 4.6, "service": 4.0},
                            "tags": ["创意菜", "环境好", "约会"]
                        }
                    }
                ]
            })

        # ── 行程模式 ─────────────────────────────────────
        if active_mode == "trip":
            if found_dest and found_dest in DEST_DATA:
                dest_info = DEST_DATA[found_dest]
                spots = dest_info["spots"][:4]
            else:
                spots = [
                    {"time": "09:00", "name": "市中心广场", "duration": "1小时", "transport": "步行", "note": "先了解一下城市中心"},
                    {"time": "11:00", "name": "历史博物馆", "duration": "2小时", "transport": "公交", "note": "了解当地历史文化"},
                    {"time": "14:00", "name": "特色街区", "duration": "3小时", "transport": "步行", "note": "逛逛当地最有特色的街道"},
                    {"time": "18:00", "name": "美食街", "duration": "2小时", "transport": "步行", "note": "品尝当地特色美食"},
                ]
            return json.dumps({
                "reply": f"好的，这是为你规划的前往{found_dest or '目的地'}的行程：",
                "cards": [
                    {
                        "type": "trip",
                        "data": {
                            "destination": found_dest or "目的地",
                            "days": 3,
                            "travelers": "朋友",
                            "itinerary": [
                                {
                                    "day": 1,
                                    "title": "初识目的地",
                                    "spots": spots[:2],
                                    "total_cost": 200
                                },
                                {
                                    "day": 2,
                                    "title": "深度探索",
                                    "spots": [
                                        {"time": "09:00", "name": "著名景点A", "duration": "3小时", "transport": "打车", "note": "提前预约门票"},
                                        {"time": "14:00", "name": "当地特色体验", "duration": "2小时", "transport": "步行", "note": "融入当地生活"},
                                        {"time": "18:00", "name": "夜景打卡地", "duration": "2小时", "transport": "地铁", "note": "傍晚去最好"},
                                    ],
                                    "total_cost": 300
                                },
                                {
                                    "day": 3,
                                    "title": "休闲收尾",
                                    "spots": [
                                        {"time": "09:00", "name": "早茶/早市", "duration": "2小时", "transport": "步行", "note": "体验当地早餐文化"},
                                        {"time": "12:00", "name": "购物中心", "duration": "2小时", "transport": "打车", "note": "买伴手礼"},
                                    ],
                                    "total_cost": 150
                                }
                            ],
                            "total_cost": 650
                        }
                    }
                ]
            })

        # ── 攻略模式（默认） ─────────────────────────────
        if found_dest and found_dest in DEST_DATA:
            dest_info = DEST_DATA[found_dest]
            spots = dest_info["spots"]
            return json.dumps({
                "reply": f"好的，我来给你介绍{found_dest}的游玩攻略：",
                "cards": [
                    {
                        "type": "guide",
                        "data": {
                            "destination": found_dest,
                            "overview": dest_info["overview"],
                            "spots": spots,
                            "food_recommendations": dest_info["food_recommendations"],
                            "transport": dest_info["transport"],
                            "avoid_pitfalls": dest_info["avoid_pitfalls"]
                        }
                    }
                ]
            })

        # 无目的地时返回通用数据
        return json.dumps({
            "reply": f"好的，我来帮您了解这个地方的信息：",
            "cards": [
                {
                    "type": "guide",
                    "data": {
                        "destination": last_msg[:20] or "目的地",
                        "overview": "这里风景优美，气候宜人，是非常值得一去的旅行目的地。建议提前做好规划，安排好交通和住宿。",
                        "spots": [
                            {"name": "主要景点", "address": "市中心", "open_time": "全天", "ticket": "免费", "best_time": "春秋", "summary": "当地最著名的景点，建议安排足够时间细细游览。", "tips": ["建议提前查看天气", "节假日人流量大，建议错峰"], "tags": ["景点", "拍照"]},
                            {"name": "特色体验", "address": "景区内", "open_time": "09:00-18:00", "ticket": "50元", "best_time": "上午", "summary": "非常具有当地特色的体验项目，不容错过。", "tips": ["建议提前购票", "穿舒适的鞋子"], "tags": ["体验", "文化"]},
                        ],
                        "food_recommendations": ["特色美食A", "特色美食B", "街边小吃C"],
                        "transport": "建议乘坐公共交通或包车出行",
                        "avoid_pitfalls": ["节假日提前预约门票", "注意防晒", "带好随身物品"]
                    }
                }
            ]
        })
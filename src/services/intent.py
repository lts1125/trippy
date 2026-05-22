"""
意图识别服务
从用户消息中提取关键参数并判断模式
"""
import re
from typing import Literal, Optional


# 模式关键词
MODE_KEYWORDS = {
    "food": ["吃", "美食", "餐厅", "饭馆", "川菜", "火锅", "烧烤", "日料", "早茶", "午餐", "晚餐", "早餐", "外卖", "附近", "推荐", "好吃", "哪家"],
    "trip": ["行程", "天", "几天", "规划", "安排", "旅游", "游玩", "自由行", "自助游", "旅行", "亲子", "情侣", "朋友", "自由行"],
    "guide": ["攻略", "景点", "旅游", "观光", "打卡", "路线", "必去", "推荐去", "介绍", "博物馆", "公园", "古镇", "海滩", "爬山"],
}


def extract_location(message: str) -> Optional[str]:
    """从消息中提取地点"""
    patterns = [
        r"在(.+?)想",
        r"去(.+?)玩",
        r"去(.+?)吃",
        r"到(.+?)(?:找|吃|玩|去|有)",
        r"^(.{2,6})(?:吃|玩|去)",
        r"在(.+?)(?:附近|有什么)",
    ]
    for pattern in patterns:
        m = re.search(pattern, message)
        if m:
            return m.group(1).strip()
    return None


def extract_days(message: str) -> Optional[int]:
    """从消息中提取天数"""
    patterns = [
        r"(\d+)天(\d+)?夜?",
        r"(\d+)天",
        r"(\d+)晚",
        r"玩(\d+)天",
    ]
    for pattern in patterns:
        m = re.search(pattern, message)
        if m:
            return int(m.group(1))
    return None


def extract_budget(message: str) -> Optional[int]:
    """从消息中提取预算"""
    patterns = [
        r"人均\s*(\d+)",
        r"预算\s*(\d+)",
        r"(\d+)\s*元",
        r"不超过\s*(\d+)",
        r"(\d+)块",
    ]
    for pattern in patterns:
        m = re.search(pattern, message)
        if m:
            return int(m.group(1))
    return None


def extract_cuisine(message: str) -> Optional[str]:
    """从消息中提取菜系"""
    cuisines = [
        "川菜", "湘菜", "粤菜", "鲁菜", "苏菜", "浙菜", "闽菜", "徽菜",
        "火锅", "烧烤", "日料", "寿司", "刺身", "韩式", "泰国菜", "越南菜",
        "西餐", "意大利菜", "法餐", "印度菜", "新疆菜", "东北菜", "北京烤鸭",
        "自助餐", "快餐", "小吃", "早茶", "甜品", "咖啡", "川菜", "麻辣",
    ]
    for cuisine in cuisines:
        if cuisine in message:
            return cuisine
    return None


def extract_traveler_type(message: str) -> str:
    """从消息中提取出行类型"""
    if any(k in message for k in ["亲子", "小孩", "孩子", "小朋友", "儿童"]):
        return "亲子"
    elif any(k in message for k in ["情侣", "夫妻", "蜜月", "浪漫"]):
        return "情侣"
    elif any(k in message for k in ["朋友", "闺蜜", "兄弟", "同学", "同事"]):
        return "朋友"
    elif any(k in message for k in ["一个人", "独自", "独行", "solo"]):
        return "独行"
    return "朋友"  # 默认


def extract_destination(message: str) -> Optional[str]:
    """从消息中提取目的地"""
    # 优先用地点提取
    loc = extract_location(message)
    if loc:
        return loc

    # 常见目的地关键词
    destinations = [
        "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "苏州",
        "南京", "西安", "厦门", "三亚", "青岛", "大连", "丽江", "大理",
        "昆明", "长沙", "武汉", "天津", "郑州", "济南", "合肥", "南昌",
        "乌镇", "西塘", "平遥", "凤凰", "阳朔", "桂林", "黄山", "泰山",
        "日本", "泰国", "韩国", "新加坡", "马尔代夫", "欧洲", "美国",
    ]
    for dest in destinations:
        if dest in message:
            return dest
    return None


def detect_mode(message: str) -> Literal["food", "trip", "guide"]:
    """
    根据消息内容判断用户意图模式。
    优先级：food > trip > guide
    """
    # 检查模式关键词
    for mode, keywords in MODE_KEYWORDS.items():
        if any(kw in message for kw in keywords):
            return mode

    # 隐含意图判断
    if any(k in message for k in ["附近", "这家", "那家", "餐厅"]):
        return "food"
    if any(k in message for k in ["玩", "游", "行程", "天"]):
        return "trip"
    return "guide"


def parse_request(message: str) -> dict:
    """
    解析用户消息，返回结构化参数。
    """
    mode = detect_mode(message)
    params = {
        "mode": mode,
        "location": extract_location(message),
        "destination": extract_destination(message),
        "days": extract_days(message),
        "budget": extract_budget(message),
        "cuisine": extract_cuisine(message),
        "traveler_type": extract_traveler_type(message),
        "raw_message": message,
    }
    return params

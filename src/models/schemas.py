"""
Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Literal, Union, List, Dict, Any, Optional


# ── 请求模型 ──────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入的消息")
    mode: Literal["food", "trip", "guide"] = Field(
        default="guide", description="模式：food=美食 trip=行程 guide=攻略"
    )
    history: List[Dict[str, Any]] = Field(
        default_factory=list, description="对话历史"
    )


# ── 响应卡片模型 ──────────────────────────────────────

class FoodScore(BaseModel):
    taste: float = Field(default=0, description="口味评分 0-5")
    env: float = Field(default=0, description="环境评分 0-5")
    service: float = Field(default=0, description="服务评分 0-5")


class FoodCardData(BaseModel):
    name: str = ""
    rating: float = Field(default=0, description="综合评分 0-5")
    avg_price: int = Field(default=0, description="人均价格")
    cuisine: str = Field(default="", description="菜系")
    address: str = Field(default="", description="地址")
    summary: str = Field(default="", description="推荐理由")
    scores: FoodScore = Field(default_factory=FoodScore)
    tags: List[str] = Field(default_factory=list, description="标签")


class FoodCard(BaseModel):
    type: Literal["food"] = "food"
    data: FoodCardData


class TripSpot(BaseModel):
    time: str = Field(default="", description="建议时间，如 09:00")
    name: str = Field(default="", description="景点/活动名")
    duration: str = Field(default="", description="建议时长，如 2小时")
    transport: Union[str, dict] = Field(default="", description="交通方式：字符串或 {type, route, detail} 结构")
    note: str = Field(default="", description="备注")
    location: Optional[str] = Field(default="", description="景点坐标，经度,纬度格式")


class TripDayData(BaseModel):
    day: int = Field(default=1, description="第几天")
    title: str = Field(default="", description="今日主题，如 美食之旅")
    spots: List[TripSpot] = Field(default_factory=list)
    total_cost: int = Field(default=0, description="今日总花费估算")


class TripCardData(BaseModel):
    destination: str = Field(default="", description="目的地")
    days: int = Field(default=1, description="总天数")
    travelers: str = Field(default="朋友", description="出行类型")
    itinerary: List[TripDayData] = Field(default_factory=list)
    total_cost: int = Field(default=0, description="总花费估算")


class TripCard(BaseModel):
    type: Literal["trip"] = "trip"
    data: TripCardData


class GuideSpotData(BaseModel):
    name: str = Field(default="", description="景点名")
    address: str = Field(default="", description="地址")
    open_time: str = Field(default="", description="开放时间")
    ticket: str = Field(default="", description="门票信息")
    best_time: str = Field(default="", description="最佳游览时间")
    summary: str = Field(default="", description="简介")
    tips: List[str] = Field(default_factory=list, description="避坑提示")
    tags: List[str] = Field(default_factory=list, description="标签")
    location: Optional[str] = Field(default="", description="景点坐标，经度,纬度格式")


class GuideCardData(BaseModel):
    destination: str = Field(default="", description="目的地")
    overview: str = Field(default="", description="整体介绍")
    spots: List[GuideSpotData] = Field(default_factory=list)
    food_recommendations: List[str] = Field(default_factory=list, description="必吃推荐")
    transport: str = Field(default="", description="内部交通")
    avoid_pitfalls: List[str] = Field(default_factory=list, description="总体避坑")


class GuideCard(BaseModel):
    type: Literal["guide"] = "guide"
    data: GuideCardData


# ── 统一响应 ─────────────────────────────────────────

class ChatResponse(BaseModel):
    reply: str = Field(default="", description="AI 文字回复")
    cards: List[Union[FoodCard, TripCard, GuideCard]] = Field(default_factory=list)

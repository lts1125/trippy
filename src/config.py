"""
Trippy 配置管理
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # MiniMax API
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7-32K")

    # 高德地图 API（预留）
    AMAP_KEY = os.getenv("AMAP_KEY", "")

    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "18790"))

    # 模式
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"


config = Config()

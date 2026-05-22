"""
Trippy — FastAPI 入口
"""
import os
import sys

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.routers.chat import router as chat_router

app = FastAPI(title="Trippy", description="信息聚合助手", version="0.1.0")

# 注册路由
app.include_router(chat_router)


@app.get("/")
async def root():
    """重定向到前端页面"""
    return RedirectResponse(url="/static/index.html")


@app.get("/api/modes")
async def modes():
    """返回三种模式的描述"""
    return {
        "modes": [
            {
                "id": "food",
                "label": "🍜 美食推荐",
                "description": "输入地点、菜系、预算，获取餐厅推荐",
                "examples": [
                    "上海想吃川菜，人均150",
                    "附近有什么好吃的火锅",
                    "广州早茶推荐"
                ]
            },
            {
                "id": "trip",
                "label": "✈️ 行程安排",
                "description": "输入目的地和天数，获取定制行程",
                "examples": [
                    "重庆3天2夜亲子游",
                    "苏州2天文艺青年行程",
                    "成都5天吃货之旅"
                ]
            },
            {
                "id": "guide",
                "label": "🗺️ 游玩攻略",
                "description": "输入目的地，获取景点+美食+交通指南",
                "examples": [
                    "厦门鼓浪屿攻略",
                    "带孩子去北京玩5天",
                    "重庆3日网红打卡路线"
                ]
            }
        ]
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "trippy"}


# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    from src.config import config
    uvicorn.run("src.main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)

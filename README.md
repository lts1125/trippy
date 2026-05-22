# Trippy - 智能旅行助手

基于 AI 的本地生活信息助手，帮你找美食、规划行程、了解游玩攻略。

## 功能

- **美食推荐**：输入地点和菜系，获取真实商户推荐（集成高德地图）
- **行程规划**：输入目的地和天数，自动生成带地图的行程卡片
- **游玩攻略**：查询目的地，获取景点、美食、交通一站式指南
- **地图可视化**：行程卡片内嵌 Leaflet 地图，显示景点位置和推荐路线
- **搜索历史**：本地存储搜索记录，支持快速重新查询

## 技术栈

- **后端**：Python + FastAPI
- **前端**：原生 HTML/JS/CSS + Leaflet.js
- **AI 模型**：MiniMax
- **地图服务**：高德地图 API（地点搜索 + 路线规划）

## 安装

```bash
# 克隆仓库
git clone https://github.com/lts1125/trippy.git
cd trippy

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 MINIMAX_API_KEY 和 AMAP_KEY

# 启动服务
python -m uvicorn src.main:app --reload --port 18790
```

## 环境变量

复制 `.env.example` 为 `.env` 并填写：

| 变量 | 说明 |
|------|------|
| `MINIMAX_API_KEY` | MiniMax API Key |
| `AMAP_KEY` | 高德地图 Web服务 Key |

## 使用

浏览器打开 `http://localhost:18790`，选择模式后输入即可：

- `上海想吃川菜，人均150` -> 美食推荐
- `帮我规划一个杭州3天2夜的行程` -> 行程规划
- `厦门鼓浪屿有什么必去的景点？` -> 游玩攻略

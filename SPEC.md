# Trippy — 信息聚合助手

> 基于 MiniMax 大模型 + OpenClaw Agent 架构的信息聚合助手，提供美食推荐、出行行程安排、游玩攻略等本地生活服务。

---

## 1. Concept & Vision

Trippy 是一个有**生活气息**的 AI 助手，不像搜索引擎那样冰冷，而是像一个本地的朋友，帮你做选择、整理信息、规划行程。它的回答不是干巴巴的列表，而是带温度的推荐——"这家店我去过，烤鱼确实不错，但周末排队太恐怖了"。

交互风格：简洁卡片式输出，对话式交互，支持多轮追问和调整。

---

## 2. Design Language

### 色彩系统
```
Primary:     #1E88E5  (科技蓝 - 主按钮、标题)
Secondary:   #FF7043  (暖橙色 - 美食标签、重点强调)
Accent:      #26A69A  (薄荷绿 - 出行/交通相关)
Background:  #F5F7FA  (浅灰白 - 页面背景)
Surface:     #FFFFFF  (卡片背景)
Text:        #1A1A2E  (深色正文)
Text-muted:  #6B7280  (次要文字)
Border:      #E5E7EB  (卡片边框)
```

### 字体
- 中文：`"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
- 数字/英文：`"SF Pro Display", "Roboto", monospace`
- 代码：`"JetBrains Mono", "Fira Code", monospace`

### 卡片设计
- 圆角：12px
- 阴影：`0 2px 8px rgba(0,0,0,0.08)`
- 内边距：16px ~ 20px
- 间距：相邻卡片间距 12px

### 动画
- 卡片进入：`opacity 0→1, translateY 8px→0, 300ms ease-out`
- 加载状态：骨架屏 shimmer 动画
- 按钮点击：`scale 0.96→1, 100ms`

---

## 3. Layout & Structure

### 页面结构
```
┌─────────────────────────────────────────────┐
│  Header: Logo + 模式切换标签 (美食/行程/攻略)  │
├─────────────────────────────────────────────┤
│                                             │
│  Chat Area: 对话流 + 结果卡片                 │
│  (用户消息 右对齐，助手消息 左对齐)             │
│                                             │
├─────────────────────────────────────────────┤
│  Input Area: 文本输入框 + 发送按钮            │
└─────────────────────────────────────────────┘
```

### 模式标签
- 🍜 **美食推荐**：输入地点/菜系/预算，返回商家列表 + 推荐理由
- ✈️ **行程安排**：输入目的地+天数+偏好，返回每日行程表
- 🗺️ **游玩攻略**：输入目的地，返回景点/美食/交通/避坑指南

### 响应卡片类型
- `food_card`：商家名、评分、均价、标签、简评、评分分布
- `trip_card`：每日时间线，每站景点+时长+交通方式
- `guide_card`：景点名、简介、最佳游览时间、门票、避坑提示

---

## 4. Features & Interactions

### 4.1 美食推荐
**输入格式（支持自然语言）**：
- `"上海想吃川菜，人均150"`
- `"附近有什么好吃的火锅"`
- `"广州早茶推荐，不超过100块"`

**输出**：3-5 个商家卡片，按匹配度排序

**追问支持**：
- "第二个贵吗？" → 返回价格详情
- "有没有更便宜的？" → 重新筛选
- "帮我预约" → 调用预订接口

### 4.2 行程安排
**输入格式**：
- `"重庆3天2夜亲子游，小孩5岁"`
- `"苏州2天，文艺青年，喜欢拍照"`
- `"成都5天，吃货行程"`

**输出**：按天分组的时间线行程表，每项包含景点名、建议时长、交通、备注

**交互**：
- "把第三天换成室内活动" → 局部修改
- "生成分享图片" → 输出行程卡片图
- "导出到日历" → 生成 .ics 文件

### 4.3 游玩攻略
**输入格式**：
- `"厦门鼓浪屿攻略"`
- `"带孩子去北京玩5天"`
- `"重庆3日游，网红打卡路线"`

**输出**：景点详情卡片 + 实用信息（门票/开放时间/建议时长/防坑提示）

### 4.4 通用交互
- **清空对话**：header 右角按钮
- **复制内容**：点击卡片右上角复制图标
- **加载状态**：骨架屏，不显示 loading 动画
- **错误处理**：卡片显示友好提示 + 重试按钮
- **空状态**：显示使用引导 + 示例问题

---

## 5. Component Inventory

### 5.1 MessageBubble
- 用户消息：蓝色背景 (#1E88E5)，白色文字，右对齐
- 助手消息：白色背景卡片，左对齐，带头像
- 状态：normal / loading（骨架屏）/ error

### 5.2 ResultCard
- 通用卡片容器：圆角白卡 + 阴影
- 子类：FoodCard / TripDayCard / GuideCard
- 右上角：复制按钮、展开按钮（长内容）

### 5.3 FoodCard
- 商家名（大字）+ 评分星级
- 均价、人均、菜系标签
- 简评（2-3句话）
- 评分分布柱状图（口味/环境/服务）

### 5.4 TripDayCard
- 日期标签（第一天/第二天...）
- 时间线布局，每站：时间 + 景点名 + 时长 + 交通图标
- 当日总花费估算

### 5.5 GuideCard
- 景点封面图（占位图，无版权问题）
- 景点名、地址、开放时间、门票
- 避坑提示（黄色标签）
- 相关美食/购物推荐

### 5.6 InputBar
- 圆角输入框，带 placeholder
- 右侧发送按钮（图标）
- 支持回车发送

### 5.7 ModeTab
- 三个标签，当前选中态：下划线 + 颜色变化
- 切换动画：下划线滑动

### 5.8 SuggestionPills
- 3个快速入口按钮："附近美食" "帮我规划" "查个攻略"
- 点击直接带入输入框

---

## 6. Technical Approach

### 6.1 系统架构
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   FastAPI    │────▶│   MiniMax    │
│   (HTML/CSS) │◀────│   Backend    │────▶│   API        │
└──────────────┘     └──────┬───────┘     └──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Data Sources   │
                    │  (高德/大众点评) │
                    └─────────────────┘
```

### 6.2 技术栈
- **后端**：Python 3.11 + FastAPI + uvicorn
- **AI 层**：MiniMax API (chatcompletion)
- **数据获取**：高德地图 API、腾讯地图 API（预留）
- **前端**：纯 HTML/CSS/JS（无框架依赖），CDN 加载
- **Agent 调度**：OpenClaw Skill（可选，第二阶段集成）

### 6.3 API 设计

#### POST /api/chat
**Request**:
```json
{
  "message": "上海想吃川菜，人均150",
  "mode": "food",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response**:
```json
{
  "cards": [
    {
      "type": "food",
      "data": {
        "name": "xxx",
        "rating": 4.5,
        "avg_price": 120,
        "cuisine": "川菜",
        "summary": "...",
        "scores": {"taste": 4.5, "env": 4.2, "service": 4.0}
      }
    }
  ],
  "reply": "这是我在上海找到的..."
}
```

#### GET /api/modes
返回三个模式的描述和示例问题

#### GET /api/health
健康检查

### 6.4 数据模型

```python
class FoodRequest(BaseModel):
    message: str
    location: str | None  # 自动从消息提取
    cuisine: str | None
    budget: int | None

class TripRequest(BaseModel):
    destination: str
    days: int
    travelers: str  # "亲子" / "情侣" / "独行" / "朋友"
    preferences: list[str]  # ["拍照", "美食", "慢节奏"]

class GuideRequest(BaseModel):
    destination: str
    days: int | None
    focus: list[str]  # ["景点" , "美食", "购物"]
```

### 6.5 Prompt 设计

**意图识别 Prompt**（系统级）：
> 你是一个信息聚合助手，用户会输入旅游/美食相关的需求。你需要判断用户意图并提取关键参数...

**美食推荐 Prompt**：
> 用户想要在{location}寻找{cuisine}，预算{price}...

**行程规划 Prompt**：
> 用户计划去{destination}，{days}天，类型是{travelers}...

**攻略生成 Prompt**：
> 用户需要一份{ destination}的游玩攻略，重点关注：{focus}...

### 6.6 项目目录结构

```
trippy/
├── SPEC.md
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py             # 配置管理
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py          # /api/chat
│   │   └── health.py        # /api/health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intent.py        # 意图识别
│   │   ├── minimax.py       # MiniMax API 调用
│   │   ├── food.py          # 美食数据服务
│   │   ├── trip.py          # 行程规划服务
│   │   └── guide.py         # 攻略生成服务
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic 模型
│   └── utils/
│       ├── __init__.py
│       └── extract.py       # 参数提取工具
├── static/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── data/
    └── sample_food.json     # 测试数据
```

---

## 7. Milestones

| 阶段 | 内容 | 目标 |
|------|------|------|
| M1 | 项目框架 + 纯 Prompt 版本 | 能跑通对话，不调真实 API |
| M2 | 接入 MiniMax API | AI 生成质量可用 |
| M3 | 美食推荐功能完成 | 展示真实卡片 |
| M4 | 行程规划功能完成 | 时间线输出 |
| M5 | 游玩攻略功能完成 | 景点卡片输出 |
| M6 | 前端页面美化 | 设计稿落地 |
| M7 | OpenClaw Skill 封装 | 可以通过自然语言调用 |

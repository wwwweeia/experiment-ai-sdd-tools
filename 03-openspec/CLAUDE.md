# AI Prompt Lab — 项目上下文

AI 智能体管理平台。后端 FastAPI + SQLAlchemy，前端 Vue 3 + Element Plus。

## 项目结构

```
backend/
├── app/main.py           # FastAPI 入口
├── app/core/             # 配置 & 数据库
├── app/models/entity.py  # 数据模型（Model, Prompt, Agent, Skill）
├── app/api/v1/           # API 端点
├── app/services/         # 业务逻辑
└── app/schemas/          # Pydantic schemas

frontend/
├── src/views/            # 页面组件
├── src/stores/           # Pinia 状态管理
├── src/api/              # HTTP 客户端
└── src/router/           # 路由配置
```

## 启动命令

```bash
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

## 已实现

- Model CRUD API（完整）
- Agent/Prompt/Skill 只有数据模型，没有 API
- 前端：首页统计 + Prompt 列表页

## 业务规则

- Agent 状态机：DRAFT → ACTIVE → INACTIVE
- Agent 需关联 Model 和 Prompt 才能激活
- API 响应格式：`{"code": 0, "data": ..., "message": "..."}`

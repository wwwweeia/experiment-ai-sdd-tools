# AI Prompt Lab

AI 智能体管理平台。管理 Model、Prompt、Agent、Skill 四个核心实体。

## 技术栈

- **后端**：FastAPI + SQLAlchemy 2.x + SQLite
- **前端**：Vue 3 + Element Plus + Pinia + Vite
- **测试**：Playwright E2E

## 启动

```bash
# 后端
cd backend
pip install -r requirements.txt
python scripts/seed.py
uvicorn app.main:app --reload   # http://localhost:8000

# 前端
cd frontend
npm install
npm run dev                     # http://localhost:5173

# E2E 测试
cd e2e
npm install
npx playwright install chromium
npm test
```

## 业务实体

- **Model**：LLM 模型配置（GPT-4、Claude 等）
- **Prompt**：提示词模板，支持变量和标签
- **Agent**：绑定 Model + Prompt 的智能体，状态机 DRAFT → ACTIVE → INACTIVE
- **Skill**：Agent 可调用的工具能力

## 已实现功能

- Model CRUD API
- Prompt 列表页面（前端）
- 首页统计展示
- E2E 测试（首页 + Prompt 列表）

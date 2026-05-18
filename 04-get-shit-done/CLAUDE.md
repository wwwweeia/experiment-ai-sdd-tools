# AI Prompt Lab — 实验项目

> **这是一个工具对比实验项目**，不是生产项目。你需要基于下方需求完成功能开发。请按照你所使用工具的推荐流程来工作。

## 项目结构

```
backend/
├── app/main.py              # FastAPI 入口（已注册 Prompt 路由，Agent 路由待注册）
├── app/core/database.py     # 数据库配置（SQLite）
├── app/models/entity.py     # 数据模型（Model, Prompt, Agent, Skill）
├── app/api/v1/endpoints.py  # API 端点（Model + Prompt CRUD 已实现）
├── app/api/v1/router.py     # 路由注册
├── app/services/            # 业务逻辑（model_service.py + prompt_service.py 已实现）
└── app/schemas/schema.py    # Pydantic schemas（AgentCreate/AgentRead 已有基础定义）

frontend/
├── src/views/PromptList.vue  # Prompt 列表页（参考模式）
├── src/views/AgentList.vue   # Agent 占位页面（待完善，当前仅 15 行）
├── src/stores/prompt.js      # Prompt store（参考模式）
├── src/api/prompts.js        # Prompt API 客户端（参考模式）
└── src/router/index.js       # 路由（Agent 路由已注册）

e2e/                          # Playwright E2E 测试
```

## 启动命令

```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload   # http://localhost:8000

# 前端
cd frontend && npm install && npm run dev   # http://localhost:5173
```

## 已实现功能

- **Model CRUD API**：完整，参考 `endpoints.py` + `model_service.py`
- **Prompt CRUD API**：完整，参考 `endpoints.py` + `prompt_service.py`
- **Agent 数据模型**：`entity.py` 中已有 `Agent` 和 `AgentStatus(DRAFT/ACTIVE/INACTIVE)` 定义，但**无 API、无 Service、前端仅占位**
- **Skill 数据模型**：`entity.py` 中已有，关联 Agent（多对一）
- **前端**：首页统计 + Prompt 列表页 + Agent 导航入口（指向占位页面）

## 本次需求：Agent 激活/停用功能

### 业务规则

1. **DRAFT → ACTIVE**：必须已关联有效的 Model 和 Prompt
2. **ACTIVE → INACTIVE**：直接允许，关联的 Skill 标记为不可用
3. **INACTIVE → ACTIVE**：重新检查 Model 和 Prompt 是否仍有效
4. **ACTIVE 状态不可删除**：必须先停用才能删除
5. **状态变更记录**（可选）：记录变更时间和原因

### 后端需求

| 端点 | 说明 |
|------|------|
| `GET /api/v1/agents/` | Agent 列表（分页，支持按状态筛选） |
| `GET /api/v1/agents/{id}` | Agent 详情 |
| `POST /api/v1/agents/` | 创建 Agent（默认 DRAFT） |
| `PATCH /api/v1/agents/{id}/status` | 状态切换（需验证业务规则） |
| `DELETE /api/v1/agents/{id}` | 删除 Agent（仅 DRAFT/INACTIVE 可删） |

### 前端需求

- Agent 列表页：名称、状态标签、关联 Model/Prompt 名称，支持状态筛选
- 状态切换按钮：DRAFT→激活、ACTIVE→停用、INACTIVE→激活/删除
- 创建表单：名称、描述、Model 下拉选择、Prompt 下拉选择
- 确认对话框 + 错误提示

## 代码风格参考

- **分层模式**：Router → Service → Model（参考 `prompt_service.py` 和 `endpoints.py`）
- **Schema**：Pydantic v2，参考 `schema.py` 已有定义
- **前端**：Vue 3 Composition API + Pinia + Element Plus（参考 `PromptList.vue`）
- **API 客户端**：参考 `frontend/src/api/prompts.js` 的封装模式

## 实验说明

本实验目的是测试 AI 工具在真实开发场景中的表现。完成后，用户会基于以下维度评估：

- 业务规则覆盖完整性（5 条规则是否全部实现）
- 前端功能完整性（创建时可关联 Model/Prompt、状态切换、删除）
- 代码质量（分层、错误处理、查询优化）
- 测试覆盖（如果有）

---

## Round 4 工具：Get Shit Done（get-shit-done-cc）

**工具定位**：面向 Claude Code 的轻量 meta-prompting + 上下文工程框架。通过安装 slash commands 让 Claude Code 按规范化流程推进开发，核心解决"context rot"（上下文膨胀导致质量退化）问题。

**安装**（在本目录执行，会将 slash commands 写入 `.claude/commands/`）：

```bash
npx get-shit-done-cc@latest
# 提示选择 runtime → 选 Claude Code
# 提示安装 scope → 选 local（只在本项目生效）
```

**注意**：GSD 是为"从零开始的新项目"设计的，本实验是在已有 codebase 上加功能。接入策略：
- 先跑 `/gsd-map-codebase` 让它理解现有项目结构
- 再用 `/gsd-new-project` 或直接 `/gsd-plan-phase 1` 对接需求

**核心工作流**（6 步循环）：

| 命令 | 作用 |
|------|------|
| `/gsd-map-codebase` | 分析现有代码架构（首次必跑） |
| `/gsd-new-project` | 问答 → 生成 requirements + roadmap |
| `/gsd-discuss-phase 1` | 讨论实现细节（可选，灰色地带决策） |
| `/gsd-plan-phase 1` | research + plan + verify 循环，产出执行计划 |
| `/gsd-execute-phase 1` | 并行子 agent 执行（每个 executor 获得独立 200k 上下文） |
| `/gsd-verify-work 1` | 验收，失败则生成 fix plan |

**产出物**：`.planning/` 目录，包含 `PROJECT.md`、`REQUIREMENTS.md`、`ROADMAP.md`、`STATE.md`、`CONTEXT.md`。

**与前三轮的关键差异**：
- 子 agent 并行执行是 GSD 的核心卖点，主 context 保持在 30-40%
- 每个执行 task 有独立提交，产出 clean git history
- 有专门的 verify step（其他工具基本跳过这一环）

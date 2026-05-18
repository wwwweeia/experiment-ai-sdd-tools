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

## Round 5 工具：GSD-2（gsd-pi）

**工具定位**：这是一个**完全独立的 Agent CLI**，不是 Claude Code 的插件。基于 Pi SDK 构建，有自己的 TUI、SQLite 状态数据库（`gsd.db`）、worktree 管理、并行子 agent 编排。它替代 Claude Code 成为 agent runner 本身。

> ⚠️ 与前四轮最大的区别：**本轮不是"Claude Code + 工具"，而是"gsd CLI 直接运行"**。实验中应启动 `gsd` 而非 `claude`。

**安装**（全局安装）：

```bash
npm install -g gsd-pi@latest
```

**初始化**（在本目录执行）：

```bash
gsd init
# 按提示配置项目，生成 .gsd/ 目录和 gsd.db
```

**核心工作流**：

```bash
# 进入 TUI
gsd

# 或直接自动模式（完全无人干预）
gsd auto
```

| 概念 | 说明 |
|------|------|
| **Milestone** | 一个大目标（对应本次"Agent 激活/停用"需求） |
| **Slice** | milestone 下的阶段（类似 phase） |
| **Unit** | 最小执行单元，有独立 worktree |
| **ROADMAP.md** | 自动生成，milestone 的执行路线图 |
| **STATE.md** | 当前进度（跨 session 持久） |
| **gsd.db** | SQLite，记录所有状态、决策、记忆 |

**验证相关命令**：

```bash
gsd doctor          # 检查项目状态，识别 drift
gsd verdict pass    # 手动确认 milestone 通过
gsd forensics       # 排查异常
```

**与其他轮次的关键差异**：
- 不依赖 Claude Code session，gsd 自己管理 context 和 session 边界
- 有数据库驱动的跨 session 持久记忆（Decisions、Knowledge、memories table）
- worktree 隔离：每个 unit 在独立 git worktree 中执行，自动 merge
- 完全自主模式：`gsd auto` 理论上可以"走开，回来看结果"

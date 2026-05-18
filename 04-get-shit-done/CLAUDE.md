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

<!-- GSD:project-start source:PROJECT.md -->
## Project

**AI Prompt Lab — Agent 状态管理**

AI Prompt Lab 是一个 AI 智能体管理平台，核心实体为 Model（模型）、Prompt（提示词模板）、Agent（智能体）、Skill（工具能力）。本次目标是在已有 CRUD 基础上，完整实现 Agent 的三状态生命周期管理（DRAFT → ACTIVE → INACTIVE），包括业务规则验证、API 端点、状态变更记录和前端管理页面。

**Core Value:** Agent 能够被安全地激活和停用——激活时确保必要依赖（Model + Prompt）就绪，停用时有完整记录，状态管理对前端透明可操作。

### Constraints

- **Tech Stack**: FastAPI + SQLAlchemy 2.x + SQLite / Vue 3 + Element Plus + Pinia — 不引入新依赖
- **Code Style**: 遵循 `prompt_service.py` 和 `endpoints.py` 的现有模式，保持一致性
- **Schema**: Pydantic v2，参考 `schema.py` 已有定义扩展
- **Test**: 后端 pytest 覆盖业务规则（5 条规则），前端手动验证
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.13.9 - FastAPI backend application
- JavaScript (ES Module) - Vue 3 SPA application
- TypeScript 5.8 - E2E testing (Playwright)
## Runtime & Build
- Python 3.13.9 (local development)
- Uvicorn 0.34.0 - ASGI server with `uvicorn[standard]` extras
- Development: `uvicorn app.main:app --reload`
- Node.js v22.22.2 (verified)
- Vite 6.0.0 - Build tool and dev server
- Dev server: `npm run dev` (runs on http://localhost:5173)
- Build: `npm run build` (production bundle)
- Preview: `npm run preview` (serve built assets)
## Frameworks
- FastAPI 0.115.6 - Web framework
- Vue 3.5.0 - SPA framework (Composition API)
- Vue Router 4.4.0 - Client-side routing
- Pinia 2.2.0 - State management store
- Element Plus 2.9.0 - UI component library
- Playwright 1.52.0 (@playwright/test) - E2E testing framework
## Key Dependencies
- SQLAlchemy 2.0.36 - ORM for database operations
- Pydantic 2.10.4 - Data validation and serialization
- Axios 1.7.0 - HTTP client
- Sass/SCSS (sass-embedded 1.80.0) - CSS preprocessing
- @vitejs/plugin-vue 5.2.0 - Vue 3 Vite integration
- @types/node 22.0.0 - TypeScript node types (E2E)
## Configuration
- Location: `backend/app/core/config.py`
- `PROJECT_NAME`: "AI Prompt Lab"
- `VERSION`: "1.0.0"
- `API_PREFIX`: "/api/v1"
- `DATABASE_URL`: SQLite at `prompt_lab.db` (root of backend directory)
- Vite config: `frontend/vite.config.js`
- Entry point: `frontend/index.html`
- Mount: `<div id="app"></div>`
- Proxy: `/api/*` → `http://localhost:8000`
- Port: 5173
- Type: SQLite (file-based)
- Path: `{project_root}/prompt_lab.db`
- Auto-created on startup via `Base.metadata.create_all(bind=engine)`
- Configuration: `backend/app/core/database.py`
- Config: `e2e/playwright.config.ts`
- Test directory: `e2e/tests/`
- Test files: `*.spec.ts`
- Base URL: `http://localhost:5173` (configurable via `E2E_BASE_URL` env var)
- Headless mode: Enabled by default (configurable via `E2E_HEADLESS` env var)
- Timeout: 30 seconds per test, 5 seconds per assertion
- CI configuration: Retry 2 times on CI, single worker
- CORS: Enabled for localhost:5173 on FastAPI app
- Health check endpoint: `GET /health` (returns status, service name, version)
## Package Management
- Package Manager: pip
- Lock file: N/A (requirements.txt with pinned versions)
- Dependency location: `backend/requirements.txt`
- Package Manager: npm
- Lock file: `frontend/package-lock.json` (present)
- Dependency location: `frontend/package.json`
- Workspace: None (single root)
- Package Manager: npm
- Lock file: `e2e/package-lock.json` (present)
- Dependency location: `e2e/package.json`
- Separate from frontend dependencies
## Platform Requirements
- Python 3.13.9+
- Node.js v22+ (verified v22.22.2)
- npm (comes with Node)
- Bash/shell for running startup scripts
- Python runtime (FastAPI + Uvicorn)
- Web server (Nginx/Apache to reverse proxy Uvicorn)
- Node.js build environment (for frontend build step)
- SQLite support (included in Python stdlib)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Code Style
### Backend (Python)
- Python with type hints throughout
- Pydantic v2 schemas using `ConfigDict(from_attributes=True)`
- SQLAlchemy 2.x with `Mapped[T]` type annotations for all columns
- FastAPI dependency injection via `Depends(get_db)` for database sessions
### Frontend (JavaScript/Vue)
- Vue 3 Composition API with `<script setup>` syntax
- No TypeScript — plain JavaScript with JSDoc where needed
- Element Plus UI components
## Naming Conventions
### Backend
- **Files**: snake_case (`model_service.py`, `prompt_service.py`)
- **Classes**: PascalCase (`ModelService`, `PromptService`, `AgentStatus`)
- **Functions/methods**: snake_case (`get_all`, `create`, `update_status`)
- **Database columns**: snake_case (`model_id`, `created_at`)
- **Enums**: uppercase values (`DRAFT`, `ACTIVE`, `INACTIVE`)
### Frontend
- **Components**: PascalCase (`AgentList.vue`, `PromptList.vue`)
- **Stores**: camelCase (`usePromptStore`, `useAgentStore`)
- **API modules**: camelCase (`prompts.js`, `agents.js`)
- **Functions**: camelCase (`fetchPrompts`, `createAgent`)
- **CSS classes**: kebab-case
## Patterns
### Service Layer Pattern (Backend)
### Unified Response Wrapper
### Pinia Store Structure
### API Client Pattern
### Router → Service → Model Flow
## Error Handling
### Backend
- FastAPI `HTTPException` for HTTP-level errors (404, 422, etc.)
- Business rule violations returned as `400 Bad Request` with descriptive message
- No global exception handler — each endpoint handles its own errors
### Frontend
- API errors caught in store actions via try/catch
- `ElMessage.error()` for user-facing error display
- `ElMessageBox.confirm()` for destructive action confirmation
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern
```
```
```
```
## Layers
### Backend
| Layer | Location | Responsibility |
|-------|----------|----------------|
| Entry Point | `app/main.py` | App init, middleware, router registration |
| Config | `app/core/config.py` | Constants (PROJECT_NAME, API_PREFIX, etc.) |
| Database | `app/core/database.py` | SQLite engine, SessionLocal, `get_db` dependency |
| Models | `app/models/entity.py` | SQLAlchemy ORM models (all entities in one file) |
| Schemas | `app/schemas/schema.py` | Pydantic v2 request/response schemas |
| Services | `app/services/` | Business logic, DB queries |
| API | `app/api/v1/endpoints.py` | HTTP handlers (all routers in one file) |
| Router | `app/api/v1/router.py` | Aggregates routers, registers with prefix `/api/v1` |
### Frontend
| Layer | Location | Responsibility |
|-------|----------|----------------|
| Views | `src/views/` | Page components, UI logic |
| Stores | `src/stores/` | Pinia state management |
| API | `src/api/` | Axios HTTP calls |
| Router | `src/router/index.js` | Vue Router — client-side navigation |
| Entry | `src/main.js` | Vue app init, plugin registration |
## Data Flow
### Read (list agents example)
```
```
### Write (status update example)
```
```
### Frontend flow
```
```
## Key Abstractions
### Generic Response Wrapper
```python
```
### Service Constructor Pattern
```python
```
### AgentStatus Enum (State Machine)
```python
```
## Entry Points
- **Backend**: `uvicorn app.main:app --reload` → `backend/app/main.py`
- **Frontend**: `npm run dev` → `frontend/src/main.js` → `App.vue`
- **API docs**: `http://localhost:8000/docs` (FastAPI auto-generated Swagger)
- **Health check**: `GET /health`
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

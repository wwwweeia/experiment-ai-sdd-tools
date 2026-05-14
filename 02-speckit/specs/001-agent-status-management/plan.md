# Implementation Plan: Agent 状态管理（激活/停用）

**Branch**: `001-agent-status-management` | **Date**: 2026-05-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-agent-status-management/spec.md`

## Summary

实现 Agent 实体的完整 CRUD 和状态管理功能，包括：创建 Agent（DRAFT 状态）、激活/停用状态切换（含业务规则校验）、删除保护，以及前端管理页面。后端新增 AgentService 和 API 端点，前端实现 Agent 列表页（含状态筛选、操作按钮、确认对话框和创建表单）。

## Technical Context

**Language/Version**: Python 3.11+ / JavaScript (ES2022)

**Primary Dependencies**: FastAPI 0.115.6, SQLAlchemy 2.0.36, Pydantic 2.10.4, Vue 3.5.0, Element Plus 2.9.0, Pinia 2.2.0

**Storage**: SQLite (via SQLAlchemy 2.x ORM)

**Testing**: pytest (后端), Playwright (E2E)

**Target Platform**: Web 应用（本地开发环境）

**Project Type**: Web application (monorepo: backend/ + frontend/ + e2e/)

**Performance Goals**: 50 条数据内列表加载 < 1s，状态切换响应 < 500ms

**Constraints**: SQLite 单文件数据库，开发阶段不需要生产级性能优化

**Scale/Scope**: 单用户/小团队使用，预计 Agent 数量 < 100

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. API-First Design | ✅ PASS | API 契约在 contracts/ 中先行定义 |
| II. Entity Relationship Integrity | ✅ PASS | Agent 状态机和 FK 约束在 data-model.md 中定义 |
| III. Consistent API Contract | ✅ PASS | 使用现有 Response[T] 包装器 |
| IV. Full-Stack Synchronization | ✅ PASS | 后端 API + 前端页面同步交付 |
| V. Simplicity & Iteration | ✅ PASS | 复用现有模式，不引入新依赖 |

**Post-Design Re-check**: ✅ All gates pass (see below).

## Project Structure

### Documentation (this feature)

```text
specs/001-agent-status-management/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── agents-api.md    # Agent API contracts
└── tasks.md             # Phase 2 output (by /speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── entity.py          # 修改: Agent 增加 activated_at, deactivated_at
│   ├── schemas/
│   │   └── schema.py          # 修改: 增加 AgentStatusUpdate, AgentDetail 等 schema
│   ├── services/
│   │   ├── model_service.py   # 不变
│   │   ├── prompt_service.py  # 不变
│   │   └── agent_service.py   # 新增: Agent CRUD + 状态管理业务逻辑
│   └── api/
│       └── v1/
│           ├── endpoints.py   # 修改: 增加 agents_router
│           └── router.py      # 修改: 注册 agents_router
└── requirements.txt           # 不变

frontend/
├── src/
│   ├── api/
│   │   ├── index.js           # 不变
│   │   ├── prompts.js         # 不变
│   │   └── agents.js          # 新增: Agent API 函数
│   ├── stores/
│   │   ├── prompt.js          # 不变
│   │   └── agent.js           # 修改: 完善 Agent store
│   ├── views/
│   │   ├── Home.vue           # 不变
│   │   ├── PromptList.vue     # 不变
│   │   └── AgentList.vue      # 修改: 完整 Agent 管理页面
│   ├── router/
│   │   └── index.js           # 不变（已有 /agents 路由）
│   ├── App.vue                # 不变
│   └── main.js                # 不变
```

**Structure Decision**: 复用现有 Web application 目录结构，新增 `agent_service.py`、`agents.js`（API 层），修改 `AgentList.vue` 和 `agent.js`（store）。

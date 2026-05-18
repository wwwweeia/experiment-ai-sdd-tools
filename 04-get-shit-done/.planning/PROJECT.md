# AI Prompt Lab — Agent 状态管理

## What This Is

AI Prompt Lab 是一个 AI 智能体管理平台，核心实体为 Model（模型）、Prompt（提示词模板）、Agent（智能体）、Skill（工具能力）。本次目标是在已有 CRUD 基础上，完整实现 Agent 的三状态生命周期管理（DRAFT → ACTIVE → INACTIVE），包括业务规则验证、API 端点、状态变更记录和前端管理页面。

## Core Value

Agent 能够被安全地激活和停用——激活时确保必要依赖（Model + Prompt）就绪，停用时有完整记录，状态管理对前端透明可操作。

## Requirements

### Validated

- ✓ Model CRUD API（列表、详情、创建、更新、删除）— 已有
- ✓ Prompt CRUD API（列表、详情、创建、更新、删除）— 已有
- ✓ Agent 数据模型（AgentStatus 枚举：DRAFT/ACTIVE/INACTIVE）— 已有
- ✓ Skill 数据模型（关联 Agent，多对一）— 已有
- ✓ 前端 Prompt 列表页（参考实现模式）— 已有

### Active

- [ ] Agent CRUD API（列表分页+状态筛选、详情、创建默认 DRAFT）
- [ ] Agent 状态切换 API（PATCH /agents/{id}/status，含业务规则验证）
- [ ] Agent 删除保护（ACTIVE 不可删，必须先停用）
- [ ] AgentService：状态机验证、激活前置检查（Model + Prompt 存在性）
- [ ] 状态变更记录（记录变更时间和原因，随 PATCH 请求写入）
- [ ] 前端 Agent 列表页（名称、状态标签、关联 Model/Prompt 名称、状态筛选、分页）
- [ ] 前端状态切换操作（确认对话框、失败原因展示）
- [ ] 前端创建 Agent 表单（名称、描述、Model 下拉、Prompt 下拉）

### Out of Scope

- Skill `is_active` 字段 — 停用时不批量更新 Skill 字段，可用性通过 Agent 状态隐式反映，避免引入冗余状态
- Skill 管理 UI — 本次聚焦 Agent 状态管理
- OAuth / 认证 — 实验项目，无需鉴权
- 前端单元测试 — 手动验证即可，后端 pytest 覆盖业务逻辑

## Context

- 现有代码已按分层模式组织（Router → Service → Model），新功能需遵循同一模式
- `PromptList.vue` + `stores/prompt.js` + `api/prompts.js` 是前端三层联动的标准参考
- 统一响应体：`Response[T]`（code=0, data, message="success"），所有端点一致
- SQLAlchemy 2.x 风格（Session.execute + select()），非 legacy query API
- Agent 已有 `model_id → Model`、`prompt_id → Prompt` 外键和反向关联 `skills → Skill[]`

## Constraints

- **Tech Stack**: FastAPI + SQLAlchemy 2.x + SQLite / Vue 3 + Element Plus + Pinia — 不引入新依赖
- **Code Style**: 遵循 `prompt_service.py` 和 `endpoints.py` 的现有模式，保持一致性
- **Schema**: Pydantic v2，参考 `schema.py` 已有定义扩展
- **Test**: 后端 pytest 覆盖业务规则（5 条规则），前端手动验证

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Skill 不加 is_active 字段 | 避免冗余状态，停用意图已通过 Agent.status 完整表达 | — Pending |
| 状态变更记录本阶段实现 | 变更历史是状态机的重要组成，利于 debug 和审计 | — Pending |
| PATCH /agents/{id}/status 为独立端点 | 状态变更有业务规则，独立端点比 PUT 更语义清晰 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-18 after initialization*

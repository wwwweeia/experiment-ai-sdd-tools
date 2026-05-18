# Research Summary — Agent 状态管理

**Synthesized from:** STACK.md · FEATURES.md · ARCHITECTURE.md · PITFALLS.md
**Date:** 2026-05-18

---

## Executive Summary

本项目在已有 FastAPI monolith 中为 Agent 实体添加三状态生命周期（DRAFT / ACTIVE / INACTIVE）。现有代码库已有完整的 Model / Prompt CRUD 堆栈、分层约定（Router → Service → ORM）和 Vue 3 + Pinia + Element Plus 前端。工作是纯增量式的——**不需要新依赖**。主要挑战是在现有模式中干净地实现状态机。

推荐方案：纯 Python `VALID_TRANSITIONS` dict 写在 AgentService 中、独立的 append-only AgentStatusHistory 表用于审计日志、列表查询 eager-load model/prompt 名称、前端 AgentList.vue 含逐行 loading 状态和懒加载下拉。状态机只有 3 个状态和 4 个有效转换——python-statemachine 之类的库是不必要的开销，也违反了 PROJECT.md 中"不引入新依赖"的约束。

---

## Stack

| 技术 | 版本 | 状态 |
|------|------|------|
| FastAPI | 0.115.6 | 已安装 |
| SQLAlchemy | 2.0.36 | 已安装 |
| Pydantic | 2.10.4 | 已安装 |
| Vue 3 + Element Plus | 已安装 | 已安装 |

**关键决策：**
- AgentService 使用 `session.execute(select(...))` 风格，不用现有服务中的 legacy `db.query()`（SQLAlchemy 3.0 会废弃）
- 状态机用 `VALID_TRANSITIONS` dict，无需外部库
- AgentStatusHistory 使用独立表（可查询历史），不用 JSON 列

---

## Table Stakes Features (P1)

- Agent 列表含状态标签、Model 名称、Prompt 名称列
- 状态筛选 + 服务端分页
- 每行操作按钮（激活 / 停用 / 重新激活）+ ElMessageBox.confirm 确认
- 创建 Agent 对话框含 Model + Prompt 下拉（懒加载，仅在对话框打开时）
- ACTIVE 状态隐藏 / 禁用删除按钮
- 逐行 loading 状态（防止双击竞态）
- 内联错误提示（已有 `api/index.js` 拦截器，无需额外代码）

## Defer (v2+)

- 批量状态操作、状态历史时间线 UI、实时轮询

---

## Architecture — Build Order

```
entity.py
  ↓ (import)
schema.py
  ↓ (import)
agent_service.py
  ↓ (import)
endpoints.py (add agents_router)
  ↓ (register)
router.py
  ↓ (parallel)
tests/           frontend/
```

**AgentStatusHistory 字段：**
`id` · `agent_id` (FK + ondelete=CASCADE) · `from_status` (nullable Enum) · `to_status` (Enum) · `reason` (nullable String 500) · `changed_at` (DateTime)

**AgentRead 需扩展：** `model_name: str | None` · `prompt_name: str | None` · `status: AgentStatus`（not str）

**错误分层：** Service 抛 `ValueError` / 自定义领域异常 → Router 捕获映射到 HTTP

---

## Top Pitfalls

| # | 陷阱 | 预防 |
|---|------|------|
| 1 | `status: str` 在 schema 中 — 任意字符串绕过验证 | 改为 `AgentStatus` 枚举；AgentCreate 不暴露 status 字段 |
| 2 | 状态转换逻辑写在 endpoint 层 | 所有验证在 AgentService；endpoint 只做 ValueError → HTTPException |
| 3 | Agent 列表 N+1 查询 | `selectinload(Agent.model, Agent.prompt)` 写在 list_agents |
| 4 | HTTP 状态码混用 | 409 = 无效转换；422 = 前置条件不满足（缺 model/prompt） |
| 5 | dev DB 无 AgentStatusHistory 表 | pytest 使用 `sqlite:///:memory:`；提供 `reset_db.py` |
| 6 | 前端 el-select 选项晚于 v-model 加载 | 懒加载：仅在对话框 open 时 fetch |
| 7 | 状态按钮无逐行 loading → 双击竞态 | 每行维护独立 loading 状态 |

---

## Roadmap Implications

**建议 2 个阶段：**

**Phase 1 — Backend: AgentService + API Endpoints**
- 交付：AgentStatusHistory ORM、扩展 AgentRead schema、StatusChangeRequest schema、AgentService（状态机 + 前置检查 + 历史记录）、5 个 API 端点、pytest 覆盖 5 条业务规则

**Phase 2 — Frontend: AgentList.vue + State**
- 交付：`api/agents.js`、`stores/agent.js`、完整 AgentList.vue（替换 15 行占位页面）

---

## Gaps to Address During Planning

1. Skill.is_active 在停用时处理：PROJECT.md 决策是"不加字段，隐式反映"——执行前确认 entity.py 中 Skill 模型无 is_active 字段
2. AgentCreate 中 model_id/prompt_id 是否可选：应可选（创建时为草稿，激活前配置）
3. 错误信息语言：后端返回中文还是英文 detail？按现有 codebase 约定决定

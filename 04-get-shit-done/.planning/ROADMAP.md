# Roadmap: AI Prompt Lab — Agent 状态管理

## Overview

在已有 FastAPI + Vue 3 平台上，为 Agent 实体添加完整的三状态生命周期管理。Phase 1 交付稳定的后端 API（含状态机验证、审计日志），Phase 2 在其上构建前端管理页面。两个阶段之间有硬依赖：前端接口合约在 Phase 1 完成后才确定。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Backend** - Agent CRUD API + 状态机 + 审计日志（6 个需求，后端完整交付）
- [x] **Phase 2: Frontend** - Agent 列表页 + 状态操作 + 创建表单（3 个需求，前端完整交付） (completed 2026-05-18)

## Phase Details

### Phase 1: Backend
**Goal**: 用户可以通过 HTTP API 对 Agent 进行 CRUD 操作，并安全地执行三状态切换，每次变更自动记录历史
**Depends on**: Nothing (first phase)
**Requirements**: AGENT-01, AGENT-02, AGENT-03, AGENT-04, STATE-01, STATE-02
**Success Criteria** (what must be TRUE):
  1. GET /api/v1/agents/ 返回分页列表，支持按 DRAFT/ACTIVE/INACTIVE 状态筛选，且响应中包含关联 Model 和 Prompt 名称（无 N+1 查询）
  2. POST /api/v1/agents/ 创建 Agent 成功，初始状态固定为 DRAFT，无法在创建时指定其他状态
  3. PATCH /api/v1/agents/{id}/status 执行合法转换（DRAFT→ACTIVE、ACTIVE→INACTIVE、INACTIVE→ACTIVE）时返回 200；激活时若 model_id 或 prompt_id 不存在则返回 422 含具体原因；非法转换（如 ACTIVE→DRAFT）返回 409
  4. DELETE /api/v1/agents/{id} 对 DRAFT/INACTIVE Agent 成功删除；对 ACTIVE Agent 返回 409 错误
  5. 每次合法的状态切换后，AgentStatusHistory 表中自动写入一条记录，含 from_status、to_status、changed_at
**Plans**: 4 plans
- [x] 01-01-PLAN.md — 数据层：AgentStatusHistory ORM 表 + Schema 修整（AgentCreate 去 status、AgentRead 加 enum 与 relation 名）
- [x] 01-02-PLAN.md — 服务层：AgentService 状态机 + 双异常 + 原子 history 写入（VALID_TRANSITIONS、selectinload）
- [x] 01-03-PLAN.md — HTTP 层：agents_router 5 个端点 + 409/422 异常映射 + router.py 注册
- [x] 01-04-PLAN.md — 测试层：pytest 脚手架 + AgentService 单测 + API 集成测试（覆盖全部 6 个 REQ-ID）

### Phase 2: Frontend
**Goal**: 用户可以通过浏览器页面查看所有 Agent、创建新 Agent、并通过按钮操作切换 Agent 状态
**Depends on**: Phase 1
**Requirements**: FRONT-01, FRONT-02, FRONT-03
**Success Criteria** (what must be TRUE):
  1. Agent 列表页展示名称、状态标签（颜色区分三种状态）、关联 Model 名称、关联 Prompt 名称，支持按状态筛选和分页导航
  2. 每行按当前状态显示对应操作按钮（DRAFT 显示"激活"；ACTIVE 显示"停用"；INACTIVE 显示"激活"和"删除"），点击后弹出确认对话框，后端返回错误时在页面上展示具体原因
  3. 点击"创建 Agent"打开表单，填写名称（必填）、描述（选填）、从下拉中选择 Model 和 Prompt（懒加载），提交后新 Agent 以 DRAFT 状态出现在列表中
**Plans**: 1 plan
- [x] 02-01-PLAN.md — Agent 管理前端：API 客户端 + Pinia Store + AgentList 页面（表格、状态筛选、创建表单、状态操作）

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend | 4/4 | Complete | 2026-05-18 |
| 2. Frontend | 1/1 | Complete   | 2026-05-18 |

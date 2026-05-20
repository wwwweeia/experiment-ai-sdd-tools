<!-- 此文件由 docs:collect 自动生成，源：04-get-shit-done/.planning/phases/01-backend/01-VERIFICATION.md。请编辑源文件而非本文件。 -->

---
phase: 01-backend
verified: 2026-05-18T10:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 1: Backend Verification Report

**Phase Goal:** 用户可以通过 HTTP API 对 Agent 进行 CRUD 操作，并安全地执行三状态切换，每次变更自动记录历史
**Verified:** 2026-05-18T10:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                        | Status     | Evidence                                                                                                 |
|-----|----------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------------------|
| SC1 | GET /api/v1/agents/ 返回分页列表，支持状态筛选，响应含 model_name/prompt_name，无 N+1       | ✓ VERIFIED | `selectinload(Agent.model/prompt)` 在 list_agents()；`_agent_to_read()` 映射两个名称字段；测试通过      |
| SC2 | POST /api/v1/agents/ 创建成功，初始状态固定 DRAFT，无法指定其他状态                         | ✓ VERIFIED | AgentCreate schema 无 status 字段；service 层有防御性 `agent.status = AgentStatus.DRAFT`；测试验证通过  |
| SC3 | PATCH /api/v1/agents/{id}/status 合法转换 200、激活缺依赖 422、非法转换 409                  | ✓ VERIFIED | VALID_TRANSITIONS 映射表 + InvalidTransitionError→409 + ActivationNotReadyError→422；3条路径均有测试   |
| SC4 | DELETE /api/v1/agents/{id} DRAFT/INACTIVE 成功，ACTIVE 返回 409                             | ✓ VERIFIED | delete_agent() 检测 ACTIVE 抛 ValueError，端点捕获映射为 409；测试覆盖3条路径                           |
| SC5 | 每次合法状态切换后 AgentStatusHistory 自动写入，含 from_status/to_status/changed_at         | ✓ VERIFIED | change_status() 在同一 commit 中原子写 history 行；创建时也写初始行；cascade 删除已测试                  |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact                                      | Expected                        | Status     | Details                                              |
|-----------------------------------------------|---------------------------------|------------|------------------------------------------------------|
| `backend/app/models/entity.py`                | AgentStatusHistory ORM 表       | ✓ VERIFIED | 含 from_status/to_status/changed_at，CASCADE 配置   |
| `backend/app/schemas/schema.py`               | AgentCreate 无 status，AgentRead 含关联名 | ✓ VERIFIED | AgentCreate 无 status 字段；AgentRead 含 model_name/prompt_name |
| `backend/app/services/agent_service.py`       | 状态机 + 双异常 + 原子写入       | ✓ VERIFIED | VALID_TRANSITIONS + InvalidTransitionError + ActivationNotReadyError + 原子 commit |
| `backend/app/api/v1/endpoints.py`             | 5 个 Agent 端点 + 异常映射       | ✓ VERIFIED | GET list/detail、POST、PATCH status、DELETE，异常映射完整 |
| `backend/app/api/v1/router.py`                | agents_router 注册              | ✓ VERIFIED | `include_router(agents_router, prefix="/agents")` |
| `backend/tests/conftest.py`                   | in-memory SQLite + fixtures      | ✓ VERIFIED | StaticPool + dependency_override + seed fixtures 完整 |
| `backend/tests/test_agent_service.py`         | 服务层单元测试                   | ✓ VERIFIED | 18 个测试，覆盖所有状态转换路径 + history 写入       |
| `backend/tests/test_agent_api.py`             | HTTP 集成测试                   | ✓ VERIFIED | 23 个测试，覆盖全部 5 个端点 + 各业务规则路径       |

### Key Link Verification

| From                  | To                          | Via                                      | Status     | Details                                           |
|-----------------------|-----------------------------|------------------------------------------|------------|---------------------------------------------------|
| `endpoints.py`        | `AgentService`              | `service = AgentService(db)` 调用        | ✓ WIRED    | 5 个端点均实例化并调用 service                   |
| `router.py`           | `agents_router`             | `include_router(agents_router, ...)`     | ✓ WIRED    | prefix="/agents" 已注册                          |
| `main.py`             | `v1_router`                 | `app.include_router(v1_router, prefix=API_PREFIX)` | ✓ WIRED | API_PREFIX="/api/v1"，路由全链路通 |
| `AgentService`        | `AgentStatusHistory`        | `self.db.add(AgentStatusHistory(...))` + `self.db.commit()` | ✓ WIRED | 原子写入，含 create_agent 和 change_status |
| `endpoints.py`        | `_agent_to_read()`          | 所有 agent 响应均经此函数转换            | ✓ WIRED    | 正确映射 model.name → model_name，prompt.title → prompt_name |
| `list_agents()`       | `selectinload`              | `.options(selectinload(Agent.model), selectinload(Agent.prompt))` | ✓ WIRED | N+1 防护实际生效 |

### Data-Flow Trace (Level 4)

| Artifact              | Data Variable            | Source                          | Produces Real Data | Status     |
|-----------------------|--------------------------|---------------------------------|--------------------|------------|
| `list_agents()`       | agents list              | `db.execute(select(Agent))` 数据库查询 | Yes            | ✓ FLOWING  |
| `_agent_to_read()`    | model_name/prompt_name   | `agent.model.name` / `agent.prompt.title`（已 selectinload） | Yes | ✓ FLOWING |
| `change_status()`     | AgentStatusHistory row   | `db.add(AgentStatusHistory(...))` + `db.commit()` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior                          | Command                                  | Result                          | Status  |
|-----------------------------------|------------------------------------------|---------------------------------|---------|
| 41 个 pytest 测试全部通过          | `cd backend && python -m pytest tests/ -v` | 41 passed in 0.34s              | ✓ PASS  |
| AgentCreate schema 不含 status 字段 | grep schema.py                           | status 字段注释明确标注已省略    | ✓ PASS  |
| 状态机映射表精确匹配需求           | test_valid_transitions_shape             | 断言通过                        | ✓ PASS  |

### Probe Execution

Step 7c: SKIPPED — 无 probe-*.sh 脚本，通过 pytest 进行行为验证。

### Requirements Coverage

| Requirement | Source Plan       | Description                                | Status      | Evidence                                      |
|-------------|-------------------|--------------------------------------------|-------------|-----------------------------------------------|
| AGENT-01    | 01-02/01-03 PLAN  | 分页列表 + 状态筛选                          | ✓ SATISFIED | list_agents() + ?status= 筛选 + 7 个列表测试  |
| AGENT-02    | 01-02/01-03 PLAN  | 单个 Agent 详情含关联名称                   | ✓ SATISFIED | get_agent() + joinedload + model_name/prompt_name |
| AGENT-03    | 01-02/01-03 PLAN  | 创建 Agent，初始 DRAFT                      | ✓ SATISFIED | AgentCreate 无 status + service 防御性赋值    |
| AGENT-04    | 01-02/01-03 PLAN  | 删除 DRAFT/INACTIVE；ACTIVE 返回错误        | ✓ SATISFIED | delete_agent() + ValueError → 409             |
| STATE-01    | 01-02/01-03 PLAN  | 状态切换 + 转换规则验证 + 激活前置检查      | ✓ SATISFIED | VALID_TRANSITIONS + 双异常 + change_status()  |
| STATE-02    | 01-01/01-02 PLAN  | AgentStatusHistory 自动写入                 | ✓ SATISFIED | 原子写入 + 4 行 history 测试（3 次转换）      |

### Anti-Patterns Found

无 TBD、FIXME、XXX、HACK 等 debt marker。
无空实现（return null/return []）。
无占位符文本。

所有 `return []` 模式均在测试数据为空时由数据库查询返回，非硬编码。

### Human Verification Required

本 Phase 为纯后端 API，所有成功标准均可通过 pytest 自动验证。无需人工测试。

### Gaps Summary

无 gaps。所有 5 条成功标准均通过代码层面（Levels 1-4）和 pytest 行为测试双重验证。

---

## Detailed Finding Per Success Criterion

### SC1: GET /api/v1/agents/ — 分页、状态筛选、关联名称、N+1 防护

**VERIFIED.**

- `agent_service.py:69-76`：`list_agents()` 使用 `selectinload(Agent.model)` + `selectinload(Agent.prompt)`，单次额外查询加载所有关联，无 N+1。
- `endpoints.py:108-117`：路由支持 `status: AgentStatus | None = None` 查询参数，FastAPI 自动枚举校验（无效值返回 422）。
- `endpoints.py:86-102`：`_agent_to_read()` 映射 `agent.model.name → model_name`，`agent.prompt.title → prompt_name`。
- 测试：`test_list_includes_relation_names`、`test_list_filter_by_status_draft/active`、`test_list_pagination`、`test_list_invalid_status_returns_422` 全部通过。

### SC2: POST /api/v1/agents/ — 初始状态固定 DRAFT

**VERIFIED.**

- `schema.py:62-67`：`AgentCreate` 不含 `status` 字段，注释明确说明"status intentionally omitted"。
- `agent_service.py:102-104`：防御性赋值 `agent.status = AgentStatus.DRAFT`，即使 schema 将来引入 status 也会被覆盖。
- 测试：`test_create_returns_201_default_draft`、`test_create_ignores_status_in_body` 均通过。

### SC3: PATCH /api/v1/agents/{id}/status — 合法转换/非法转换/激活前置

**VERIFIED.**

- `agent_service.py:17-27`：`VALID_TRANSITIONS` 映射表精确定义 DRAFT→ACTIVE、ACTIVE→INACTIVE、INACTIVE→ACTIVE 三条合法路径。
- `agent_service.py:39-43`：`InvalidTransitionError` 抛出 → `endpoints.py:143-144` 捕获映射为 HTTP 409。
- `agent_service.py:39-43`：`ActivationNotReadyError` 抛出 → `endpoints.py:145-146` 捕获映射为 HTTP 422，错误消息包含"模型"/"提示词"具体原因。
- `_assert_activation_ready()` 同时验证 model_id/prompt_id 存在且关联实体仍在数据库中（防 Pitfall #6）。
- 覆盖 INACTIVE→ACTIVE 的重新激活校验：`test_inactive_to_active_revalidates_dependencies` 通过。

### SC4: DELETE /api/v1/agents/{id} — DRAFT/INACTIVE 可删，ACTIVE 返回 409

**VERIFIED.**

- `agent_service.py:185-207`：`delete_agent()` 检测 `AgentStatus.ACTIVE` 抛出 `ValueError`（非子类，与路由层 `except ValueError` 匹配）。
- `endpoints.py:151-158`：捕获 `ValueError` → HTTP 409；not found → HTTP 404。
- 测试：`test_delete_draft_returns_200`、`test_delete_inactive_returns_200`、`test_delete_active_returns_409` 全部通过，且验证 ACTIVE agent 删除后仍可 GET。

### SC5: AgentStatusHistory 自动写入 — from_status/to_status/changed_at

**VERIFIED.**

- `entity.py:78-95`：`AgentStatusHistory` 表含 `from_status`（nullable，创建时为 None）、`to_status`（nullable=False）、`changed_at`（default=datetime.now, nullable=False）。
- `agent_service.py:107-113`：`create_agent()` 在 flush 后写初始 history 行（`from_status=None, to_status=DRAFT`），与状态创建同一 `commit()`。
- `agent_service.py:175-181`：`change_status()` 将状态更新和 history 写入放在同一 `commit()` 中——原子性保证。
- `cascade="all, delete-orphan"`：Agent 删除时 history 自动级联清理，`test_cascade_deletes_history` 验证通过。
- `test_every_transition_creates_history_row`：3 次转换 + 1 条初始行 = 4 行，精确匹配。

---

_Verified: 2026-05-18T10:30:00Z_
_Verifier: Claude (gsd-verifier)_

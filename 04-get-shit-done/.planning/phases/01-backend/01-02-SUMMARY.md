---
phase: 01-backend
plan: 02
subsystem: api
tags: [python, fastapi, sqlalchemy, state-machine, agent-service, business-logic]

# Dependency graph
requires:
  - phase: 01-01
    provides: AgentStatusHistory ORM model, Agent.status_history relationship, AgentCreate/StatusChangeRequest schemas

provides:
  - AgentService class with 5 public methods + 1 private guard
  - VALID_TRANSITIONS state machine dict (DRAFT→ACTIVE, ACTIVE→INACTIVE, INACTIVE→ACTIVE)
  - InvalidTransitionError (→ HTTP 409 Conflict)
  - ActivationNotReadyError (→ HTTP 422 Unprocessable Entity)
  - Atomic status update + history row write in change_status()
  - Selectinload-optimized list_agents() (no N+1)
  - Joinedload-optimized get_agent() (single-query detail)

affects:
  - 01-03  # endpoints.py 需要 import AgentService + 捕获 InvalidTransitionError / ActivationNotReadyError
  - 01-04  # pytest 测试直接实例化 AgentService，不走 HTTP 层

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SQLAlchemy 2.x select()+execute() style (agent_service.py) vs legacy db.query() (prompt_service.py) — 两种模式在同一代码库共存，注释说明有意设计"
    - "双异常类模型：InvalidTransitionError vs ActivationNotReadyError 让路由层用单个 except 子句映射到 409 vs 422"
    - "flush() before history insert — 确保 agent.id 在同一 transaction 内可用"
    - "_assert_activation_ready() 对所有 target=ACTIVE 路径统一调用，防止 INACTIVE→ACTIVE 绕过校验"

key-files:
  created:
    - backend/app/services/agent_service.py
  modified: []

key-decisions:
  - "使用 SQLAlchemy 2.x select()+execute() 而非 db.query()，与 prompt_service.py 有意不同，模块 docstring 说明原因"
  - "InvalidTransitionError 和 ActivationNotReadyError 都继承 ValueError，确保 except ValueError 降级捕获可用，同时路由层可精确捕获"
  - "create_agent() 在 flush() 后写初始 history 行（from_status=None），从创建时刻起即有完整审计追踪"
  - "delete_agent() 对 ACTIVE 状态直接 raise ValueError（中文消息），由级联删除自动清理 history 行"

patterns-established:
  - "Service 层拥有所有业务规则，endpoint 只做 HTTP 翻译（Plan 03 责任边界）"
  - "校验顺序：not_found → 转换合法性 → 激活前置 → 原子写入（404 before 409 before 422）"
  - "selectinload 用于列表（批量 IN-clause），joinedload 用于单条详情（单查询 JOIN）"

requirements-completed: [AGENT-01, AGENT-02, AGENT-03, AGENT-04, STATE-01, STATE-02]

# Metrics
duration: 8min
completed: 2026-05-18
---

# Phase 01 Plan 02: AgentService Summary

**AgentService 状态机核心：VALID_TRANSITIONS 字典 + 双异常类 + 6 个方法（含 selectinload/joinedload 查询优化和原子 status+history 写入）**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-18T10:36:00Z
- **Completed:** 2026-05-18T10:44:55Z
- **Tasks:** 1
- **Files modified:** 1 (created)

## Accomplishments

- 实现完整的 AgentService，单文件包含所有业务规则（状态机 + CRUD + 查询优化）
- 双异常类设计（InvalidTransitionError / ActivationNotReadyError）使路由层用最少代码实现精确 HTTP 状态码映射
- list_agents() 使用 selectinload 确保无论返回多少条记录，最多只发 3 条 SQL（主查询 + model IN-clause + prompt IN-clause）
- change_status() 原子性保证：status 更新和 history 行在同一 db.commit() 中，SQLite 事务确保两者同时成功或回滚
- _assert_activation_ready() 同时守护 DRAFT→ACTIVE 和 INACTIVE→ACTIVE，防止重新激活时依赖已删除

## Method Signatures

```python
class AgentService:
    def __init__(self, db: Session): ...
    def list_agents(self, skip: int = 0, limit: int = 100, status: AgentStatus | None = None) -> list[Agent]: ...
    def get_agent(self, agent_id: int) -> Agent | None: ...
    def create_agent(self, data: AgentCreate) -> Agent: ...
    def _assert_activation_ready(self, agent: Agent) -> None: ...  # raises ActivationNotReadyError
    def change_status(self, agent_id: int, data: StatusChangeRequest) -> Agent: ...
    def delete_agent(self, agent_id: int) -> bool: ...
```

## Exception Subclasses

| Exception | Inherits | HTTP Mapping | When Raised |
|-----------|----------|--------------|-------------|
| `InvalidTransitionError` | `ValueError` | 409 Conflict | 转换不在 VALID_TRANSITIONS 中（如 ACTIVE→DRAFT） |
| `ActivationNotReadyError` | `ValueError` | 422 Unprocessable | 激活前置条件不满足（无 model_id/prompt_id，或实体已删除） |

## Task Commits

1. **Task 1: Create AgentService with state machine, custom exceptions, and 6 methods** - `53a1861` (feat)

## Files Created/Modified

- `backend/app/services/agent_service.py` — AgentService（207 行），包含 VALID_TRANSITIONS、2 个异常类、6 个方法

## Functional Smoke Test Output

```
OK              ← 单元验证（状态机结构、异常继承、方法存在、源码无 db.query）
functional OK   ← 完整功能测试（内存 SQLite，覆盖所有 6 条业务规则）
```

具体覆盖场景：
- create_agent → 强制 DRAFT + 初始 history 行（from_status=None）
- DRAFT→ACTIVE 激活 + history 写入
- ACTIVE→DRAFT 非法转换 → InvalidTransitionError
- ACTIVE 状态删除 → ValueError（"激活状态"）
- ACTIVE→INACTIVE→删除 → True（级联清理 history）
- 无 model_id 激活 → ActivationNotReadyError

## Decisions Made

- 使用 SQLAlchemy 2.x `select()+execute()` 风格，与 `prompt_service.py` 的 `db.query()` 有意不同，模块 docstring 说明原因
- 两个异常类均继承 `ValueError`，保证旧代码 `except ValueError` 降级兼容
- `create_agent()` 在 `flush()` 后立即写初始 history 行，确保 `agent.id` 在同一事务内可用
- 删除 ACTIVE Agent 使用中文错误消息（"无法删除：Agent 正处于激活状态，请先停用"），直接适合前端展示

## Deviations from Plan

None - plan executed exactly as written.

唯一需要说明的细节：验收标准中的 `db.query` 过滤命令（`grep -v '^\s*"""'`）在模块级多行 docstring 的中间行会误判，但通过 `inspect.getsource(AgentService)` 验证证实 AgentService 类体内无任何 `db.query` 调用，符合要求。

## Issues Encountered

None.

## Known Stubs

None — AgentService 所有方法均有完整实现，无 placeholder。

## Next Phase Readiness

- Plan 03（endpoints.py）可直接 `from app.services.agent_service import AgentService, InvalidTransitionError, ActivationNotReadyError` 并实现 5 个 HTTP 端点
- Plan 04（pytest）可实例化 `AgentService(db)` 不走 HTTP 层，直接测试业务规则
- `AgentRead.model_name` / `AgentRead.prompt_name` 字段需要 endpoint 层或 schema validator 处理（`prompt.title` vs `prompt_name` 字段名不同）——这是 Plan 03 需要处理的

---
*Phase: 01-backend*
*Completed: 2026-05-18*

## Self-Check: PASSED

- `backend/app/services/agent_service.py`: FOUND (207 lines)
- commit `53a1861`: FOUND

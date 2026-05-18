# Architecture Research

**Domain:** Agent state machine in brownfield FastAPI + SQLAlchemy 2.x monolith
**Researched:** 2026-05-18
**Confidence:** HIGH (based on direct codebase analysis, no speculation)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     HTTP Layer (FastAPI)                          │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────┐  │
│  │ models_     │  │  prompts_router  │  │    agents_router     │  │
│  │ router      │  │  (existing)      │  │    (NEW — to add)    │  │
│  └──────┬──────┘  └────────┬────────┘  └──────────┬───────────┘  │
├─────────┴──────────────────┴──────────────────────┴──────────────┤
│                    Service Layer (business logic)                  │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────┐  │
│  │ ModelService│  │  PromptService   │  │    AgentService      │  │
│  │ (existing)  │  │  (existing)      │  │    (NEW — to build)  │  │
│  └──────┬──────┘  └────────┬────────┘  └──────────┬───────────┘  │
├─────────┴──────────────────┴──────────────────────┴──────────────┤
│                    ORM Layer (SQLAlchemy 2.x)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │  Model   │  │  Prompt  │  │  Agent   │  │ AgentStatusHistory│ │
│  │(existing)│  │(existing)│  │(existing)│  │    (NEW — to add) │ │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘ │
│                                     SQLite                         │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Notes |
|-----------|----------------|-------|
| `agents_router` | HTTP boundary: parse request, call service, wrap in `Response[T]`, raise `HTTPException` | Mirror `models_router` / `prompts_router` pattern |
| `AgentService` | All business logic: state machine validation, activation pre-checks, history writes, delete guard | All rules live here, never in router |
| `Agent` (ORM) | Persistence model for agent rows; holds FK refs to Model and Prompt | Already exists in `entity.py` |
| `AgentStatusHistory` (ORM) | Append-only audit log: who changed what state to what, when, and why | New table — add to `entity.py` |

---

## AgentStatusHistory Table Design

Add to `backend/app/models/entity.py` alongside existing models:

```python
class AgentStatusHistory(Base):
    """Agent 状态变更审计日志（append-only）"""
    __tablename__ = "agent_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, comment="所属 Agent"
    )
    from_status: Mapped[AgentStatus | None] = mapped_column(
        Enum(AgentStatus), nullable=True, comment="变更前状态（创建时为 NULL）"
    )
    to_status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus), nullable=False, comment="变更后状态"
    )
    reason: Mapped[str | None] = mapped_column(String(500), comment="变更原因（可选）")
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, comment="变更时间"
    )

    agent: Mapped["Agent"] = relationship(back_populates="status_history")
```

Also add to `Agent` model:

```python
status_history: Mapped[list["AgentStatusHistory"]] = relationship(
    back_populates="agent", cascade="all, delete-orphan", order_by="AgentStatusHistory.changed_at"
)
```

**Design rationale:**
- `from_status` is nullable so the initial DRAFT creation can be recorded (no prior state)
- `ondelete="CASCADE"` — history rows are meaningless without the agent; deleting agent cleans up history automatically
- `reason` is nullable — only PATCH /status requests need it; auto-transitions (creation) don't
- No `changed_by` field — the project has no auth (out of scope per PROJECT.md)
- `changed_at` uses `default=datetime.now` matching the rest of the codebase (not `server_default`)

**Table auto-creation:** `main.py` already calls `Base.metadata.create_all(bind=engine)` at startup. Adding `AgentStatusHistory` to `entity.py` is sufficient — no migration needed for SQLite.

---

## AgentService Method Signatures

File: `backend/app/services/agent_service.py`

```python
from sqlalchemy.orm import Session
from app.models.entity import Agent, AgentStatus, AgentStatusHistory
from app.schemas.schema import AgentCreate, StatusChangeRequest

# State machine: valid (from, to) pairs
VALID_TRANSITIONS: dict[AgentStatus, list[AgentStatus]] = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def list_agents(
        self, skip: int = 0, limit: int = 100,
        status: AgentStatus | None = None
    ) -> list[Agent]:
        """列表（分页 + 状态筛选）。使用 joinedload 避免 N+1，前端需要 model_name / prompt_name。"""

    def get_agent(self, agent_id: int) -> Agent | None:
        """单条查询，joinedload model + prompt。"""

    def create_agent(self, data: AgentCreate) -> Agent:
        """创建 Agent（status 强制为 DRAFT），同时写入首条 AgentStatusHistory。"""

    def change_status(
        self, agent_id: int, data: StatusChangeRequest
    ) -> Agent:
        """
        核心状态机方法。
        1. 验证 (current → target) 是否在 VALID_TRANSITIONS 中，否则 raise ValueError
        2. 若 target == ACTIVE：检查 model_id / prompt_id 不为 None，
           且对应 Model / Prompt 行存在，否则 raise ValueError（带具体原因）
        3. 更新 agent.status
        4. 写入 AgentStatusHistory(from_status=old, to_status=new, reason=data.reason)
        5. commit + refresh
        Returns updated Agent.
        Raises ValueError with descriptive message (router translates to 422).
        """

    def delete_agent(self, agent_id: int) -> bool:
        """
        删除保护：ACTIVE 状态不可删除，raise ValueError。
        DRAFT / INACTIVE 直接删除（CASCADE 清理 history）。
        Returns False if not found.
        """
```

**Why `ValueError` not `HTTPException` in service:**
- Service layer must not import `fastapi` — keeps it unit-testable without HTTP context
- Router layer catches `ValueError` and converts to `HTTPException(status_code=422)`
- This is the standard pattern in this codebase (service raises, router handles HTTP mapping)

---

## Schema Extensions

All additions go in `backend/app/schemas/schema.py`.

### New schemas to add

```python
# ─── AgentStatusHistory ──────────────────────────────────────────

class StatusChangeRequest(BaseModel):
    """PATCH /agents/{id}/status 的请求体"""
    status: AgentStatus          # target state (use the enum, not raw str)
    reason: str | None = None    # optional, stored in history


class StatusHistoryRead(BaseModel):
    id: int
    from_status: AgentStatus | None
    to_status: AgentStatus
    reason: str | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### Extend existing `AgentRead`

Replace the current `AgentRead` with:

```python
class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    model_id: int | None
    prompt_id: int | None
    status: AgentStatus           # use enum type, not raw str
    created_at: datetime
    # resolved names for frontend display (no extra round-trips needed)
    model_name: str | None = None
    prompt_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
```

**Why `model_name`/`prompt_name` on `AgentRead`:**
- Frontend needs to display these in the list view
- If omitted, frontend must call `/models/{id}` and `/prompts/{id}` for each row (N+1 in the client)
- These fields are populated by `AgentService.list_agents()` using `joinedload`
- Pydantic `from_attributes=True` with `agent.model.name` requires eager loading — service must use `options(joinedload(Agent.model), joinedload(Agent.prompt))`

**Change `status` type from `str` to `AgentStatus`:**
- Current `AgentRead.status: str` accepts any string
- Using `AgentStatus` enum makes OpenAPI spec self-documenting and prevents invalid values slipping through serialization

---

## Recommended Project Structure (new files only)

```
backend/app/
├── models/
│   └── entity.py              # ADD: AgentStatusHistory class + Agent.status_history backref
├── schemas/
│   └── schema.py              # ADD: StatusChangeRequest, StatusHistoryRead; EXTEND: AgentRead
├── services/
│   ├── prompt_service.py      # unchanged
│   └── agent_service.py       # NEW: AgentService with state machine
└── api/v1/
    ├── endpoints.py            # ADD: agents_router (5 endpoints)
    └── router.py               # ADD: include_router(agents_router, prefix="/agents")
```

---

## Build Order (dependency chain)

```
1. entity.py — add AgentStatusHistory model + Agent.status_history relationship
      ↓ (table must exist before service writes rows)
2. schema.py — add StatusChangeRequest, StatusHistoryRead; extend AgentRead
      ↓ (service imports schemas)
3. agent_service.py — implement AgentService (imports entity + schema)
      ↓ (router imports service)
4. endpoints.py — add agents_router (imports service + schemas)
      ↓ (router.py imports endpoints)
5. router.py — register agents_router with prefix="/agents"
      ↓ (already picked up by main.py via v1_router)
6. Tests — pytest for the 5 business rules (unit tests on AgentService with in-memory SQLite)
      ↓
7. Frontend — AgentList.vue + stores/agent.js + api/agents.js
```

**Critical ordering note:** Steps 1–5 are a hard sequential dependency. Steps 6 and 7 can run in parallel once steps 1–5 complete.

---

## Router Registration (non-breaking addition)

Current `router.py`:
```python
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
```

After addition:
```python
from .endpoints import models_router, prompts_router, agents_router   # extend import

router.include_router(models_router,  prefix="/models",  tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
router.include_router(agents_router,  prefix="/agents",  tags=["agents"])   # add this line
```

This is purely additive — existing routes are unaffected. Final URL prefix for agents: `/api/v1/agents/` (via `API_PREFIX` in `main.py`).

---

## Data Flow: State Transition Request

```
PATCH /api/v1/agents/{id}/status
  { "status": "active", "reason": "ready for production" }
         ↓
  agents_router.change_agent_status(agent_id, body, db)
         ↓
  AgentService(db).change_status(agent_id, data)
    ├── get_agent(agent_id) → 404 if missing
    ├── validate transition: DRAFT → ACTIVE in VALID_TRANSITIONS? ✓
    ├── if target == ACTIVE:
    │     check agent.model_id is not None → else ValueError("model required")
    │     check db.get(Model, agent.model_id) exists → else ValueError("model not found")
    │     check agent.prompt_id is not None → else ValueError("prompt required")
    │     check db.get(Prompt, agent.prompt_id) exists → else ValueError("prompt not found")
    ├── agent.status = AgentStatus.ACTIVE
    ├── db.add(AgentStatusHistory(agent_id, from=DRAFT, to=ACTIVE, reason=...))
    └── db.commit() + db.refresh(agent)
         ↓
  Response[AgentRead](data=agent)
         ↓  (on ValueError)
  HTTPException(status_code=422, detail=str(e))
```

---

## Architectural Patterns

### Pattern 1: VALID_TRANSITIONS dict as state machine

**What:** A module-level dict mapping `AgentStatus → list[AgentStatus]` defines all legal transitions. Validation is a single `if target not in VALID_TRANSITIONS[current]` check.

**When to use:** When transitions are static business rules (not data-driven). Adding a new status means updating the dict in one place.

**Trade-offs:** Simple and readable; not suitable if transitions need per-instance conditions beyond what the service already handles.

```python
VALID_TRANSITIONS = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

def _validate_transition(self, current: AgentStatus, target: AgentStatus) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ValueError(f"Cannot transition from {current.value} to {target.value}")
```

### Pattern 2: joinedload for related names in list queries

**What:** Use `options(joinedload(Agent.model), joinedload(Agent.prompt))` to eagerly load related rows in a single SQL JOIN, then map `agent.model.name` to `AgentRead.model_name`.

**When to use:** Any list endpoint where the response schema requires fields from related tables.

**Trade-offs:** Adds a JOIN on every list query; acceptable at this scale (SQLite, small dataset). Avoids N+1 at zero additional complexity cost.

```python
from sqlalchemy.orm import joinedload

def list_agents(self, skip=0, limit=100, status=None) -> list[Agent]:
    query = self.db.query(Agent).options(
        joinedload(Agent.model),
        joinedload(Agent.prompt),
    )
    if status:
        query = query.filter(Agent.status == status)
    return query.offset(skip).limit(limit).all()
```

Note: The codebase uses legacy `self.db.query()` style (not `select()`). Match that style for consistency, even though SQLAlchemy 2.x supports both.

### Pattern 3: Service raises ValueError, router converts to HTTPException

**What:** Service methods raise plain `ValueError` with a descriptive message. The router catches it and raises `HTTPException(422)`.

**When to use:** All business rule violations in this codebase.

**Trade-offs:** Keeps service layer testable without FastAPI; router becomes the HTTP-to-domain translator. No custom exception classes needed for this scale.

```python
# In router (endpoints.py):
@agents_router.patch("/{agent_id}/status", response_model=Response[AgentRead])
def change_agent_status(agent_id: int, body: StatusChangeRequest, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        updated = service.change_status(agent_id, body)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return Response(data=updated)
```

---

## Anti-Patterns

### Anti-Pattern 1: Business logic in the router

**What people do:** Put state transition validation directly in the endpoint function.

**Why it's wrong:** Untestable without HTTP context; duplicates if multiple endpoints trigger the same validation; diverges from the established `prompt_service.py` pattern.

**Do this instead:** All validation in `AgentService.change_status()`. Router only handles HTTP concerns (404, wrapping response).

### Anti-Pattern 2: Querying related entities separately to get names

**What people do:** Return `agent.model_id` from the list endpoint, then call `/models/{id}` from the frontend for each row.

**Why it's wrong:** N+1 HTTP requests in the frontend; poor UX (list renders then names populate with delay).

**Do this instead:** Use `joinedload` in `list_agents`, expose `model_name`/`prompt_name` directly on `AgentRead`.

### Anti-Pattern 3: Storing status as raw string in `AgentRead`

**What people do:** Keep `status: str` on the schema (as it currently exists).

**Why it's wrong:** Frontend receives arbitrary strings; OpenAPI spec doesn't constrain values; bugs like `"Active"` vs `"active"` slip through.

**Do this instead:** Use `AgentStatus` enum type. Pydantic will serialize it to its `.value` (e.g. `"active"`) in JSON responses automatically.

---

## Sources

- Direct codebase analysis: `entity.py`, `schema.py`, `prompt_service.py`, `endpoints.py`, `router.py`, `main.py`
- SQLAlchemy `joinedload` with legacy query API: consistent with existing `self.db.query()` pattern in `prompt_service.py`
- Pydantic v2 `from_attributes=True` with nested relationship access: standard pattern, requires eager loading
- State machine as dict lookup: pattern used in Round 3 (OpenSpec) of this experiment (`TRANSITIONS` mapping table — noted as best design in `CLAUDE.md`)

---
*Architecture research for: Agent state machine in FastAPI + SQLAlchemy 2.x (brownfield)*
*Researched: 2026-05-18*

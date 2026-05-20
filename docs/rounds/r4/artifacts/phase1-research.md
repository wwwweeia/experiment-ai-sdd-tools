<!-- 此文件由 docs:collect 自动生成，源：04-get-shit-done/.planning/phases/01-backend/01-RESEARCH.md。请编辑源文件而非本文件。 -->

# Phase 1: Backend - Research

**Researched:** 2026-05-18
**Domain:** FastAPI + SQLAlchemy 2.x state machine — Agent CRUD + three-state lifecycle (DRAFT/ACTIVE/INACTIVE) + append-only audit history
**Confidence:** HIGH

---

## Summary

Phase 1 adds a complete Agent management API to an already-running FastAPI monolith. The existing codebase provides a fully working Model + Prompt CRUD stack (3 layers: Router → Service → ORM), a `Response[T]` wrapper convention, and a SQLite database managed by `create_all()`. The `Agent` ORM model and skeleton Pydantic schemas already exist in `entity.py` and `schema.py` — they need targeted extension, not replacement.

The work is purely additive. No new Python dependencies are required. The state machine has 3 states and 3 valid transitions (DRAFT→ACTIVE, ACTIVE→INACTIVE, INACTIVE→ACTIVE), implemented as a `VALID_TRANSITIONS` dict inside `AgentService`. A new `AgentStatusHistory` table provides the append-only audit log required by STATE-02. The existing `PromptService` / `endpoints.py` files serve as the implementation reference for every structural decision.

The most consequential design choice — already locked in prior research — is separating business-rule errors into two HTTP status codes: 409 for invalid state transitions and 422 for activation pre-condition failures (missing model/prompt). This two-code convention is the foundation the frontend will build its error-display logic on.

**Primary recommendation:** Follow the build order entity.py → schema.py → agent_service.py → endpoints.py → router.py → tests, writing each layer to completion before starting the next. No parallel work within this phase until step 5 is done.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGENT-01 | 用户可以获取 Agent 列表（支持分页、按状态筛选） | `list_agents()` with `selectinload` + optional `status` filter; `AgentRead` extended with `model_name`/`prompt_name` |
| AGENT-02 | 用户可以获取单个 Agent 详情（含关联 Model 和 Prompt 名称） | `get_agent()` with `joinedload`; same extended `AgentRead` schema |
| AGENT-03 | 用户可以创建 Agent（初始状态固定为 DRAFT） | `AgentCreate` must NOT expose `status` field; service hard-codes `AgentStatus.DRAFT` |
| AGENT-04 | 用户可以删除 DRAFT 或 INACTIVE Agent；ACTIVE 返回错误 | Delete guard in `AgentService.delete_agent()`; raise `ValueError` → 409 Conflict in router |
| STATE-01 | PATCH /agents/{id}/status 执行状态机转换，含业务规则验证 | `VALID_TRANSITIONS` dict; `_assert_activation_ready()` guard; 409 for invalid transition; 422 for pre-condition fail |
| STATE-02 | 每次状态变更自动写入 AgentStatusHistory 记录 | `AgentStatusHistory` ORM table (new); written in same `db.commit()` as status update |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agent CRUD operations | API / Backend (AgentService) | Database (SQLAlchemy ORM) | Service layer owns business logic; ORM owns persistence |
| State machine enforcement | API / Backend (AgentService) | — | All transition rules live in service, never in router or ORM |
| Activation pre-condition checks | API / Backend (AgentService) | Database (db.get lookups) | Requires DB reads for Model/Prompt existence; done inside service |
| History audit writes | API / Backend (AgentService) | Database (AgentStatusHistory table) | Atomic write alongside status update; both in single `db.commit()` |
| HTTP error mapping (409/422/404) | API / Backend (agents_router) | — | Router is the HTTP boundary; translates domain ValueError to HTTP codes |
| Query optimization (no N+1) | API / Backend (AgentService.list_agents) | Database (JOIN/selectinload) | Eager-load at query time; schema exposes resolved names |
| Schema validation (status as enum) | API / Backend (Pydantic schemas) | — | `status: AgentStatus` not `str`; prevents invalid values at deserialization |

---

## Standard Stack

### Core (no new installs — everything already present)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.6 | HTTP routing, request/response model, dependency injection | Already installed; `HTTPException` gives precise status code control |
| SQLAlchemy | 2.0.36 | ORM for Agent + AgentStatusHistory; `select()` + `session.execute()` query style | Already installed; 2.x `Mapped[]` type hints already in use in entity.py |
| Pydantic | 2.10.4 | Schema validation — `AgentCreate`, `AgentRead`, `StatusChangeRequest` | Already installed; v2 `ConfigDict(from_attributes=True)` pattern already established |
| pytest | 8.3.4 | Unit tests for AgentService business rules | Already installed in system Python; no test dir exists yet — Wave 0 creates it |
| httpx | 0.28.1 | FastAPI `TestClient` integration testing | Already installed; required for FastAPI's `TestClient` |

**Installation:** No `pip install` required. All packages are present.

[VERIFIED: direct codebase read — backend/requirements.txt and system pip show]

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sqlalchemy.orm.selectinload` | (part of SQLAlchemy) | Eager-load Agent.model and Agent.prompt on list queries | Always on `list_agents()` — avoids N+1 |
| `sqlalchemy.orm.joinedload` | (part of SQLAlchemy) | Eager-load on single-agent detail queries | `get_agent()` — one agent, one JOIN is fine |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure Python `VALID_TRANSITIONS` dict | python-statemachine 3.1.1 | Library adds install + learning overhead for 3 states; dict is transparent and zero-dep |
| Separate `AgentStatusHistory` table | JSON column on Agent | JSON is unindexable, wasteful to deserialize for every agent read, and harder to query |
| `selectinload` for list queries | `joinedload` on list | `selectinload` issues 2 queries total (cleaner than JOIN for list); `joinedload` better for single-object |

---

## Package Legitimacy Audit

No new packages are installed in this phase. All required libraries are already present in `backend/requirements.txt`.

**Packages removed due to slopcheck [SLOP] verdict:** none — no new packages
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
HTTP Request
    │
    ▼
agents_router  (endpoints.py — FastAPI APIRouter)
    │  parse request body, inject db session via Depends(get_db)
    │  catch ValueError → HTTPException (409 / 422)
    │  wrap result in Response[AgentRead]
    ▼
AgentService(db)  (agent_service.py — business logic)
    │
    ├── list_agents(skip, limit, status?)
    │     └── select(Agent).options(selectinload(Agent.model), selectinload(Agent.prompt))
    │           .where(Agent.status == status?)  →  [Agent, ...]
    │
    ├── get_agent(agent_id)
    │     └── select(Agent).options(joinedload(Agent.model), joinedload(Agent.prompt))
    │           .where(Agent.id == agent_id)  →  Agent | None
    │
    ├── create_agent(data: AgentCreate)
    │     └── Agent(status=DRAFT) + AgentStatusHistory(from=None, to=DRAFT)
    │           → db.commit()  →  Agent
    │
    ├── change_status(agent_id, data: StatusChangeRequest)
    │     ├── validate: target in VALID_TRANSITIONS[current]?  →  ValueError (→ 409)
    │     ├── if target == ACTIVE: _assert_activation_ready()  →  ValueError (→ 422)
    │     ├── agent.status = target
    │     └── AgentStatusHistory(from=old, to=target, reason=data.reason)
    │           → db.commit()  →  Agent
    │
    └── delete_agent(agent_id)
          ├── if ACTIVE: ValueError (→ 409)
          └── db.delete(agent) → db.commit() → True
                (CASCADE deletes AgentStatusHistory rows)
    │
    ▼
SQLAlchemy ORM  (entity.py)
    ├── Agent  (existing table — agents)
    └── AgentStatusHistory  (new table — agent_status_history)
         └── ondelete="CASCADE" FK → agents.id
    │
    ▼
SQLite  (prompt_lab.db)
```

### Recommended Project Structure (new/modified files only)

```
backend/app/
├── models/
│   └── entity.py              # ADD: AgentStatusHistory class; ADD: Agent.status_history backref
├── schemas/
│   └── schema.py              # MODIFY: AgentRead (add model_name, prompt_name, fix status type)
│                              # MODIFY: AgentCreate (remove status field)
│                              # ADD: StatusChangeRequest, StatusHistoryRead
├── services/
│   └── agent_service.py       # NEW: AgentService with VALID_TRANSITIONS state machine
└── api/v1/
    ├── endpoints.py            # ADD: agents_router with 5 endpoints
    └── router.py               # ADD: include_router(agents_router, prefix="/agents")

backend/tests/                 # NEW DIRECTORY (Wave 0 gap)
├── conftest.py                # in-memory SQLite fixture + TestClient factory
└── test_agent_service.py      # unit tests for AgentService business rules
```

### Pattern 1: VALID_TRANSITIONS dict as state machine

**What:** Module-level dict mapping `AgentStatus → list[AgentStatus]` defines all legal transitions. Single lookup validates any transition attempt.

**When to use:** Static business rules with no data-driven branching. Adding a state = update one dict.

```python
# Source: ARCHITECTURE.md (codebase research, cross-referenced with R3 OpenSpec pattern)
VALID_TRANSITIONS: dict[AgentStatus, list[AgentStatus]] = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

def _validate_transition(self, current: AgentStatus, target: AgentStatus) -> None:
    allowed = VALID_TRANSITIONS.get(current, [])
    if target not in allowed:
        raise ValueError(f"Cannot transition from {current.value} to {target.value}")
```

### Pattern 2: Activation guard as separate private method

**What:** Extract the ACTIVE precondition check (model_id + prompt_id non-null, records exist) into `_assert_activation_ready()`. Called from `change_status()` only when target == ACTIVE.

**When to use:** Any activation path — both DRAFT→ACTIVE and INACTIVE→ACTIVE must pass through the same guard.

```python
# Source: ARCHITECTURE.md (codebase research)
def _assert_activation_ready(self, agent: Agent) -> None:
    if not agent.model_id:
        raise ValueError("激活失败：Agent 未关联模型")
    if not agent.prompt_id:
        raise ValueError("激活失败：Agent 未关联提示词")
    model = self.db.get(Model, agent.model_id)
    if not model:
        raise ValueError(f"激活失败：关联模型 (id={agent.model_id}) 已不存在")
    prompt = self.db.get(Prompt, agent.prompt_id)
    if not prompt:
        raise ValueError(f"激活失败：关联提示词 (id={agent.prompt_id}) 已不存在")
```

### Pattern 3: Service raises ValueError, router maps to HTTP status codes

**What:** Service layer raises plain `ValueError`. Router catches and maps: invalid transition → 409, precondition failure → 422, not found → 404.

**When to use:** All business rule violations in this codebase. Keeps service testable without HTTP context.

```python
# Source: endpoints.py pattern (existing models_router / prompts_router)
@agents_router.patch("/{agent_id}/status", response_model=Response[AgentRead])
def change_agent_status(agent_id: int, body: StatusChangeRequest, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        updated = service.change_status(agent_id, body)
    except ValueError as e:
        # Distinguish: invalid transition (409) vs precondition failure (422)
        # Simplest approach: use a custom exception subclass per error category
        raise HTTPException(status_code=422, detail=str(e))
    return Response(data=updated)
```

**Note on 409 vs 422 distinction:** The router must differentiate invalid-transition errors (409 Conflict) from precondition errors (422 Unprocessable). Two options:
1. Use two custom exception subclasses (`InvalidTransitionError(ValueError)`, `ActivationNotReadyError(ValueError)`) and `except` each separately.
2. Use a single `ValueError` but include a machine-readable code in the message and parse it in the router.

Option 1 is cleaner and recommended. [ASSUMED — no locked decision in CONTEXT.md on exception subclass vs single ValueError]

### Pattern 4: Atomic status update + history write in single transaction

**What:** `agent.status = target` and `db.add(AgentStatusHistory(...))` both happen before `db.commit()`. If either fails, the transaction rolls back — no orphaned history rows, no status updates without records.

```python
# Source: ARCHITECTURE.md (codebase research)
def change_status(self, agent_id: int, data: StatusChangeRequest) -> Agent:
    agent = self.get_agent(agent_id)
    if not agent:
        raise ValueError("not found")  # router maps to 404

    old_status = agent.status
    self._validate_transition(old_status, data.status)
    if data.status == AgentStatus.ACTIVE:
        self._assert_activation_ready(agent)

    agent.status = data.status
    history = AgentStatusHistory(
        agent_id=agent.id,
        from_status=old_status,
        to_status=data.status,
        reason=data.reason,
    )
    self.db.add(history)
    self.db.commit()
    self.db.refresh(agent)
    return agent
```

### Pattern 5: selectinload for list queries (no N+1)

**What:** Use `selectinload` for `list_agents()` — issues 2 SQL queries total (one for agents, one each for models/prompts as batched IN-clause), not N+1.

```python
# Source: ARCHITECTURE.md (codebase research) + SQLAlchemy 2.x docs [CITED: docs.sqlalchemy.org]
from sqlalchemy import select
from sqlalchemy.orm import selectinload

def list_agents(self, skip=0, limit=100, status=None) -> list[Agent]:
    stmt = (
        select(Agent)
        .options(selectinload(Agent.model), selectinload(Agent.prompt))
    )
    if status:
        stmt = stmt.where(Agent.status == status)
    stmt = stmt.offset(skip).limit(limit)
    return self.db.execute(stmt).scalars().all()
```

### Anti-Patterns to Avoid

- **Business logic in the router:** Putting `if agent.status == "draft"` in endpoint functions makes rules untestable without HTTP context. All rules belong in AgentService.
- **`status: str` in schema:** Accepts arbitrary strings. Use `AgentStatus` enum type on both `AgentCreate` (remove entirely) and `AgentRead`.
- **`db.query()` in AgentService:** Existing services use legacy query API. New AgentService must use `select()` + `session.execute()` style — document the intention at the top of the file.
- **All errors returning 422:** Invalid transition is a 409 Conflict. Using 422 for everything conflates schema validation errors with state conflicts — the frontend cannot branch.
- **Querying Agent.model separately in a loop:** Classic N+1. Use `selectinload` on the list query.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Eager loading related model names | Manual loop querying Model/Prompt per Agent | `selectinload(Agent.model)` + `selectinload(Agent.prompt)` | SQLAlchemy loads all in 2 queries via IN-clause; manual loop = N+1 |
| Request body validation for status field | Custom string parsing + if/elif for status values | `status: AgentStatus` in Pydantic schema | Pydantic rejects invalid values automatically; enum ensures OpenAPI spec is accurate |
| State machine library | Do NOT install python-statemachine | `VALID_TRANSITIONS` dict | 3 states, 3 transitions — a library adds zero value and violates the no-new-deps constraint |
| Database migration tooling | Do NOT add Alembic | `Base.metadata.create_all()` (already used) | SQLite + `create_all()` is sufficient; new tables are auto-created; existing tables are preserved |
| Test database management | Do NOT use the dev `prompt_lab.db` in tests | `sqlite:///:memory:` + `Base.metadata.create_all()` in pytest fixture | In-memory DB gives test isolation; dev DB accumulates state between runs |

**Key insight:** The existing codebase already provides every building block. The work is wiring, not invention.

---

## Common Pitfalls

### Pitfall 1: `status: str` in existing AgentRead/AgentCreate schemas

**What goes wrong:** `AgentCreate` has `status: str = "draft"` — callers can POST any string and pass Pydantic validation. `AgentRead` has `status: str` — no type constraint on output.

**Why it happens:** Schema was written as a placeholder before state machine design. Importing the enum seemed unnecessary at the time.

**How to avoid:** Remove `status` from `AgentCreate` entirely (creation always yields DRAFT — callers cannot set it). Change `AgentRead.status` to `AgentStatus`. Add `use_enum_values=True` to `model_config` if you want the serialized JSON value to be `"active"` not `<AgentStatus.ACTIVE: 'active'>`.

**Warning signs:** Swagger UI shows `status` as a free-text string in the create request body. `?status=garbage` on GET /agents/ returns an empty list instead of 422.

### Pitfall 2: N+1 queries on Agent list

**What goes wrong:** `Agent.model` and `Agent.prompt` are lazy-loaded by default. Returning 20 agents with `model_name` in the response triggers 41 SQL queries.

**How to avoid:** Use `selectinload(Agent.model), selectinload(Agent.prompt)` in `list_agents()`. The `AgentRead` schema's `model_name`/`prompt_name` fields are then populated from the already-loaded relationship objects.

**Warning signs:** Enable SQLAlchemy `echo=True` and count SELECT statements for a 5-agent list response.

### Pitfall 3: Mixing legacy `db.query()` style in AgentService

**What goes wrong:** Existing services use `self.db.query(Model)`. If AgentService copies this, the codebase has two query styles. SQLAlchemy 3.0 will remove legacy query API.

**How to avoid:** Write AgentService exclusively with `select()` + `session.execute()`. Add a comment: "Uses SQLAlchemy 2.x query style — do NOT use db.query()."

### Pitfall 4: All state errors returning 422 (conflates schema errors with state conflicts)

**What goes wrong:** FastAPI auto-generates 422 for Pydantic failures. If the service also raises 422 for invalid transitions, the frontend cannot distinguish "you sent bad JSON" from "the transition is not allowed."

**How to avoid:** Invalid transition → 409 Conflict. Activation pre-condition failure (missing model/prompt) → 422 Unprocessable. Document this in the router comment and test both codes explicitly.

### Pitfall 5: AgentStatusHistory table missing on existing dev DB

**What goes wrong:** `create_all()` skips existing tables but does create new ones. However, if the dev DB has stale schema from before `AgentStatusHistory` was added, tests may pass locally but break after a DB reset.

**How to avoid:** pytest fixtures must use `sqlite:///:memory:` with fresh `create_all()` per test session. Provide `scripts/reset_db.py` for developers with existing `prompt_lab.db`.

### Pitfall 6: INACTIVE→ACTIVE skips activation guard

**What goes wrong:** Developer implements guard only in the DRAFT→ACTIVE path ("we only check on first activation"). An Agent whose model was deleted while INACTIVE gets re-activated with a dangling FK.

**How to avoid:** The `_assert_activation_ready()` guard runs for any transition where `target == AgentStatus.ACTIVE`, regardless of `from_status`. The `VALID_TRANSITIONS` dict is separate from the precondition check.

### Pitfall 7: 409 returned for ACTIVE agent delete, not a clean error message

**What goes wrong:** Router raises `HTTPException(409)` but with no `detail`, or with an english-only string. Frontend shows a generic error.

**How to avoid:** Return `HTTPException(status_code=409, detail="无法删除：Agent 正处于激活状态，请先停用")`. Frontend Phase 2 will display this directly.

---

## Code Examples

### AgentStatusHistory ORM model

```python
# Source: ARCHITECTURE.md (codebase research)
# Add to backend/app/models/entity.py

class AgentStatusHistory(Base):
    """Agent 状态变更审计日志（append-only — 永不更新，只新增）"""
    __tablename__ = "agent_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, comment="所属 Agent"
    )
    from_status: Mapped[AgentStatus | None] = mapped_column(
        Enum(AgentStatus), nullable=True, comment="变更前状态（首次创建为 NULL）"
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

Also add to `Agent` class:

```python
# In Agent class (entity.py) — add this relationship
status_history: Mapped[list["AgentStatusHistory"]] = relationship(
    back_populates="agent", cascade="all, delete-orphan", order_by="AgentStatusHistory.changed_at"
)
```

### Extended AgentRead schema

```python
# Source: ARCHITECTURE.md (codebase research) + pitfalls analysis
# Replaces existing AgentRead in schema.py

from app.models.entity import AgentStatus   # add this import

class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    model_id: int | None = None
    prompt_id: int | None = None
    # status field REMOVED — always DRAFT on creation

class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    model_id: int | None
    prompt_id: int | None
    status: AgentStatus           # enum type, not str
    created_at: datetime
    model_name: str | None = None   # resolved from Agent.model.name via eager load
    prompt_name: str | None = None  # resolved from Agent.prompt.title via eager load

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class StatusChangeRequest(BaseModel):
    status: AgentStatus
    reason: str | None = None
```

### pytest conftest.py (Wave 0 — must create before any tests)

```python
# Source: PITFALLS.md (codebase research) + pytest docs [ASSUMED for exact fixture structure]
# New file: backend/tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### Router pattern for agents (mirrors existing models_router)

```python
# Source: endpoints.py pattern (existing — direct codebase read)
# Add to backend/app/api/v1/endpoints.py

agents_router = APIRouter()

@agents_router.get("/", response_model=Response[list[AgentRead]])
def list_agents(skip: int = 0, limit: int = 100, status: AgentStatus | None = None,
                db: Session = Depends(get_db)):
    service = AgentService(db)
    data = service.list_agents(skip=skip, limit=limit, status=status)
    return Response(data=data)

@agents_router.patch("/{agent_id}/status", response_model=Response[AgentRead])
def change_agent_status(agent_id: int, body: StatusChangeRequest, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        updated = service.change_status(agent_id, body)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ActivationNotReadyError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return Response(data=updated)

@agents_router.delete("/{agent_id}", response_model=Response[None])
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    try:
        if not service.delete_agent(agent_id):
            raise HTTPException(status_code=404, detail="Agent not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return Response(message="Deleted")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `db.query(Model)` (legacy API) | `session.execute(select(Model))` | SQLAlchemy 2.0 (2023) | New AgentService uses 2.x style; existing services remain legacy until refactor |
| `BaseModel.dict()` | `BaseModel.model_dump()` | Pydantic v2 (2023) | Existing code already uses v2; no action needed |
| `orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` | Pydantic v2 | Already applied in existing Read schemas |

**Deprecated/outdated in this codebase:**
- `self.db.query()` in `prompt_service.py` and `model_service.py`: Still functional in SQLAlchemy 2.x, but deprecated for 3.0. Do not replicate in AgentService.
- `status: str` in existing `AgentRead` / `AgentCreate`: Placeholder — replace with `AgentStatus` enum.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Two custom exception subclasses (`InvalidTransitionError`, `ActivationNotReadyError`) are the cleanest way to distinguish 409 vs 422 in the router | Architecture Patterns (Pattern 3) | Low — single `ValueError` with a flag field also works; either approach is ~5 lines |
| A2 | `prompt_name` maps to `Prompt.title` (not `Prompt.name`) — Prompt model has `title` field, not `name` | Code Examples (AgentRead schema) | Low — confirmed by reading entity.py: `title: Mapped[str]` is the field name |
| A3 | Tests directory should be `backend/tests/` (not `backend/app/tests/` or root-level `tests/`) | Architecture Patterns (project structure) | Low — convention only; adjust to taste |
| A4 | Error messages should be Chinese, consistent with CLAUDE.md language preference | Common Pitfalls | Low — experiment project; either language is acceptable |

**Note on A2:** Confirmed by reading entity.py directly — `Prompt` model has field `title: Mapped[str]`. So `AgentRead.prompt_name` is populated as `agent.prompt.title`. [VERIFIED: direct file read]

---

## Open Questions

1. **Exception subclass vs single ValueError for 409/422 distinction**
   - What we know: Router must return 409 for invalid transition, 422 for pre-condition failure
   - What's unclear: Whether to use two `ValueError` subclasses or a single class with a `code` attribute
   - Recommendation: Two subclasses (`InvalidTransitionError`, `ActivationNotReadyError`) — explicit `except` clauses in router are readable and testable

2. **`create_agent()` should it write an AgentStatusHistory row for initial DRAFT?**
   - What we know: STATE-02 says "每次状态变更" — creation sets initial state but may not be a "change"
   - What's unclear: Does the success criterion ("每次合法的状态切换后") include creation?
   - Recommendation: Write a history row on creation with `from_status=None, to_status=DRAFT`. The `from_status` nullable field was designed for exactly this. Provides complete audit trail.

3. **Prompt.title vs model.name field naming in AgentRead**
   - What we know: `Model.name` and `Prompt.title` are the actual field names (confirmed from entity.py)
   - What's unclear: Should `AgentRead` expose `prompt_name` (aliased) or `prompt_title` (exact)?
   - Recommendation: Use `prompt_name: str | None` aliasing `agent.prompt.title` — frontend consistency is more important than mirroring DB field names exactly

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All backend code | ✓ | (system) | — |
| pytest | Business rule tests | ✓ | 8.3.4 | — |
| httpx | FastAPI TestClient | ✓ | 0.28.1 | — |
| FastAPI | API endpoints | ✓ | 0.115.6 (requirements.txt) | — |
| SQLAlchemy | ORM | ✓ | 2.0.36 (requirements.txt) | — |
| Pydantic | Schema validation | ✓ | 2.10.4 (requirements.txt) | — |
| SQLite | Database | ✓ | (bundled with Python) | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

**Note:** `pytest-asyncio` is NOT required — FastAPI endpoints are synchronous in this codebase (no `async def` on any existing endpoint). `TestClient` from `httpx` handles sync endpoints correctly.

---

## Validation Architecture

> `nyquist_validation` is explicitly `false` in config.json — this section is included for reference but not gating.

The existing codebase has no `backend/tests/` directory. All five business rules (AGENT-04, STATE-01 x3, STATE-02) require new test files. The planner should include a Wave 0 task to create the test infrastructure before any implementation task that claims test coverage.

### Wave 0 Gaps

- [ ] `backend/tests/__init__.py` — makes tests/ a package
- [ ] `backend/tests/conftest.py` — in-memory SQLite fixture + TestClient factory
- [ ] `backend/tests/test_agent_service.py` — unit tests for AgentService (no HTTP client needed)
- [ ] `backend/tests/test_agent_api.py` — integration tests via TestClient for all 5 endpoints

### Business Rule → Test Map

| Req ID | Behavior | Test Type | File |
|--------|----------|-----------|------|
| AGENT-01 | GET /agents/ returns paginated list with model_name/prompt_name | integration | test_agent_api.py |
| AGENT-01 | GET /agents/?status=active returns only ACTIVE agents | integration | test_agent_api.py |
| AGENT-01 | GET /agents/?status=garbage returns 422 | integration | test_agent_api.py |
| AGENT-02 | GET /agents/{id} returns model_name + prompt_name | integration | test_agent_api.py |
| AGENT-03 | POST /agents/ creates with status=DRAFT regardless of body | integration | test_agent_api.py |
| AGENT-04 | DELETE DRAFT/INACTIVE agent → 200 | integration | test_agent_api.py |
| AGENT-04 | DELETE ACTIVE agent → 409 | integration | test_agent_api.py |
| STATE-01 | DRAFT→ACTIVE with valid model+prompt → 200 | unit | test_agent_service.py |
| STATE-01 | DRAFT→ACTIVE without model_id → 422 | unit | test_agent_service.py |
| STATE-01 | DRAFT→ACTIVE with deleted model → 422 | unit | test_agent_service.py |
| STATE-01 | ACTIVE→INACTIVE → 200 | unit | test_agent_service.py |
| STATE-01 | INACTIVE→ACTIVE re-validates model+prompt | unit | test_agent_service.py |
| STATE-01 | ACTIVE→DRAFT → 409 (invalid transition) | unit | test_agent_service.py |
| STATE-02 | Every valid transition writes AgentStatusHistory row | unit | test_agent_service.py |
| STATE-02 | History row contains correct from_status/to_status | unit | test_agent_service.py |

---

## Project Constraints (from CLAUDE.md)

Extracted from `./CLAUDE.md` (project-level) and `../CLAUDE.md` (parent workspace):

| Directive | Source | Impact on Phase 1 |
|-----------|--------|-------------------|
| No new Python dependencies | PROJECT.md / STACK.md | No `pip install` in this phase; state machine is pure Python dict |
| Use SQLAlchemy 2.x style (`select()` + `execute()`) in AgentService | PROJECT.md / STACK.md | Do NOT use `db.query()` in `agent_service.py` |
| All validation/business rules in Service layer, not Router | ARCHITECTURE.md / PITFALLS.md | Router only: 404 lookup + HTTPException mapping |
| Unified `Response[T]` wrapper on all endpoints | `schema.py` / `endpoints.py` pattern | All 5 agent endpoints return `Response[AgentRead]` or `Response[None]` |
| AgentCreate must NOT expose `status` field | REQUIREMENTS.md (AGENT-03) | Remove `status: str = "draft"` from existing `AgentCreate` schema |
| 409 for invalid transition, 422 for precondition failure | PITFALLS.md / STATE-01 | Distinct exception types required to route to correct HTTP code |
| `AgentRead` must include `model_name`/`prompt_name` | REQUIREMENTS.md (AGENT-01, AGENT-02) | Extend schema + use `selectinload` / `joinedload` in service |
| Tests use in-memory SQLite, never the dev DB | PITFALLS.md | `sqlite:///:memory:` in conftest.py fixture |

---

## Sources

### Primary (HIGH confidence)
- Direct codebase read: `entity.py`, `schema.py`, `prompt_service.py`, `endpoints.py`, `router.py`, `main.py`, `database.py`, `requirements.txt` — all read at research time
- `.planning/research/ARCHITECTURE.md` — full AgentService method signatures and data flow diagram
- `.planning/research/STACK.md` — no-new-deps decision, VALID_TRANSITIONS pattern rationale
- `.planning/research/PITFALLS.md` — 9 pitfalls with exact file/line references from codebase
- `.planning/research/SUMMARY.md` — executive decisions already locked

### Secondary (MEDIUM confidence)
- `.planning/codebase/CONVENTIONS.md` — naming conventions, Pinia store structure, error handling patterns
- `.planning/codebase/TESTING.md` — confirmed no existing backend tests dir; E2E only

### Tertiary (LOW confidence — none)
No claims in this research rely on WebSearch-only sources. All findings are derived from direct codebase analysis and locked prior research.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — read directly from requirements.txt and system pip
- Architecture: HIGH — derived from direct codebase analysis and prior research; no speculation
- Pitfalls: HIGH — all grounded in actual file contents (line references included in PITFALLS.md)
- Test infrastructure: HIGH — pytest 8.3.4 confirmed installed; gap is lack of test directory, not missing tools

**Research date:** 2026-05-18
**Valid until:** 2026-06-18 (stable stack — FastAPI/SQLAlchemy versions locked in requirements.txt)

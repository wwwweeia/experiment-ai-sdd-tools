# Phase 1: Backend - Pattern Map

**Mapped:** 2026-05-18
**Files analyzed:** 7 (new/modified)
**Analogs found:** 7 / 7

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/models/entity.py` | model | CRUD | self (existing file — add AgentStatusHistory class) | exact |
| `backend/app/schemas/schema.py` | model | request-response | self (existing file — extend AgentRead, add StatusChangeRequest) | exact |
| `backend/app/services/agent_service.py` | service | CRUD + event-driven (state machine) | `backend/app/services/prompt_service.py` | role-match |
| `backend/app/api/v1/endpoints.py` | controller | request-response | self (existing file — add agents_router) | exact |
| `backend/app/api/v1/router.py` | config | request-response | self (existing file — register agents_router) | exact |
| `backend/tests/conftest.py` | config (test infra) | CRUD | `01-superpowers/backend/tests/conftest.py` | exact |
| `backend/tests/test_agent_api.py` | test | request-response | `01-superpowers/backend/tests/test_agent_api.py` | exact |

---

## Pattern Assignments

### `backend/app/models/entity.py` (model — additive modification)

**Analog:** self (`backend/app/models/entity.py`) — new class appended after existing ones.

**Existing import block** (lines 1-5) — AgentStatusHistory needs the same imports plus `datetime`:
```python
import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
```

**Existing ORM model pattern** (lines 14-25) — copy `Model` as structural template:
```python
class Model(Base):
    """LLM 模型配置"""
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模型名称")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    agents: Mapped[list["Agent"]] = relationship(back_populates="model")
```

**Existing enum pattern** (lines 8-11) — `AgentStatus` is already defined, `AgentStatusHistory` uses it:
```python
class AgentStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
```

**Existing nullable FK pattern** (lines 49-50) — `AgentStatusHistory.agent_id` follows the same FK convention but adds `ondelete="CASCADE"`:
```python
model_id: Mapped[int | None] = mapped_column(ForeignKey("models.id"), comment="关联模型")
prompt_id: Mapped[int | None] = mapped_column(ForeignKey("prompts.id"), comment="关联提示词")
```

**Existing relationship with cascade pattern** (lines 58-59) — `Agent.skills` shows back_populates + cascade direction to copy for `Agent.status_history`:
```python
skills: Mapped[list["Skill"]] = relationship(back_populates="agent")
```

**What to ADD to `Agent` class** (after existing `skills` relationship, line 59):
```python
# Add this relationship to Agent class
status_history: Mapped[list["AgentStatusHistory"]] = relationship(
    back_populates="agent", cascade="all, delete-orphan", order_by="AgentStatusHistory.changed_at"
)
```

**New class to APPEND at end of file:**
```python
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

---

### `backend/app/schemas/schema.py` (model — additive modification)

**Analog:** self (`backend/app/schemas/schema.py`) — extend AgentRead in place, add new schemas.

**Existing Read schema pattern** (lines 46-56) — `PromptRead` is the canonical template for `AgentRead`:
```python
class PromptRead(BaseModel):
    id: int
    title: str
    content: str
    variables: str | None
    tags: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Existing Create schema pattern** (lines 38-43) — `PromptCreate` shows the no-status, optional-fields pattern to follow for `AgentCreate`:
```python
class PromptCreate(BaseModel):
    title: str
    content: str
    variables: str | None = None
    tags: str | None = None
    created_by: str | None = None
```

**Existing AgentCreate to REPLACE** (lines 61-66) — current has `status: str = "draft"` which must be removed:
```python
# CURRENT (to replace):
class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    model_id: int | None = None
    prompt_id: int | None = None
    status: str = "draft"          # <- REMOVE this field
```

**Existing AgentRead to REPLACE** (lines 69-78) — current `status: str` must become `AgentStatus`, add `model_name`/`prompt_name`:
```python
# CURRENT (to replace):
class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    model_id: int | None
    prompt_id: int | None
    status: str                    # <- change to AgentStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**Required import to add at top of schema.py** — `AgentStatus` is in entity.py:
```python
from app.models.entity import AgentStatus
```

**New / replacement schemas to write in the `# ─── Agent ───` section:**
```python
class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    model_id: int | None = None
    prompt_id: int | None = None
    # status intentionally omitted — creation always yields DRAFT

class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    model_id: int | None
    prompt_id: int | None
    status: AgentStatus
    created_at: datetime
    model_name: str | None = None   # populated by eager-load in service
    prompt_name: str | None = None  # populated by eager-load in service

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class StatusChangeRequest(BaseModel):
    status: AgentStatus
    reason: str | None = None

class StatusHistoryRead(BaseModel):
    id: int
    from_status: AgentStatus | None
    to_status: AgentStatus
    reason: str | None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

### `backend/app/services/agent_service.py` (service — new file)

**Analog:** `backend/app/services/prompt_service.py`

**Imports pattern** (prompt_service.py lines 1-3):
```python
from sqlalchemy.orm import Session
from app.models.entity import Prompt
from app.schemas.schema import PromptCreate
```
AgentService equivalent:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, joinedload
from app.models.entity import Agent, AgentStatus, AgentStatusHistory, Model, Prompt
from app.schemas.schema import AgentCreate, StatusChangeRequest
```

**Service class constructor pattern** (prompt_service.py lines 6-8):
```python
class PromptService:
    def __init__(self, db: Session):
        self.db = db
```

**CRUD method pattern — list** (prompt_service.py lines 10-16) — shows `db.query()` style; AgentService MUST use `select()` style instead (see anti-patterns in RESEARCH.md):
```python
def list_prompts(self, skip: int = 0, limit: int = 100, ...) -> list[Prompt]:
    query = self.db.query(Prompt)
    ...
    return query.offset(skip).limit(limit).all()
```

**CRUD method pattern — create with commit/refresh** (prompt_service.py lines 21-26):
```python
def create_prompt(self, data: PromptCreate) -> Prompt:
    prompt = Prompt(**data.model_dump())
    self.db.add(prompt)
    self.db.commit()
    self.db.refresh(prompt)
    return prompt
```

**CRUD method pattern — delete with not-found guard** (prompt_service.py lines 28-34):
```python
def delete_prompt(self, prompt_id: int) -> bool:
    prompt = self.get_prompt(prompt_id)
    if not prompt:
        return False
    self.db.delete(prompt)
    self.db.commit()
    return True
```

**New patterns specific to AgentService (no analog in existing services):**

State machine dict — put at module level above class:
```python
# Uses SQLAlchemy 2.x select() style — do NOT use db.query()
VALID_TRANSITIONS: dict[AgentStatus, list[AgentStatus]] = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

class InvalidTransitionError(ValueError):
    """状态转换不合法（HTTP 409）"""

class ActivationNotReadyError(ValueError):
    """激活前置条件不满足（HTTP 422）"""
```

selectinload list query (no analog in codebase — new SQLAlchemy 2.x style):
```python
def list_agents(self, skip=0, limit=100, status=None) -> list[Agent]:
    stmt = (
        select(Agent)
        .options(selectinload(Agent.model), selectinload(Agent.prompt))
    )
    if status:
        stmt = stmt.where(Agent.status == status)
    stmt = stmt.offset(skip).limit(limit)
    return list(self.db.execute(stmt).scalars().all())
```

Atomic status + history write (new pattern):
```python
def change_status(self, agent_id: int, data: StatusChangeRequest) -> Agent:
    agent = self.get_agent(agent_id)
    if not agent:
        raise ValueError("not found")          # router maps to 404
    old_status = agent.status
    allowed = VALID_TRANSITIONS.get(old_status, [])
    if data.status not in allowed:
        raise InvalidTransitionError(
            f"无法从 {old_status.value} 切换到 {data.status.value}"
        )
    if data.status == AgentStatus.ACTIVE:
        self._assert_activation_ready(agent)    # raises ActivationNotReadyError
    agent.status = data.status
    self.db.add(AgentStatusHistory(
        agent_id=agent.id,
        from_status=old_status,
        to_status=data.status,
        reason=data.reason,
    ))
    self.db.commit()
    self.db.refresh(agent)
    return agent
```

---

### `backend/app/api/v1/endpoints.py` (controller — additive modification)

**Analog:** self (`backend/app/api/v1/endpoints.py`) — append `agents_router` block after `prompts_router`.

**Existing import block** (lines 1-7) — extend to add Agent-specific imports:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schema import ModelCreate, ModelRead, PromptCreate, PromptRead, Response
from app.services.model_service import ModelService
from app.services.prompt_service import PromptService
```

**Router instantiation pattern** (lines 9, 43):
```python
models_router = APIRouter()
# ...
prompts_router = APIRouter()
```

**GET list endpoint pattern** (lines 12-16):
```python
@models_router.get("/", response_model=Response[list[ModelRead]])
def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = ModelService(db)
    data = service.list_models(skip=skip, limit=limit)
    return Response(data=data)
```

**GET single with 404 pattern** (lines 19-25):
```python
@models_router.get("/{model_id}", response_model=Response[ModelRead])
def get_model(model_id: int, db: Session = Depends(get_db)):
    service = ModelService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return Response(data=model)
```

**POST with 201 pattern** (lines 28-31):
```python
@models_router.post("/", response_model=Response[ModelRead], status_code=201)
def create_model(body: ModelCreate, db: Session = Depends(get_db)):
    service = ModelService(db)
    model = service.create_model(body)
    return Response(data=model)
```

**DELETE with service bool pattern** (lines 35-40):
```python
@models_router.delete("/{model_id}", response_model=Response[None])
def delete_model(model_id: int, db: Session = Depends(get_db)):
    service = ModelService(db)
    if not service.delete_model(model_id):
        raise HTTPException(status_code=404, detail="Model not found")
    return Response(message="Deleted")
```

**New PATCH endpoint pattern for agents** (no analog — new pattern, derived from RESEARCH.md):
```python
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
```

**DELETE with active-guard pattern for agents:**
```python
@agents_router.delete("/{agent_id}", response_model=Response[None])
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    try:
        found = service.delete_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not found:
        raise HTTPException(status_code=404, detail="Agent not found")
    return Response(message="Deleted")
```

---

### `backend/app/api/v1/router.py` (config — minimal modification)

**Analog:** self (`backend/app/api/v1/router.py`) — one import extension and one `include_router` line.

**Current file** (lines 1-6 — entire file):
```python
from fastapi import APIRouter
from .endpoints import models_router, prompts_router

router = APIRouter()
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
```

**After modification** — extend import on line 2 and append one `include_router` call:
```python
from fastapi import APIRouter
from .endpoints import models_router, prompts_router, agents_router

router = APIRouter()
router.include_router(models_router,  prefix="/models",  tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
router.include_router(agents_router,  prefix="/agents",  tags=["agents"])
```

---

### `backend/tests/conftest.py` (config — new file)

**Analog:** `01-superpowers/backend/tests/conftest.py` — exact structural match.

**Full analog file** (01-superpowers lines 1-83):
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.entity import AgentStatus

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,          # critical: single connection for in-memory SQLite
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def seed_model(client):
    """创建一个 Model 并返回其数据"""
    res = client.post("/api/v1/models/", json={
        "name": "GPT-4o",
        "provider": "OpenAI",
        "model_type": "chat",
        "version": "2024-08-06",
    })
    return res.json()["data"]

@pytest.fixture
def seed_prompt(client):
    """创建一个 Prompt 并返回其数据"""
    res = client.post("/api/v1/prompts/", json={
        "title": "翻译助手",
        "content": "将以下内容翻译为{language}: {text}",
    })
    return res.json()["data"]

@pytest.fixture
def seed_agent(client, seed_model, seed_prompt):
    """创建一个关联了 Model 和 Prompt 的 DRAFT Agent"""
    res = client.post("/api/v1/agents/", json={
        "name": "翻译智能体",
        "description": "多语言翻译",
        "model_id": seed_model["id"],
        "prompt_id": seed_prompt["id"],
    })
    return res.json()["data"]
```

**Key detail:** `StaticPool` is required for in-memory SQLite with `TestClient` — without it, each connection gets a separate in-memory database and the tables created in setup won't be visible to the test client.

Also create `backend/tests/__init__.py` as an empty file to make the directory a Python package.

---

### `backend/tests/test_agent_api.py` (test — new file)

**Analog:** `01-superpowers/backend/tests/test_agent_api.py`

**Test class structure pattern** (lines 4-82) — class per feature area, method per business rule:
```python
from app.models.entity import AgentStatus

class TestAgentCRUD:
    """Agent 基础 CRUD 测试"""

    def test_create_agent_default_draft(self, client):
        res = client.post("/api/v1/agents/", json={"name": "Test Agent"})
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["name"] == "Test Agent"
        assert data["status"] == AgentStatus.DRAFT.value

    def test_get_agent_with_relation_names(self, client, seed_agent, seed_model, seed_prompt):
        res = client.get(f"/api/v1/agents/{seed_agent['id']}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["model_name"] == seed_model["name"]
        assert data["prompt_name"] == seed_prompt["title"]   # Prompt uses .title not .name

    def test_delete_draft_agent(self, client):
        res = client.post("/api/v1/agents/", json={"name": "To Delete"})
        agent_id = res.json()["data"]["id"]
        res = client.delete(f"/api/v1/agents/{agent_id}")
        assert res.status_code == 200


class TestAgentStatusMachine:
    """状态机业务规则测试"""

    def test_activate_draft_success(self, client, seed_agent):
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == AgentStatus.ACTIVE.value

    def test_activate_without_model_returns_422(self, client, seed_prompt):
        # Note: 422 for pre-condition failure (missing model), NOT 409
        res = client.post("/api/v1/agents/", json={
            "name": "No Model",
            "prompt_id": seed_prompt["id"],
        })
        agent_id = res.json()["data"]["id"]
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422

    def test_invalid_transition_returns_409(self, client, seed_agent):
        # DRAFT -> INACTIVE is not in VALID_TRANSITIONS — must return 409 not 422
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        assert res.status_code == 409

    def test_delete_active_agent_returns_409(self, client, seed_agent):
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        res = client.delete(f"/api/v1/agents/{seed_agent['id']}")
        assert res.status_code == 409
```

**Response envelope pattern** — all assertions on agent data go through `res.json()["data"]`, matching the `Response[T]` wrapper (code=0, data, message).

---

## Shared Patterns

### Response Envelope
**Source:** `backend/app/schemas/schema.py` lines 10-13
**Apply to:** All 5 agent endpoints
```python
class Response(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "success"
```
Every endpoint returns `Response(data=...)` or `Response(message="Deleted")`. Never return raw dicts.

### Service Constructor + get_db Dependency Injection
**Source:** `backend/app/api/v1/endpoints.py` lines 12-16 and `backend/app/core/database.py` lines 15-19
**Apply to:** All endpoint functions in agents_router
```python
# In every endpoint:
service = AgentService(db)
# db comes from:
db: Session = Depends(get_db)

# get_db pattern (database.py):
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 404 Guard Pattern
**Source:** `backend/app/api/v1/endpoints.py` lines 19-25
**Apply to:** `get_agent`, `change_agent_status`, `delete_agent` endpoints
```python
entity = service.get_entity(entity_id)
if not entity:
    raise HTTPException(status_code=404, detail="Entity not found")
```

### db.add / db.commit / db.refresh Transaction Pattern
**Source:** `backend/app/services/prompt_service.py` lines 21-26
**Apply to:** `agent_service.create_agent()` and `agent_service.change_status()`
```python
self.db.add(obj)
self.db.commit()
self.db.refresh(obj)
return obj
```

### Pydantic v2 ORM Config
**Source:** `backend/app/schemas/schema.py` lines 33, 55-56
**Apply to:** `AgentRead`, `StatusHistoryRead`
```python
model_config = ConfigDict(from_attributes=True)
# Add use_enum_values=True on AgentRead so JSON serializes "active" not <AgentStatus.ACTIVE>
model_config = ConfigDict(from_attributes=True, use_enum_values=True)
```

### `data.model_dump()` for ORM object creation
**Source:** `backend/app/services/prompt_service.py` line 22
**Apply to:** `agent_service.create_agent()`
```python
agent = Agent(**data.model_dump())
# NOTE: AgentCreate no longer has a status field, so this is safe.
# Manually add: agent.status = AgentStatus.DRAFT after construction, or set default in ORM.
# entity.py already has default=AgentStatus.DRAFT in the Agent model — no override needed.
```

---

## No Analog Found

No files are without a codebase analog. All 7 files have either a direct self-modification analog (for existing files) or a close structural match (R1-superpowers tests for the new test files).

---

## Metadata

**Analog search scope:** `backend/app/` (models, schemas, services, api/v1), `01-superpowers/backend/tests/`
**Files read:** 9 source files + 2 research documents
**Pattern extraction date:** 2026-05-18

**Critical notes for planner:**
1. `backend/tests/__init__.py` (empty) must be created as Wave 0 before any test file — pytest needs it to resolve `from app.` imports.
2. `agent_service.py` must use `select()` + `session.execute()` style — NOT `db.query()` — this is the only file in the codebase to adopt SQLAlchemy 2.x style. Add a module-level comment documenting this intentional divergence.
3. `Prompt.title` (not `.name`) is the field to populate `AgentRead.prompt_name` — confirmed by reading entity.py line 33.
4. `StaticPool` in conftest is mandatory for in-memory SQLite + TestClient — the R1-superpowers conftest already demonstrates this correctly.
5. `use_enum_values=True` in `AgentRead.model_config` serializes `AgentStatus.ACTIVE` as `"active"` in JSON — without it, the response body contains the Python enum repr.

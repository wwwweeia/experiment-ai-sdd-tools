---
title: Architecture
last_mapped: 2026-05-18
---

# Architecture

## Pattern

**Layered / N-tier architecture** with clear separation between HTTP, business logic, and data layers.

```
HTTP Request
    ↓
Router (FastAPI APIRouter)
    ↓
Endpoint Handler (endpoints.py)
    ↓
Service Layer (XxxService)
    ↓
SQLAlchemy ORM
    ↓
SQLite Database
```

Frontend is a SPA with its own layered pattern:
```
Vue Component (views/)
    ↓
Pinia Store (stores/)
    ↓
API Client (api/)
    ↓
Backend REST API
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
GET /api/v1/agents/
  → agents_router handler in endpoints.py
  → AgentService(db).get_all(skip, limit, status_filter)
  → SQLAlchemy query with optional WHERE status=?
  → Returns list of Agent ORM objects
  → Serialized to List[AgentRead] via Pydantic
  → Wrapped in Response[List[AgentRead]] {code:0, data:[...]}
```

### Write (status update example)
```
PATCH /api/v1/agents/{id}/status
  → agents_router handler
  → AgentService(db).update_status(id, new_status)
  → Business rule validation (DRAFT→ACTIVE requires model+prompt)
  → db.commit()
  → Returns updated AgentRead
```

### Frontend flow
```
User clicks "Activate" button in AgentList.vue
  → store.updateStatus(id, 'ACTIVE')
  → api/agents.js: PATCH /api/v1/agents/{id}/status
  → Response interceptor checks code === 0
  → Store updates local state
  → Vue reactivity re-renders list
```

## Key Abstractions

### Generic Response Wrapper
All endpoints return the same shape:
```python
class Response(BaseModel, Generic[T]):
    code: int = 0
    data: Optional[T] = None
    message: str = "success"
```

### Service Constructor Pattern
Services receive SQLAlchemy `Session` at construction time:
```python
class AgentService:
    def __init__(self, db: Session):
        self.db = db
```

### AgentStatus Enum (State Machine)
```python
class AgentStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
```

Valid transitions: DRAFT→ACTIVE, ACTIVE→INACTIVE, INACTIVE→ACTIVE. No other transitions allowed.

## Entry Points

- **Backend**: `uvicorn app.main:app --reload` → `backend/app/main.py`
- **Frontend**: `npm run dev` → `frontend/src/main.js` → `App.vue`
- **API docs**: `http://localhost:8000/docs` (FastAPI auto-generated Swagger)
- **Health check**: `GET /health`

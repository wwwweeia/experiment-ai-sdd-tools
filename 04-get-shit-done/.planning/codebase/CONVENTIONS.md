---
title: Code Conventions
last_mapped: 2026-05-18
---

# Code Conventions

## Code Style

### Backend (Python)
- Python with type hints throughout
- Pydantic v2 schemas using `ConfigDict(from_attributes=True)`
- SQLAlchemy 2.x with `Mapped[T]` type annotations for all columns
- FastAPI dependency injection via `Depends(get_db)` for database sessions

### Frontend (JavaScript/Vue)
- Vue 3 Composition API with `<script setup>` syntax
- No TypeScript — plain JavaScript with JSDoc where needed
- Element Plus UI components

## Naming Conventions

### Backend
- **Files**: snake_case (`model_service.py`, `prompt_service.py`)
- **Classes**: PascalCase (`ModelService`, `PromptService`, `AgentStatus`)
- **Functions/methods**: snake_case (`get_all`, `create`, `update_status`)
- **Database columns**: snake_case (`model_id`, `created_at`)
- **Enums**: uppercase values (`DRAFT`, `ACTIVE`, `INACTIVE`)

### Frontend
- **Components**: PascalCase (`AgentList.vue`, `PromptList.vue`)
- **Stores**: camelCase (`usePromptStore`, `useAgentStore`)
- **API modules**: camelCase (`prompts.js`, `agents.js`)
- **Functions**: camelCase (`fetchPrompts`, `createAgent`)
- **CSS classes**: kebab-case

## Patterns

### Service Layer Pattern (Backend)
Constructor receives db session, all DB operations encapsulated in service:
```python
class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100):
        return self.db.query(Prompt).offset(skip).limit(limit).all()
```

### Unified Response Wrapper
All API endpoints return `Response[T]` with `code=0` on success:
```python
# Schema definition
class Response(BaseModel, Generic[T]):
    code: int = 0
    data: Optional[T] = None
    message: str = "success"
```

### Pinia Store Structure
Stores use section dividers:
```javascript
// ==================== State ====================
const items = ref([])

// ==================== Getters ====================
const activeItems = computed(...)

// ==================== Actions ====================
async function fetchItems() { ... }
```

### API Client Pattern
Axios interceptor checks `code === 0` and returns `res.data`:
```javascript
// frontend/src/api/index.js
instance.interceptors.response.use(res => {
  if (res.data.code === 0) return res.data
  return Promise.reject(res.data)
})
```

### Router → Service → Model Flow
Endpoints import services, construct with db, delegate all logic:
```python
@agent_router.get("/", response_model=Response[List[AgentRead]])
def list_agents(db: Session = Depends(get_db)):
    service = AgentService(db)
    return Response(data=service.get_all())
```

## Error Handling

### Backend
- FastAPI `HTTPException` for HTTP-level errors (404, 422, etc.)
- Business rule violations returned as `400 Bad Request` with descriptive message
- No global exception handler — each endpoint handles its own errors

### Frontend
- API errors caught in store actions via try/catch
- `ElMessage.error()` for user-facing error display
- `ElMessageBox.confirm()` for destructive action confirmation

---
phase: 01-backend
plan: 03
subsystem: api
tags: [fastapi, routing, http, agent, state-machine]

requires:
  - phase: 01-backend/01-02
    provides: AgentService with VALID_TRANSITIONS, InvalidTransitionError, ActivationNotReadyError, all 6 methods
  - phase: 01-backend/01-01
    provides: AgentCreate, AgentRead, StatusChangeRequest schemas; AgentStatusHistory ORM

provides:
  - agents_router with 5 HTTP endpoints registered at /api/v1/agents/*
  - _agent_to_read() helper mapping ORM Agent -> AgentRead (model_name/prompt_name)
  - HTTP exception mapping: InvalidTransitionError->409, ActivationNotReadyError->422

affects:
  - 01-backend/01-04 (integration tests call these endpoints)
  - phase-2-frontend (all 5 endpoints are the contract the frontend calls)

tech-stack:
  added: []
  patterns:
    - "ORM->Schema mapping helper: _agent_to_read() handles model.name / prompt.title divergence"
    - "Exception-to-HTTP mapping: domain exceptions caught in endpoint, translated to status codes"
    - "Thin HTTP boundary: no business logic in endpoints, only request parsing + response wrapping"

key-files:
  created: []
  modified:
    - backend/app/api/v1/endpoints.py
    - backend/app/api/v1/router.py

key-decisions:
  - "_agent_to_read() helper added (not in plan): AgentRead.model_name maps agent.model.name, prompt_name maps agent.prompt.title — requires explicit mapping since from_attributes=True cannot traverse to non-matching field names"
  - "except InvalidTransitionError before except ActivationNotReadyError: defensive ordering prevents future ambiguity even though both are ValueError subclasses"
  - "DELETE tries service first then checks bool: mirrors PATTERNS.md — ValueError(ACTIVE) becomes 409, False return becomes 404"

patterns-established:
  - "_agent_to_read(): ORM-to-schema mapping function pattern when field names diverge (prompt.title vs prompt_name)"
  - "Dual exception mapping in PATCH: InvalidTransitionError→409 BEFORE ActivationNotReadyError→422"

requirements-completed:
  - AGENT-01
  - AGENT-02
  - AGENT-03
  - AGENT-04
  - STATE-01

duration: 8min
completed: 2026-05-18
---

# Phase 01-backend Plan 03: HTTP Routing Layer Summary

**FastAPI agents_router wiring 5 endpoints under /api/v1/agents with dual exception-to-HTTP-status mapping (409/422) for state machine errors**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-18T00:00:00Z
- **Completed:** 2026-05-18T00:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Appended `agents_router = APIRouter()` with all 5 endpoints to endpoints.py, preserving existing models/prompts routers untouched
- Added `_agent_to_read()` helper to correctly map ORM Agent -> AgentRead (model_name from model.name, prompt_name from prompt.title)
- Registered agents_router at `/agents` prefix with `tags=["agents"]` in router.py — all 5 routes reachable at `/api/v1/agents/*`

## Task Commits

Each task was committed atomically:

1. **Task 1: Append agents_router with 5 endpoints to endpoints.py** - `3d62336` (feat)
2. **Task 2: Register agents_router in router.py at /agents prefix** - `0bb3db1` (feat)

## Route Table

| Method | Path | Status Codes | Notes |
|--------|------|--------------|-------|
| GET | /api/v1/agents/ | 200 | skip/limit/status filter |
| GET | /api/v1/agents/{agent_id} | 200, 404 | detail with 404 guard |
| POST | /api/v1/agents/ | 201 | status forced DRAFT by service |
| PATCH | /api/v1/agents/{agent_id}/status | 200, 404, 409, 422 | InvalidTransition→409, NotReady→422 |
| DELETE | /api/v1/agents/{agent_id} | 200, 404, 409 | ACTIVE guard→409 |

## Files Created/Modified

- `backend/app/api/v1/endpoints.py` — Added AgentStatus/AgentCreate/AgentRead/StatusChangeRequest imports, AgentService/InvalidTransitionError/ActivationNotReadyError imports, `_agent_to_read()` helper, `agents_router` with 5 endpoint functions
- `backend/app/api/v1/router.py` — Extended import to include `agents_router`, added `include_router(agents_router, prefix="/agents", tags=["agents"])`

## Decisions Made

- **_agent_to_read() helper (unplanned but necessary):** Plan referenced `AgentRead` with `model_name` and `prompt_name` fields, but the ORM Agent object stores these as `agent.model.name` and `agent.prompt.title`. Since `from_attributes=True` only maps same-named attributes, explicit mapping was required. Added a thin helper function rather than inline code in each endpoint for DRY consistency.
- **Defensive exception ordering in PATCH:** `except InvalidTransitionError` placed before `except ActivationNotReadyError` even though both are `ValueError` subclasses. Prevents future ambiguity if exception hierarchy changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added `_agent_to_read()` helper for ORM→schema field mapping**
- **Found during:** Task 1 (Append agents_router)
- **Issue:** `AgentRead.model_name` must map from `agent.model.name`; `AgentRead.prompt_name` must map from `agent.prompt.title`. Pydantic `from_attributes=True` cannot handle this mismatch automatically — would result in `None` for both fields even when model/prompt are loaded.
- **Fix:** Added `_agent_to_read(agent) -> AgentRead` helper that explicitly builds the schema with correct field mappings. All 5 endpoints use this helper instead of `Response(data=agent)`.
- **Files modified:** `backend/app/api/v1/endpoints.py`
- **Verification:** `python -c "from app.api.v1.endpoints import agents_router; print('OK')"` passes; schema mapping logic verified at design level.
- **Committed in:** `3d62336` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 - missing critical field mapping)
**Impact on plan:** Auto-fix essential for correctness — without it, model_name and prompt_name would always be None in API responses, breaking frontend display. No scope creep.

## Smoke Test Outputs

```
# Task 1 verify
OK

# Task 2 verify (router-level)
OK

# End-to-end app boot (all 5 routes)
[('/api/v1/agents/', ['GET']), ('/api/v1/agents/', ['POST']), ('/api/v1/agents/{agent_id}', ['DELETE']), ('/api/v1/agents/{agent_id}', ['GET']), ('/api/v1/agents/{agent_id}/status', ['PATCH'])]
```

## Issues Encountered

None — both tasks executed cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 Agent API endpoints are reachable and correctly typed
- Plan 01-04 (integration tests) can now call these endpoints via pytest + TestClient
- Phase 2 frontend has a stable HTTP contract to build against
- OpenAPI docs at `/docs` will auto-show all 5 endpoints under "agents" tag

---
*Phase: 01-backend*
*Completed: 2026-05-18*

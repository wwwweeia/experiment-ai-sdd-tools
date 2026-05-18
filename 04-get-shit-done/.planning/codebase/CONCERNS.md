---
title: Technical Concerns
last_mapped: 2026-05-18
---

# Technical Concerns

## Tech Debt

### Incomplete Agent Feature Implementation

**Issue:** Agent endpoints, service layer, and full frontend functionality are not yet implemented per the experiment requirements.

**Files:**
- `backend/app/api/v1/router.py` — Agent routes not registered (only models/prompts)
- `backend/app/services/` — No `agent_service.py` exists; Agent business logic unimplemented
- `backend/app/api/v1/endpoints.py` — No Agent endpoint handlers (only Model/Prompt)
- `frontend/src/views/AgentList.vue` — Placeholder only (15 lines, no functional code)
- `frontend/src/api/` — No `agents.js` API client exists

**Impact:** Agent activation/deactivation feature (5 business rules in CLAUDE.md) cannot function. Frontend has no list view, create form, status toggle, or delete buttons.

**Fix approach:** Implement full Agent CRUD stack:
1. Create `backend/app/services/agent_service.py` with status transition validation
2. Add Agent endpoint handlers to `endpoints.py` and register in `router.py`
3. Implement `frontend/src/api/agents.js` following `prompts.js` pattern
4. Complete `AgentList.vue` with full feature parity to `PromptList.vue`
5. Create/extend `frontend/src/stores/agent.js` with CRUD operations

### Missing Cascading Delete & Foreign Key Constraints

**Issue:** Database relationships lack explicit cascade rules. Deleting Model or Prompt referenced by Agent will fail or leave dangling foreign keys.

**Files:**
- `backend/app/models/entity.py` — Model/Prompt relationships have no cascade delete configured
  - Line 25: `agents: Mapped[list["Agent"]] = relationship(back_populates="model")` — no cascade
  - Line 49-50: Agent model_id/prompt_id ForeignKeys but no cascade on Model/Prompt side

**Impact:** 
- Cannot delete a Model if Agents reference it (FOREIGN KEY constraint violation)
- Skill records attached to deleted Agents become orphaned
- Business rule #4 ("ACTIVE status not deletable") has no cascade support

**Fix approach:**
- Add `cascade="all, delete-orphan"` to Model.agents relationship
- Add `cascade="all, delete-orphan"` to Agent.skills relationship
- Implement explicit cascade logic in Agent deletion when Agent is ACTIVE (validate first, then cascade to Skills)

### No Input Validation Beyond Pydantic

**Issue:** Schema validation exists but no business-level validation for Agent state transitions.

**Files:**
- `backend/app/schemas/schema.py` — AgentCreate/AgentRead schemas lack validators
  - `AgentCreate.status` field accepts any string (line 66), should validate AgentStatus enum values

**Impact:**
- Cannot enforce business rules:
  - Rule 1: DRAFT→ACTIVE requires valid Model and Prompt before transition
  - Rule 3: INACTIVE→ACTIVE needs to re-check Model/Prompt validity
  - Rule 4: ACTIVE agents cannot be deleted
- Invalid status strings can bypass enum validation if sent directly to DB

**Fix approach:**
- Add Pydantic field validators to `AgentCreate` for status field
- Add business logic validators in `AgentService` methods (`activate()`, `deactivate()`) to check related Model/Prompt existence

### Overly Permissive CORS Configuration

**Issue:** CORS is hardcoded to allow only localhost:5173 but lacks error handling for configuration changes.

**Files:**
- `backend/app/main.py` (lines 14-20) — CORS middleware allows all methods/headers with single origin

**Impact:**
- Frontend development tied to localhost:5173 (no dev server port flexibility)
- No environment-based configuration (dev vs. production CORS rules differ)
- Adding new dev environments requires code changes

**Fix approach:**
- Move CORS origins to config: `backend/app/core/config.py`
- Support comma-separated `ALLOWED_ORIGINS` env var for flexibility

### SQLite Threading Issue Suppressed Without Investigation

**Issue:** `check_same_thread=False` is set globally for SQLite.

**Files:**
- `backend/app/core/database.py` (line 7) — `connect_args={"check_same_thread": False}`

**Impact:**
- SQLite is single-threaded by design; disabling this check masks concurrency bugs
- OK for single-threaded request handling (FastAPI default) but risky if async workers added
- No comment explaining why this is safe in this context

**Fix approach:**
- Document the assumption: "Single-threaded request handling via FastAPI's default event loop"
- Remove this flag and use SQLite properly or migrate to PostgreSQL for production

## Known Bugs

### Prompt List Hardcoded Statistics in Home View

**Issue:** Home view displays hardcoded stats (3 models, 3 agents, 3 prompts, 2 skills) that don't sync with actual data.

**Files:**
- `frontend/src/views/Home.vue` (lines 43-48) — `stats` object is reactive but manually assigned from seed data

**Trigger:** Create/delete any Model, Prompt, or Agent via API → Home stats remain unchanged.

**Workaround:** Refresh the page manually.

**Fix approach:** 
- Fetch actual counts from backend stats endpoint or auto-fetch on mount
- Or mark stats as approximate/demo-only with a note

### Agent Store Makes Unregistered API Call

**Issue:** `useAgentStore` tries to fetch `/api/v1/agents` which doesn't exist yet.

**Files:**
- `frontend/src/stores/agent.js` (lines 12-14) — Calls `api.get('/api/v1/agents')` before endpoint exists

**Trigger:** Navigate to Agent page or any component that calls `fetchAgents()`.

**Impact:** Will return 404 once attempted, failing silently with current error handling.

## Security Considerations

### No Authentication/Authorization

**Risk:** All endpoints are public. No user context, role checks, or access control.

**Files:**
- `backend/app/api/v1/endpoints.py` — All route handlers lack `Depends(verify_token)` or similar
- `backend/app/main.py` — No auth middleware

**Current mitigation:** Localhost-only CORS, implicit assumption this is demo/lab environment.

**Recommendations:**
- Add optional JWT auth layer (can be a Phase 2 improvement)
- Document that this is not production-ready
- For lab use, keep localhost restriction enforced

### No SQL Injection Prevention for Tag Filtering

**Issue:** Tag filtering uses string `contains()` which may be vulnerable if tags aren't sanitized.

**Files:**
- `backend/app/services/prompt_service.py` (line 15) — `Prompt.tags.contains(tag)` without parameterization check

**Current mitigation:** SQLAlchemy ORM handles parameterization automatically; direct risk is low.

**Recommendations:**
- Tags are stored as JSON strings, so `contains()` searches for literal substring
- If switching to array columns (PostgreSQL), use explicit array operators
- Add input validation to reject special characters in tag searches

## Performance Bottlenecks

### N+1 Query Problem: Agents with Related Model/Prompt

**Issue:** Listing agents will trigger N+1 queries if frontend needs model.name and prompt.title alongside agent data.

**Files:**
- `backend/app/services/agent_service.py` — Will be created; likely missing `.joinedload()` for relationships
- `backend/app/models/entity.py` (lines 56-57) — Model and Prompt relationships exist but won't auto-load

**Example scenario:**
```
GET /api/v1/agents/  → Query 1: SELECT * FROM agents (N rows)
                      Queries 2-N+1: SELECT * FROM models WHERE id=? for each agent.model_id
                      + SELECT * FROM prompts WHERE id=? for each agent.prompt_id
```

**Impact:** With 100 agents, 200+ queries instead of 1 join.

**Fix approach:**
- Implement in `AgentService.list_agents()`:
  ```python
  from sqlalchemy.orm import joinedload
  return self.db.query(Agent).options(
      joinedload(Agent.model),
      joinedload(Agent.prompt)
  ).offset(skip).limit(limit).all()
  ```

### Missing Database Indexes

**Issue:** No explicit indexes on frequently queried columns.

**Files:**
- `backend/app/models/entity.py` — No `index=True` on foreign keys or status field

**Impact:**
- `SELECT * FROM agents WHERE status = 'active'` scans full table
- `SELECT * FROM agents WHERE model_id = ?` scans full table
- Negligible at small scale (<1000 rows) but poor practice

**Fix approach:**
- Add `index=True` to `Agent.status`, `Agent.model_id`, `Agent.prompt_id`
- Add `index=True` to `Prompt.title`, `Model.name` for common searches

### Unbounded List Endpoints

**Issue:** `GET /api/v1/agents/` and other list endpoints lack default pagination limits in some cases.

**Files:**
- `backend/app/api/v1/endpoints.py` (lines 47, 13) — `limit: int = 100` default, but no max enforcement

**Impact:**
- Client can request `?limit=999999` and force loading entire table into memory
- No cursor-based pagination for large datasets

**Fix approach:**
- Enforce max_limit: `limit: int = Query(default=10, le=100)`
- Consider cursor-based pagination for Agent/Prompt lists if >1000 records expected

## Fragile Areas

### Hardcoded Frontend API Baseurl Assumption

**Issue:** `frontend/src/api/index.js` creates axios instance without explicit baseURL.

**Files:**
- `frontend/src/api/index.js` (lines 4-6) — `axios.create({ timeout: 10000 })` assumes default origin

**Problem:** Frontend deployed to different host than backend → all requests fail (no baseURL = same-origin only).

**Safe modification:**
- Set `baseURL` to environment variable: `baseURL: process.env.VITE_API_BASE_URL || 'http://localhost:8000'`
- Define in `.env.local` and `.env.production`

### Monolithic Endpoint Handler File

**Issue:** All Model and Prompt endpoints are in single `endpoints.py` file (74 lines now; will grow to 150+ with Agent endpoints).

**Files:**
- `backend/app/api/v1/endpoints.py` — Should split by entity type

**Problem:** 
- Hard to find specific endpoint among 30+ route definitions
- No clear separation of concerns (models_router, prompts_router are defined together)
- Adding Agent endpoints will make file unwieldy

**Safe modification:**
- Refactor: Create separate modules `backend/app/api/v1/models.py`, `agents.py`, `prompts.py`
- Import routers into `router.py`

### Frontend Store Structure Mismatch

**Issue:** `AgentStore.fetchAgents()` implementation doesn't match data shape from backend.

**Files:**
- `frontend/src/stores/agent.js` (line 13) — Expects `res.data?.data` but backend response format is `Response[list]`
- Compare to `frontend/src/stores/prompt.js` (line 74) — Uses same pattern

**Problem:** If backend returns `{ code: 0, data: [...], message: "success" }`, response interceptor in `api/index.js` (line 16) already unwraps to `res.data`, so Store gets `{ data: [...] }` not `res.data?.data`.

**Safe modification:**
- Verify actual response structure once Agent API is built
- Either `prompts.value = res.data` or `prompts.value = res` (if interceptor fully unwraps)

## Missing Critical Features

### No Agent State Transition Logging

**Issue:** Business rule #5 is "状态变更记录（可选）" (optional), but no audit trail exists.

**Files:**
- `backend/app/models/entity.py` — No `AgentStatusLog` or similar audit table
- `backend/app/services/` — No logging on status changes

**Gap:** Cannot trace when/why Agent status changed; important for debugging stuck agents.

**Fix approach:**
- Add `AgentStatusLog(agent_id, old_status, new_status, changed_at, reason)` table if audit required
- Or use application-level logging (cheaper)

### No Soft Delete / Archive for Agents

**Issue:** Business rule #4 says "ACTIVE status not deletable" but there's no archive/soft delete path.

**Files:**
- `backend/app/api/v1/endpoints.py` — Will have hard DELETE endpoint only

**Gap:** Deleted Agents can't be recovered; historical data lost.

**Fix approach:**
- Add `archived_at: datetime | None` field to Agent
- Only hard-delete if `archived_at` is not null
- Or implement soft delete: mark `deleted_at` instead of removing rows

### Frontend Missing Error Recovery UI

**Issue:** Error messages from API are shown but no retry/recovery mechanism.

**Files:**
- `frontend/src/api/index.js` (line 19) — Shows error message, rejects promise
- No retry logic for failed requests

**Gap:** User sees error but has no guidance on next steps (is it network? server? user error?).

**Fix approach:**
- Enhance error interceptor to categorize errors (validation, auth, server, network)
- Provide contextual guidance: "Agent name already exists" vs. "Server error, try again"

## Test Coverage Gaps

### No Backend Unit Tests for Agent Service

**Issue:** No test files exist for Agent operations.

**Files:**
- `backend/` — No `tests/` directory; no `pytest.ini` or test configuration
- No Agent service validation tests

**Risk:** 
- State transition validation (5 business rules) untested
- Cascade delete edge cases untested
- Foreign key constraint violations won't be caught until runtime

**Priority:** High — State machine logic (DRAFT→ACTIVE→INACTIVE transitions) is complex and error-prone without tests.

**Fix approach:**
- Create `backend/tests/test_agent_service.py` with fixtures for Models/Prompts
- Test each transition rule, boundary conditions (null foreign keys, missing relationships)
- Add `pytest` and `pytest-cov` to `requirements.txt`

### No Frontend Component Tests

**Issue:** Vue components have no unit or integration tests.

**Files:**
- `frontend/` — No jest/vitest config, no `.spec.js` files
- Components untested for user interactions (form submission, status toggle, delete confirmation)

**Risk:**
- Frontend feature implementation unverified until manual testing
- Regressions undetected (e.g., accidentally breaking list filter after refactor)

**Priority:** Medium — Functional testing via E2E is available (Playwright in `e2e/` directory), but unit tests would catch UI logic bugs faster.

### E2E Tests Incomplete for Agent Feature

**Issue:** E2E tests exist for Home and Prompt pages but not Agents.

**Files:**
- `e2e/tests/home.spec.ts`, `prompt-list.spec.ts` — Existing tests
- No `agent-list.spec.ts`; Agent feature untested end-to-end

**Impact:** Can't verify full user workflow (create agent → activate → deactivate → delete).

**Fix approach:**
- Add `e2e/pages/agent-list.page.ts` with selectors for Agent list UI
- Add `e2e/tests/agent-list.spec.ts` with workflow tests

## Scaling Limits

### SQLite Single-File Database

**Issue:** SQLite file-based database stored at project root.

**Files:**
- `backend/app/core/config.py` (line 8) — `DB_PATH = os.path.join(..., "prompt_lab.db")`

**Current capacity:**
- SQLite handles ~100k rows fine
- Single writer at a time (locks entire database during write)
- File I/O bottleneck for large result sets

**Limit:** Concurrent user requests hit lock contention at ~50-100 simultaneous writes.

**Scaling path:**
- Phase 1 (current): Accept SQLite for lab/demo
- Phase 2: Migrate to PostgreSQL for production (100+ concurrent users)
- Use SQLAlchemy's connection pooling: `pool_size=5, max_overflow=10`

## Dependencies at Risk

### Pinned Versions May Have Security Issues

**Issue:** `requirements.txt` pins to specific versions, some from Feb 2024.

**Files:**
- `backend/requirements.txt`
  - `fastapi==0.115.6` (Feb 2025 release, OK)
  - `sqlalchemy==2.0.36` (2024 release, should check for CVEs)
  - `pydantic==2.10.4` (2024 release)
  - `uvicorn[standard]==0.34.0` (2024 release)

**Risk:** No automated security scanning; may have known CVEs.

**Recommendations:**
- Run `pip-audit -r requirements.txt` to check for known issues
- Consider `pip-compile` with `--upgrade` to auto-update safely
- Add pre-commit hook: `pip-audit` check before commits

### Frontend Dependencies Outdated

**Issue:** `frontend/package.json` has loose version constraints.

**Files:**
- `frontend/package.json`
  - `"vue": "^3.5.0"` allows 3.6, 3.7, etc.
  - `"element-plus": "^2.9.0"` allows 2.10, 2.11, etc.

**Risk:**
- Breaking changes in minor versions not covered by tests
- Incompatible dependency upgrades (e.g., Element Plus 2.10 breaking changes)

**Fix approach:**
- Lock to exact versions: `"vue": "3.5.12"`
- Or use `.npmrc` with `legacy-peer-deps=true` and test thoroughly before upgrades
- Add `npm audit` to CI pipeline

---

*Concerns audit: 2026-05-18*

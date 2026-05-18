# Pitfalls Research

**Domain:** Brownfield state machine feature addition — FastAPI + SQLAlchemy 2.x + Vue 3 + Element Plus
**Researched:** 2026-05-18
**Confidence:** HIGH (codebase read directly; pitfalls grounded in actual file contents)

---

## Critical Pitfalls

### Pitfall 1: AgentRead schema uses `status: str` — loses type safety at the API boundary

**What goes wrong:**
`AgentRead` declares `status: str` (line 75, schema.py). When FastAPI serializes the ORM object, `AgentStatus` is a `str` enum, so the raw string value flows through. However, the *input* side of `AgentCreate` also uses `status: str = "draft"` — meaning any arbitrary string is accepted by Pydantic validation. A caller can POST `{"status": "hacked"}` and it silently passes schema validation, only failing (or not, if unchecked) at the DB write.

**Why it happens:**
The schema was written as a placeholder before the status machine was designed. Using `str` avoids import of `AgentStatus`, which feels simpler early on.

**How to avoid:**
Change both input and output schemas to use `AgentStatus` directly:
```python
from app.models.entity import AgentStatus

class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    model_id: int | None = None
    prompt_id: int | None = None
    # do NOT expose status on creation — always DRAFT

class AgentRead(BaseModel):
    ...
    status: AgentStatus   # enum, not str
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
```
Remove `status` from `AgentCreate` entirely — creation always yields DRAFT; callers cannot set status at creation time.

**Warning signs:**
- Unit tests pass `status="anything"` to the create endpoint and get 201 back
- Swagger UI shows `status` as a free-text string field in the request body
- Status filter query param accepts values that are not enum members without erroring

**Phase to address:** Phase 1 (AgentService + Schema definition), before any endpoint is written.

---

### Pitfall 2: N+1 queries on Agent list because relationships are lazy-loaded by default

**What goes wrong:**
`Agent` has `model: Mapped["Model | None"]` and `prompt: Mapped["Prompt | None"]` as plain `relationship()` calls — SQLAlchemy 2.x defaults these to `lazy="select"`. When the Agent list endpoint returns 20 agents and the response schema includes `model_name` or `prompt_title`, the service loop triggers 20 + 20 additional SELECT statements — 41 queries for what should be 1.

The existing `PromptList.vue` only shows prompt data (no joins), so this pattern wasn't visible before. Agent list *explicitly requires* showing "关联 Model/Prompt 名称" per the requirements, making this a guaranteed N+1 scenario.

**Why it happens:**
Developers follow the existing `model_service.py` / `prompt_service.py` pattern (plain `db.query(Model).all()`) without adding join hints, because those services never needed joins.

**How to avoid:**
Use `selectinload` (preferred for lists) or `joinedload` (for single-object fetches):
```python
from sqlalchemy.orm import selectinload
from sqlalchemy import select

stmt = (
    select(Agent)
    .options(selectinload(Agent.model), selectinload(Agent.prompt))
    .offset(skip)
    .limit(limit)
)
result = self.db.execute(stmt).scalars().all()
```
The response schema must then include nested `ModelRead` / `PromptRead` (or just `model_name: str | None`) — commit to one approach before writing the schema.

**Warning signs:**
- SQLAlchemy debug logging (`echo=True`) shows SELECT statements multiplying with list size
- Response times scale linearly with Agent count even with small datasets
- Service code uses `agent.model.name` inside a loop without any `options()` call

**Phase to address:** Phase 1 (AgentService list method), before the list endpoint is verified.

---

### Pitfall 3: Mixing legacy `db.query()` with SQLAlchemy 2.x `session.execute(select())` in the same service

**What goes wrong:**
Both `model_service.py` and `prompt_service.py` use the legacy `db.query()` API. The project `CLAUDE.md` and `PROJECT.md` both state "SQLAlchemy 2.x style (Session.execute + select())" is the target. If `AgentService` is written in 2.x style while the existing services remain legacy, the codebase has two conflicting patterns. Worse, if a developer cargo-cults the legacy style into AgentService (because that's what they see in the existing files), the codebase drifts further from the stated target.

The real danger: `db.query()` has subtle behavioral differences around expiry, identity map handling, and result types compared to `session.execute(select())`. Mixing them in a service that does status-change + audit-log writes in one transaction can produce unexpected behavior.

**Why it happens:**
Both services are already written in legacy style. A new developer reads them as "the pattern" and copies it — the CLAUDE.md note about 2.x style is easy to miss.

**How to avoid:**
Write `AgentService` exclusively in 2.x style (`select()` + `session.execute()`). Add a comment at the top of `agent_service.py`:
```python
# Uses SQLAlchemy 2.x query style (session.execute + select()).
# Do NOT use db.query() — existing services are legacy and pending update.
```
Do not "fix" the existing services in the same PR — surgical changes only.

**Warning signs:**
- `AgentService` methods start with `self.db.query(Agent)` instead of `select(Agent)`
- Result type is `Query` object instead of `Result` / `ScalarResult`
- `.first()` on a `Query` vs `.scalars().first()` on an `execute()` result — both work but signal mixed styles

**Phase to address:** Phase 1 (AgentService scaffolding), enforce at code review.

---

### Pitfall 4: State transition validation implemented in the endpoint layer instead of the service layer

**What goes wrong:**
Business rules (DRAFT→ACTIVE requires model+prompt, ACTIVE cannot be deleted) end up in the endpoint function as `if/else` chains. This makes the rules untestable without an HTTP client, duplicates logic if multiple endpoints need the same check, and means the service layer has no concept of "invalid transition" — it just blindly updates.

**Why it happens:**
FastAPI's `HTTPException` is convenient to raise in endpoints. Developers put the check "close to the HTTP response" for simplicity.

**How to avoid:**
All transition rules live in `AgentService.change_status()`. The endpoint catches domain exceptions and maps them to HTTP status codes:
```python
# In AgentService:
VALID_TRANSITIONS = {
    AgentStatus.DRAFT: [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE: [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

def change_status(self, agent_id: int, new_status: AgentStatus, reason: str | None) -> Agent:
    agent = self._get_or_404(agent_id)
    if new_status not in self.VALID_TRANSITIONS[agent.status]:
        raise InvalidTransitionError(agent.status, new_status)
    if new_status == AgentStatus.ACTIVE:
        self._assert_activation_ready(agent)
    ...
```
Endpoint maps `InvalidTransitionError` → 409, `ActivationNotReadyError` → 422.

**Warning signs:**
- `endpoints.py` contains `if agent.status == "draft" and new_status == "active"` logic
- No unit tests exist for `AgentService.change_status` independent of HTTP
- `pytest` tests hit the endpoint for every business rule check instead of testing the service directly

**Phase to address:** Phase 1 (AgentService design). This is the single most important structural decision.

---

### Pitfall 5: `AgentStatusHistory` table added to `entity.py` but `create_all()` skips it on existing DB

**What goes wrong:**
The project uses `Base.metadata.create_all(engine)` in `main.py` for schema management (no Alembic). `create_all()` is idempotent — it skips tables that already exist. However, it **does create new tables** that are not yet in the DB. The risk is ordering: if `agents` table was created in a previous run *before* `AgentStatusHistory` model was added, `agents` exists and is skipped, but `AgentStatusHistory` is new and will be created correctly.

The real pitfall: if a developer deletes and recreates the SQLite file, the `status_history` table appears. But anyone with an existing `agents.db` file must either delete it or manually run `CREATE TABLE`. During testing, this creates "works on my machine" failures.

**Why it happens:**
No migration tooling is set up. Developers assume `create_all()` handles schema evolution — it only handles initial creation.

**How to avoid:**
Add an explicit note in `AgentStatusHistory` model and `main.py`:
```python
# main.py startup
logger.info("Running create_all — new tables will be created, existing tables are NOT modified")
```
Include a `scripts/reset_db.py` that drops and recreates all tables for development use. In tests, always use a fresh in-memory SQLite or temp-file DB (never the dev DB).

For `conftest.py`:
```python
@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)  # fresh schema every test run
    ...
```

**Warning signs:**
- Tests fail with `no such table: agent_status_history` on CI but pass locally
- Developers manually edit the SQLite file after adding new models
- The `agents.db` file is committed to git (it shouldn't be)

**Phase to address:** Phase 1 (test setup + model definition), before any service code runs against a real DB.

---

### Pitfall 6: HTTP 422 returned for invalid state transitions instead of 409 Conflict

**What goes wrong:**
FastAPI auto-generates 422 for Pydantic validation failures. If the state transition request body has valid structure (`{"status": "active"}`) but the transition is invalid (Agent is already ACTIVE, or model_id is null), raising a plain `HTTPException(422)` is semantically wrong — the data is valid, the *state* is what conflicts. Frontend developers then can't distinguish "you sent bad JSON" from "your business rule failed" without inspecting the `detail` string.

**Why it happens:**
`HTTPException(status_code=422)` is what developers reach for when they want to show a validation error, because FastAPI already uses 422 for Pydantic errors.

**How to avoid:**
- Invalid transition (ACTIVE→ACTIVE, ACTIVE→DRAFT): **409 Conflict**
- Activation pre-condition failed (null model/prompt): **422 Unprocessable Entity** — the entity is unprocessable in its current form
- Agent not found: **404**

Frontend can then branch on status code to show different messages.

**Warning signs:**
- All business rule failures return 422 regardless of cause
- Frontend error handler cannot distinguish validation errors from state conflicts
- Swagger shows only one error response schema for the PATCH endpoint

**Phase to address:** Phase 1 (endpoint error handling convention), document before writing the first endpoint.

---

### Pitfall 7: Frontend Agent list fetches Model and Prompt lists on every mount, causing redundant requests

**What goes wrong:**
The Agent creation form needs `<el-select>` dropdowns for Model and Prompt. If `AgentList.vue` calls `fetchModels()` and `fetchPrompts()` in `onMounted`, those API calls fire on every navigation to the Agent page — even when the user is just browsing the list, not creating an agent.

If Model/Prompt counts grow, or if the backend is slow, the list page load visibly stutters while waiting for three parallel API calls before showing anything.

**Why it happens:**
Copying the `PromptList.vue` pattern literally — that component calls `fetchPrompts()` on mount because it needs the data immediately. The Agent list page only conditionally needs Model/Prompt data (when create dialog is open).

**How to avoid:**
Fetch Model/Prompt options lazily — only when the "创建 Agent" dialog is opened:
```javascript
// In AgentList.vue
function openCreateDialog() {
  if (!agentStore.models.length) agentStore.fetchModels()
  if (!agentStore.prompts.length) agentStore.fetchPrompts()
  showCreateDialog.value = true
}
```
Store result in Pinia so the second open doesn't re-fetch.

**Warning signs:**
- Network tab shows 3 simultaneous requests on every visit to /agents
- List table is blank for 300–500ms while waiting for all fetches to complete
- `onMounted` contains `fetchModels()`, `fetchPrompts()`, `fetchAgents()` all called unconditionally

**Phase to address:** Phase 2 (frontend implementation), during AgentList.vue creation.

---

### Pitfall 8: el-select shows blank label when options load after v-model value is set

**What goes wrong:**
When editing an existing Agent (or displaying the Agent detail with pre-selected Model/Prompt), the `el-select` value is bound before the options array is populated from the API. Element Plus renders the select with the correct `value` but no matching `label` — showing a blank or the raw ID instead of "GPT-4o".

This is a known Element Plus timing issue: the component needs the matching option to already be in the list to display the label correctly at initial render.

**Why it happens:**
`v-model="form.model_id"` is set when the Agent is fetched, but `models` array is fetched in a separate async call that resolves later.

**How to avoid:**
Two options:
1. Ensure options are fetched and awaited *before* setting form data (use `Promise.all`)
2. Use `:key` on the `el-select` to force re-render when options arrive:
```javascript
// Option 1 — preferred
const [agentRes, modelsRes] = await Promise.all([fetchAgent(id), fetchModels()])
// Now set form data after options are ready
```

**Warning signs:**
- Create form works but edit form shows blank Model/Prompt selects
- Dropdown options appear correctly after clicking the select, but the initial display is empty
- Works in development (fast localhost) but fails in staging (higher latency)

**Phase to address:** Phase 2 (frontend), if an edit flow is added. For create-only flow, this is less critical since no pre-selected value exists.

---

### Pitfall 9: Status change button triggers immediate API call without loading state, allowing double-clicks

**What goes wrong:**
Clicking "激活" fires `PATCH /agents/{id}/status`. If the response takes 200ms and the user double-clicks (common on mobile/trackpad), two PATCH requests are in-flight simultaneously. Depending on timing, both may succeed — the second one may transition from ACTIVE to ACTIVE (a 409), or if the service doesn't handle it, corrupt the history log with a duplicate entry.

**Why it happens:**
Vue event handlers don't debounce by default. The `@click` handler fires on every click.

**How to avoid:**
Use a per-row loading state and disable the button while the request is in-flight:
```javascript
const loadingStates = ref({}) // { [agentId]: true/false }

async function changeStatus(agent, newStatus) {
  if (loadingStates.value[agent.id]) return
  loadingStates.value[agent.id] = true
  try {
    await agentStore.changeStatus(agent.id, newStatus)
  } finally {
    loadingStates.value[agent.id] = false
  }
}
```
Button: `:loading="loadingStates[row.id]" :disabled="loadingStates[row.id]"`

**Warning signs:**
- No `:loading` prop on action buttons
- Clicking the button rapidly causes multiple success notifications
- Network tab shows two simultaneous PATCH requests for the same agent ID

**Phase to address:** Phase 2 (frontend implementation), in the AgentList.vue action column.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep `status: str` in AgentRead schema | Avoids enum import in schema.py | Invalid statuses accepted, IDE can't autocomplete | Never — fix before any endpoint |
| Put transition logic in endpoint | Faster to write first pass | Rules duplicated if another endpoint needs same check; untestable without HTTP client | Never for this domain |
| Use `db.query()` in AgentService (legacy style) | Consistent with existing services | Contradicts stated 2.x style; mixed patterns in codebase | Acceptable as temporary if you plan to migrate all services together post-experiment |
| Skip `selectinload` on Agent list | Simpler service code | N+1 queries; visible once Agent count > 10 | Never if response includes model/prompt names |
| Omit per-row loading state on status buttons | Less boilerplate in template | Double-click race conditions; bad UX on slow connections | Never — 5 lines of code, high value |
| Skip in-memory DB in pytest fixtures | Faster to set up tests | Tests share state across runs; `create_all()` schema drift hides bugs | Never for business rule tests |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| AgentStatus enum in Pydantic v2 | Use `str` type in schema, rely on enum's `str` inheritance | Declare `status: AgentStatus` explicitly; add `use_enum_values=True` to model_config if you want the serialized value (not the enum object) in JSON |
| `create_all()` for new `AgentStatusHistory` table | Assume it auto-runs on server start for existing DBs | It does create new tables; existing tables are NOT altered. Document this and add a dev reset script |
| Element Plus `el-select` with async options | Bind `v-model` before options array is populated | Fetch options with `Promise.all` before setting form data; alternatively use `remote-method` with built-in loading state |
| PATCH `/agents/{id}/status` response body | Return only `{code, message}` without the updated Agent | Return the full updated `AgentRead` — frontend needs the new status to update its local state without a refetch |
| pytest TestClient and SQLite WAL mode | Tests using file-based DB share state between test functions | Always use `sqlite:///:memory:` or a temp file in fixtures with `Base.metadata.create_all` + teardown drop |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| N+1 on Agent list (model + prompt names) | Response time scales with Agent count | `selectinload(Agent.model, Agent.prompt)` in list query | Visible at ~20 agents in dev; painful at 200+ |
| Loading all Models + Prompts into memory for dropdowns | Dropdown takes 1s+ to open if 500+ prompts exist | Paginate or use `remote-method` search on el-select | When Prompt count exceeds ~200 records |
| No pagination on AgentStatusHistory | History table grows unbounded; GET agent detail becomes slow | Add `limit=50` to history fetch; return most-recent N entries | When any agent has > 100 status changes (unlikely in this experiment, but still) |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Generic error "操作失败" for status change failures | User doesn't know why activation failed (is it missing model? wrong state?) | Return structured error with reason: `{"code": 422, "message": "激活失败：未关联模型"}` |
| Delete button visible for ACTIVE agents | User clicks delete, gets error — confusing | Hide or disable delete button for ACTIVE status; show tooltip "请先停用再删除" |
| No confirmation dialog before ACTIVE→INACTIVE | Accidental deactivation of running agent | `ElMessageBox.confirm()` before any state-changing action |
| Status badge shows raw enum value ("active") | Unprofessional; no visual distinction | Map to Chinese labels + `el-tag` type: `active→success`, `draft→info`, `inactive→warning` |
| Create form allows submitting with no model/prompt selected | Creates DRAFT agent silently; user confused when activation fails later | Show inline warning (not error) in create form: "未选择模型，创建后无法直接激活" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Status filter on GET /agents/**: Filter query param accepts only valid `AgentStatus` values — verify that `?status=garbage` returns 422, not an empty list
- [ ] **ACTIVE cannot be deleted**: Verify `DELETE /agents/{id}` returns 409 (not 404 or 500) when agent is ACTIVE
- [ ] **AgentStatusHistory written atomically**: Verify that if the history INSERT fails, the status update is also rolled back (both writes in same transaction)
- [ ] **INACTIVE→ACTIVE re-validates model+prompt**: Verify that an Agent whose model was deleted while INACTIVE cannot be re-activated (regression-prone: easy to check only at DRAFT→ACTIVE path)
- [ ] **AgentRead includes model_name/prompt_name, not just IDs**: Verify the list response shows names, not foreign key integers — frontend must not need a second lookup
- [ ] **Enum serialization in JSON response**: Verify the `status` field in JSON response is `"active"` (string value), not `"AgentStatus.active"` or `"ACTIVE"` (name)
- [ ] **Test DB isolation**: Verify that running `pytest` twice in a row produces the same results — no shared state between test runs

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Business logic in endpoint layer discovered late | MEDIUM | Extract to `AgentService.change_status()`, update endpoint to delegate; tests must be rewritten against service directly |
| N+1 queries found in production | LOW | Add `selectinload` to service list method; no schema changes needed |
| `status: str` schema in production with bad data in DB | HIGH | Need data migration to normalize status values + schema change + frontend update; prevent by fixing schema before first deploy |
| `AgentStatusHistory` table missing on existing dev DB | LOW | Delete `agents.db`, restart server — `create_all()` recreates all tables fresh |
| Double-click race condition creates duplicate history entries | LOW | Add deduplication check in `AgentService.change_status()`: if `new_status == agent.status`, return early with no-op |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| `status: str` in schema | Phase 1 — Schema definition | `pytest` with `status="invalid"` POST returns 422 |
| N+1 on Agent list | Phase 1 — AgentService.list_agents | Enable `echo=True` and count SQL statements for a 10-agent list |
| Legacy vs 2.x query style | Phase 1 — AgentService scaffolding | Code review: no `db.query()` in `agent_service.py` |
| Transition logic in endpoint | Phase 1 — AgentService.change_status design | `pytest` tests call service methods directly without HTTP |
| Missing table on existing DB | Phase 1 — Test fixtures + model definition | CI runs with fresh DB; `create_all()` before each test session |
| Wrong HTTP status for transitions | Phase 1 — Endpoint error mapping | `pytest` asserts 409 for invalid transition, 422 for pre-condition fail |
| Redundant Model/Prompt fetches on mount | Phase 2 — AgentList.vue | Network tab shows 1 request on list load, 2 extra only on dialog open |
| el-select blank label on pre-selected value | Phase 2 — AgentList.vue edit flow | Manual test: edit existing agent, verify Model name shows in select |
| Double-click race on status buttons | Phase 2 — AgentList.vue action column | Manual test: rapid-click Activate, check only 1 PATCH in network tab |

---

## Sources

- SQLAlchemy 2.x query style: [Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html), [ORM Querying Guide](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
- Lazy loading / N+1: [Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
- Pydantic v2 enum handling: [Pydantic Discussion #4967](https://github.com/pydantic/pydantic/discussions/4967), [Pydantic Discussion #9270](https://github.com/pydantic/pydantic/discussions/9270)
- HTTP status codes for state conflicts: [HTTP Status Codes — Mastering Backend](https://masteringbackend.com/posts/http-status-codes-for-clear-api-responses)
- Element Plus el-select async loading: [Official Docs](https://element-plus.org/en-US/component/select.html)
- `create_all()` with existing tables: [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)
- N+1 in FastAPI/SQLAlchemy context: [Medium — Amjad Jibon](https://medium.com/@amjad.jibon/the-n-1-query-problem-how-one-innocent-loop-can-kill-your-fastapi-performance-4de473abc27f)
- Direct codebase analysis: `entity.py`, `schema.py`, `prompt_service.py`, `endpoints.py` (all read at research time)

---
*Pitfalls research for: brownfield state machine feature addition (DRAFT/ACTIVE/INACTIVE lifecycle) on FastAPI + SQLAlchemy 2.x + Vue 3 + Element Plus*
*Researched: 2026-05-18*

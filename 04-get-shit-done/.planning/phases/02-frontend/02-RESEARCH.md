# Phase 2: Frontend - Research

**Researched:** 2026-05-18
**Domain:** Vue 3 + Element Plus + Pinia frontend (Agent management page)
**Confidence:** HIGH

## Summary

Phase 2 builds a complete Agent management page on top of the Phase 1 backend API. The backend delivers 5 REST endpoints (list, get, create, status-change, delete) with a unified `Response[T]` wrapper (`code=0, data, message`). The frontend must implement a table view with status tags, conditional action buttons, confirmation dialogs, server-side pagination, status filtering, and a create form with lazy-loaded Model/Prompt dropdowns.

The existing codebase provides a strong reference pattern: `PromptList.vue` + `stores/prompt.js` + `api/prompts.js` demonstrate the exact three-layer pattern (View -> Store -> API) that the Agent page should follow. The `api/index.js` interceptor already handles `ElMessage.error()` globally, so store actions only need `try/catch` for state cleanup.

No new packages need to be installed. All required Element Plus components (`el-table`, `el-dialog`, `el-form`, `el-select`, `el-tag`, `el-pagination`, `ElMessageBox`, `ElMessage`) are already available via the global import in `main.js`. The UI-SPEC.md has already been approved and provides the complete design contract.

**Primary recommendation:** Mirror the PromptList.vue three-layer pattern exactly. Create `api/agents.js`, extend `stores/agent.js`, and rewrite `AgentList.vue` to match the UI-SPEC.md contract. No new dependencies required.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FRONT-01 | Agent 列表页显示名称、状态标签、关联 Model 名称、关联 Prompt 名称，支持状态筛选和分页 | Backend `GET /api/v1/agents/` supports `status` filter + `skip/limit` pagination. `AgentRead` schema includes `model_name` and `prompt_name`. Element Plus `el-table` + `el-tag` + `el-select` + `el-pagination` are all pre-installed. |
| FRONT-02 | 每行操作按钮按状态显示，确认对话框，失败时展示具体原因 | Backend returns 409 (InvalidTransition) and 422 (ActivationNotReady) with descriptive `detail` messages. Global error interceptor in `api/index.js` already calls `ElMessage.error()`. `ElMessageBox.confirm()` handles confirmation dialogs. |
| FRONT-03 | 创建 Agent 表单含名称（必填）、描述（选填）、Model 下拉选择（懒加载）、Prompt 下拉选择（懒加载） | Backend `POST /api/v1/agents/` accepts `AgentCreate` (name, description, model_id, prompt_id). `GET /api/v1/models/` and `GET /api/v1/prompts/` provide dropdown data. `el-dialog` + `el-form` + `el-select` handle the form UI. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agent list display (table, tags, pagination) | Browser / Client | - | Pure rendering of API response data |
| Status filtering | Browser / Client | API / Backend | Filter params sent to backend; backend performs server-side filtering |
| Pagination | Browser / Client | API / Backend | skip/limit params sent to backend; backend handles offset pagination |
| State transition buttons | Browser / Client | - | Conditional UI rendering based on row data |
| Confirmation dialogs | Browser / Client | - | `ElMessageBox.confirm()` is a client-side modal |
| Error message display | Browser / Client | - | Global interceptor + `ElMessage.error()` |
| Create form with dropdowns | Browser / Client | API / Backend | Form validation client-side; data fetch and submit via API |
| Lazy loading dropdowns | Browser / Client | API / Backend | Fetch Model/Prompt lists on dialog open, not on page mount |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vue 3 | ^3.5.0 | SPA framework (Composition API) | Already installed, project standard |
| Element Plus | ^2.9.0 | UI component library | Already installed, project standard |
| Pinia | ^2.2.0 | State management | Already installed, project standard |
| Axios | ^1.7.0 | HTTP client | Already installed, project standard |
| Vue Router | ^4.4.0 | Client-side routing | Already installed, route already registered |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @element-plus/icons-vue | bundled with EP | Icons for buttons/tags | Inline button icons (optional enhancement) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Element Plus | Ant Design Vue / Naive UI | Not applicable -- EP is the installed library, no alternative needed |
| Global `ElMessage.error()` in interceptor | Per-action error handling in store | Already implemented in `api/index.js`; per-action handling only for state cleanup |

**Installation:** No new packages needed. All dependencies are pre-installed in `frontend/package.json`.

## Package Legitimacy Audit

> No new packages are being installed in this phase. All required libraries (Vue 3, Element Plus, Pinia, Axios, Vue Router) are already present in `frontend/package.json` and were installed during project initialization.

| Package | Registry | Status | Disposition |
|---------|----------|--------|-------------|
| vue | npm | Already installed | No action needed |
| element-plus | npm | Already installed | No action needed |
| pinia | npm | Already installed | No action needed |
| axios | npm | Already installed | No action needed |
| vue-router | npm | Already installed | No action needed |

**Packages to install:** None.

## Architecture Patterns

### System Architecture Diagram

```
[Browser]
    |
    v
[AgentList.vue] ───────────────────────────────────────────────┐
    |                                                           |
    |  mount → fetchAgents()                                    |
    v                                                           |
[stores/agent.js] ─── api/agents.js ─── [Axios Instance]       |
    |                                    |                      |
    |  GET /api/v1/agents/?status=X&skip=Y&limit=10             |
    |  POST /api/v1/agents/                                     |
    |  PATCH /api/v1/agents/{id}/status                         |
    |  DELETE /api/v1/agents/{id}                               |
    v                                                            |
[Backend FastAPI] ─── AgentService ─── SQLite                  |
    |                                                           |
    |  Response[T] = { code: 0, data: [...], message: "ok" }    |
    |  Error: HTTP 409/422 → interceptor → ElMessage.error()   |
    v                                                           |
[Element Plus]                                                 |
    ├── el-table (list display)                                 |
    ├── el-tag (status labels)                                  |
    ├── el-pagination (pagination controls)                     |
    ├── el-dialog + el-form (create form)                       |
    ├── el-select (status filter + model/prompt dropdowns)      |
    └── ElMessageBox.confirm() (confirmation dialogs)           |
```

### Recommended Project Structure

```
frontend/src/
├── api/
│   ├── index.js          # Existing — Axios instance + global error interceptor
│   ├── prompts.js        # Existing — Prompt API client (reference pattern)
│   └── agents.js         # NEW — Agent API client
├── stores/
│   ├── prompt.js         # Existing — Prompt store (reference pattern)
│   └── agent.js          # EXTEND — Replace stub with full implementation
├── views/
│   ├── Home.vue          # Existing — Navigation to /agents already wired
│   ├── PromptList.vue    # Existing — Reference pattern for list page
│   └── AgentList.vue     # REWRITE — Replace 15-line stub with full page
├── router/index.js       # Existing — /agents route already registered
└── main.js               # Existing — Element Plus globally imported
```

### Pattern 1: Three-Layer Data Flow (View -> Store -> API)

**What:** The standard pattern used throughout the project. View components never call `api.*` directly; they go through the Pinia store.

**When to use:** All data fetching and mutation operations.

**Example (from existing codebase):**

```javascript
// api/agents.js — flat named exports wrapping Axios
import api from './index'

export function fetchAgents(params = {}) {
  return api.get('/api/v1/agents/', { params })
}

export function createAgent(data) {
  return api.post('/api/v1/agents/', data)
}

export function updateAgentStatus(id, data) {
  return api.patch(`/api/v1/agents/${id}/status`, data)
}

export function deleteAgent(id) {
  return api.delete(`/api/v1/agents/${id}`)
}
```

```javascript
// stores/agent.js — Setup Store syntax with ref/computed/actions
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchAgents, createAgent, updateAgentStatus, deleteAgent } from '../api/agents'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)
  const statusFilter = ref(null)

  async function loadAgents() {
    loading.value = true
    try {
      const res = await fetchAgents({
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        status: statusFilter.value || undefined,
      })
      agents.value = res.data || []
    } catch (e) {
      console.error('[AgentStore] load failed:', e)
    } finally {
      loading.value = false
    }
  }

  // ... more actions
  return { agents, loading, total, currentPage, pageSize, statusFilter, loadAgents }
})
```

**Important note on response unwrapping:** The Axios interceptor in `api/index.js` already unwraps the response — when `res.code === 0`, it returns `res` (the full `{ code, data, message }` object). So store actions access data via `res.data`, NOT `res.data.data`. This is confirmed by the existing prompt store: `prompts.value = res.data || []`.

### Pattern 2: Server-Side Pagination

**What:** Pagination handled by the backend via `skip` and `limit` query params. The frontend sends these params and renders `el-pagination` controls.

**When to use:** All list views that may grow beyond a single page.

**Example:**

```vue
<el-pagination
  v-model:current-page="agentStore.currentPage"
  v-model:page-size="agentStore.pageSize"
  :total="agentStore.total"
  layout="total, prev, pager, next"
  @current-change="agentStore.loadAgents"
/>
```

**Backend limitation:** The current `GET /api/v1/agents/` endpoint does NOT return a `total` count in its response. It returns `Response[list[AgentRead]]` where `data` is a flat list. This means the frontend has two options:

1. **Fetch total separately** — Add a `count` endpoint or use the full list length (only works if not filtering).
2. **Workaround** — Fetch one extra record beyond the page to detect "has next", but this doesn't give exact total.

**Recommendation for planner:** The cleanest approach is to accept the limitation and either: (a) not show total count initially (just show prev/next pager), or (b) add a lightweight `GET /api/v1/agents/count?status=X` backend endpoint. Option (a) is simpler and avoids backend changes. Option (b) provides better UX. Since Phase 1 is complete, a small backend addition for count is reasonable but should be flagged for user decision.

### Pattern 3: Conditional Action Buttons with Confirmation

**What:** Each table row shows different buttons based on the Agent's status. All actions require `ElMessageBox.confirm()` before calling the API.

**When to use:** All destructive or state-changing operations.

**Example:**

```vue
<el-table-column label="操作" width="200">
  <template #default="{ row }">
    <el-button
      v-if="row.status === 'draft'"
      type="primary"
      size="small"
      @click="handleActivate(row)"
    >激活</el-button>
    <el-button
      v-if="row.status === 'active'"
      type="warning"
      size="small"
      @click="handleDeactivate(row)"
    >停用</el-button>
    <template v-if="row.status === 'inactive'">
      <el-button type="primary" size="small" @click="handleActivate(row)">激活</el-button>
      <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
    </template>
  </template>
</el-table-column>
```

```javascript
import { ElMessageBox } from 'element-plus'

async function handleActivate(agent) {
  await ElMessageBox.confirm(
    `确认激活 Agent「${agent.name}」？激活前系统将验证关联的 Model 和 Prompt 是否有效。`,
    '激活确认'
  )
  await agentStore.updateStatus(agent.id, 'active')
}
```

### Pattern 4: Lazy-Loaded Dropdowns in Dialog

**What:** Model and Prompt dropdown options are fetched only when the create dialog opens, not on page mount.

**When to use:** Reference data needed only in specific contexts (forms, dialogs).

**Example:**

```javascript
const createDialogVisible = ref(false)
const models = ref([])
const prompts = ref([])

async function openCreateDialog() {
  createDialogVisible.value = true
  // Lazy load dropdown options only when dialog opens
  const [modelsRes, promptsRes] = await Promise.all([
    api.get('/api/v1/models/'),
    api.get('/api/v1/prompts/'),
  ])
  models.value = modelsRes.data || []
  prompts.value = promptsRes.data || []
}
```

### Anti-Patterns to Avoid

- **Direct API calls from View components:** Always go through the Pinia store. PromptList.vue does this correctly.
- **Double error handling:** The `api/index.js` interceptor already shows `ElMessage.error()` for all errors. Do NOT add another `ElMessage.error()` in the store or view — this would show duplicate error messages. Only use `try/catch` in store actions for state cleanup (e.g., `agents.value = []`).
- **Client-side filtering when backend supports it:** The backend accepts `status` query param. Use server-side filtering, not `computed` filters on the frontend.
- **Hardcoded status strings:** Use the backend's enum values: `'draft'`, `'active'`, `'inactive'` (lowercase, matching `AgentStatus` enum values).
- **Not handling empty model_name/prompt_name:** When an Agent has no associated model or prompt, `model_name` and `prompt_name` will be `null`. Display a dash or "未关联" instead of "null" or blank.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP error display | Custom toast/notification system | `ElMessage.error()` via existing interceptor | Already wired globally in `api/index.js` |
| Confirmation dialogs | Custom modal component | `ElMessageBox.confirm()` | Built into Element Plus, handles promise-based confirm/cancel |
| Form validation | Manual validation logic | `el-form` rules + `el-form-item` prop | Declarative validation rules, automatic error display |
| Status tags | Custom badge component | `el-tag` with `type` prop | Semantic color mapping: info/success/warning |
| Table with loading | Custom loading overlay | `v-loading` directive | One directive, handles skeleton state |
| Pagination UI | Custom page controls | `el-pagination` | Handles page numbers, prev/next, total count |

**Key insight:** Element Plus covers every UI need for this phase. The project imports EP globally in `main.js` (`app.use(ElementPlus)`), so all components are available without per-component imports.

## Common Pitfalls

### Pitfall 1: Response Unwrapping Confusion

**What goes wrong:** Store tries to access `res.data.data` (double unwrap) because the backend wraps in `Response[T]` and Axios wraps in `response.data`.

**Why it happens:** The `api/index.js` interceptor already unwraps once — it returns `res` (which is `response.data`), so the structure is `{ code: 0, data: [...], message: "success" }`. Access the array via `res.data`.

**How to avoid:** Follow the existing prompt store pattern exactly: `prompts.value = res.data || []`.

**Warning signs:** `undefined` data in templates, double-nested arrays.

### Pitfall 2: Duplicate Error Messages

**What goes wrong:** User sees two error toasts for the same API failure.

**Why it happens:** The global interceptor in `api/index.js` calls `ElMessage.error()` for all errors. If the store action also calls `ElMessage.error()`, the user gets double notifications.

**How to avoid:** Only use `try/catch` in store actions for cleanup logic (resetting state), NOT for showing error messages. The interceptor handles all user-facing error display.

**Warning signs:** Two identical toast messages appearing simultaneously.

### Pitfall 3: Backend Returns Total Count Missing

**What goes wrong:** `el-pagination` shows "total 0" or pagination doesn't work correctly because the backend doesn't return total count.

**Why it happens:** The current `GET /api/v1/agents/` endpoint returns `Response[list[AgentRead]]` — a flat list, no total count field.

**How to avoid:** Either (a) show pagination without total count (just prev/pager/next), or (b) plan a small backend addition to return count. The planner should decide which approach.

**Warning signs:** Pagination component shows "total 0" when records exist.

### Pitfall 4: AgentStatus Enum Value Case Mismatch

**What goes wrong:** Frontend compares status with wrong case (e.g., `row.status === 'DRAFT'` instead of `row.status === 'draft'`).

**Why it happens:** The `AgentStatus` enum has uppercase keys (`DRAFT`, `ACTIVE`, `INACTIVE`) but lowercase values (`"draft"`, `"active"`, `"inactive"`). The schema uses `use_enum_values=True`, so the API returns lowercase string values.

**How to avoid:** Always compare with lowercase values: `'draft'`, `'active'`, `'inactive'`.

**Warning signs:** Status buttons never appear, or wrong buttons appear.

### Pitfall 5: Not Refreshing List After Mutation

**What goes wrong:** After creating, activating, or deleting an Agent, the table still shows stale data.

**Why it happens:** The store action completes but doesn't trigger a list refresh.

**How to avoid:** Every mutation action (create, updateStatus, delete) must call `loadAgents()` (or equivalent) after success to refresh the table.

**Warning signs:** User creates an Agent but doesn't see it in the list until manual page refresh.

### Pitfall 6: Create Form Model/Prompt as Required When They Should Be Optional

**What goes wrong:** Form validation prevents submission when Model and Prompt are not selected, but the backend allows creating an Agent without them (status is always DRAFT).

**Why it happens:** Developer assumes model_id and prompt_id are always required, but `AgentCreate` schema has `model_id: int | None = None` and `prompt_id: int | None = None`.

**How to avoid:** Set Model and Prompt as optional in form validation rules. Only require `name`.

**Warning signs:** User cannot create an Agent without selecting Model/Prompt.

## Code Examples

### API Client Pattern (new file: api/agents.js)

```javascript
// Source: Based on existing api/prompts.js pattern
import api from './index'

export function fetchAgents(params = {}) {
  return api.get('/api/v1/agents/', { params })
}

export function createAgent(data) {
  return api.post('/api/v1/agents/', data)
}

export function updateAgentStatus(id, data) {
  return api.patch(`/api/v1/agents/${id}/status`, data)
}

export function deleteAgent(id) {
  return api.delete(`/api/v1/agents/${id}`)
}
```

### Status Tag Mapping

```vue
<!-- Source: UI-SPEC.md status color mapping -->
<el-tag :type="statusTagType(row.status)" size="small">
  {{ statusLabel(row.status) }}
</el-tag>
```

```javascript
function statusTagType(status) {
  const map = { draft: 'info', active: 'success', inactive: 'warning' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { draft: 'DRAFT', active: 'ACTIVE', inactive: 'INACTIVE' }
  return map[status] || status
}
```

### Backend Error Response Handling

The backend returns specific HTTP status codes and messages for state transitions:

| Scenario | HTTP Status | Response `detail` |
|----------|-------------|-------------------|
| Agent not found | 404 | "Agent not found" |
| Invalid transition | 409 | "无法从 active 切换到 draft" |
| Activation failed (no model) | 422 | "激活失败：Agent 未关联模型" |
| Activation failed (model deleted) | 422 | "激活失败：关联模型 (id=1) 已不存在" |
| Delete active agent | 409 | "无法删除：Agent 正处于激活状态，请先停用" |

All of these are caught by the global interceptor and displayed via `ElMessage.error()`. The store only needs `try/catch` for state cleanup.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Options API | Composition API with `<script setup>` | Vue 3.0+ | Cleaner code, better TypeScript support |
| Vuex | Pinia Setup Stores | Vue 3 / Pinia 2+ | Better DX, no mutations, full TS support |
| `db.query()` (legacy SA) | `select()` + `execute()` (SA 2.x) | SQLAlchemy 2.0 | Phase 1 already uses new style |

**Deprecated/outdated:**
- Options API: Project already uses Composition API throughout -- no risk.
- Vuex: Project already uses Pinia -- no risk.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Backend pagination does NOT return total count (only flat list) | Pattern 2, Pitfall 3 | Frontend pagination UX degrades; needs backend fix or workaround |
| A2 | Element Plus icons (@element-plus/icons-vue) are bundled with the main package | Standard Stack | Icons might not render; may need explicit import or separate install |
| A3 | `el-form` rules validation supports `required: false` for optional fields | Pattern 4 | Form might reject valid submissions |

## Open Questions

1. **Pagination total count**
   - What we know: Backend `GET /api/v1/agents/` returns `Response[list[AgentRead]]` with no total field
   - What's unclear: Should we add a count endpoint, or work without total display?
   - Recommendation: Accept the limitation initially -- use `el-pagination` without `total` prop (just prev/pager/next). If UX needs improvement later, add `GET /api/v1/agents/count` backend endpoint.

2. **Create dialog reset behavior**
   - What we know: After successful creation, the dialog should close and the list should refresh
   - What's unclear: Should the form fields be preserved for rapid creation, or reset?
   - Recommendation: Reset form fields on close (standard UX pattern). This is a minor detail the planner can decide.

## Environment Availability

> Step 2.6: SKIPPED (no external dependencies identified -- all libraries are pre-installed in the project)

## Validation Architecture

> SKIPPED: `workflow.nyquist_validation` is explicitly set to `false` in `.planning/config.json`.

## Security Domain

> No server-side security concerns for this phase. All operations go through the existing Axios interceptor. No user input is rendered as HTML (Element Plus handles escaping). No auth requirements (per REQUIREMENTS.md "Out of Scope" section).

## Sources

### Primary (HIGH confidence)
- Existing codebase: `frontend/src/views/PromptList.vue` -- reference pattern for list pages
- Existing codebase: `frontend/src/stores/prompt.js` -- reference pattern for Pinia stores
- Existing codebase: `frontend/src/api/prompts.js` + `api/index.js` -- reference pattern for API clients
- Existing codebase: `backend/app/api/v1/endpoints.py` -- all Agent API endpoints and error responses
- Existing codebase: `backend/app/schemas/schema.py` -- AgentCreate, AgentRead, StatusChangeRequest schemas
- UI-SPEC: `.planning/phases/02-frontend/02-UI-SPEC.md` -- approved design contract
- Backend service: `backend/app/services/agent_service.py` -- business rules and error messages

### Secondary (MEDIUM confidence)
- Element Plus 2.9.0 documentation -- component APIs (el-table, el-dialog, el-form, el-pagination, ElMessageBox)

### Tertiary (LOW confidence)
- None -- all findings are based on verified codebase inspection.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all packages verified in package.json, no new installs needed
- Architecture: HIGH - patterns verified against existing codebase (PromptList, prompt store, API client)
- Pitfalls: HIGH - all pitfalls derived from actual code inspection and confirmed API contracts

**Research date:** 2026-05-18
**Valid until:** 60 days (stable codebase, no external dependency changes)

# Feature Research

**Domain:** AI Agent Lifecycle Management UI (brownfield, Vue 3 + Element Plus + Pinia)
**Researched:** 2026-05-18
**Confidence:** HIGH — based on direct codebase analysis + established patterns from comparable admin UIs

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features an admin UI for stateful entities must have. Missing any of these makes the page feel broken.

| Feature | Why Expected | Complexity | Element Plus Component | Notes |
|---------|--------------|------------|----------------------|-------|
| Status badge on each row | Users must instantly see which agents are live vs draft | LOW | `el-tag` with `type` prop (success/warning/info) | ACTIVE=success, DRAFT=warning, INACTIVE=info |
| State transition button in each row | Users expect to act directly from the list, not navigate away | LOW | `el-button` with `size="small"` | Label changes per current state (see UX section below) |
| Confirmation dialog before state change | Destructive-ish actions need friction; activating a live agent or deactivating one in use has real consequences | LOW | `ElMessageBox.confirm` | Different copy for activate vs deactivate |
| Inline error message when transition fails | Business rule violations (missing Model/Prompt) must surface clearly, not silently swallow | LOW | `ElMessage.error` already wired in `api/index.js` | Backend 400 detail already propagates via interceptor |
| Status filter on list | Users operate on subsets — "show me all active agents" is the most common query | LOW | `el-select` with enum options | Maps to `GET /agents/?status=active` |
| Create Agent form with Model + Prompt dropdowns | Can't create a usable agent without associating dependencies | MEDIUM | `el-dialog` + `el-form` + `el-select` (remote or preloaded) | Must fetch Model list and Prompt list to populate dropdowns |
| Delete button (conditional visibility) | ACTIVE agents must not be deletable; button should be absent or disabled, not just gated server-side | LOW | `el-button` with `disabled` or `v-if` based on status | Show tooltip "请先停用 Agent" when ACTIVE |
| Loading states | List fetch, transition, create — all need spinners or disabled states | LOW | `v-loading` directive on table, `loading` prop on buttons | Follow `promptStore.loading` pattern already in `PromptList.vue` |
| Empty state | First-time view with no agents should guide users to create | LOW | `el-empty` or `el-table` `empty-text` prop | "暂无 Agent，点击创建" |
| Pagination or total count | List can grow; users need orientation | LOW | `el-pagination` (server-side) or static total (client-side) | API supports `skip/limit`; use server-side from day one |

### Differentiators (Competitive Advantage)

Features that make the state management experience notably better than a bare CRUD table.

| Feature | Value Proposition | Complexity | Element Plus Component | Notes |
|---------|-------------------|------------|----------------------|-------|
| Dependency validation feedback before confirm | Show "Model: GPT-4 / Prompt: xxx" in the confirm dialog so users know what they're activating | LOW | `ElMessageBox.confirm` with `message` as VNode or HTML | Eliminates "what did I just activate?" confusion |
| Visual dependency status in list | Show Model name and Prompt name inline — users can spot "Agent has no model" without opening detail | MEDIUM | `el-table-column` with formatted cell; `null` shown as `el-tag type="danger"` "未配置" | Requires `joinedload` on backend to avoid N+1 |
| Transition button label that anticipates outcome | "激活" vs "停用" as the label (not just a generic "Change Status") — removes cognitive load | LOW | Standard `el-button` | Already implied by the requirement; highlight it as intentional design |
| Optimistic UI on status toggle | Show new status immediately; revert on error | MEDIUM | Local state mutation before API call completes | Only do this if rollback is clean; otherwise skip (see anti-features) |
| Status change timestamp in detail/tooltip | "Activated 2 hours ago" provides operational context | LOW | `el-tooltip` wrapping the status tag | Backend must store `status_changed_at`; this is the "变更记录" requirement |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Optimistic UI for state transitions | Feels snappier | State transitions have server-side validation; if optimistic flip shows ACTIVE and then reverts after 200ms because Model was deleted between page load and click, the flicker is more confusing than a brief spinner | Use `loading` prop on the button instead — disable it during the PATCH call, re-enable on response |
| Bulk status change (select all + activate) | Power users want batch ops | Multiplies validation failure surface area dramatically; one failed agent in a batch of 20 needs careful per-item error display, which is significant complexity for this scope | Single-row operations only for v1; add bulk with a dedicated batch validation endpoint later |
| Inline editing of Agent name/description | Reduces clicks | Two-mode (read/edit) inline cells in `el-table` are a known complexity trap — `el-table-column` editing state management conflicts with row selection and status action buttons | Use a separate edit dialog or detail page; keep table rows read-only |
| Real-time status polling | Agents could be activated externally | Adds websocket or polling complexity with no clear benefit for a single-user admin tool | Manual refresh button ("刷新") next to the create button |
| Status history timeline UI | "Show me when each state change happened" | Significant frontend complexity (timeline component, pagination of history entries) for an audit feature that belongs in a logs view, not an admin list | Store `status_changed_at` and `status_change_reason` in backend now; surface as a tooltip or simple field; defer full history to v2 |
| Cascading Skill deactivation UI | Mark Skills as unavailable when Agent stops | PROJECT.md explicitly put `Skill.is_active` out of scope; status is implicit via Agent.status | If Skills need individual availability, that's a separate Skill management feature |

---

## Feature Dependencies

```
[Status Filter]
    └──requires──> [Agent List API with ?status= param]

[Create Agent Form]
    └──requires──> [Model List API]
    └──requires──> [Prompt List API]

[Status Transition Button]
    └──requires──> [PATCH /agents/{id}/status]
    └──requires──> [Confirmation Dialog]
                       └──enhances──> [Dependency Validation Feedback]

[Delete Button]
    └──requires──> [Status Transition Button] (must deactivate before delete is enabled)

[Status Change Timestamp tooltip]
    └──requires──> [status_changed_at field in backend] (变更记录)
```

### Dependency Notes

- **Create Agent Form requires Model + Prompt lists:** Both `GET /api/v1/models/` and `GET /api/v1/prompts/` must be called when the create dialog opens. These APIs already exist.
- **Delete requires prior deactivation:** The delete button must be conditionally rendered/disabled based on `agent.status === 'active'`. This is a frontend guard; backend enforces it too.
- **Status timestamp tooltip requires backend 变更记录:** If the backend does not store `status_changed_at`, the tooltip cannot show meaningful data. Since PROJECT.md includes 变更记录 in scope, implement it in the same phase.

---

## MVP Definition

### Launch With (v1 — this milestone)

- [x] Agent list table with status badge, Model name, Prompt name columns
- [x] Status filter (`el-select` bound to `?status=` query param)
- [x] Activate / Deactivate button per row with `ElMessageBox.confirm`
- [x] Error surface via existing `ElMessage.error` interceptor (covers business rule violations)
- [x] Create Agent dialog with name, description, Model dropdown, Prompt dropdown
- [x] Delete button visible only for DRAFT/INACTIVE agents
- [x] Loading states on table and action buttons
- [x] Pagination (server-side, `el-pagination`)

### Add After Validation (v1.x)

- [ ] Dependency validation preview in confirm dialog — show Model/Prompt names inline
- [ ] Status change timestamp in tooltip over status badge
- [ ] "未配置" warning badge when Agent has no Model or Prompt assigned

### Future Consideration (v2+)

- [ ] Bulk status operations
- [ ] Status history timeline
- [ ] Real-time status sync (websocket)

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Status badge + filter | HIGH | LOW | P1 |
| Activate/Deactivate button + confirm dialog | HIGH | LOW | P1 |
| Inline error message on failure | HIGH | LOW | P1 |
| Create form with dropdowns | HIGH | MEDIUM | P1 |
| Delete with ACTIVE guard | HIGH | LOW | P1 |
| Loading states | MEDIUM | LOW | P1 |
| Pagination | MEDIUM | LOW | P1 |
| Model/Prompt name in table row | MEDIUM | LOW | P1 |
| Dependency preview in confirm | MEDIUM | LOW | P2 |
| Status changed_at tooltip | LOW | LOW | P2 |
| "未配置" warning indicator | MEDIUM | LOW | P2 |
| Bulk operations | LOW | HIGH | P3 |
| Real-time polling | LOW | HIGH | P3 |

---

## UX Patterns for State Transitions

### Button Label Convention

Buttons must describe the action the user is about to take, not the current state:

| Current Status | Button Label | Button Type |
|----------------|--------------|-------------|
| DRAFT | 激活 | `type="primary"` |
| ACTIVE | 停用 | `type="warning"` |
| INACTIVE | 重新激活 | `type="primary"` |

Delete button: shown for DRAFT and INACTIVE only. Use `el-popconfirm` (inline) for delete — simpler than `ElMessageBox` for a less consequential action.

### Confirmation Dialog Copy

**Activate (DRAFT → ACTIVE or INACTIVE → ACTIVE):**
```
标题: 确认激活 Agent？
正文: 激活后，Agent 将进入运行状态。请确认已关联有效的模型和提示词。
按钮: 取消 / 确认激活
```

**Deactivate (ACTIVE → INACTIVE):**
```
标题: 确认停用 Agent？
正文: 停用后，该 Agent 的关联技能将不可用。可随时重新激活。
按钮: 取消 / 确认停用
```

**Delete:**
Use `el-popconfirm` directly on the button — no dialog, just inline "确认删除？" with 确定/取消.

### Business Rule Error UX

When the backend returns 400 (e.g., Agent has no Model assigned):
- `api/index.js` interceptor already calls `ElMessage.error(res.message)` — no extra code needed
- Backend must return a human-readable `message` in Chinese: "激活失败：未关联有效模型"
- The button loading state must reset after error so the user can retry

### Status Tag Color Map (Element Plus `el-tag`)

```javascript
const statusTagType = {
  draft: 'warning',    // yellow — incomplete
  active: 'success',  // green — running
  inactive: 'info',   // gray — stopped
}

const statusLabel = {
  draft: '草稿',
  active: '运行中',
  inactive: '已停用',
}
```

---

## Competitor Feature Analysis

Comparable UIs: Flowise agent list, Dify app management, LangFlow flow list.

| Feature | Flowise | Dify | Our Approach |
|---------|---------|------|--------------|
| Status badge | Toggle switch (on/off) | Status dot + text | `el-tag` with color — more descriptive than a toggle for 3-state systems |
| Transition confirmation | No confirmation on toggle | Confirmation modal for delete only | `ElMessageBox.confirm` for activate/deactivate — appropriate friction for state-changing ops |
| Dependency visibility | Not shown in list | Not shown in list | Show Model + Prompt name inline — reduces navigation cost |
| Delete guard | No ACTIVE guard | Archive instead of delete | Hard disable + tooltip on ACTIVE agents — clearest intent |

Confidence: MEDIUM — based on publicly available UI screenshots and usage patterns; exact implementation details not verified against source code.

---

## Sources

- Direct codebase analysis: `entity.py`, `schema.py`, `PromptList.vue`, `prompt.js`, `api/index.js`
- PROJECT.md requirements and out-of-scope decisions
- Element Plus 2.x documentation patterns (el-tag, el-table, ElMessageBox, el-popconfirm)
- Comparable AI agent management UIs: Flowise, Dify, LangFlow (MEDIUM confidence, UI observation only)

---
*Feature research for: AI Agent Lifecycle Management UI*
*Researched: 2026-05-18*

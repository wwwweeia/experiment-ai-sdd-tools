# Phase 2: Frontend - Pattern Map

**Mapped:** 2026-05-18
**Files analyzed:** 3 (new/modified)
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `frontend/src/api/agents.js` | api-client | request-response | `frontend/src/api/prompts.js` | exact |
| `frontend/src/stores/agent.js` | store | request-response | `frontend/src/stores/prompt.js` | role-match |
| `frontend/src/views/AgentList.vue` | component | request-response | `frontend/src/views/PromptList.vue` | role-match |

## Pattern Assignments

### `frontend/src/api/agents.js` (api-client, request-response)

**Analog:** `frontend/src/api/prompts.js` (entire file, 17 lines)

**Imports + export pattern** (lines 1-17):
```javascript
import api from './index'

export function fetchPrompts(params = {}) {
  return api.get('/api/v1/prompts/', { params })
}

export function fetchPrompt(id) {
  return api.get(`/api/v1/prompts/${id}`)
}

export function createPrompt(data) {
  return api.post('/api/v1/prompts/', data)
}

export function deletePrompt(id) {
  return api.delete(`/api/v1/prompts/${id}`)
}
```

**Key pattern to copy:**
- Single import of the shared Axios instance from `./index`
- Flat named exports (one function per endpoint)
- `params = {}` default for list endpoints (supports filtering/pagination)
- Template literals for path params (`/api/v1/agents/${id}`)
- No error handling here — the interceptor in `api/index.js` handles all errors globally

**New file should export:** `fetchAgents`, `createAgent`, `updateAgentStatus`, `deleteAgent`, `fetchModels`, `fetchPrompts` (for dropdown data)

---

### `frontend/src/stores/agent.js` (store, request-response)

**Analog:** `frontend/src/stores/prompt.js` (entire file, 106 lines)

**Store definition pattern** (lines 1-3, 20-21):
```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchPrompts as fetchPromptsApi } from '../api/prompts'

export const usePromptStore = defineStore('prompt', () => {
  // ...
})
```

**State + loading pattern** (lines 22-24):
```javascript
const prompts = ref([])
const loading = ref(false)
const searchForm = ref({
  keyword: '',
  tags: [],
})
```

**Core fetch action pattern** (lines 70-81):
```javascript
async function fetchPrompts() {
  loading.value = true
  try {
    const res = await fetchPromptsApi()
    prompts.value = res.data || []
  } catch (e) {
    console.error('[PromptStore] 加载失败:', e)
    prompts.value = []
  } finally {
    loading.value = false
  }
}
```

**CRITICAL — response unwrapping:** Note `res.data || []` on line 74. The interceptor in `api/index.js` (lines 10-17) already unwraps `response.data` and returns `res` (the `{ code, data, message }` object). So `res.data` gives you the actual array, NOT `res.data.data`.

**Existing stub to replace** (`frontend/src/stores/agent.js`, lines 1-21):
```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)

  async function fetchAgents() {
    loading.value = true
    try {
      const res = await api.get('/api/v1/agents')
      agents.value = res.data?.data || []
    } finally {
      loading.value = false
    }
  }

  return { agents, loading, fetchAgents }
})
```

**Bug in existing stub:** Line 13 uses `res.data?.data` (double unwrap). The interceptor already strips one layer. Must use `res.data` to match the prompt store pattern. Also, the stub imports `api` directly instead of using a dedicated `api/agents.js` module — both patterns exist in the codebase, but the prompt store's pattern of importing from a dedicated API module is cleaner.

**New file needs these additions over the stub:**
- `statusFilter` ref for server-side filtering
- `currentPage`, `pageSize`, `total` refs for pagination
- `createAgent`, `updateStatus`, `deleteAgent` actions
- Every mutation action must call `loadAgents()` after success
- Use `try/catch` only for state cleanup, NOT for showing error messages (interceptor handles that)

---

### `frontend/src/views/AgentList.vue` (component, request-response)

**Analog:** `frontend/src/views/PromptList.vue` (entire file, 157 lines)

**Component structure pattern** (lines 1-81):
```vue
<template>
  <div class="prompt-list">
    <!-- 搜索区 -->
    <div class="search-area">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        ...
      </el-form>
    </div>

    <!-- 表格区 -->
    <el-table
      v-loading="promptStore.loading"
      :data="promptStore.filteredPrompts"
      style="width: 100%"
      empty-text="暂无数据"
      :default-sort="{ prop: 'createdTime', order: 'descending' }"
    >
      ...
    </el-table>

    <!-- 底部信息 -->
    <div class="table-footer">
      <span class="total-count">共 {{ promptStore.filteredPrompts.length }} 条记录</span>
    </div>
  </div>
</template>
```

**Script setup pattern** (lines 83-115):
```javascript
<script setup>
import { reactive, onMounted } from 'vue'
import { usePromptStore } from '../stores/prompt'

const promptStore = usePromptStore()

// 搜索表单（与 Store searchForm 保持同步）
const searchForm = reactive({
  keyword: '',
  tags: [],
})

// ... helper functions ...

onMounted(() => {
  promptStore.fetchPrompts()
})
</script>
```

**CSS pattern** (lines 118-157):
```css
.prompt-list {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 60px);
}

.search-area {
  margin-bottom: 20px;
  padding: 16px 20px;
  border-radius: 4px;
}

.table-footer {
  margin-top: 16px;
  text-align: right;
}

.total-count {
  font-size: 13px;
  color: #909399;
}
```

**Note on spacing scale:** The UI-SPEC specifies `padding: 24px` (token `lg`) for the page wrapper instead of the legacy `20px` used by PromptList. AgentList should use the updated scale value.

**Key differences from PromptList that AgentList needs:**
- `el-pagination` component (PromptList has no pagination — it fetches all records)
- Conditional action buttons per row (`v-if` on status)
- `ElMessageBox.confirm()` before mutations
- `el-dialog` + `el-form` for create form (PromptList has no create dialog)
- Status filter dropdown sends params to backend (PromptList filters client-side)
- `el-tag` with type mapping for status display

**Existing stub to replace** (`frontend/src/views/AgentList.vue`, lines 1-15):
```vue
<template>
  <div class="agent-list">
    <h2>Agent 管理</h2>
    <p>Agent 管理页面（待实现）</p>
  </div>
</template>

<script setup>
</script>

<style scoped>
.agent-list {
  padding: 20px;
}
</style>
```

---

## Shared Patterns

### Global Error Interceptor

**Source:** `frontend/src/api/index.js` (lines 8-22)
**Apply to:** All files — store and view layers must NOT duplicate error display

```javascript
api.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== undefined && res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  (error) => {
    ElMessage.error(error.response?.data?.detail || error.message || '网络错误')
    return Promise.reject(error)
  }
)
```

**Implication:** When backend returns 409/422 errors for invalid transitions, `error.response.data.detail` (the Chinese error message) is already displayed to the user via this interceptor. The store action only needs `try/catch` for cleanup — no `ElMessage.error()` calls in store or view.

### Element Plus Global Registration

**Source:** `frontend/src/main.js` (lines 1-13)
**Apply to:** All view files — no per-component imports needed for EP components

```javascript
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// ...
app.use(ElementPlus)
```

All `el-*` components and `ElMessage`/`ElMessageBox` are available globally. Exception: `ElMessageBox` may need explicit import in `<script setup>` for tree-shaking clarity, but it works without import due to global registration.

### Response Unwrapping Convention

**Source:** `api/index.js` interceptor (line 16: `return res`) + `stores/prompt.js` (line 74: `res.data || []`)
**Apply to:** All store actions

The interceptor returns the unwrapped `{ code: 0, data: [...], message: "success" }` object. Store actions access the payload via `res.data`. The existing agent store stub has a bug using `res.data?.data` — this must be fixed.

### Router Registration (no changes needed)

**Source:** `frontend/src/router/index.js` (line 7)
**Apply to:** No action needed — `/agents` route already registered

```javascript
{ path: '/agents', name: 'AgentList', component: () => import('../views/AgentList.vue') },
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All 3 files have strong analogs in the codebase |

## Metadata

**Analog search scope:** `frontend/src/api/`, `frontend/src/stores/`, `frontend/src/views/`
**Files scanned:** 6 (api/index.js, api/prompts.js, stores/prompt.js, stores/agent.js, views/PromptList.vue, views/AgentList.vue)
**Pattern extraction date:** 2026-05-18

# Tasks: Agent 状态管理（激活/停用）

**Input**: Design documents from `/specs/001-agent-status-management/`

**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/agents-api.md, research.md

**Tests**: Spec 中未明确要求测试，不生成测试任务。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/`, `frontend/src/`

---

## Phase 1: Setup (Model & Schema Changes)

**Purpose**: 更新数据模型和 Pydantic Schema，为所有 User Story 提供基础

- [x] T001 修改 Agent 模型，新增 activated_at 和 deactivated_at 字段 in backend/app/models/entity.py
- [x] T002 [P] 修改 Skill 模型，新增 is_active 布尔字段（默认 True） in backend/app/models/entity.py
- [x] T003 修改 Pydantic schemas，新增 AgentStatusUpdate（status + reason）、AgentDetail（含 model_name/prompt_title/activated_at/deactivated_at）等 schema in backend/app/schemas/schema.py
- [x] T004 重建数据库（删除旧 db 文件后重启 uvicorn，SQLite auto-create）

---

## Phase 2: Foundational (AgentService + Router)

**Purpose**: 实现 AgentService 核心业务逻辑和 API 路由注册，所有 User Story 依赖此阶段

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 实现 AgentService 基础 CRUD（list_agents, get_agent, create_agent） in backend/app/services/agent_service.py
- [x] T006 实现 AgentService 状态管理逻辑（activate_agent 含 Model/Prompt 校验、deactivate_agent 含 Skill 标记） in backend/app/services/agent_service.py
- [x] T007 实现 AgentService 删除逻辑（delete_agent 含 ACTIVE 状态保护） in backend/app/services/agent_service.py
- [x] T008 创建 agents_router，实现所有 5 个 API 端点（GET list, GET detail, POST create, PATCH status, DELETE） in backend/app/api/v1/endpoints.py
- [x] T009 注册 agents_router 到主路由 in backend/app/api/v1/router.py

**Checkpoint**: 后端 API 全部就绪，可通过 curl 验证

---

## Phase 3: User Story 5 - Agent 列表页 (Priority: P1)

**Goal**: 用户可以查看所有 Agent 列表，按状态筛选，分页浏览

**Independent Test**: 打开 /agents 页面，能看到 Agent 列表和状态筛选

### Implementation for User Story 5

- [x] T010 [P] [US5] 创建 Agent API 模块，实现 fetchAgents（含 status 参数）、fetchAgent、createAgent、changeAgentStatus、deleteAgent 函数 in frontend/src/api/agents.js
- [x] T011 [P] [US5] 完善 Agent Pinia store，增加 agents 列表、loading 状态、statusFilter、fetchAgents（含状态筛选）、分页逻辑 in frontend/src/stores/agent.js
- [x] T012 [US5] 实现 AgentList.vue 主体：el-table 显示 Agent 列表（名称、状态 el-tag、关联 Model 名、关联 Prompt 名），顶部 el-radio-group 状态筛选，el-pagination 分页 in frontend/src/views/AgentList.vue

**Checkpoint**: Agent 列表页可正常展示数据，状态筛选和分页工作正常

---

## Phase 4: User Story 1 - 创建 Agent (Priority: P1)

**Goal**: 用户可以通过表单创建新 Agent，默认 DRAFT 状态

**Independent Test**: 在列表页点击创建按钮，填写表单提交，列表刷新显示新 Agent

### Implementation for User Story 1

- [x] T013 [US1] 在 AgentList.vue 中实现创建 Agent 对话框：el-dialog + el-form（名称必填、描述、Model 下拉选择、Prompt 下拉选择），提交后刷新列表 in frontend/src/views/AgentList.vue
- [x] T014 [US1] Agent store 增加 createAgent action，调用 API 后刷新列表 in frontend/src/stores/agent.js

**Checkpoint**: 用户可以创建 DRAFT 状态的 Agent 并在列表中看到

---

## Phase 5: User Story 2+3 - 激活/停用 Agent (Priority: P1)

**Goal**: 用户可以激活或停用 Agent，激活时校验关联关系，停用时标记 Skill 不可用

**Independent Test**: 在列表页点击激活/停用按钮，确认后状态变更；缺少关联时显示错误提示

### Implementation for User Story 2+3

- [x] T015 [US2] 在 AgentList.vue 操作列中，根据 Agent 状态显示对应按钮（DRAFT: 激活；ACTIVE: 停用；INACTIVE: 激活+删除），点击激活按钮弹出确认对话框 in frontend/src/views/AgentList.vue
- [x] T016 [US2] Agent store 增加 changeStatus action，调用 PATCH API，成功后刷新列表，失败时 ElMessage.error 显示具体原因 in frontend/src/stores/agent.js
- [x] T017 [US3] 停用确认对话框显示影响说明（"Agent 将暂停运行，关联 Skill 将不可用"），确认后调用 deactivate API in frontend/src/views/AgentList.vue
- [x] T018 [US2+US3] 状态 el-tag 使用不同颜色区分：draft=info/warning、active=success、inactive=info/gray in frontend/src/views/AgentList.vue

**Checkpoint**: 激活/停用流程完整，校验失败有明确错误提示，Skill 标记正确

---

## Phase 6: User Story 4 - 删除 Agent (Priority: P2)

**Goal**: 用户可以删除 DRAFT/INACTIVE 的 Agent，ACTIVE 状态不允许删除

**Independent Test**: INACTIVE Agent 可删除，ACTIVE Agent 无删除按钮

### Implementation for User Story 4

- [x] T019 [US4] 在 AgentList.vue 中，INACTIVE 状态 Agent 显示删除按钮，点击弹出确认对话框，确认后调用 DELETE API in frontend/src/views/AgentList.vue
- [x] T020 [US4] Agent store 增加 deleteAgent action，调用 DELETE API 后刷新列表，422 错误时提示"请先停用" in frontend/src/stores/agent.js

**Checkpoint**: 删除保护功能正常，ACTIVE Agent 无法删除

---

## Phase 7: Polish & Validation

**Purpose**: 端到端验证和代码清理

- [x] T021 删除旧数据库文件，运行 seed.py 重新生成测试数据，验证所有 API 端点正常
- [x] T022 按 quickstart.md 步骤执行端到端验证（curl 后端 + 浏览器前端）
- [x] T023 检查 AgentList.vue 代码风格，确保与 PromptList.vue 一致

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Phase 2 completion
  - US5 (Phase 3) must complete first — it builds the page shell
  - US1 (Phase 4) depends on US5 — adds create dialog to the page
  - US2+US3 (Phase 5) depends on US5 — adds action buttons to the page
  - US4 (Phase 6) depends on US5 — adds delete button to the page
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US5 (P1)**: Can start after Phase 2 - builds the list page
- **US1 (P1)**: Can start after US5 - adds create to the page
- **US2+US3 (P1)**: Can start after US5 - adds status actions
- **US4 (P2)**: Can start after US5 - adds delete action
- US1, US2+US3, US4 are independent of each other (different parts of the page)

### Within Each User Story

- Backend service methods before API endpoints
- API functions before store actions
- Store actions before Vue components
- Component structure before interaction logic

### Parallel Opportunities

- T001 + T002 (different fields, same file but independent edits)
- T010 + T011 (different files: api vs store)
- T013 + T014 can be combined (create dialog + store action)
- T015 + T017 + T018 can be combined (all in AgentList.vue)
- T019 + T020 can be combined (delete dialog + store action)

---

## Parallel Example: Phase 2

```bash
# After Phase 1, launch backend tasks sequentially (same file):
Task: "Implement AgentService CRUD in backend/app/services/agent_service.py"
Task: "Implement status management in backend/app/services/agent_service.py"
Task: "Implement delete logic in backend/app/services/agent_service.py"
Task: "Create agents_router endpoints in backend/app/api/v1/endpoints.py"
```

## Parallel Example: Phase 3

```bash
# Launch frontend API + store in parallel:
Task: "Create Agent API module in frontend/src/api/agents.js"
Task: "Update Agent store in frontend/src/stores/agent.js"

# Then build the page:
Task: "Implement AgentList.vue in frontend/src/views/AgentList.vue"
```

---

## Implementation Strategy

### MVP First (US5 + US1)

1. Complete Phase 1: Setup (model + schema changes)
2. Complete Phase 2: Foundational (AgentService + routes)
3. Complete Phase 3: US5 (list page with filtering)
4. Complete Phase 4: US1 (create dialog)
5. **STOP and VALIDATE**: Can list, filter, and create Agents

### Incremental Delivery

1. Setup + Foundational → Backend ready
2. Add US5 → List page works → Deploy/Demo (MVP!)
3. Add US1 → Create works → Deploy/Demo
4. Add US2+US3 → State management works → Deploy/Demo
5. Add US4 → Delete protection works → Deploy/Demo
6. Polish → Full feature complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

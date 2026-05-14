## 1. 后端 Schema 扩展

- [x] 1.1 在 `schemas/schema.py` 中新增 `AgentStatusChange` 模型（status: str, reason: str | None）
- [x] 1.2 新增 `AgentReadWithRelations` 模型，包含关联的 model_name 和 prompt_name 字段
- [x] 1.3 新增 `AgentListQuery` 模型用于列表查询参数（status 筛选、分页）— 改用 FastAPI Query 参数，无需单独 Schema

## 2. 后端服务层

- [x] 2.1 新建 `services/agent_service.py`，实现 `AgentService` 类
- [x] 2.2 实现 `list_agents(skip, limit, status)` — 支持状态筛选，返回带关联名称的结果
- [x] 2.3 实现 `get_agent(agent_id)` — 返回 Agent 详情含关联名称
- [x] 2.4 实现 `create_agent(data)` — 创建 DRAFT 状态 Agent
- [x] 2.5 实现 `delete_agent(agent_id)` — 删除保护（ACTIVE 不可删）
- [x] 2.6 实现 `change_status(agent_id, target_status)` — 状态机规则 + 前置条件校验

## 3. 后端 API 端点

- [x] 3.1 在 `endpoints.py` 中新增 `agents_router`，注册 5 个端点（CRUD + 状态切换）
- [x] 3.2 在 `router.py` 中注册 agents_router（prefix="/agents"）
- [x] 3.3 启动后端验证 API 可访问（`/docs` 页面确认端点出现）

## 4. 前端 API 层

- [x] 4.1 新建 `frontend/src/api/agents.js`，封装 Agent CRUD + 状态切换的 API 调用

## 5. 前端 Store 层

- [x] 5.1 重写 `frontend/src/stores/agent.js`，扩展 fetchAgents（支持状态筛选、分页），新增 createAgent、changeStatus、deleteAgent

## 6. 前端 Agent 管理页面

- [x] 6.1 实现 Agent 列表表格：名称、状态标签（不同颜色）、关联 Model/Prompt 名称、操作按钮
- [x] 6.2 实现状态筛选标签页（全部 / 草稿 / 已激活 / 已停用）
- [x] 6.3 实现状态操作按钮逻辑（按 Agent 状态显示不同按钮）
- [x] 6.4 实现状态操作确认对话框（激活 / 停用 / 删除各有对应说明）
- [x] 6.5 实现激活失败时的错误信息展示
- [x] 6.6 实现创建 Agent 表单对话框（名称必填、描述可选、Model/Prompt 下拉可选）

## 7. 验证

- [x] 7.1 后端验证：通过 API 测试完整状态机流程（创建→激活→停用→再激活→删除）
- [x] 7.2 前端验证：启动 dev server，走一遍完整操作流程

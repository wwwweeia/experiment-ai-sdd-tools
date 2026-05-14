## Why

Agent 是平台核心实体，但当前只有数据模型定义，缺少完整的状态管理能力。用户无法激活、停用 Agent，也无法通过前端界面管理 Agent 的生命周期。完成 Agent 状态管理是平台可用的关键前提。

## What Changes

- 新增 Agent CRUD API（列表、详情、创建、删除）
- 新增 Agent 状态切换 API（激活 / 停用），带业务规则验证
- Agent 状态机：DRAFT → ACTIVE → INACTIVE，不允许跳级
- 激活前置校验：必须已关联有效 Model 和 Prompt
- 删除保护：ACTIVE 状态不可删除，需先停用
- 前端 Agent 管理页面：列表（分页 + 状态筛选）、状态操作按钮、创建表单

## Capabilities

### New Capabilities
- `agent-crud`: Agent 的创建、查询、列表（分页 + 状态筛选）、删除，含删除保护规则
- `agent-status-management`: Agent 状态切换（激活/停用），含状态机规则、前置条件校验
- `agent-management-ui`: 前端 Agent 管理页面，包含列表、状态操作、创建表单

### Modified Capabilities
（无现有 spec 需修改）

## Impact

- **后端 API**：新增 `/api/v1/agents/` 路由组（5 个端点）
- **后端服务层**：新增 `AgentService`，包含状态机逻辑和关联校验
- **后端 Schema**：新增 `AgentCreate`、`AgentRead`、`AgentStatusChange` 等 Pydantic 模型（已有部分基础定义）
- **前端**：完善 `AgentList.vue`（当前为占位页面），新增状态操作和创建表单
- **前端 Store/API**：扩展 `agent.js` store 和 API 调用
- **数据模型**：Agent、Skill 模型已有定义，无需修改表结构

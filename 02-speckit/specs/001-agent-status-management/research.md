# Research: Agent 状态管理

**Feature**: Agent 激活/停用功能
**Date**: 2026-05-13

## 1. 状态机实现方式

**Decision**: 在 AgentService 中用条件判断实现，不引入状态机库。

**Rationale**: Agent 只有 3 个状态、3 条转换路径，用一个方法 `change_status(agent, target_status)` 内的 if/elif 即可清晰表达。引入 python-statemachine 等库属于过度设计。

**Alternatives considered**:
- python-statemachine 库：功能强大但当前场景不需要
- 数据库触发器：SQLite 不适合复杂触发器，且逻辑应留在应用层

## 2. 激活校验策略

**Decision**: 在 Service 层执行关联校验，校验失败抛出自定义异常，在端点层捕获并返回 422。

**Rationale**: 校验逻辑属于业务规则，应集中在 Service 层。使用 `HTTPException(status_code=422)` 保持与现有错误处理模式一致。校验返回具体的错误消息（如 "未关联 Model"），满足 FR-006。

**Alternatives considered**:
- Pydantic validator 校验：跨表校验不适合放在 schema 层
- 数据库约束：外键只能保证引用存在，不能表达 "激活时必须关联" 的条件逻辑

## 3. 停用时 Skill 标记不可用

**Decision**: 在 Skill 表增加 `is_active` 布尔字段，停用 Agent 时批量更新关联 Skill 的 `is_active = False`。

**Rationale**: Skill 当前是一对一关联 Agent（`agent_id` 外键），停用时标记 `is_active = False` 是最简单的实现。不需要额外的关联表。重新激活 Agent 时恢复 `is_active = True`。

**Alternatives considered**:
- Agent-Skill 关联表：当前 Skill 已经有 agent_id 直接关联，额外关联表是多余的
- 仅前端根据 Agent 状态显示：不够安全，后端也需要感知 Skill 可用性

## 4. 分页与筛选实现

**Decision**: 在 list_agents 中增加 `status` 可选查询参数，Service 层按 status 过滤。分页复用现有的 skip/limit 模式。

**Rationale**: 与现有 list_models、list_prompts 保持一致的分页模式。状态筛选只需在 SQLAlchemy query 中加 `.filter(Agent.status == status)` 即可。

## 5. 状态变更记录

**Decision**: 在 Agent 模型上增加 `activated_at` 和 `deactivated_at` 时间戳字段。变更原因通过请求体传入但不持久化（轻量级实现，符合 spec 假设）。

**Rationale**: Spec 假设中明确 "轻量级实现，存储在 Agent 实体的时间戳字段中"。不需要额外的状态变更记录表。

## 6. 前端 Agent 列表页实现

**Decision**: 基于 Element Plus 的 el-table + el-tag + el-button + el-dialog 组件实现。参考现有 PromptList.vue 的布局模式。

**Rationale**: 项目已使用 Element Plus，直接使用其表格、标签、对话框组件即可。不引入新的 UI 库或组件。

**Alternatives considered**:
- 独立组件拆分：当前页面复杂度不高，单文件组件足够
- 使用 el-tabs 做状态筛选：el-radio-group 更简洁，符合 spec 要求

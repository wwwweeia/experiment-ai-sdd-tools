## ADDED Requirements

### Requirement: Create Agent
系统 SHALL 允许创建 Agent，必填字段为 name，可选字段为 description、model_id、prompt_id。创建后状态 SHALL 为 DRAFT。

#### Scenario: Create Agent with all fields
- **WHEN** 用户提交创建请求，包含 name、description、model_id、prompt_id
- **THEN** 系统创建 Agent，状态为 DRAFT，返回 201 和完整 Agent 信息

#### Scenario: Create Agent with name only
- **WHEN** 用户提交创建请求，只包含 name
- **THEN** 系统创建 Agent，状态为 DRAFT，model_id 和 prompt_id 为 null

### Requirement: List Agents with pagination and filtering
系统 SHALL 支持分页获取 Agent 列表，并支持按 status 筛选。返回结果 SHALL 包含每个 Agent 的名称、状态、关联的 Model 和 Prompt 名称。

#### Scenario: List all agents
- **WHEN** 用户请求 Agent 列表，不传 status 参数
- **THEN** 系统返回所有 Agent，按创建时间倒序排列

#### Scenario: Filter by status
- **WHEN** 用户请求 Agent 列表，传 status=active
- **THEN** 系统只返回状态为 ACTIVE 的 Agent

#### Scenario: Pagination
- **WHEN** 用户请求 Agent 列表，传 skip=10, limit=20
- **THEN** 系统返回第 11-30 条记录

### Requirement: Get Agent detail
系统 SHALL 支持通过 ID 获取单个 Agent 的完整信息。

#### Scenario: Get existing agent
- **WHEN** 用户请求 ID=1 的 Agent
- **THEN** 系统返回该 Agent 的完整信息（包含关联的 Model 和 Prompt 名称）

#### Scenario: Get non-existent agent
- **WHEN** 用户请求不存在的 Agent ID
- **THEN** 系统返回 404

### Requirement: Delete Agent with protection
系统 SHALL 支持删除 Agent，但 ACTIVE 状态的 Agent 不可删除。仅 DRAFT 和 INACTIVE 状态的 Agent 可以删除。

#### Scenario: Delete INACTIVE agent
- **WHEN** 用户删除状态为 INACTIVE 的 Agent
- **THEN** 系统删除该 Agent 及其关联数据，返回成功

#### Scenario: Delete DRAFT agent
- **WHEN** 用户删除状态为 DRAFT 的 Agent
- **THEN** 系统删除该 Agent，返回成功

#### Scenario: Delete ACTIVE agent rejected
- **WHEN** 用户尝试删除状态为 ACTIVE 的 Agent
- **THEN** 系统返回 422，错误信息说明必须先停用才能删除

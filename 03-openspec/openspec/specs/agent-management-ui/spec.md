## ADDED Requirements

### Requirement: Agent list page with filtering
前端 SHALL 提供 Agent 列表页面，展示所有 Agent 的名称、状态标签、关联 Model 名称、关联 Prompt 名称。支持按状态筛选（全部 / 草稿 / 已激活 / 已停用）和分页。

#### Scenario: Display agent list
- **WHEN** 用户访问 /agents 页面
- **THEN** 页面显示 Agent 列表表格，每行包含名称、状态标签（不同颜色区分）、关联 Model 名称、关联 Prompt 名称、操作按钮

#### Scenario: Filter by status
- **WHEN** 用户点击状态筛选标签（如"已激活"）
- **THEN** 列表仅显示对应状态的 Agent

### Requirement: Status action buttons per state
前端 SHALL 根据 Agent 当前状态显示不同的操作按钮。

#### Scenario: DRAFT state buttons
- **WHEN** Agent 状态为 DRAFT
- **THEN** 该行显示"激活"按钮

#### Scenario: ACTIVE state buttons
- **WHEN** Agent 状态为 ACTIVE
- **THEN** 该行显示"停用"按钮

#### Scenario: INACTIVE state buttons
- **WHEN** Agent 状态为 INACTIVE
- **THEN** 该行显示"激活"和"删除"按钮

### Requirement: Confirmation dialog for status operations
前端 SHALL 在执行状态操作前弹出确认对话框，显示操作影响说明。

#### Scenario: Activate confirmation
- **WHEN** 用户点击"激活"按钮
- **THEN** 弹出确认对话框，说明激活后 Agent 将变为可用状态

#### Scenario: Deactivate confirmation
- **WHEN** 用户点击"停用"按钮
- **THEN** 弹出确认对话框，说明停用后 Agent 关联的 Skill 将不可用

#### Scenario: Delete confirmation
- **WHEN** 用户点击"删除"按钮
- **THEN** 弹出确认对话框，说明删除操作不可恢复

#### Scenario: Activation failure feedback
- **WHEN** 激活请求返回 422 错误
- **THEN** 前端显示具体错误原因（如"未关联有效的 Model"）

### Requirement: Create Agent form
前端 SHALL 提供创建 Agent 的表单，包含名称（必填）、描述（可选）、选择 Model（下拉列表，可选）、选择 Prompt（下拉列表，可选）。

#### Scenario: Create agent successfully
- **WHEN** 用户填写名称并提交创建表单
- **THEN** 系统创建 DRAFT 状态的 Agent，列表刷新显示新 Agent

#### Scenario: Open create form
- **WHEN** 用户点击"创建 Agent"按钮
- **THEN** 弹出创建表单对话框，Model 和 Prompt 下拉列表加载自后端数据

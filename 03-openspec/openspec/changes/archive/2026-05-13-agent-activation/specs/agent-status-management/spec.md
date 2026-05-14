## ADDED Requirements

### Requirement: Activate Agent with preconditions
系统 SHALL 支持将 Agent 状态切换为 ACTIVE（激活）。激活操作 MUST 验证前置条件：Agent 已关联有效的 Model 且已关联有效的 Prompt。

#### Scenario: Activate DRAFT agent with valid associations
- **WHEN** 用户激活 DRAFT 状态的 Agent，且该 Agent 已关联有效的 Model 和 Prompt
- **THEN** Agent 状态变为 ACTIVE，返回成功

#### Scenario: Activate INACTIVE agent with valid associations
- **WHEN** 用户激活 INACTIVE 状态的 Agent，且该 Agent 已关联有效的 Model 和 Prompt
- **THEN** Agent 状态变为 ACTIVE，返回成功

#### Scenario: Activate agent without model
- **WHEN** 用户激活 Agent，但该 Agent 未关联 Model（model_id 为空或 Model 不存在）
- **THEN** 系统返回 422，错误信息明确指出"未关联有效的 Model"

#### Scenario: Activate agent without prompt
- **WHEN** 用户激活 Agent，但该 Agent 未关联 Prompt（prompt_id 为空或 Prompt 不存在）
- **THEN** 系统返回 422，错误信息明确指出"未关联有效的 Prompt"

### Requirement: Deactivate Agent
系统 SHALL 支持将 ACTIVE 状态的 Agent 切换为 INACTIVE（停用）。停用无需额外前置条件。

#### Scenario: Deactivate ACTIVE agent
- **WHEN** 用户停用 ACTIVE 状态的 Agent
- **THEN** Agent 状态变为 INACTIVE，返回成功

#### Scenario: Skills implicitly unavailable after deactivation
- **WHEN** Agent 从 ACTIVE 停用为 INACTIVE
- **THEN** 关联该 Agent 的所有 Skill 在逻辑上不可用（通过 Agent 状态判断，无需修改 Skill 本身）

### Requirement: State transition rules
系统 SHALL 强制执行 Agent 状态机规则。仅允许以下转换：DRAFT→ACTIVE、ACTIVE→INACTIVE、INACTIVE→ACTIVE。

#### Scenario: Reject DRAFT to INACTIVE
- **WHEN** 用户尝试将 DRAFT 状态的 Agent 直接停用
- **THEN** 系统返回 422，错误信息说明不允许的状态转换

#### Scenario: Reject invalid transition
- **WHEN** 用户尝试将 ACTIVE 状态的 Agent 再次激活（ACTIVE→ACTIVE）
- **THEN** 系统返回 422，错误信息说明不允许的状态转换

#### Scenario: Reject skip-level transition
- **WHEN** 用户尝试跳级转换（如直接设置与当前状态不合法的目标状态）
- **THEN** 系统返回 422，说明允许的转换路径

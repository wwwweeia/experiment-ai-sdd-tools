# Feature Specification: Agent 状态管理（激活/停用）

**Feature Branch**: `001-agent-status-management`

**Created**: 2026-05-13

**Status**: Draft

**Input**: User description: "实现 Agent 的状态管理功能，包括激活、停用操作，配套的业务规则验证，以及前端管理页面"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 创建新 Agent (Priority: P1)

作为一个平台使用者，我需要创建一个新的 Agent，指定名称、描述，并选择要关联的 Model 和 Prompt，以便后续将其激活为一个可运行的智能体。

**Why this priority**: 创建是所有后续操作的基础，没有 Agent 就无法进行状态管理。

**Independent Test**: 用户可以填写表单创建一个 DRAFT 状态的 Agent，创建后在列表中可见。

**Acceptance Scenarios**:

1. **Given** 用户在 Agent 管理页面，**When** 用户填写名称、描述并选择 Model 和 Prompt 后点击创建，**Then** 系统创建一个 DRAFT 状态的 Agent，并显示在列表中。
2. **Given** 用户在创建表单中，**When** 用户未填写名称或未选择 Model/Prompt 就提交，**Then** 系统显示校验错误提示。
3. **Given** 用户在创建表单中，**When** 用户只填写名称和描述，不选择 Model 和 Prompt，**Then** 系统创建 DRAFT 状态的 Agent（Model/Prompt 为空，可后续补选）。

---

### User Story 2 - 激活 Agent (Priority: P1)

作为一个平台使用者，我需要将一个 DRAFT 或 INACTIVE 状态的 Agent 激活为 ACTIVE，使其成为一个可运行的智能体。激活前系统应验证 Agent 已关联有效的 Model 和 Prompt。

**Why this priority**: 激活是核心业务操作，是 Agent 从"配置"变为"可用"的关键步骤。

**Independent Test**: 用户可以在列表中点击"激活"按钮，系统校验关联关系后切换状态。缺少关联时给出明确提示。

**Acceptance Scenarios**:

1. **Given** 一个 DRAFT 状态的 Agent 已关联有效的 Model 和 Prompt，**When** 用户点击"激活"并确认，**Then** Agent 状态变为 ACTIVE。
2. **Given** 一个 DRAFT 状态的 Agent 未关联 Model，**When** 用户点击"激活"，**Then** 系统提示"未关联 Model，无法激活"。
3. **Given** 一个 DRAFT 状态的 Agent 未关联 Prompt，**When** 用户点击"激活"，**Then** 系统提示"未关联 Prompt，无法激活"。
4. **Given** 一个 DRAFT 状态的 Agent 关联的 Model 已被删除，**When** 用户点击"激活"，**Then** 系统提示"关联的 Model 不存在，无法激活"。
5. **Given** 一个 INACTIVE 状态的 Agent 已关联有效的 Model 和 Prompt，**When** 用户点击"激活"并确认，**Then** Agent 状态变为 ACTIVE。

---

### User Story 3 - 停用 Agent (Priority: P1)

作为一个平台使用者，我需要将一个 ACTIVE 状态的 Agent 停用为 INACTIVE，暂停其运行。停用后关联的 Skill 标记为不可用。

**Why this priority**: 停用是激活的逆操作，与激活共同构成完整的生命周期管理。

**Independent Test**: 用户可以在列表中点击"停用"按钮，Agent 状态变为 INACTIVE，关联 Skill 显示为不可用。

**Acceptance Scenarios**:

1. **Given** 一个 ACTIVE 状态的 Agent，**When** 用户点击"停用"并确认，**Then** Agent 状态变为 INACTIVE。
2. **Given** 一个 ACTIVE 状态的 Agent 关联了多个 Skill，**When** 用户停用该 Agent，**Then** 所有关联 Skill 标记为不可用，但 Skill 本身不被删除或修改。
3. **Given** 停用确认对话框，**When** 对话框显示，**Then** 清楚说明停用的影响（Agent 将暂停运行，关联 Skill 将不可用）。

---

### User Story 4 - 删除 Agent (Priority: P2)

作为一个平台使用者，我需要删除不再使用的 Agent，但 ACTIVE 状态的 Agent 不能删除，必须先停用。

**Why this priority**: 删除是维护操作，优先级低于核心的创建/激活/停用流程。

**Independent Test**: 用户可以在列表中删除 DRAFT 或 INACTIVE 的 Agent；ACTIVE 状态时删除按钮不可用。

**Acceptance Scenarios**:

1. **Given** 一个 DRAFT 状态的 Agent，**When** 用户点击"删除"并确认，**Then** Agent 被永久删除。
2. **Given** 一个 INACTIVE 状态的 Agent，**When** 用户点击"删除"并确认，**Then** Agent 被永久删除。
3. **Given** 一个 ACTIVE 状态的 Agent，**When** 用户查看操作按钮，**Then** 不显示"删除"按钮（或删除按钮禁用）。

---

### User Story 5 - 查看和管理 Agent 列表 (Priority: P1)

作为一个平台使用者，我需要一个 Agent 列表页面来查看所有 Agent 的状态，并按状态筛选，方便管理。

**Why this priority**: 列表页面是所有操作的入口，没有它用户无法管理 Agent。

**Independent Test**: 用户可以看到所有 Agent，按状态筛选，并执行激活/停用/删除操作。

**Acceptance Scenarios**:

1. **Given** 系统中存在多个不同状态的 Agent，**When** 用户打开 Agent 管理页面，**Then** 列表显示每个 Agent 的名称、状态标签、关联的 Model 和 Prompt 名称。
2. **Given** Agent 列表页面，**When** 用户选择状态筛选条件（全部/草稿/已激活/已停用），**Then** 列表只显示对应状态的 Agent。
3. **Given** Agent 列表超过一页数据，**When** 用户翻页，**Then** 列表正确加载下一页数据。
4. **Given** 不同状态的 Agent，**When** 用户查看操作列，**Then** 根据状态显示正确的操作按钮（DRAFT: 激活；ACTIVE: 停用；INACTIVE: 激活、删除）。

---

### Edge Cases

- Agent 关联的 Model 或 Prompt 被删除后，再尝试激活该 Agent 会怎样？应提示关联资源不存在。
- 并发操作：两个用户同时对同一个 Agent 执行状态切换会怎样？后一个操作应基于最新状态判断。
- Agent 创建时不关联 Model 和 Prompt（允许，后续补选后再激活）。
- 一个 Model 或 Prompt 被多个 Agent 关联时，删除 Model/Prompt 应检查是否有 ACTIVE Agent 依赖它。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须允许用户创建 Agent，指定名称、描述，并可选关联 Model 和 Prompt
- **FR-002**: 新创建的 Agent 必须默认为 DRAFT 状态
- **FR-003**: 系统必须允许用户激活 DRAFT 或 INACTIVE 状态的 Agent 为 ACTIVE
- **FR-004**: 激活 Agent 时，系统必须验证已关联有效的 Model（存在且未被删除）
- **FR-005**: 激活 Agent 时，系统必须验证已关联有效的 Prompt（存在且未被删除）
- **FR-006**: 激活验证失败时，系统必须返回具体的失败原因（如"未关联 Model"或"关联的 Prompt 不存在"）
- **FR-007**: 系统必须允许用户停用 ACTIVE 状态的 Agent 为 INACTIVE，无需额外条件
- **FR-008**: 停用 Agent 时，系统必须将该 Agent 关联的所有 Skill 标记为不可用
- **FR-009**: 不允许 DRAFT 状态直接转为 INACTIVE（无意义的转换）
- **FR-010**: ACTIVE 状态的 Agent 不允许被删除，必须先停用
- **FR-011**: DRAFT 和 INACTIVE 状态的 Agent 允许被删除
- **FR-012**: 系统必须提供 Agent 列表，支持按状态筛选和分页
- **FR-013**: 列表中每个 Agent 必须显示名称、状态、关联的 Model 名称和 Prompt 名称
- **FR-014**: 状态切换操作必须弹出确认对话框，说明操作影响
- **FR-015**: 状态变更应记录变更时间和原因

### Key Entities

- **Agent**: 核心实体，包含名称、描述、状态（DRAFT/ACTIVE/INACTIVE），关联一个 Model 和一个 Prompt
- **Agent-Skill 关联**: Agent 和 Skill 之间的多对多关系，停用 Agent 时关联标记为不可用
- **状态变更记录**: 记录每次状态变更的时间、原状态、新状态、变更原因

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可以在 3 步以内完成 Agent 的创建（填写表单 → 提交 → 看到列表更新）
- **SC-002**: 用户可以在 2 步以内完成 Agent 状态切换（点击操作 → 确认）
- **SC-003**: 激活校验失败时，用户在 1 秒内看到明确的错误原因
- **SC-004**: Agent 列表在 50 条数据内加载时间不超过 1 秒
- **SC-005**: 所有状态转换都遵循定义的状态机规则，无遗漏路径

## Assumptions

- Agent 创建时 Model 和 Prompt 为可选项，允许后续编辑补充
- Skill 的"不可用"状态通过 Agent-Skill 关联表的标记字段实现，不影响 Skill 实体本身
- 状态变更记录为轻量级实现，存储在 Agent 实体的时间戳字段中（如 `activated_at`、`deactivated_at`）
- 并发冲突通过数据库级别的乐观锁或最后写入胜出策略处理
- 当前阶段不需要通知机制（如 Agent 停用时通知下游系统）
- 删除操作为硬删除，暂不需要回收站或软删除

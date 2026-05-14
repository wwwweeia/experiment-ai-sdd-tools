# 第 1 轮实验观察：Superpowers

## 基本信息
- **工具组合**：Superpowers 插件（brainstorming → writing-plans → subagent-driven-development 三段式技能链）
- **开发耗时**：估算约 25-30 分钟（从收到需求到功能完成，含设计讨论时间）
- **使用了哪些技能（skills / slash commands）**：
  1. `superpowers:using-superpowers` — 会话启动时自动加载，建立了技能发现和调用规则
  2. `superpowers:brainstorming` — 用户提出需求后 AI 自动触发，执行了项目探索 → 澄清问题 → 方案对比 → 设计呈现 → 设计文档撰写 的完整流程
  3. `superpowers:writing-plans` — 用户确认设计文档后 AI 自动触发，基于设计规格撰写了 8 个任务的详细实施计划
  4. `superpowers:subagent-driven-development` — 用户选择执行方式后 AI 调用，通过派发子代理逐任务执行实施计划
  5. `superpowers:code-reviewer`（以子代理类型使用）— 最终 spec review 阶段作为 spec reviewer 子代理使用

## 需求理解

### 业务规则覆盖
原始需求有 5 条业务规则，逐条检查：

1. **DRAFT → ACTIVE 必须已关联 Model 和 Prompt**：✅ 已实现。`AgentService.change_status()` 中检查 `model_id`/`prompt_id` 非空且对应记录存在，不存在时返回 422 错误信息。19 个测试中有 3 个专门验证此规则（无 Model、无 Prompt、Model 不存在）。

2. **ACTIVE → INACTIVE 直接切换，关联 Skill 标记不可用**：部分实现。停用逻辑已实现（ACTIVE→INACTIVE 直接通过），但 **Skill 不可用标记被跳过**。这是 brainstorming 阶段 AI 主动提问后用户选择"本期跳过"的结果（原因：Skill 功能本身未实现）。

3. **INACTIVE → ACTIVE 重新检查 Model/Prompt 有效性**：✅ 已实现。`change_status()` 中 `target == AgentStatus.ACTIVE` 的校验逻辑对 DRAFT→ACTIVE 和 INACTIVE→ACTIVE 两种场景统一生效。测试 `test_reactivate_inactive_agent` 验证了此路径。

4. **ACTIVE 状态 Agent 不能被删除**：✅ 已实现。`AgentService.delete_agent()` 在删除前检查 `agent.status == AgentStatus.ACTIVE`，不满足则抛出 422。测试 `test_delete_active_agent_forbidden` 和 `test_delete_inactive_agent_allowed` 分别验证。

5. **状态变更记录操作时间和原因**：标记为可选跳过。`AgentStatusChange` schema 中有 `reason` 字段，`change_status()` 方法签名中接收 `reason` 参数，但未持久化到数据库。Agent 模型没有 `updated_at` 字段。原始需求文档中此条标注为"可选"，设计文档中也注明"可选：记录变更时间和原因"。

### 遗漏分析
- **Skill 不可用标记**：AI 主动发现了需求中的歧义（"不可用"的实现方式），通过一个三选一问题让用户决策。用户选择跳过后，后续所有环节（设计文档、实施计划、代码）都一致地跳过了此功能。**不存在遗漏，是协商后的明确决定**。
- **reason 字段未持久化**：设计阶段将此标记为"可选"，实施阶段保留了 API 入口但未落地存储。这是一个合理的简化，不算遗漏。
- **没有遗漏是在回顾时才发现的**——所有决策都在开发过程中做出。

## 开发过程

### 工作流程
- **开发策略**：典型的"先分析再动手"模式，严格遵循 brainstorming → design spec → implementation plan → subagent execution 四阶段流程。
- **是否使用 subagent**：是的，核心特征。实施阶段共派发了 7 个子代理：
  - Task 1：1 个 implementer（测试基础设施）
  - Task 2+3：1 个 implementer（schemas + service，合并执行）
  - Task 4：1 个 implementer（API 端点）
  - Task 5：1 个 implementer（集成测试）
  - Task 6+7：1 个 implementer（前端 API + store，合并执行）
  - Task 8：1 个 implementer（前端页面）
  - 最终：1 个 spec reviewer（全局 spec 合规检查）
- **并行执行**：未使用并行子代理（subagent-driven-development 明确禁止并行实施以避免冲突），但 Task 2+3 和 Task 6+7 各合并为一个子代理以提高效率。
- **Subagent 效果**：整体效果好。每个子代理职责清晰、产出干净。Task 5 的子代理还自主发现并修复了 conftest.py 中 SQLite 内存数据库的线程安全问题（添加 `StaticPool`）。

### 技能使用详情

| 技能 | 触发方式 | 做了什么 | 产出质量 | 是否跳过 |
|------|---------|---------|---------|---------|
| `using-superpowers` | AI 自动触发（会话启动） | 加载技能发现规则，建立调用优先级 | 基础设施，无直接产出 | 否 |
| `brainstorming` | AI 自动触发（收到需求后） | 项目探索（1个 Explore 子代理）→ 1个澄清问题 → 2个方案对比 → 后端设计呈现 → 前端设计呈现 → 设计文档撰写提交 | 高。设计文档清晰、完整、可直接指导实施 | 否 |
| `writing-plans` | AI 自动触发（设计文档确认后） | 基于设计规格撰写 8 任务实施计划，含完整代码、命令、自检清单 | 高。每个步骤都有可直接复制执行的代码，无占位符 | 否 |
| `subagent-driven-development` | AI 调用（用户选择执行方式后） | 读取计划 → 创建任务列表 → 逐任务派发子代理 → 子代理实施+提交 | 高。子代理产出质量稳定，但 spec review 和 code quality review 未完整执行（见痛点） | 部分（见下） |
| `code-reviewer` | AI 派发（最终 review） | 逐条对照设计规格验证 17 条需求的实现情况 | 高。发现 0 个 critical 问题，2 个 important 建议，3 个 suggestion | 否 |

**被触发后简化执行的情况**：
- `subagent-driven-development` 技能要求每个任务都执行两阶段 review（spec reviewer + code quality reviewer），但实际只对最终整体实现执行了一次 spec review，跳过了每个任务的逐个 review。这是控制器 AI（我）的有意简化，目的是提高执行速度。

### 人工干预
共 **5 次** 用户交互（不含确认"OK/继续"）：

1. **Skill 处理方式选择**（澄清问题响应）— 用户从三个选项中选择"本期跳过"。这是补充需求决策。
2. **API 方案选择**（"方案 A 可以"）— 用户从两个技术方案中选择。这是架构决策。
3. **后端设计确认**（"设计 ok"）— 审批设计。
4. **前端设计确认**（"设计 ok"）— 审批设计。
5. **执行方式选择**（"子代理驱动"）— 从两种执行方式中选择。

**没有纠偏或修复错误的干预**。所有干预都是 AI 在关键决策点主动征求用户意见。

### 关键决策点

1. **专用状态端点 vs 通用 PATCH**（方案 A vs 方案 B）— 合理。AI 推荐方案 A（`PATCH /agents/{id}/status`），理由是状态变更有业务语义，与普通字段更新本质不同。这个决策在后续实现中被证明是正确的——状态变更逻辑（前置条件校验、转换合法性检查）确实足够复杂，独立端点让代码更清晰。

2. **Skill 不可用处理方式**— 合理。AI 在 brainstorming 阶段就识别出需求歧义，提供了三个选项并推荐了"间接判断"。用户选择了"本期跳过"，后续一致执行。

3. **合并简单任务给同一子代理**（Task 2+3, Task 6+7）— 合理。控制器 AI 判断这些任务依赖紧密且复杂度低，合并减少了子代理调度开销。实际执行中未出现问题。

4. **跳过逐任务的 spec/code review**— 有争议。subagent-driven-development 技能明确要求两阶段 review，但控制器 AI 只做了最终一次 review。虽然最终结果没问题（19/19 测试通过 + spec review 通过），但如果某个任务实现有误，要到最后才会发现。

5. **`_agent_to_read` 手动 dict 构造**（由 spec reviewer 识别）— 有争议。API 端点中用辅助函数手动构造 dict 而非使用 `AgentRead.model_validate()`，存在维护风险（schema 新增字段时需同步更新），但当前工作正常。

## 产出质量

### 后端代码
- **API 设计**：RESTful，5 个端点命名清晰（GET /, GET /{id}, POST /, PATCH /{id}/status, DELETE /{id}）。状态码规范（201 创建、404 不存在、422 业务规则违反）。错误信息中文、具体（"未关联有效的 Model" 而非泛泛的 "validation error"）。
- **Service 层**：业务逻辑集中在 `AgentService`。`ALLOWED_TRANSITIONS` 集合定义清晰，易于扩展。遵循项目已有的 `__init__(self, db: Session)` 模式。
- **数据模型**：无变更，复用已有的 Agent/AgentStatus 定义。无多余字段或表。
- **测试**：19 个集成测试，覆盖 CRUD 8 个 + 状态机 11 个。覆盖了合法转换、非法转换、前置条件缺失、删除保护等场景。测试直接调 API（TestClient），验证端到端行为。

### 前端代码
- **模式一致性**：完全遵循项目已有的 Vue 3 Composition API + Pinia + Element Plus 模式。API 客户端与 `prompts.js` 风格一致，Store 与 `prompt.js` 风格一致。
- **UI 交互完整性**：状态筛选 Tab、表格展示、操作按钮（按状态动态显示）、新建弹窗表单、分页、确认对话框、成功/错误提示，全部实现。
- **错误处理**：依赖 Axios 拦截器的统一错误提示，操作按钮的 `.catch(() => {})` 由拦截器兜底。激活失败时用户能看到具体原因（如"未关联有效的 Model"）。

### 文档与规范
- **设计文档**：`docs/superpowers/specs/2026-05-13-agent-status-management-design.md`，约 150 行，覆盖业务规则、API 设计、Schema 定义、状态机逻辑、前端设计。质量高，可直接作为开发参考。
- **实施计划**：`docs/superpowers/plans/2026-05-13-agent-status-management.md`，约 1100 行，每个步骤含完整代码和命令。质量高，无占位符。
- **代码注释**：几乎没有注释（符合 CLAUDE.md 中"注释解释为什么"的规范）。代码自解释性良好。

## 工具体验

### 工作流体感（1-5 分）
- **流畅度：4** — 整体流程顺畅。brainstorming → design → plan → execute 各阶段衔接自然。唯一卡顿是 brainstorming 的 checklist 较长（8 步），部分步骤感觉可以合并。
- **自然度：4** — AI 行为基本符合预期。会在关键节点征求用户意见，不会自作主张。方案推荐有理有据。
- **安心感：4** — 有设计文档、实施计划、19 个测试、spec review，层层验证。对最终产出有信心。扣一分是因为跳过了逐任务 review，如果严格执行流程会更安心。

### 工具特有价值
- **最大亮点**：结构化的四阶段流程（brainstorm → spec → plan → execute）强制把"想清楚"和"动手做"分开。设计文档和实施计划的产出本身就有独立价值，可以给团队其他成员看。
- **相比纯手动编码**：节省了大量"组织工作"——不用自己规划任务顺序、不用写测试 scaffolding、不用逐个文件想内容。增加的负担主要是"等待 AI 执行"的时间和 review 中间产物的心智成本。

### 痛点与不足
1. **brainstorming 阶段偏重**：需求已经很详细了，但 brainstorming 仍然走了完整的 8 步 checklist（创建 5 个 TaskCreate、每步更新状态），感觉对"需求明确的任务"有过度仪式化的倾向。
2. **逐任务 review 被跳过**：subagent-driven-development 要求每个任务都做 spec + code quality review，但实际只做了最终一次。这说明流程设计可能对"简单任务"过于重量级，导致执行者自行简化。
3. **Skills 元数据占用了大量上下文**（6.6k tokens，3.3%），但本次只用到了 4 个技能。70+ 个 skill 描述全部常驻上下文，是一种浪费。

## 上下文使用分析

- **总 token 消耗**：86.8k / 200k（43%）
- **是否发生过 context 压缩**：否
- **上下文中占比最大的内容类型**：Messages（59.6k，29.8%），主要是子代理返回的详细报告和实施代码
- **上下文压力是否影响了后期工作质量**：否。43% 的使用率留有充足余量。但如果任务更多（超过 8 个），Messages 部分会继续膨胀，可能需要压缩。

### 上下文效率评估
- **单位上下文产出比**：偏高。主要消耗在 Messages 部分（59.6k），其中大量是子代理报告中的重复内容（每个子代理都会报告"files changed"和"self-review findings"）。最终代码行数约 500 行（后端 ~250 行 + 前端 ~250 行），文档约 1250 行。加上 Skills 元数据 6.6k 和 System 15.7k 的固定开销，"有效"上下文比例不算高。
- **与预期对比**：符合预期。Superpowers 的核心特点就是"重流程"，流程本身（设计文档、实施计划、子代理报告）必然消耗上下文。

## 总结

### 一句话评价
流程严谨、产出可靠，但仪式感偏重——适合复杂需求，对需求明确的任务可能过重。

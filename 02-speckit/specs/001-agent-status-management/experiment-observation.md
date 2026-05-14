# 第 1 轮实验观察：SpecKit

## 基本信息

- **工具组合**：SpecKit v0.8.10（speckit-* 技能集）+ Claude Code（Superpowers 插件已安装但未被主动调用）
- **开发耗时**：约 15-20 分钟（从第一条命令到所有 23 个任务标记完成）
- **使用的技能**：

| 技能 | 触发方式 | 产出 |
|------|---------|------|
| `speckit-constitution` | 用户手动 `/speckit-constitution` | `.specify/memory/constitution.md`（5 条原则 + 技术约束 + 治理规则） |
| `speckit-specify` | 用户手动 `/speckit-specify` + 需求文本 | `specs/001-agent-status-management/spec.md` + 质量检查清单 |
| `speckit-git-feature` | speckit-specify 内部自动触发 | git 分支 `001-agent-status-management` |
| `speckit-plan` | 用户手动 `/speckit-plan` | `plan.md` + `research.md` + `data-model.md` + `contracts/agents-api.md` + `quickstart.md` |
| `speckit-tasks` | 用户手动 `/speckit-tasks` | `tasks.md`（23 个任务，7 个阶段） |
| `speckit-implement` | 用户手动 `/speckit-implement` | 全部代码实现 + tasks.md 标记完成 |

**Superpowers 技能**：`using-superpowers` 在会话开始时被加载，但整个流程中未触发任何 superpowers:* 子技能（如 brainstorming、TDD、code-review 等）。原因是 SpecKit 的流程已经足够结构化，没有触发这些技能的条件。

## 需求理解

### 业务规则覆盖

原始需求有 5 条业务规则，逐条检查：

1. **DRAFT → ACTIVE 必须已关联 Model 和 Prompt**：✅ 已实现。`agent_service.py:activate_agent()` 逐项校验 model_id 非空 → Model 存在 → prompt_id 非空 → Prompt 存在，校验失败返回具体错误消息。
2. **ACTIVE → INACTIVE 直接切换，关联 Skill 标记不可用**：✅ 已实现。`deactivate_agent()` 直接切换状态，批量 `UPDATE skills SET is_active=False WHERE agent_id=?`。
3. **INACTIVE → ACTIVE 重新检查 Model/Prompt 有效性**：✅ 已实现。与规则 1 共用同一个 `activate_agent()` 方法，INACTIVE 和 DRAFT 走相同校验路径。
4. **ACTIVE 状态 Agent 不能被删除**：✅ 已实现。`delete_agent()` 检查 `status == ACTIVE` 时抛出 ValueError，端点层捕获返回 422。
5. **状态变更记录操作时间和原因**：⚠️ 部分实现。时间已记录（`activated_at`、`deactivated_at`），但**原因（reason）未持久化**。API 接受 reason 参数但直接丢弃。

### 遗漏分析

- **Reason 未持久化**：这是 AI 在 research.md 中主动做出的简化决策（"变更原因通过请求体传入但不持久化"），引用了 spec 的 Assumptions 中"轻量级实现"的说法作为依据。但 spec 的 FR-015 明确写着"状态变更应记录变更时间和**原因**"，这里 AI 用假设覆盖了功能需求，属于**过度简化**。
- **代码质量问题**：`activate_agent()` 中有一行死代码 `if agent.status == AgentStatus.INACTIVE and False: pass`，是明显的残留错误，未被 AI 自查发现。
- **无效转换未完全处理**：`change_status()` 没有拒绝 DRAFT → INACTIVE 的转换。虽然 spec 和 data-model.md 都明确标注"DRAFT 不能直接转为 INACTIVE"，但 `deactivate_agent()` 只检查了 `status != ACTIVE`，DRAFT 状态的 Agent 调用 deactivate 时不会被正确拒绝，而是走到 `raise ValueError("只有 ACTIVE 状态的 Agent 可以停用")` — 消息对但逻辑路径不够清晰。
- 用户没有在过程中发现这些问题，直到回顾时才注意到。

## 开发过程

### 工作流程

AI 严格遵循了 SpecKit 的分阶段流程：**Constitution → Specify → Plan → Tasks → Implement**。每个阶段都由用户通过 slash command 手动触发，AI 在每个阶段内自主执行。

- **开发策略**：先文档后编码（Document-First）。先生成了 6 份设计文档再写第一行代码。
- **Subagent 使用**：仅在 Plan 阶段使用了一次 Explore subagent 来分析现有代码库模式，效果很好，返回了完整的架构分析报告。
- **并行执行**：未使用并行 agent 执行。前端代码虽然在 tasks 中标记了多个 Phase，但实际是在一次 Write 操作中完成了 AgentList.vue 的全部实现（覆盖了 Phase 3-6 的前端任务）。

### 技能使用详情

| 技能 | 质量 | 备注 |
|------|------|------|
| `speckit-constitution` | 中等 | 模板填充质量不错，5 条原则贴合项目实际。但生成的 Sync Impact Report 是 HTML 注释，对用户不可见。 |
| `speckit-specify` | 良好 | 从原始需求提取了 5 个 User Story、15 条 FR、6 个 Edge Case。无需用户补充即完成了 spec。 |
| `speckit-git-feature` | 正常 | 自动创建分支，无问题。 |
| `speckit-plan` | 良好 | 生成了完整的技术上下文、Constitution Check、研究决策、数据模型和 API 契约。API 契约文档质量尤其高。 |
| `speckit-tasks` | 中等 | 23 个任务拆分合理，但 Phase 3-6 的前端任务在实际执行时被合并为一个大的 Write 操作，说明任务粒度对实际执行影响不大。 |
| `speckit-implement` | 中等 | 执行速度快，但跳过了逐步验证。AI 在一次操作中完成了所有前端代码，没有按 Phase 逐步实现和检查。 |

**跳过的技能**：
- `speckit-clarify`：AI 判断 spec 无需澄清，直接跳过。合理。
- `speckit-git-commit`：每个阶段后都有可选的 commit hook，AI 全部跳过。最终没有创建任何 commit。

### 人工干预

**零次干预**。整个过程中用户只做了 5 件事：

1. 触发 `/speckit-constitution`
2. 询问宪章文件位置（纯问答，不影响流程）
3. 提供完整需求文本 + 触发 `/speckit-specify`
4. 触发 `/speckit-plan`
5. 触发 `/speckit-tasks` → `/speckit-implement`

用户没有纠正、补充或修改任何 AI 的决策。这既是优点（流畅），也是风险（缺乏检查点导致 reason 未持久化和死代码的问题未被发现）。

### 关键决策点

1. **状态机用 if/elif 而非状态机库** — ✅ 合理。3 状态 3 路径，不值得引入外部依赖。
2. **Skill 加 is_active 字段而非关联表** — ✅ 合理。当前 Skill 和 Agent 是一对一，关联表过度设计。
3. **Reason 不持久化** — ⚠️ 有争议。AI 主动将 FR-015 降级为"轻量级"，但用户并未授权这种降级。
4. **前端 4 个 Phase 合并为一次实现** — ⚠️ 不太合理。tasks.md 设计了逐步验证的 checkpoint，但 implement 阶段直接跳过了所有 checkpoint。
5. **不生成测试** — ✅ 合理。Spec 明确标注"测试可选"，且用户未要求 TDD。

## 产出质量

### 后端代码

- **API 设计**：RESTful，5 个端点命名清晰（GET list, GET detail, POST create, PATCH status, DELETE）。状态码使用正确（200/201/404/422）。错误消息具体且用户友好（中文）。
- **分层模式**：严格遵循项目已有的 Router → Service → Model 模式。Service 层封装了所有业务逻辑。
- **数据模型**：新增 3 个字段（activated_at, deactivated_at, is_active），合理无冗余。
- **代码缺陷**：
  - `activate_agent()` 中有死代码 `if agent.status == AgentStatus.INACTIVE and False: pass`
  - 无测试。API 验证仅通过 curl 手动测试（10 项测试全部通过）。
- **Response 格式**：列表和详情端点通过 `_enrich_agent()` 辅助函数附加 model_name/prompt_title，在 API 层而非 Service 层处理关联数据的展平，符合关注点分离原则。

### 前端代码

- **模式遵循**：Vue 3 Composition API + Pinia + Element Plus，与现有 PromptList.vue 风格一致。
- **UI 完整性**：列表 + 状态筛选 + 创建对话框 + 激活/停用/删除按钮 + 确认对话框，全部实现。
- **错误处理**：激活失败时 ElMessage.error 显示后端返回的具体原因（如"未关联 Model"）。✅ 到位。
- **小问题**：`el-radio-button` 的 `value` 属性用法可能与 Element Plus 2.9 的 API 有兼容性问题（应用 `label` 而非 `value`，取决于版本）。

### 文档与规范

- **文档数量**：生成了 7 份文档（constitution, spec, plan, research, data-model, contracts, quickstart, tasks），覆盖完整。
- **文档质量**：
  - spec.md：结构完整，User Story 有优先级和验收场景，FR 可测试。质量高。
  - contracts/agents-api.md：API 契约精确到请求/响应 JSON 示例，可作前后端对接文档。质量高。
  - data-model.md：状态机图 + 校验规则 + 关系图，清晰。
  - research.md：6 项决策有选择理由和备选方案，决策透明。
- **代码注释**：几乎没有注释，符合"代码自解释"原则。
- **冗余感**：7 份文档中有大量重复内容（如状态机在 spec、plan、research、data-model、contracts 中各描述了一次）。

## 工具体验

### 工作流体感（1-5 分）

- **流畅度**：4/5 — 流程非常顺畅，没有卡顿或反复。唯一不流畅的是用户需要在每个阶段结束后手动触发下一个命令。
- **自然度**：3/5 — AI 的行为高度可预测（严格遵循模板），但缺乏"主动思考"的痕迹。比如它从未质疑需求或提出替代建议。
- **安心感**：3/5 — 代码产出能工作，但有死代码和 reason 未持久化的问题。测试覆盖为零，只能靠手动验证。

### 工具特有价值

**最大亮点**：结构化的分阶段流程。从需求到设计到实现，每一步都有文档产出，整个过程可追溯。API 契约文档的质量尤其好。

**相比纯手动编码**：
- **节省了**：需求分析、架构设计、API 设计的思考时间。这些文档如果手写可能需要 1-2 小时。
- **增加了**：大量中间文档的 token 消耗。7 份文档中有约 40% 的内容是重复的。

### 痛点与不足

1. **Phase 间的等待感**：用户需要在每个 Phase 结束后手动触发下一步。虽然只是打个命令，但打断了心流。且 AI 每次都要重新检查 extensions.yml hook，重复输出 hook 信息，消耗注意力。
2. **文档冗余严重**：状态机规则在 spec → research → data-model → contracts 中重复了 4 次。每次 AI 还要把这些文档重新 Read 一遍，浪费 token。
3. **Implement 阶段跳过 checkpoint**：tasks.md 设计了逐步验证，但 implement 直接一口气全写了。如果中途有错误，没有机会早期发现。

## 上下文使用分析

- **总 token 消耗**：105.8k / 200k（53%）
- **是否发生 compaction**：否
- **占比最大**：Messages 78.6k（39.3%），其次是 System tools 9.7k（4.9%）、System prompt 5.6k（2.8%）
- **File reads**：21.4k（11%），提示可节省约 6.4k
- **上下文压力影响**：53% 占用，后期工作未受影响。但文档重复加载（如 tasks.md 被读取 3 次，plan.md 被读取 2 次）是浪费。

### 上下文效率评估

- **单位上下文产出比**：偏低。105.8k token 中，约 30-40% 花在重复读取和生成冗余文档上。实际代码产出（3 个新增文件 + 4 个修改文件）约 500 行代码，token 产出比约为 200:1（token:代码行）。
- **与预期对比**：偏高。SpecKit 的多阶段文档生成机制天然消耗更多 token。如果目标是"写出能工作的代码"，60-70k 应该足够。

## 总结

### 一句话评价

SpecKit 提供了一套结构化的"需求→设计→实现"流水线，文档质量好、流程可追溯，但以较高的 token 消耗为代价，且中间文档的大量重复和 Implement 阶段的检查点缺失削弱了其"质量保障"的核心价值主张。

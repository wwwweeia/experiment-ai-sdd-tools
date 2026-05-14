# 第 2 轮实验观察：Spec-Kit + Superpowers

> **工具速览**：Spec-Kit 是 GitHub 出品的规范驱动开发 CLI（v0.8.10），强制把开发拆成 5 个阶段，每阶段产出独立的设计文档。本轮 Superpowers 虽已安装，但全程未被触发。
>
> - **怎么装**：`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
> - **初始化**：`specify init . --integration claude` （注意：`--ai` 参数已废弃）
> - **核心命令**：`/speckit.constitution` → `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`
> - **触发方式**：用户**手动**打 slash command，每阶段需主动触发下一步
> - **本轮截图**（30 张）：[`02-speckit/specs/001-agent-status-management/images/`](../02-speckit/specs/001-agent-status-management/images/)
> - **本轮工具产出**：[规范文档全套（spec/plan/tasks/contracts/quickstart 等 9 份）](../02-speckit/specs/001-agent-status-management/)
> - **AI 自评笔记**：[`experiment-observation.md`](../02-speckit/specs/001-agent-status-management/experiment-observation.md)（同 session 内 AI 用模板自我回顾，可与本人评笔记对照看）
> - **官方**：https://github.com/github/spec-kit

## 基本信息

| 项 | 值 |
|---|---|
| 工具组合 | Spec-Kit v0.8.10（speckit-* 技能集）+ Claude Code（Superpowers 已安装但未被主动调用） |
| 开发耗时 | **44 分钟**（会话 wall time，含 6 次手动 slash command 触发 + AI 执行等待） |
| 代码变更 | 10 文件，+541 / -48 行（未提交，仅 branch `001-agent-status-management`） |
| 提交数 | **0**（代码未提交，全部为工作区变更） |
| Context 使用 | 123k / 200k（**61%**），未触发压缩 |
| 子代理 | Explore [sonnet] ×1（6m 18s — 分析现有代码库模式） |
| 待办完成 | 7/7 |

### 技能使用

| 技能 | 触发方式 | 产出质量 |
|------|---------|---------|
| `speckit-constitution` | 用户手动 `/speckit-constitution` | 中 — 5 条原则贴合项目，但 Sync Impact Report 是 HTML 注释，对用户不可见 |
| `speckit-specify` | 用户手动 `/speckit-specify` + 需求文本 | 良好 — 5 个 User Story、15 条 FR、6 个 Edge Case |
| `speckit-git-feature` | specify 内部自动触发 | 正常 — 自动创建分支 |
| `speckit-plan` | 用户手动 `/speckit-plan` | 良好 — 6 份文档（plan + research + data-model + contracts + quickstart + checklist） |
| `speckit-tasks` | 用户手动 `/speckit-tasks` | 中 — 23 个任务拆分合理，但实际执行时被大幅合并 |
| `speckit-implement` | 用户手动 `/speckit-implement` | 中 — 执行快，但跳过了逐步验证 |

**注意**：Superpowers 的 `using-superpowers` 虽在会话开始时加载，但整个流程中**未触发任何 superpowers:* 子技能**（brainstorming、TDD、code-review 等）。Spec-Kit 的流程已经足够结构化，没有触发条件。

### 产出物构成

| 类别 | 文件 | 行数 |
|------|------|------|
| 规范文档（spec 系列） | 9 个 .md 文件 | 1,121 行 |
| 后端业务代码 | AgentService + endpoints + schemas + entity | ~193 行新增 |
| 前端业务代码 | AgentList.vue + agents.js API + agent store | ~235 行新增 |
| 测试代码 | **无** | 0 行 |
| 测试基础设施 | **无** | 0 行 |

## 需求理解

### 业务规则覆盖

| # | 规则 | 状态 | 说明 |
|---|------|------|------|
| 1 | DRAFT → ACTIVE 必须已关联 Model 和 Prompt | ✅ 完整 | `activate_agent()` 逐项校验 model_id → Model 存在 → prompt_id → Prompt 存在 |
| 2 | ACTIVE → INACTIVE，关联 Skill 标记不可用 | ✅ 完整 | `deactivate_agent()` 切换状态 + 批量 `UPDATE skills SET is_active=False` |
| 3 | INACTIVE → ACTIVE 重新检查 Model/Prompt 有效性 | ✅ 完整 | 与规则 1 共用 `activate_agent()`，走相同校验路径 |
| 4 | ACTIVE 状态 Agent 不能被删除 | ✅ 完整 | `delete_agent()` 检查 status == ACTIVE 抛出 ValueError |
| 5 | 状态变更记录操作时间和原因 | ⚠️ 部分 | 时间已记录（activated_at / deactivated_at），但**原因（reason）未持久化**，API 接受参数后直接丢弃 |

### 遗漏与缺陷分析

- **Reason 未持久化**：AI 在 research.md 中主动将 FR-015（"记录原因"）降级为"轻量级实现"，引用 Assumptions 为依据。但 spec 的 FR-015 明确要求记录原因，属于**AI 自行降级需求，用户未授权**
- **死代码**：`activate_agent()` 第 21 行 `if agent.status == AgentStatus.INACTIVE and False: pass`，明显的残留错误，AI 自查未发现
- **DRAFT → INACTIVE 边界**：spec 和 data-model 明确标注"DRAFT 不能直接转为 INACTIVE"，`deactivate_agent()` 的错误消息正确拒绝了 DRAFT 状态（"只有 ACTIVE 状态的 Agent 可以停用"），但逻辑路径依赖 `status != ACTIVE` 的单一判断而非状态白名单
- **以上问题用户均未在过程中发现**，直到回顾时才注意到

## 开发过程

### 工作流程

严格五阶段递进，每阶段由用户手动 slash command 触发：

```
Constitution → Specify → Plan → Tasks → Implement
```

- **策略**：Document-First，先生成 6 份设计文档再写第一行代码
- **子代理**：仅 Plan 阶段用了一次 Explore subagent（6m 18s），分析现有代码库模式，返回完整架构报告
- **无并行执行**：前端任务在 tasks 中分了多个 Phase，但 implement 阶段一次 Write 操作完成了 AgentList.vue 全部实现

### 人工干预

**零次决策干预**。用户全程只做了 5 个动作：

1. `/speckit-constitution`
2. 询问宪章文件位置（纯问答）
3. 提供需求 + `/speckit-specify`
4. `/speckit-plan`
5. `/speckit-tasks` → `/speckit-implement`

没有任何纠正、补充或修改。优点是流畅，风险是缺乏检查点导致 reason 未持久化和死代码未被发现。

### 关键决策

| # | 决策 | 评价 |
|---|------|------|
| 1 | 状态机用 if/elif 而非状态机库 | ✅ 合理 — 3 状态 3 路径，不值得引入依赖 |
| 2 | Skill 加 is_active 字段而非关联表 | ✅ 合理 — 一对一关系，关联表过度设计 |
| 3 | Reason 不持久化 | ⚠️ 有争议 — AI 主动降级需求，用户未授权 |
| 4 | 前端 4 个 Phase 合并为一次实现 | ⚠️ 不合理 — tasks 设计了逐步 checkpoint，被 implement 跳过 |
| 5 | 不生成测试 | ✅ 合理 — spec 标注"测试可选" |

## 产出质量

### 后端代码

- **API 设计**：RESTful，5 个端点，状态码规范（201/404/422），错误信息中文且具体
- **分层模式**：Router → Service → Model，遵循项目已有模式。`_enrich_agent()` 辅助函数在 API 层展平关联数据，关注点分离得当
- **数据模型**：新增 activated_at、deactivated_at、Skill.is_active，合理无冗余
- **代码缺陷**：
  - 死代码 `if agent.status == AgentStatus.INACTIVE and False: pass`
  - 无测试（仅 curl 手动验证 10 项通过）

### 前端代码

- **模式遵循**：Vue 3 Composition API + Pinia + Element Plus，与现有 PromptList 风格一致
- **UI 完整性**：列表 + 状态筛选 + 创建对话框 + 激活/停用/删除 + 确认对话框
- **错误处理**：ElMessage.error 显示后端具体原因（如"未关联 Model"）
- **小问题**：`el-radio-button` 的 `value` 属性用法可能与 Element Plus 2.9 有兼容性问题（应用 `label`）

### 文档

- **数量**：9 份 .md 文件，1,121 行，覆盖 spec → plan → research → data-model → contracts → quickstart → tasks → checklist
- **亮点**：contracts/agents-api.md（258 行）精确到请求/响应 JSON 示例，可作前后端对接文档
- **问题**：状态机规则在 spec、research、data-model、contracts 中重复 4 次，约 40% 内容冗余

## 上下文使用

| 指标 | 数据 |
|------|------|
| 总消耗 | 123k / 200k（**61%**） |
| Context 压缩 | 未发生 |
| 最大内容类型 | Messages（78.6k，39.3%）— AI 输出 |
| 文档重复加载 | tasks.md 读取 3 次，plan.md 读取 2 次 |
| 质量影响 | 未影响 |

### 效率评估

- **单位产出比偏低**：123k token 中约 30-40% 花在重复读取和冗余文档上。实际代码 ~430 行
- **与 Round 1 对比**：多消耗 27k token（+28%），代码产出少了约 70 行，测试为 0
- **固定开销**：7 份规范文档的重复内容是主要浪费源

## 工具体验

### 工作流体感（1-5 分）

| 维度 | 分 | 说明 |
|------|---|------|
| 流畅度 | 4 | 流程顺畅，无卡顿。但每个阶段需手动触发下一命令，打断心流 |
| 自然度 | 3 | AI 高度可预测（严格遵循模板），但缺乏主动思考，从未质疑需求或提替代建议 |
| 安心感 | 3 | 代码能工作，但有死代码和 reason 未持久化。零测试，只能靠手动验证 |

### 亮点

- **结构化五阶段**：从需求到设计到实现，每步有文档产出，全过程可追溯
- **API 契约文档质量极高**：contracts/agents-api.md 可直接作前后端对接文档
- **相比纯手动**：省了需求分析 + 架构设计 + API 设计的思考时间（手写可能需 1-2h），增加了大量中间文档的 token 消耗

### 痛点

1. **阶段间等待感**：用户需手动触发 6 个 slash command，AI 每次重新检查 extensions.yml hook 并重复输出，消耗注意力
2. **文档冗余严重**：状态机规则在 4 份文档中重复，每次 AI 还要重新 Read 这些文档，浪费 token
3. **Implement 跳过 checkpoint**：tasks 设计了逐步验证，但 implement 一口气全写了，中间错误无法早期发现
4. **零提交**：所有变更留在工作区，没有 git history 可追溯

## 用户评分

**功能完成度：8 / 10**

加分项（相对 Round 1）：
- 创建 Agent 时可关联 Model 和 Prompt（下拉选择，调用了 Model/Prompt API）
- 前端有删除操作（INACTIVE 状态可删除，带确认对话框）
- Skill is_active 标记完整实现（激活恢复、停用标记）
- 时间戳字段（activated_at / deactivated_at）

扣分项：
- reason 参数未持久化（AI 自行降级需求）

## 总结

**一句话评价**：文档驱动的"需求→设计→实现"流水线，功能覆盖比 Round 1 更完整，但零测试和死代码暴露了 Implement 阶段的质量把控短板。

### 数据速览

```
耗时:       44m（wall time）
提交:       0（未提交）
代码变更:   +541 / -48 行（10 文件，未提交）
测试:       0 个
文档:       9 个文件，1,121 行（spec 系列）
Context:    123k / 200k（61%）
子代理:     Explore[sonnet] 6m18s
人工干预:   0 次（6 次手动 slash command，无纠偏）
业务规则:   4/5 完整，1 部分实现（reason 未持久化），1 死代码缺陷
代码质量:   无测试，有死代码，reason 被 AI 自行降级
```

### 与 Round 1（Superpowers）对比速览

| 指标 | Round 1: Superpowers | Round 2: Spec-Kit |
|------|---------------------|-------------------|
| 耗时 | 1h 4m | 44m |
| Context | 96.1k（48%） | 123k（61%） |
| 代码行数 | +2123 行 | +541 行 |
| 测试 | 19 个集成测试 | 0 |
| 提交 | 11 个 | 0 |
| 文档 | 1,266 行（2 份） | 1,121 行（9 份） |
| 业务规则 | 4/5 完整，1 可选跳过 | 4/5 完整，1 AI 自行降级 |
| 代码缺陷 | 无 | 死代码 + reason 丢弃 |
| 人工干预 | 5 次（决策审批） | 0 次（纯命令触发） |

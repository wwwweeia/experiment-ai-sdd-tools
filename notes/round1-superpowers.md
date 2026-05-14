# 第 1 轮实验观察：Superpowers

> **工具速览**：Superpowers 是 Claude Code 的官方插件，提供一组可被 AI 自动触发的"方法论" skill（brainstorming、writing-plans、subagent-driven-development、code-reviewer 等）。
>
> - **怎么装**：Claude Code 插件市场安装（本实验中已预装）
> - **核心 skills**：`brainstorming` · `writing-plans` · `subagent-driven-development` · `code-reviewer`
> - **触发方式**：AI 根据上下文**自动触发**，用户不需要打 slash command
> - **本轮截图**（17 张）：[`01-superpowers/docs/images/`](../01-superpowers/docs/images/)
> - **本轮工具产出**：[设计文档](../01-superpowers/docs/superpowers/specs/) · [实施计划](../01-superpowers/docs/superpowers/plans/)

## 基本信息

| 项 | 值 |
|---|---|
| 工具组合 | Superpowers 插件（brainstorming → writing-plans → subagent-driven-development 三段式技能链） |
| 开发耗时 | **1 小时 4 分钟**（会话实际 wall time，含设计讨论 + AI 执行等待 + 用户审批） |
| 代码变更 | 20 文件，+2123 / -88 行 |
| 提交数 | 11 个（含 1 个基础补充 + 2 个文档 + 8 个功能/测试） |
| Context 使用 | 96.1k / 200k（**48%**），未触发压缩 |
| 子代理 | agent[sonnet] ×1（44s）, code-reviewer[sonnet] ×1（2m 7s） |
| 待办完成 | 13/13 |

### 技能使用

| 技能 | 触发方式 | 产出质量 |
|------|---------|---------|
| `using-superpowers` | 会话启动自动加载 | 基础设施 |
| `brainstorming` | 收到需求后 AI 自动触发 | 高 — 项目探索 → 澄清问题 → 方案对比 → 设计文档 |
| `writing-plans` | 设计确认后 AI 自动触发 | 高 — 8 个任务、完整代码、无占位符 |
| `subagent-driven-development` | 用户选择后 AI 调用 | 高 — 7 个子代理逐任务执行 |
| `code-reviewer` | 最终派发 spec reviewer | 高 — 0 critical / 2 important / 3 suggestion |

### 产出物构成

| 类别 | 文件 | 行数 |
|------|------|------|
| 设计文档 | `docs/superpowers/specs/...-design.md` | 148 行 |
| 实施计划 | `docs/superpowers/plans/...-management.md` | 1,118 行 |
| 后端业务代码 | AgentService + schemas + endpoints + router | ~200 行 |
| 前端业务代码 | AgentList.vue + agent.js API + agent store | ~320 行 |
| 测试代码 | conftest.py + test_agent_api.py | 278 行 |
| 基础设施 | pytest setup + prompt service 补充 | ~130 行 |

## 需求理解

### 业务规则覆盖

| # | 规则 | 状态 | 说明 |
|---|------|------|------|
| 1 | DRAFT → ACTIVE 必须已关联 Model 和 Prompt | ✅ 完整 | Service 层校验 model_id/prompt_id 非空且存在，返回 422。3 个专门测试覆盖 |
| 2 | ACTIVE → INACTIVE，关联 Skill 标记不可用 | ⚠️ 部分 | 停用逻辑已实现，Skill 不可用标记被**协商跳过**（Skill 功能本身未实现） |
| 3 | INACTIVE → ACTIVE 重新检查 Model/Prompt 有效性 | ✅ 完整 | 与规则 1 统一校验逻辑，`test_reactivate_inactive_agent` 验证 |
| 4 | ACTIVE 状态 Agent 不能被删除 | ✅ 完整 | delete 前检查 status，422 拒绝。正反测试覆盖 |
| 5 | 状态变更记录操作时间和原因 | ⏭️ 可选跳过 | API 接收 reason 参数，但未持久化。需求标注为"可选" |

### 遗漏分析

- **Skill 不可用标记**：不是遗漏。AI 在 brainstorming 阶段主动发现需求歧义，通过三选一问题让用户决策，用户选择"本期跳过"后全流程一致执行
- **reason 未持久化**：设计阶段标记为"可选"，保留了 API 入口，合理的简化
- **没有"回顾时才发现"的遗漏**，所有决策都在开发过程中做出

## 开发过程

### 工作流程

四阶段严格递进：

```
brainstorming（设计分析）→ writing-plans（实施计划）→ subagent-driven-development（子代理执行）→ spec review
```

- **策略**：先分析再动手，典型的"想清楚再执行"
- **子代理使用**：7 个子代理（含 1 个 spec reviewer），简单任务合并给同一代理（Task 2+3、Task 6+7）
- **未使用并行子代理**：subagent-driven-development 明确禁止并行以避免冲突
- **子代理自主能力**：Task 5 子代理自主发现并修复了 conftest.py 中 SQLite 内存数据库的线程安全问题（添加 StaticPool）

### 人工干预

共 5 次交互（不含"OK/继续"确认）：

| # | 干预点 | 类型 | 说明 |
|---|--------|------|------|
| 1 | Skill 处理方式 | 补充需求决策 | 从三个选项中选择"本期跳过" |
| 2 | API 方案选择 | 架构决策 | 选择方案 A（专用状态端点） |
| 3 | 后端设计确认 | 审批 | "设计 ok" |
| 4 | 前端设计确认 | 审批 | "设计 ok" |
| 5 | 执行方式选择 | 流程决策 | 选择"子代理驱动" |

**没有纠偏或修复错误的干预**。所有干预都是 AI 在关键决策点主动征求意见。

### 关键决策

| # | 决策 | 评价 |
|---|------|------|
| 1 | 专用状态端点 `PATCH /agents/{id}/status` 而非通用 PATCH | ✅ 合理 — 状态变更有业务语义，独立端点让校验逻辑更清晰 |
| 2 | Skill 不可用标记"本期跳过" | ✅ 合理 — AI 主动识别歧义，用户决策后一致执行 |
| 3 | 合并简单任务给同一子代理 | ✅ 合理 — 减少调度开销，实际未出问题 |
| 4 | 跳过逐任务的 spec/code review | ⚠️ 有争议 — 技能要求两阶段 review，但只做了最终一次。最终结果 OK，但风险是中间错误延迟发现 |
| 5 | `_agent_to_read` 手动 dict 构造 | ⚠️ 有争议 — spec reviewer 识别的维护风险，新增字段需同步更新 |

## 产出质量

### 后端代码

- **API 设计**：RESTful，5 个端点命名清晰。状态码规范（201/404/422），错误信息中文且具体（"未关联有效的 Model"）
- **Service 层**：业务逻辑集中在 `AgentService`，`ALLOWED_TRANSITIONS` 集合定义清晰，遵循项目已有分层模式
- **数据模型**：无变更，复用已有 Agent/AgentStatus 定义
- **测试**：19 个集成测试（CRUD 8 + 状态机 11），直接调 API 验证端到端行为

### 前端代码

- **模式一致性**：完全遵循 Vue 3 Composition API + Pinia + Element Plus 已有模式
- **UI 完整性**：状态筛选 Tab、表格展示、动态操作按钮、新建弹窗、分页、确认对话框、成功/错误提示
- **功能缺失**：
  - **新建时无法关联 Model 和 Prompt**：创建 Agent 的弹窗没有提供 Model/Prompt 的下拉选择
  - **无删除操作**：前端没有提供删除 Agent 的按钮（后端 API 已实现）
- **错误处理**：依赖 Axios 拦截器统一提示，激活失败时用户能看到具体原因

### 文档

- 设计文档 148 行、实施计划 1,118 行，质量高、无占位符，可独立给团队成员参考
- 代码注释极少，代码自解释性良好

## 上下文使用

| 指标 | 数据 |
|------|------|
| 总消耗 | 96.1k / 200k（48%） |
| Context 压缩 | 未发生 |
| 最大内容类型 | Messages（59.6k，29.8%）— 子代理报告 |
| 固定开销 | Skills 元数据 6.6k + System 15.7k |
| 质量影响 | 无。余量充足 |

### 效率评估

- **单位产出比偏高**：Messages 中大量是子代理报告的重复内容（"files changed"、"self-review findings"）
- **固定开销显著**：70+ 个 skill 描述常驻上下文（6.6k tokens），实际只用 4 个
- **与预期一致**：Superpowers 重流程，设计文档 + 实施计划 + 子代理报告必然消耗上下文

## 工具体验

### 工作流体感（1-5 分）

| 维度 | 分 | 说明 |
|------|---|------|
| 流畅度 | 4 | 各阶段衔接自然。brainstorming 的 8 步 checklist 稍长，部分可合并 |
| 自然度 | 4 | 关键节点征求意见，方案推荐有理有据 |
| 安心感 | 4 | 设计文档 + 19 测试 + spec review 层层验证。扣一分因跳过了逐任务 review |

### 亮点

- **结构化四阶段流程**：强制把"想清楚"和"动手做"分开，设计文档和实施计划有独立价值
- **子代理执行**：任务粒度清晰、产出干净，还有自主修复能力（SQLite StaticPool）
- **相比纯手动**：省了大量"组织工作"（规划顺序、写 scaffolding、逐文件想内容），增加了等待 AI 和 review 中间产物的心智成本

### 痛点

1. **brainstorming 偏重**：需求已经明确，但仍然走完 8 步 checklist，对明确需求有过度仪式化倾向
2. **逐任务 review 被跳过**：流程设计对"简单任务"过于重量级，导致执行者自行简化
3. **Skills 元数据浪费**：70+ skill 描述全部常驻上下文（6.6k tokens），实际只用 4 个

## 用户评分

**功能完成度：5 / 10**

扣分项：
- 创建 Agent 时无法关联 Model 和 Prompt（无下拉选择）
- 前端无删除操作
- Skill 不可用标记被协商跳过
- 无时间戳字段（activated_at / deactivated_at）

## 总结

**一句话评价**：流程严谨、后端可靠，但前端功能缺失较多 — 好的工程流程不等于好的功能交付。

### 数据速览

```
耗时:       1h 4m（wall time）
提交:       11 个
代码变更:   +2123 / -88 行（20 文件）
测试:       19 个集成测试（278 行测试代码）
文档:       1,266 行（设计 + 实施计划）
Context:    96.1k / 200k（48%）
子代理:     agent[sonnet] 44s + code-reviewer[sonnet] 2m7s
人工干预:   5 次（均为决策审批，无纠偏）
业务规则:   4/5 完整，1 可选跳过，0 遗漏
```

# 第 4 轮实验观察：Get Shit Done (GSD)

> **工具速览**：GSD（get-shit-done-cc）是面向 Claude Code 的重量级 meta-prompting 框架，核心思路是通过安装一套 slash commands 把 Claude Code 的工作切成 research → plan → execute → verify 四步循环，并用独立 worktree 隔离每个执行 task 的上下文，主打解决"context rot"（上下文膨胀导致质量退化）问题。
>
> - **怎么装**：`npx get-shit-done-cc@latest`（安装时选 Claude Code runtime + local scope）
> - **核心工作流**：`/gsd:map-codebase` → `/gsd:new-project` → `/gsd:plan-phase N` → `/gsd:execute-phase N` → `/gsd:verify-work N`
> - **触发方式**：用户手动打 slash command，AI 自动串联子阶段
> - **本轮产出物目录**：[`.planning/`](../.planning/)（PROJECT.md、REQUIREMENTS.md、ROADMAP.md、STATE.md + 按 phase 归档的 RESEARCH、PATTERNS、PLAN、SUMMARY、VERIFICATION）
> - **完成情况**：跨 **3 个 session** 完成，2026-05-18（两个 session）+ 2026-05-19（最终人工验证）

## 基本信息

| 项 | 值 |
|---|---|
| 工具组合 | GSD（get-shit-done-cc）slash commands + Claude Code 原生执行 |
| 开发跨度 | **约 3+ 小时 wall time**（跨 2 天 3 个 session） |
| 实际执行时间 | Session 1：≈2h（17:04–19:39）；Session 2：≈25min（21:38–22:03）；Session 3：≈10min 验证 |
| 提交数 | **27 个**（从 codebase map 到 phase-02 tracking） |
| 子代理 | **有** — Phase 1 和 Phase 2 各用了独立 worktree executor（并行任务，独立 200k 上下文） |
| Context 使用 | 不可获取精确值（跨 session 清空；worktree 执行消耗在子 agent 中） |

### 技能使用详情

| 技能 | 触发方式 | 产出 | 质量 |
|------|---------|------|------|
| `/gsd:map-codebase` | 用户手动 | `.planning/codebase/` 架构分析文档 | 良好 — 正确识别已有三层结构和参考模式 |
| `/gsd:new-project` | 用户手动 | PROJECT.md、REQUIREMENTS.md、ROADMAP.md | 良好 — 问答 8 个问题后生成，需求拆解准确，主动将 Skill.is_active 划为 out-of-scope |
| `/gsd:plan-phase 1` | 用户手动 | RESEARCH.md + PATTERNS.md + 4 × PLAN.md | 优秀 — 将后端拆成 4 个原子任务（数据层→服务层→HTTP层→测试层），每 plan 有明确边界 |
| `/gsd:execute-phase 1` | 用户手动 | 4 次原子提交 + 4 × SUMMARY.md | 优秀 — 每个 task 独立 worktree，commit 粒度干净，合计 17 分钟内完成 4 层 |
| `/gsd:verify-work 1` | AI 自动触发 | VERIFICATION.md（5/5 verified） | 良好 — 结构化验证，静态分析 + pytest 运行 |
| `/gsd:ui-phase 2` | 用户手动 | UI-SPEC.md | 一般 — 生成了完整设计合约，但触发 checker 后需要修一轮（4 个问题：字体权重/间距值/文案/视觉焦点） |
| `/gsd:plan-phase 2` | 用户手动 | RESEARCH.md + PATTERNS.md + 1 × PLAN.md | 良好 — 前端研究较简洁，plan 1 张覆盖三层 |
| `/gsd:execute-phase 2` | 用户手动 | 3 次原子提交（API client + store + Vue 页面）| 良好 — 2 分钟内完成，文件精准 |
| `/gsd:verify-work 2` | AI 自动触发 | VERIFICATION.md（6/6 verified，human_needed）| 合格 — 静态分析完整，但 5 项需浏览器运行才能最终确认，标注为 human_needed |

### 产出物构成

| 类别 | 文件 | 行数 |
|------|------|------|
| GSD 规划文档 | PROJECT.md、REQUIREMENTS.md、ROADMAP.md、STATE.md + 10+ 个 phase 文档 | ~2500+ 行规划制品 |
| 后端业务代码 | AgentService + endpoints + schemas | ~370 行新增 |
| 后端测试代码 | conftest + test_agent_service + test_agent_api | **569 行**（41 个测试） |
| 前端业务代码 | agents.js + agent.js store + AgentList.vue | 368 行（17+80+271） |
| 数据模型变更 | AgentStatusHistory ORM 表 | ~20 行 |

## 需求理解

### 业务规则覆盖

| # | 规则 | 状态 | 说明 |
|---|------|------|------|
| 1 | DRAFT → ACTIVE 必须已关联 Model 和 Prompt | ✅ 完整 | `_assert_activation_ready()` 验证 model_id/prompt_id 存在性，缺失返回 422 + 具体原因 |
| 2 | ACTIVE → INACTIVE，关联 Skill 标记不可用 | ⚠️ 有意跳过 | GSD 在 `/gsd:new-project` 问答阶段主动提议将 Skill.is_active 划为 Out of Scope，理由：停用意图已通过 Agent.status 隐式反映，避免冗余状态。用户接受了这个建议。 |
| 3 | INACTIVE → ACTIVE 重新检查 Model/Prompt | ✅ 完整 | 同一 `_assert_activation_ready()` 路径，两条到 ACTIVE 的转换都走校验 |
| 4 | ACTIVE 不可删除 | ✅ 完整 | `delete_agent()` 检测 ACTIVE 抛 ValueError → 路由层映射 409，有专属测试 |
| 5 | 状态变更记录时间和原因 | ✅ 完整 | AgentStatusHistory 独立表（append-only），含 from_status/to_status/changed_at/reason，创建时也写初始行 |

### 遗漏分析

规则 2 的 Skill.is_active 不是遗漏，是 GSD 在规划阶段主动识别并决策的 scope cut。时机：`/gsd:new-project` 问答环节（开发开始前），原因和替代方案在 PROJECT.md 的 Out of Scope 节有记录。这是 GSD 与前三轮最不同的一个行为——它在写一行代码前就把这个"需求陷阱"挑出来讨论了，而不是实现后才标注 TODO。

## 开发过程

### 工作流程

GSD 强制执行线性流程：map-codebase → new-project → plan-phase → execute-phase → verify-work。

每个 execute 阶段用独立 worktree（git worktree add）给子 agent 提供隔离上下文，执行完 merge 回主分支。这意味着主 session 的上下文不被执行细节污染，始终处于"规划态"。

Phase 1 用了 4 个串行 task（数据层→服务层→HTTP层→测试层），每 task 约 3-5 分钟。Phase 2 用了 2 个 task（API+store、Vue 页面），约 1-2 分钟每个。

### 人工干预

Session 1（Phase 1 + UI-SPEC）过程中用户基本旁观，主要在 `/gsd:new-project` 问答环节回答了 8 个问题（tech stack 确认、Skill 降级决策等）。

Session 2 的触发原因：Session 1 在 UI-SPEC 完成后暂停（因为 gsd-ui-checker 触发了修改，修完后 AI 暂停等待），用户在约 2 小时后回来继续。

Session 3（今天）是用户主动回来做最终浏览器验证 + 当前会话（写笔记）。

**实质性干预**：0 次（问答不算干预，是流程设计的一部分）。

### 关键决策点

1. **Skill.is_active 划为 Out of Scope**：GSD 问答时主动提出，理由充分（冗余状态），记录在 PROJECT.md。合理。
2. **AgentStatusHistory 独立表而非 JSON 列**：Phase 1 research 阶段决定，理由：append-only 语义，利于 debug/审计，历史不可改。合理。
3. **409/422 双错误码**：409 用于非法状态转换，422 用于激活前置条件失败。OpenSpec 轮（R3）也做了同样决策，但 GSD 在 RESEARCH.md 里把这个约定写得更明确，前端据此实现了全局拦截器。合理。
4. **selectinload 防止 N+1**：Phase 1 PLAN 明确要求列表查询用 selectinload 预加载 model/prompt 关联，Verification 也验证了这点。合理。
5. **Phase 2 UI-SPEC 单独走 checker**：gsd-ui-checker 触发了 4 个 FLAG，迫使在执行前修正设计合约（字体权重规范、间距 token 值等）。额外一轮但有价值。

## 产出质量

### 后端代码

- **API 设计**：完全遵循项目既有模式（统一 Response[T] 包装、HTTPException 语义、独立 PATCH /status 端点）。端点命名、状态码全部规范。
- **分层**：业务规则 100% 在 AgentService 内（VALID_TRANSITIONS 映射表、_assert_activation_ready、状态机检查），endpoints.py 纯做 HTTP 转换。
- **测试**：**41 个测试**，18 个 service 单元测试 + 23 个 HTTP 集成测试，覆盖所有 5 条业务规则及边界（激活无 model、激活无 prompt、非法转换 ACTIVE→DRAFT 等）。这是四轮中测试最全面的。
- **代码质量**：agent_service.py 207 行，无多余注释，命名清晰。history 记录在同一 commit 中原子写入。

### 前端代码

- **模式遵从**：agents.js (17 行) + agent.js store (80 行) + AgentList.vue (271 行) 严格镜像 PromptList 三层结构。
- **UI 完整性**：6 列表格（ID/名称/状态标签/关联模型/关联提示词/操作）+ 状态筛选 + 分页 + 创建对话框（name 必填/description 选填/model+prompt 懒加载下拉）。三种状态的操作按钮（DRAFT→激活、ACTIVE→停用、INACTIVE→激活+删除）均有 ElMessageBox.confirm 确认。
- **错误处理**：全局 axios 拦截器（api/index.js）统一展示 error.detail，后端 409/422 的错误文本直接透传到 ElMessage.error 弹窗。

### 文档与规范

GSD 是四轮中文档密度最高的工具：`.planning/` 目录约 2500 行规划制品（PROJECT.md、REQUIREMENTS.md、ROADMAP.md、STATE.md + 每个 phase 的 RESEARCH/PATTERNS/PLAN×N/SUMMARY×N/VERIFICATION）。文档质量高，VERIFICATION.md 里的"Observable Truths"设计值得借鉴。

代码本身注释适度——service 层有状态机转换规则的说明注释（业务约束，非显而易见），其他地方无多余注释。

## 工具体验

### 工作流体感

| 维度 | 分 | 说明 |
|------|------|------|
| 流畅度 | 3/5 | 流程规范但**重**——map + new-project + plan + execute + verify 5 步，每步有 AI 子阶段，一轮下来感觉走了很多"必经关卡"。Session 1 结束时停在 UI-SPEC checker 的修复等待，体验断裂。 |
| 自然度 | 4/5 | 每个命令的产出符合预期，没有意外行为。子 agent 执行后 merge 回主分支的结果很干净，commit message 也规范。UI-SPEC checker 触发 4 个 FLAG 让人意外但实际有价值。 |
| 安心感 | 5/5 | 最高分。Verification.md 的"Observable Truths"设计、41 个测试、静态分析 + 行为检查——整个过程有完整证据链。每个 plan 执行完都有 SUMMARY，每个 phase 完成都有 VERIFICATION，清楚知道"完成了什么"和"还差什么"。 |

### 工具特有价值

1. **子 agent 隔离上下文**：每个 execute task 在独立 worktree 里运行，主 session 的上下文不受执行细节污染。这让 Phase 2 的 plan 可以从相对干净的上下文起步，而不是带着 Phase 1 执行的全部细节。
2. **强制的 before-code-research 阶段**：每个 phase 都有独立 research 步骤，Phase 1 RESEARCH.md 明确写出了"VALID_TRANSITIONS dict 实现状态机""AgentStatusHistory 独立表"等架构决策，给执行 agent 减少了歧义。
3. **Verification 层**：4 轮里唯一有正式 verify 步骤的工具。Phase 1 5/5 passed，Phase 2 6/6 verified（human_needed）。虽然大多是静态分析，但结构化验证本身有价值。

### 痛点与不足

1. **流程重量太高，对"现有项目加功能"场景体验不优**：GSD 设计用于从零开始的新项目（new-project 问答、roadmap 生成、phase 规划等）。接入一个已有代码库加功能时，前 1 小时几乎在走"项目初始化"的仪式，和实际需求的关联度一般。
2. **Session 断裂体验差**：Phase 1 完成后 GSD 自动进入 Phase 2 UI-SPEC 生成，UI-SPEC checker 触发修改，AI 修完后停下来等待用户"approve"。这个等待点没有明确提示，用户需要理解 GSD 的内部状态（STATE.md 里有记录，但不直觉）。2 小时后回来需要先理解"停在哪里"。
3. **规划文档量和代码量不成比例**：Phase 1（约 370 行业务代码）产生了约 1500+ 行规划制品。对于这个规模的需求来说文档成本偏高。如果需求更复杂、周期更长，这个比例会更合理。

## 上下文使用分析

- **精确数据不可获取**：跨 3 个 session，每次 /clear 都重置了 context 计数；子 agent 的消耗在各自的 worktree 会话里，不体现在主 session。
- **设计意图**：GSD 的核心设计就是把"context 消耗"分散到子 agent 里，主 session 只保留规划状态。从 STATE.md 的记录看，每个 phase 开始时主 session 处于相对轻量的状态。
- **对比其他轮次**：R1（Superpowers）96.1k/200k，R2（Spec-Kit）123k/200k，R3（OpenSpec）91.9k/200k。GSD 如果能有主 session 的数据，预计会在 40-60%，因为大量工作下沉到子 agent。

### 上下文效率评估

子 agent 隔离这个设计从"单 session context 压力"角度是最优的，但跨 session 带来了不同的开销——每次回来要重建状态（靠 STATE.md，但需要用户主动读懂）。对比之下 R3 OpenSpec 用 24 分钟一个 session 完成，R4 GSD 用了 3 个 session 共 3+ 小时。

## 总结

### 各维度对比

| 维度 | R1 Superpowers | R2 Spec-Kit | R3 OpenSpec | R4 GSD |
|------|---------------|-------------|-------------|--------|
| 耗时 | 64min | 44min | 24min | 3+h / 3 sessions |
| Context | 96.1k (48%) | 123k (61%) | 91.9k (46%) | 不可测（跨 session） |
| 提交数 | 11 | 多 | 0 | **27** |
| 测试 | 19 | 无 | 无 | **41** |
| 文档密度 | 低 | 中 | 中 | **极高** |
| 业务规则覆盖 | 4/5 | 5/5 | 5/5 | 4/5（Skill 有意降级） |
| 前端完整性 | 不完整 | 完整 | 完整 | **完整** |

### 一句话评价

GSD 是最"像正规工程流程"的工具——有 research、有 plan、有 verify、有干净的提交历史——但这套流程的重量对"在已有项目里加一个功能"来说明显过剩，适合从零构建的大型项目而非这类实验场景，你会感受到规程本身的摩擦。

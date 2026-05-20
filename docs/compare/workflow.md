# 任务分解与设计文档

> 四轮在"先想清楚再动手"的具体落地上，粒度和侧重点差异很大。

## 任务分解粒度

| 工具 | 任务数 | 组织方式 | 文档行数 |
|------|--------|---------|---------|
| Superpowers | 23 个任务，7 个 Phase | 按用户故事分组 | 1,118 行 |
| Spec-Kit | 7 组，22 个子任务 | 按技术层分组 | 212 行 |
| OpenSpec | 8 个 Task，43 个 Step | 按组件顺序 | 42 行 |
| GSD | **5 个 plan（Phase 1: 4，Phase 2: 1）** | 按技术层（数据→服务→HTTP→测试→前端三层） | 每 plan 约 200-300 行（含研究、模式分析、计划本体） |

- **Superpowers** 最重：23 个任务按 Phase 组织（Setup → Foundational → 4 个 User Story → Polish），每个 Phase 有显式 Checkpoint。
- **Spec-Kit** 最薄：7 个逻辑组，但实际执行时被大幅合并（前端 4 个 Phase 合并为一次 Write）。
- **OpenSpec** 最精细：8 个大任务下嵌套 Step，但文档本身只有 42 行 —— 把细节留给了执行阶段。
- **GSD** 用 phase-based 组织，每个 phase 有独立的 RESEARCH/PATTERNS → PLAN×N → execute → SUMMARY/VERIFICATION 循环，最重量但也最结构化。

## 检查点设计

| 工具 | 有检查点？ | 检查点位置 | 实际执行情况 |
|------|-----------|-----------|-------------|
| Superpowers | **5 个显式 Checkpoint** | 每个 Phase 结束后 | 部分跳过（只做了最终 spec review） |
| Spec-Kit | **无**（只有最终验证） | 仅末尾 2 个验证任务 | 跳过了逐任务验证 |
| OpenSpec | **嵌入式**（每个 Task 有 Run 命令） | 每个组件完成后 | 大部分执行了 |
| GSD | **强制 verify step**（/gsd:verify-work） | 每个 Phase 执行结束后 | **实际执行了**，产出 VERIFICATION.md（P1: 5/5 passed，P2: 6/6 verified） |

前三个工具的检查点都没被严格执行。Superpowers 设计了 5 个但只做了最终 1 个；Spec-Kit 设计了 0 个；OpenSpec 嵌入了验证命令但也不是每个都跑了。

::: warning 关键观察
**检查点设计在 AI 执行中基本失效** —— AI 倾向于一口气写完，不愿中途停下来验证。GSD 通过工具化绕过了这个问题：独立的 `/gsd:verify-work` 子 agent 负责验证，而非让执行 agent 自我 review，所以 P1 和 P2 都真正执行了 verify step。框架层面如果想保证质量，**工具化 verify**（GSD 方式）比依赖 AI 自律的检查点更可靠。
:::

## 任务完成忠实度

| 工具 | 计划的任务 | 实际完成 | 偏差 |
|------|-----------|---------|------|
| Superpowers | 23 个 | 23 个标记完成 | 忠实（但跳过了逐任务 review） |
| Spec-Kit | 22 个子任务 | 全部标记完成 | 合并执行，跳过 checkpoint |
| OpenSpec | 43 个 step | 全部标记 [x] | 忠实（按 step 粒度执行） |
| GSD | 5 个 plan，每 plan 有 2-4 个 task | 全部完成 + SUMMARY | **零偏差**，每 plan 执行结果有独立 SUMMARY.md 记录 |

## API 契约精度

| 工具 | API 契约形式 | 精度 | 可对接性 |
|------|-------------|------|---------|
| Superpowers | 设计文档中内嵌 schema 定义 | 中 — 有字段定义，无 JSON 示例 | 需要阅读代码才能对接 |
| Spec-Kit | **独立的 contracts/agents-api.md** | **高 — 含请求/响应 JSON 示例** | **可直接作前后端对接文档** |
| OpenSpec | spec 文件中的 WHEN/THEN 场景 | 中 — 有场景但无 JSON | 需要补充才能对接 |
| GSD | REQUIREMENTS.md 端点表格 + PLAN.md 接口说明 | 中 — 有端点+字段+状态码，无 JSON 示例 | 可指导实现，但不如 Spec-Kit 精确 |

**Spec-Kit 胜出**：258 行的独立 API 契约文档，精确到每个端点的请求体和响应体 JSON 示例，是四个工具中唯一能直接指导前后端并行开发的文档。

查看原件：[Round 2 API 契约](/rounds/r2/artifacts/contracts/agents-api)

## 状态机描述准确性

| 工具 | 描述方式 | 与最终代码一致性 |
|------|---------|----------------|
| Superpowers | 文字 + 状态转换图 | ✅ 完全一致 |
| Spec-Kit | 分散在 spec、research、data-model、contracts 4 份文档中 | ⚠️ 一致但有冗余 |
| OpenSpec | design.md Decisions + 服务层代码 | ✅ 完全一致 |
| GSD | RESEARCH.md + PLAN.md + 代码 | ✅ 完全一致（RESEARCH 明确写出 VALID_TRANSITIONS dict 约定，代码严格遵循） |

四个工具对状态机规则的描述都与最终代码一致，没有"设计文档说 A 但代码做了 B"的情况。

## 遗漏预测

| 工具 | 是否预警了后来出现的问题？ |
|------|-------------------------|
| Superpowers | 预警了 Skill 不可用标记的歧义，主动提问让用户决策 |
| Spec-Kit | research.md 主动将 reason 降级，但**没有预警死代码风险** |
| OpenSpec | design.md 标注了"Skill 模型没有 is_available 字段"的风险，但最终选择了简化而非解决 |
| GSD | **/gsd:new-project 问答时主动提议 Skill.is_active 为 out-of-scope**，理由充分（冗余状态），记录在 PROJECT.md，用户当场确认 |

**Superpowers 和 GSD 都是真正"预测问题"的** —— Superpowers 通过 brainstorming 发现歧义，GSD 通过 new-project 问答环节结构化收集。GSD 的方式更正式（专门的问答环节，结果写入 PROJECT.md 存档）。

## 文档冗余度

| 工具 | 文档行数 | 代码行数 | 文档/代码比 | 冗余程度 |
|------|---------|---------|------------|---------|
| Superpowers | 1,266 | 2,123 | 0.6:1 | **低** — 设计 + 计划各一份，几乎无重复 |
| Spec-Kit | 1,121 | 541 | **2.1:1** | **高** — 状态机在 4 份文档中重复描述 |
| OpenSpec | 287 | 305 | 0.9:1 | 中 — spec 归档后有副本 |
| GSD | ~2,500+ | ~1,303 | **约 1.9:1** | 低 — 每份文档职责不同（RESEARCH/PATTERNS/PLAN/SUMMARY/VERIFICATION 各司其职，无重复） |

Spec-Kit 的高文档/代码比一方面说明文档"齐全"，另一方面也意味着维护成本高 —— 同一条状态机规则改一次需要同步 4 处。GSD 文档量最大但冗余度低，因为每份文档覆盖不同的 phase 和关注点。

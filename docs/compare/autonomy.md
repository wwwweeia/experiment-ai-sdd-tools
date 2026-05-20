# 自主决策质量

> "零干预"≠ 高质量。这一章拆解四轮 AI 在关键决策点的实际表现。

## 决策统计

| 工具 | 用户参与决策 | AI 自主决策 | 自主决策正确率 |
|------|-------------|-----------|--------------|
| Superpowers | **5 次** | 少量实现细节 | **高**（无错误决策） |
| Spec-Kit | **0 次** | 全部自主 | **中**（有死代码、reason 未持久化） |
| OpenSpec | **0 次** | 全部自主 | **中**（Skill 简化替代、reason 半成品） |
| GSD | **8 次**（/gsd:new-project 问答） | 实现细节 + 一次主动 scope cut | **高**（Skill out-of-scope 有记录，reason 完整实现） |

## 关键决策对比

### 决策 A：Skill 不可用如何处理？

| 工具 | 决策 | 用户参与？ | 结果 |
|------|------|-----------|------|
| Superpowers | 主动发现歧义，提供 3 个选项 | **是** — 用户选择跳过 | 需求协商，无遗漏 |
| Spec-Kit | 直接实现 `is_active` 字段 + 批量 UPDATE | 否 | **最完整的实现**，但用户不知情 |
| OpenSpec | 选择"间接判断"，不修改代码 | 否 | 最轻量但可追溯性差 |
| GSD | /gsd:new-project 问答时主动提议 out-of-scope，理由写入 PROJECT.md | **是** — 用户在问答中确认 | 有意降级，有文档记录，无"默默跳过" |

这个对比揭示了一个关键差异：

::: info 四种性格
- **Superpowers 倾向于"问用户"** —— 发现歧义就停下来
- **Spec-Kit 倾向于"做更多"** —— 自行加字段加批量更新
- **OpenSpec 倾向于"做更少"** —— 用间接判断绕过
- **GSD 倾向于"先讨论再决策，结果可查"** —— 专门的问答环节，决策记录在 PROJECT.md
:::

### 决策 B：reason 字段如何处理？

| 工具 | 决策 | 问题 |
|------|------|------|
| Superpowers | 标记为可选跳过 | 无 — 诚实跳过 |
| Spec-Kit | 接收参数但不持久化 | **半成品** — API 接了参数却丢弃 |
| OpenSpec | 同 Spec-Kit | 同上 |
| GSD | **完整实现**：AgentStatusHistory.reason 字段 + API 接收并写入 | **唯一真正持久化 reason 的实现** |

前三轮都没有做好 reason 处理。**GSD 是唯一完整实现的** —— 通过独立的 AgentStatusHistory 表持久化，而非接了参数却丢弃。

### 决策 C：创建 Agent 时是否关联 Model/Prompt？

| 工具 | 决策 | 前端实现 |
|------|------|---------|
| Superpowers | 后端 schema 支持，前端未实现 | **缺失** |
| Spec-Kit | 完整实现（下拉 + API 调用） | **完整** |
| OpenSpec | 完整实现（下拉 + API 调用） | **完整** |
| GSD | 完整实现（懒加载，dialog 打开时才拉取） | **完整**（且性能更优） |

这是 Superpowers 评分低（5/10）的直接原因 —— 后端能力存在但前端没有暴露给用户。

## "零干预"的真相

Round 2 和 Round 3 都是零人工干预，Round 4 的 8 次问答是 `/gsd:new-project` 专门的问答环节（流程设计的一部分），之后几乎不再中断。这与 Superpowers 的"执行过程中随时提问"不同，GSD 是"集中决策于开始，执行阶段自主"。

- Round 2 的死代码（`if ... and False: pass`）没有用户发现
- Round 2 的 reason 被 AI 自行降级，用户不知情
- Round 3 的 Skill 简化替代，用户不知情
- Round 3 的 reason 半成品，用户不知情

::: tip 关键观察
**Superpowers 的 5 次干预全部是 AI 主动征求用户意见，不是纠偏**。GSD 的 8 次问答同样是"AI 主动征求意见"而非纠偏，且集中在专门的问答环节（不像 Superpowers 散落在执行中）。两者都内置了"关键决策点必须用户确认"的机制，而 Spec-Kit 和 OpenSpec 的流程中缺少这个机制。

如果你的项目里有"AI 不能自行做的决策"（如安全策略、付费功能、与法务相关的字段），Superpowers 或 GSD 的决策机制比另外两个更可靠。
:::

## 对工具选型的启发

| 你的工作场景 | 推荐流程 |
|---|---|
| 需求清晰、独立项目 | Spec-Kit / OpenSpec 的零干预很爽，速度快 |
| 需求模糊、协作项目 | Superpowers / GSD 的"先问再做"避免后续返工 |
| 涉及合规/敏感字段 | Superpowers / GSD 的决策点机制必备 |
| 团队/复杂项目、需要决策历程 | GSD（有文档记录的决策历程，PROJECT.md 可查） |

更多场景推荐见 [我该选哪个？](/overview/selection)

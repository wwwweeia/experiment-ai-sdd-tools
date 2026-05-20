# 我该选哪个？

> 选型不是"哪个最好"，而是"哪个最适合你当前的场景"。下表是基于四轮实验观察出的**单次结论**，请结合 [N=1 客观性声明](/overview/disclaimer) 一起看。

## 决策表

| 你的场景 | 推荐 | 原因 |
|------|---------|------|
| **需求模糊、需要澄清** | Superpowers / GSD | brainstorming / new-project 问答能主动发现歧义并征求决策 |
| **需要前后端并行开发** | Spec-Kit | API 契约文档可独立指导对接 |
| **需求明确、追求速度** | OpenSpec | 3 步完成，token 最省 |
| **团队协作、文档沉淀** | GSD / Spec-Kit | GSD 有决策记录和完整规划历程；Spec-Kit 归档体系完善 |
| **个人项目、追求效率** | OpenSpec | Context 消耗最低，流程最简 |
| **复杂业务规则、质量优先** | GSD | 测试是 plan 的一部分，41 测试 + verify step + worktree 隔离 |
| **从零构建新项目** | GSD | map-codebase → new-project → 多 phase 循环为新项目设计 |
| **在已有项目加功能** | OpenSpec / Spec-Kit | GSD 的新项目仪式对"加功能"场景代价过高 |

## 四个工具的"性格画像"

|  | Superpowers | Spec-Kit | OpenSpec | GSD |
|---|-------------|----------|----------|-----|
| **性格** | 谨慎的顾问 | 严谨的工程师 | 高效的执行者 | **正规军项目经理** |
| **核心流程** | brainstorm → spec → plan → execute | constitution → specify → plan → tasks → implement | propose → apply → archive | map → new-project → plan → execute → verify（per phase） |
| **用户角色** | 决策者（关键节点审批） | 触发者（打 slash command） | 触发者（打 slash command） | 初始问答者，之后旁观 |
| **质量保障** | 测试 + review + 设计文档（三层） | 文档完备（但实现阶段薄弱） | 流程轻量（但缺少 review 机制） | **research + plan-check + verify（每 phase）+ 独立 worktree 执行** |
| **最大优势** | 需求理解最深入（主动发现歧义） | API 契约文档质量最高 | 速度最快、Token 最省 | **测试覆盖最全、verify 最严、跨 session 可恢复** |
| **最大劣势** | 流程仪式感重，功能覆盖反而最少 | 文档冗余，implement 跳过 checkpoint | Superpowers skills 完全"悬空" | **流程最重，已有项目接入体验不佳，跨 session 带来续接成本** |

## 一个反直觉的观察

**R2 / R3 是"零人工干预"，但这不等于质量更高**。Superpowers 的 5 次干预和 GSD 的 8 次问答，全部是 AI 主动征求意见、不是纠偏。GSD 的 8 次问答集中在专门的 `/gsd:new-project` 问答环节（不像 Superpowers 散落在执行中）。零干预的 R2/R3 意味着：

- R2 的死代码 `if ... and False: pass` 没人发现
- R2 的 reason 参数被 AI 自行降级丢弃，用户不知情
- R3 的 Skill 不可用标记被 AI 简化为"间接判断"，用户不知情

所以**"流畅度"和"质量保障"是两件事**，按场景挑工具时要分开权衡。

## 工具间的互补性

四轮实验揭示了一个重要观察：**四个工具的核心能力是互补的**。

- Superpowers 的 brainstorming 质量最高（主动发现需求歧义）
- Spec-Kit 的 API 契约文档最有价值（可指导前后端并行开发）
- OpenSpec 的执行效率最高（最少 token、最快速度）
- **GSD 的工程质量最高**（测试覆盖 + verify step + 跨 session 可恢复）

如果组合使用——用 Superpowers 或 GSD 的机制澄清需求 → 用 Spec-Kit 的契约文档指导开发 → 用 OpenSpec 的效率执行——理论上可以取四者之长。但实际操作中，**工具间的"钩子"缺失**（如 Round 3 中 Superpowers skills 全程未触发、Round 4 worktree 子 agent 孤立运行等）是主要障碍。

## 下一步

- 看 [横向对比报告](/compare/) 了解每个维度的详细数据
- 看 [Round 1](/rounds/r1/) / [Round 2](/rounds/r2/) / [Round 3](/rounds/r3/) / [Round 4](/rounds/r4/) 各轮的完整笔记

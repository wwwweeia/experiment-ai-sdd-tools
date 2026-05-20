# 综合评价与启发

> 四工具的性格画像、场景推荐，以及对框架设计的启发。

## 工具性格画像

| | Superpowers | Spec-Kit | OpenSpec | R4: GSD |
|---|-------------|----------|----------|---------|
| **性格** | 谨慎的顾问 | 严谨的工程师 | 高效的执行者 | **正规军项目经理** |
| **核心流程** | brainstorm → spec → plan → execute | constitution → specify → plan → tasks → implement | propose → apply → archive | map → new-project → plan → execute → verify（per phase） |
| **用户角色** | 决策者（关键节点审批） | 触发者（打 slash command） | 触发者（打 slash command） | 初始问答者，之后旁观 |
| **质量保障** | 测试 + review + 设计文档（三层） | 文档完备（但实现阶段薄弱） | 流程轻量（但缺少 review 机制） | **research + plan-check + verify（每 phase）+ 独立 worktree 执行** |
| **最大优势** | 需求理解最深入（主动发现歧义） | API 契约文档质量最高 | 速度最快、Token 最省 | **测试覆盖最全、verify 最严、跨 session 可恢复** |
| **最大劣势** | 流程仪式感重，功能覆盖反而最少 | 文档冗余，implement 跳过 checkpoint | Superpowers skills 完全"悬空" | **流程最重，已有项目接入体验不佳，跨 session 带来续接成本** |

## 场景推荐

| 场景 | 推荐工具 | 原因 |
|------|---------|------|
| **需求模糊、需要澄清** | Superpowers / GSD | brainstorming / new-project 问答能主动发现歧义 |
| **需要前后端并行开发** | Spec-Kit | API 契约文档可独立指导对接 |
| **需求明确、快速交付** | OpenSpec | 3 步完成，速度最快 |
| **团队协作、需要文档沉淀** | GSD / Spec-Kit | GSD 有完整的规划文档和决策记录；Spec-Kit 文档结构清晰 |
| **个人项目、追求效率** | OpenSpec | Token 消耗最低，流程最简 |
| **复杂业务规则、需要质量保障** | GSD | 测试是 plan 的一部分，41 测试 + verify step + worktree 隔离 |
| **从零构建新项目** | GSD | map-codebase → new-project → 多 phase 循环为新项目设计 |
| **在已有项目加功能** | OpenSpec / Spec-Kit | GSD 的新项目仪式对"加功能"场景过重 |

## 工具间的互补性

四轮实验揭示了一个重要发现：**四个工具的核心能力是互补的，而非竞争的**。

- Superpowers 的 brainstorming 质量最高（主动发现需求歧义）
- Spec-Kit 的 API 契约文档最有价值（可指导前后端并行开发）
- OpenSpec 的执行效率最高（最少 token、最快速度）
- **GSD 的工程质量最高**（测试覆盖 + verify step + 跨 session 可恢复 + 干净 git 历史）

如果组合使用：

```
Superpowers/GSD 澄清需求    →    Spec-Kit 契约文档    →    OpenSpec 执行
 ↑ 发现歧义、决策记录              ↑ 指导前后端开发           ↑ 高效落地

或：GSD 全流程（新项目场景）
map → new-project → plan × N → execute（worktree）→ verify
 ↑ 适合复杂多 phase 新项目
```

理论上可以取四者之长。但实际操作中，**工具间的"钩子"缺失**（如 Round 3 中 Superpowers skills 完全未触发、Round 4 worktree 子 agent 等更多案例）是主要障碍。

## 对框架设计的启发

### 值得借鉴的设计

#### 1. Superpowers 的决策点机制

在 brainstorming 阶段主动向用户提问关键决策（如 Skill 标记的三选一），而非 AI 自行决定。

**应用建议**：Spec 审核环节可以加入类似的"必问清单"，比如：

- 涉及数据迁移：必问"是否需要 backfill 现有数据？"
- 涉及权限：必问"未授权场景应该 404 还是 403？"
- 涉及失败重试：必问"是否需要幂等性保障？"

#### 2. Spec-Kit 的 API 契约分离

将 API 契约文档从 spec 中独立出来，让前后端可以并行开发。

**应用建议**：在 Spec 模板中增加独立的 "API Contract" 制品类型，强制要求：

- 请求体和响应体的 JSON 示例
- 错误码与错误消息的映射表
- 字段验证规则

#### 3. OpenSpec 的 TRANSITIONS 映射表

声明式状态机设计（Round 3）比 if/elif（Round 2）和元组集合（Round 1）都更清晰。

**应用建议**：作为编码规范推荐——任何涉及状态流转的代码，应使用映射表声明合法转换。

#### 4. OpenSpec 的归档机制

变更完成后归档 + 可选同步 specs，天然支持知识沉淀。

**应用建议**：项目的"变更级归档"思路——每个功能从 proposal 到 archive 有完整的生命周期记录，未来回顾时不需要在 git log 里翻找。

#### 5. GSD 的 verify step 设计

独立 subagent 运行 verify（不由执行 agent 自我检查），产出结构化 VERIFICATION.md，区分"自动可验证"和"需要人工验证（human_needed）"两类检查项。

**应用建议**：质量保障应内置在流程中而非依赖 AI 自律 —— 独立的 verify subagent 比 "AI 自己检查自己" 更可靠。

#### 6. GSD 的 worktree 隔离

每个 execute task 在独立 git worktree 里运行，主 session 上下文不受执行细节污染。

**应用建议**：适合长周期、多 phase 项目的上下文管理。通过隔离执行环境，主 session 始终保持在"规划态"，context 不被实现细节撑爆。

### 需要避免的做法

#### 1. Spec-Kit 的文档冗余

状态机规则在 4 份文档中重复，导致 token 浪费和一致性风险。

**对策**：确保"每条规则只定义一次"，其他文档引用而非复制。

#### 2. 前三轮共同的检查点失效

无论设计多少 checkpoint，AI 倾向于一口气写完。

**对策**：用工具化 verify（GSD 方式）或自动化手段（CI 检查、测试覆盖率门禁）替代依赖 AI 自律的检查点。详见 [自主决策质量](/compare/autonomy)。

#### 3. reason 半成品模式

API 接了参数但不用，比"明确跳过"更差。

**对策**：Spec 审核应检查"API 参数是否都有对应的持久化或处理逻辑"。如果用不上，从 schema 移除。

#### 4. 工具间钩子缺失

OpenSpec 流程中 Superpowers skills 完全未触发，说明工具组合的"集成点"设计不足。

**对策**：在集成外部工具时，需要设计明确的触发条件——什么时候应该 fallback 到另一个工具的能力？

#### 5. GSD 的场景错配

GSD 的"新项目初始化仪式"对"已有项目加功能"场景代价过高。

**对策**：框架在设计入口命令时应区分"新项目"和"现有项目加功能"两种场景，提供轻量接入路径。

## 最后

这份报告基于 **N=1 的单次实验**。如果你想自己验证：

- 跑一遍试试：[复现指南](/replicate/)
- 把第 5/6 轮补上：[贡献指南](/contribute/)
- 对比哪条结论与你的体验不符？欢迎开 Issue 讨论

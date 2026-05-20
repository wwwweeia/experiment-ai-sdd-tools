# Token 效率

> 前三轮 token 消耗差异显著（91.9k–123k），但更有意思的是 token 都花在了哪里。R4 GSD 跨 session，无法直接参与对比。

## 归一化对比

| 指标 | Superpowers | Spec-Kit | OpenSpec | GSD |
|------|-------------|----------|----------|-----|
| Token 消耗 | 96.1k | 123k | **91.9k** | **不可测**（跨 session） |
| 有效代码行（后端+前端新增） | ~520 行 | ~428 行 | ~430 行 | ~740 行（不含测试）/ **1,303 行**（含测试） |
| Token / 代码行 | **185** | 287 | **214** | 不可测 |
| 业务规则完整覆盖数 | 3/5 | **4/5** | 3/5 | 4/5（Skill out-of-scope 有记录） |
| Token / 覆盖规则 | 32k | 31k | **31k** | 不可测 |
| 用户评分 | 5 | 8 | 8 | 7 |
| Token / 评分点 | **19.2k** | 15.4k | **11.5k** | 不可测 |
| 测试覆盖 | 19 个 | 0 | 0 | **41 个** |
| 跨 session 可恢复 | 否 | 否 | 否 | **是**（STATE.md 记录断点） |

R4 GSD 无法直接参与 token 效率对比，因为：（1）跨 3 个 session，每次 /clear 重置计数；（2）大量执行工作下沉到 worktree 子 agent，不体现在主 session。设计意图是把 context 压力分散，主 session 始终处于轻量的"规划态"。

## 效率解读

### Token / 代码行

Superpowers 最省（185 token/行），但部分原因是它包含了 19 个测试（278 行测试代码），这些测试代码的生成也需要 token。

### Token / 覆盖规则

三个可比工具几乎相同（31-32k/规则），**说明"理解一条业务规则"的成本是稳定的**，差异主要在流程开销。

### Token / 评分点

OpenSpec 最优（11.5k/分），Superpowers 最差（19.2k/分）。这反映了 Superpowers 的流程开销（brainstorming + 设计文档 + 实施计划 + 子代理报告）占用了大量 token，但最终功能覆盖反而最少。

## 流程开销占比

| 开销类型 | Superpowers | Spec-Kit | OpenSpec | GSD（估算） |
|---------|-------------|----------|----------|------------|
| 固定开销（System + Skills 元数据） | ~22k（23%） | ~15k（12%） | ~17k（18%） | 低（每 session 清空后重算） |
| 制品生成（设计文档 + 计划 + spec） | ~30k（31%） | ~45k（37%） | ~15k（16%） | **高**（2,500+ 行规划文档） |
| 子代理报告 | ~25k（26%） | ~5k（4%） | 0 | 高（每 plan 有 SUMMARY，verify 报告） |
| 实际编码 | ~19k（20%） | ~58k（47%） | ~60k（65%） | 中（worktree 子 agent 隔离，主 session 轻） |

GSD 通过 worktree 隔离让主 session 保持轻量，但规划制品本身密度极高，代价转移到了子 agent 上下文和 wall time。

::: warning 关键发现
- **Superpowers 只有 20% 的 token 花在实际编码上，80% 花在流程上**
- **OpenSpec 65% 的 token 用于编码，是最"高效"的**
- **Spec-Kit 47% 用于编码但 37% 用于制品生成（且有大量冗余）**
- **GSD 的 token 分散在多个 session 和 worktree 子 agent 中，单 session 成本低但 wall time 最长**
:::

## 怎么解读这些数字

token 的"省"是一把双刃剑：

- **OpenSpec 最省 token，但也意味着流程最薄** —— 流程薄就缺少安全网（没有显式 review、没有 brainstorming、没有 subagent 隔离）
- **Superpowers 最贵的部分是 subagent 报告**（26%）—— 但这恰恰是它能避免 AI 自降级的机制
- **Spec-Kit 的 37% 制品生成是冗余的根源** —— 同一条状态机规则在 spec、research、data-model、contracts 四份文档里各写一遍
- **GSD 的 token 压力被分散到多个 session** —— 单 session 轻量，但总成本（时间 + 多 session token）最高

**所以"token 效率"不是简单的"越低越好"**。如果你的需求复杂、需要质量保障，Superpowers 或 GSD 的流程开销可能值得；如果是简单 CRUD，OpenSpec 的极简流程足够。

## 前三轮 token 消耗的可视化

```
                  System开销  制品生成  子代理  实际编码
                  ─────────  ─────────  ──────  ─────────
Superpowers (96k)  ███         ████      ███     ███
Spec-Kit (123k)    ██          █████     ▌       ██████
OpenSpec  (92k)    ██          ██        —       ███████
                  ↑ Superpowers 用得最少     ↑ OpenSpec 用得最少
```

（GSD 跨 session，不纳入可视化对比）

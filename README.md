# AI 编程"SDD"工具实战对比

[![文档站](https://img.shields.io/badge/📖%20文档站-online-ea580c?style=flat-square)](https://wwwweeia.github.io/experiment-ai-sdd-tools/)

> **同一个需求、同一份基础项目**，用三个 AI 编程辅助工具（Superpowers / Spec-Kit / OpenSpec）各跑一遍，看它们在真实开发场景下到底有什么差异。
>
> 这不是一份评测，是一份**亲手跑完三轮之后的体验笔记**。带数据、带截图、带踩坑记录，也带主观感受。

**📖 文档站：[https://wwwweeia.github.io/experiment-ai-sdd-tools/](https://wwwweeia.github.io/experiment-ai-sdd-tools/)**

---

## 30 秒速览

三个工具都属于"规范驱动开发"（Spec-Driven Development）思路：让 AI 先把需求/设计想清楚再动手写代码。但它们的"想清楚"方式差异很大。

| 指标 | R1: Superpowers | R2: Spec-Kit | R3: OpenSpec |
|------|-----------------|--------------|--------------|
| **耗时** | 1h 4m | 44m | **24m** |
| **Context 消耗** | 96.1k（48%） | 123k（61%） | **91.9k（46%）** |
| **代码变更** | +2123 行 | +541 行 | +305 行 |
| **测试** | **19 个** | 0 | 0 |
| **提交数** | **11 个** | 0 | 0 |
| **文档** | 1,266 行（2 份） | 1,121 行（9 份） | 287 行（6 份） |
| **业务规则覆盖** | 4/5（1 协商跳过） | 4/5（1 AI 自降级） | 3/5（1 简化 + 1 跳过） |
| **代码缺陷** | 无 | 死代码 + reason 丢弃 | reason 半成品 |
| **人工干预** | 5 次（均为决策审批） | 0 次 | 0 次 |
| **用户主观评分** | 5/10 | 8/10 | 8/10 |

一句话评价：

- **Superpowers** — *谨慎的顾问*。三段式流程（brainstorm → plan → subagent 执行），关键节点主动征求意见，最少 token 浪费在"理解需求"上，但流程仪式感重，最终功能覆盖反而最少。
- **Spec-Kit** — *严谨的工程师*。文档驱动 5 阶段（constitution → specify → plan → tasks → implement），生成的 API 契约文档质量最高，但文档冗余严重，implement 阶段跳过 checkpoint 导致死代码未被发现。
- **OpenSpec** — *高效的执行者*。三步走（propose → apply → archive），最快最省 token，状态机设计最优雅（声明式 TRANSITIONS 映射表），但 Superpowers 集成钩子完全悬空。

---

## 我该选哪个？

| 你的场景 | 推荐 | 原因 |
|------|---------|------|
| **需求模糊、需要澄清** | Superpowers | brainstorming 阶段能主动发现歧义并征求决策 |
| **需要前后端并行开发** | Spec-Kit | API 契约文档可独立指导对接 |
| **需求明确、追求速度** | OpenSpec | 3 步完成，token 最省 |
| **团队协作、文档沉淀** | Spec-Kit | 多份文档结构清晰，归档体系完善 |
| **个人项目、追求效率** | OpenSpec | Context 消耗最低，流程最简 |
| **复杂业务规则、质量优先** | Superpowers | 测试覆盖 + 设计文档 + spec review |

> 想看更详细的差异分析？跳到 [横向对比报告](notes/comparison.md)。

---

## 5 分钟通览

### 实验方法

- **基础项目**（`base/`）：FastAPI + Vue 3 + SQLite 的 AI 智能体管理平台，已有 Model 和 Prompt 的 CRUD，但 Agent 只有数据模型没有 API。
- **共用需求**（[`requirement.md`](requirement.md)）：给 Agent 加激活/停用功能 —— 5 条业务规则、5 个 API 端点、配套前端管理页面。
- **每轮独立**：从 `base/` 复制一份干净副本（`0N-工具名/`），在该副本里开一个全新的 Claude Code session，用对应工具完成开发。**三轮之间不共享上下文**。
- **复盘方式**：每轮结束后用 [`notes/post-round-prompt.md`](notes/post-round-prompt.md) 模板让 AI 自我回顾，再人工核对代码 diff、状态栏数据、主观感受。

### 三轮观察笔记

| 轮次 | 工具 | 笔记 | 看什么 |
|------|------|------|--------|
| R1 | Superpowers | [round1-superpowers.md](notes/round1-superpowers.md) | brainstorming → 设计文档 → 子代理执行的三段式体验 |
| R2 | Spec-Kit | [round2-speckit.md](notes/round2-speckit.md) | constitution → specify → plan → tasks → implement 五阶段的文档驱动体验 |
| R3 | OpenSpec | [round3-openspec.md](notes/round3-openspec.md) | propose → apply → archive 的轻量制品流体验 |

横向对比：[notes/comparison.md](notes/comparison.md)（含状态机实现对比、Token 效率分解、决策质量对比、对框架设计的启发）

### 截图素材

三轮各自保留了完整的过程截图：

| 轮次 | 数量 | 位置 |
|------|------|------|
| R1 (Superpowers) | 17 张 | [`01-superpowers/docs/images/`](01-superpowers/docs/images/) |
| R2 (Spec-Kit) | 30 张 | [`02-speckit/specs/001-agent-status-management/images/`](02-speckit/specs/001-agent-status-management/images/) |
| R3 (OpenSpec) | 22 张 | [`03-openspec/openspec/changes/archive/2026-05-13-agent-activation/images/`](03-openspec/openspec/changes/archive/2026-05-13-agent-activation/images/) |

截图位置不一致是有意保留的 —— 每个工具会把自己的产物放在自己的目录里，这本身也是观察项目。

### AI 自我观察笔记（彩蛋）

R2 和 R3 在开发完成后，让当时的 AI 用同一份模板自我回顾了一遍。这两份"AI 的自评"和我的"人评笔记"放在一起看很有意思：

- R2 AI 自评：[`02-speckit/specs/001-agent-status-management/experiment-observation.md`](02-speckit/specs/001-agent-status-management/experiment-observation.md)
- R3 AI 自评：[`03-openspec/openspec/changes/archive/2026-05-13-agent-activation/observation-notes.md`](03-openspec/openspec/changes/archive/2026-05-13-agent-activation/observation-notes.md)

---

## 如何阅读本报告

**这是一份 N=1 的体验报告，不是评测。** 在做任何结论引用之前，请理解以下偏差来源：

### 样本与口径
- **样本量 = 1**：每个工具只跑了一次、用同一个需求、同一个操作者、同一个时间段。换需求、换人、换 AI 状态，结论可能完全不同。
- **执行顺序效应**：R1 → R2 → R3 是固定顺序，操作者对项目结构的熟悉度在变化（虽然每轮 Claude Code session 互相独立，但人不是）。
- **耗时含等待**：R1 多次人工审批本身就拉长了 wall time，不能直接等同于"工具效率"。

### 评分口径
- 用户主观评分（5/10、8/10）侧重 **"功能覆盖完整性 + 主观体验"**，**不包括** 测试覆盖率、代码工程质量评估。
- 因此 R1 拿 5/10 不是说它"工程质量差"——恰恰相反，R1 是唯一写了 19 个测试的，但它**前端缺了创建关联和删除按钮**，从"功能交付"角度扣分。

### 工具版本（实验时）
- **Superpowers**：Claude Code 插件（无独立版本号，跟随 Claude Code）
- **Spec-Kit**：v0.8.10（`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`）
- **OpenSpec**：`@fission-ai/openspec@latest`（npm 安装，2026 年 5 月时的 latest）

工具在持续迭代，这份报告的结论对未来版本的有效性会衰减。

### 一个值得警惕的现象
**R2 / R3 是"零人工干预"，但这不等于质量更高**。Superpowers 的 5 次干预全部是 AI 主动征求意见、不是纠偏。零干预意味着：
- R2 的死代码 `if ... and False: pass` 没人发现
- R2 的 reason 参数被 AI 自行降级丢弃，用户不知情
- R3 的 Skill 不可用标记被 AI 简化为"间接判断"，用户不知情

所以"流畅度"和"质量保障"是两件事，需要分开看。

---

## 完整索引

### 给读者的入口
- 📖 [横向对比报告](notes/comparison.md) —— 最完整的对比分析，从代码实现到 token 效率
- 🧪 三轮观察笔记：[R1](notes/round1-superpowers.md) · [R2](notes/round2-speckit.md) · [R3](notes/round3-openspec.md)
- 📋 [共用需求文档](requirement.md)
- 🔧 [复现指南](docs/HOW-TO-REPLICATE.md) —— 想自己跑一轮请看这里
- 🤝 [贡献指南](CONTRIBUTING.md) —— 跑新工具补充第 4/5/6 轮

### 给自己的实验档案
- 📐 [PLAN.md](PLAN.md) —— 当时立项时的实验计划（含工具安装方式、踩坑记录）
- 💬 [post-round-prompt.md](notes/post-round-prompt.md) —— 每轮复盘用的提示词模板

### 各轮产出（保留原始代码 + 工具制品）
- [`base/`](base/) —— 干净的基础项目，所有轮次的起点
- [`01-superpowers/`](01-superpowers/) —— R1 完整产出（含设计文档、实施计划、19 个测试）
- [`02-speckit/`](02-speckit/) —— R2 完整产出（含 9 份规范文档）
- [`03-openspec/`](03-openspec/) —— R3 完整产出（含 6 份 OpenSpec 制品）
- `04-tool-tbd/`、`05-tool-tbd/`、`06-tool-tbd/` —— 占位目录，等待新一轮实验（见 [CONTRIBUTING.md](CONTRIBUTING.md)）

---

## 项目结构

```
experiment-ai-sdd-tools/
├── README.md             # 你在这里
├── PLAN.md               # 实验立项计划（含工具安装方式）
├── requirement.md        # 三轮共用的需求文档
├── CLAUDE.md             # 给 Claude Code 的工作区指引
├── CONTRIBUTING.md       # 想加新一轮实验？看这里
├── base/                 # 基础项目（实验起点，不要修改）
├── 01-superpowers/       # R1: Superpowers
├── 02-speckit/           # R2: Spec-Kit
├── 03-openspec/          # R3: OpenSpec
├── 04-tool-tbd/          # 等待第 4 轮工具
├── 05-tool-tbd/          # 等待第 5 轮工具
├── 06-tool-tbd/          # 等待第 6 轮工具
├── notes/
│   ├── comparison.md          # 横向对比报告
│   ├── round1-superpowers.md  # R1 观察笔记
│   ├── round2-speckit.md      # R2 观察笔记
│   ├── round3-openspec.md     # R3 观察笔记
│   └── post-round-prompt.md   # 复盘提示词模板
└── docs/
    └── HOW-TO-REPLICATE.md    # 复现指南
```

---

## License

本项目以 MIT License 开源 —— 笔记、代码、对比报告都可以自由引用，欢迎指出错误或补充新一轮。

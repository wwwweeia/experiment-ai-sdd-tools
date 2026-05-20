# 生态扫描：多 Agent 编排平台

> 本实验对比的是**单 Agent 工作流工具**——给一个 AI agent 加流程纪律。但在真实的软件开发中，一个人同时指挥多个 agent 协作才是更大的挑战。这篇文章扫描两个开源的多 Agent 编排平台，帮你看清"AI 编程工具"这条赛道上不同层级的产品。

## 层级定位

先对齐一个坐标系。本实验测试的工具和这篇文章介绍的平台，不在同一层级：

```
┌─────────────────────────────────────────────────┐
│  多 Agent 编排平台                               │  ← Multica / HiClaw（本文介绍）
│  管理多个 agent 实例，分配任务，跟踪进度          │
├─────────────────────────────────────────────────┤
│  Agent Runtime                                  │  ← Claude Code / Codex / Copilot CLI
│  单个 agent 的运行环境，执行编码任务              │
├─────────────────────────────────────────────────┤
│  工作流插件                                      │  ← Superpowers / Spec-Kit / OpenSpec / GSD
│  给 agent runtime 加流程纪律                     │  （本实验 R1–R5 测试的品类）
└─────────────────────────────────────────────────┘
```

本实验的 R1–R4 是第三层的插件（给 Claude Code 加流程），R5（GSD-2）是跨层（独立 runtime + 自带工作流）。而 Multica 和 HiClaw 是最上层——它们**管理多个 runtime 实例**，让人类像带团队一样指挥一群 AI agent。

---

## Multica：Agent 即员工，看板驱动

**仓库**：[multica-ai/multica](https://github.com/multica-ai/multica)

**一句话**：开源的 Managed Agents 平台——把编码 agent 变成看板上的"虚拟员工"，分配 issue、跟踪进度、积累技能。

### 核心理念

Multica 的隐喻是**项目管理工具**（Jira / Linear）。Agent 是看板上的一个成员，有档案、能被分配 issue、会自主干活并更新状态。

```
你在 Multica Web 端创建 issue → 分配给 Agent
Agent 在你的机器上（通过 daemon）执行任务
Agent 自动更新 issue 状态、提交代码、报告阻塞
```

### 架构

```
Next.js 前端  →  Go 后端 (Chi + WebSocket)  →  PostgreSQL (pgvector)
                        ↓
                 Agent Daemon（跑在你的机器上）
                 检测已安装的 Agent CLI：
                 Claude Code / Codex / Copilot CLI / Gemini / Kimi / ...
```

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| 前端 | Next.js 16 (App Router) | 看板视图 + 设置面板 |
| 后端 | Go (Chi + sqlc + gorilla/websocket) | REST + WebSocket 实时推送 |
| 数据库 | PostgreSQL 17 + pgvector | 结构化数据 + 向量搜索 |
| Agent 运行时 | 本地 daemon | 检测 PATH 中可用的 agent CLI |

### 关键特性

| 特性 | 说明 |
|------|------|
| **Agent 即队友** | 有个人档案、出现在看板上、能评论/创建 issue、报告阻塞 |
| **Squads（小队）** | 多个 agent 组队，leader agent 负责路由——用 `@前端组` 代替 `@小张或小李或小王` |
| **自主执行** | 完整任务生命周期：排队→认领→执行→完成/失败，WebSocket 实时推送 |
| **可复用技能** | 每个解决方案沉淀为团队可复用的 skill，能力随时间增长 |
| **多工作区** | 团队级别隔离，每个工作区独立的 Agent、Issue 和设置 |

### 快速上手

```bash
# 安装（macOS Homebrew）
brew install multica-ai/tap/multica

# 一条命令完成配置、认证、启动 daemon
multica setup

# 自部署（需要 Docker）
curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash -s -- --with-server
multica setup self-host
```

### 适用场景

- 小团队（2–5 人）想让 AI agent 补充人力
- 已有 GitHub issue 驱动的开发流程，想让 agent 自动认领任务
- 需要同时使用多种 agent runtime（Claude Code + Codex + Gemini 混用）
- 看板式的任务管理更符合团队习惯

---

## HiClaw：Agent 即队友，聊天室驱动

**仓库**：[agentscope-ai/HiClaw](https://github.com/agentscope-ai/HiClaw)

**一句话**：通过 Matrix 聊天室协调多个 AI agent 的协作 OS——你和 Manager agent 对话，Manager 派活给 Worker，全程透明可介入。

### 核心理念

HiClaw 的隐喻是**群聊协作**（Slack / Discord）。每个 Worker agent 有自己的 Matrix 聊天室，你、Manager 和 Worker 都在同一个房间里，所有对话透明可见，你可以随时插话干预。

```
你：Create a Worker named alice for frontend development
Manager：Done. Worker alice is ready. Room: Worker: Alice

你：@alice implement a login page with React
Alice：On it... [几分钟后] Done. PR submitted: https://github.com/xxx/pull/1

你：@bob wait, change the password rule to minimum 8 chars
Bob：Got it, updated.
Alice：Frontend validation updated too.
```

### 架构

```
你 (Element Web)
  ↕ Matrix 协议
Manager Agent
  ↕ Matrix 房间（每个 Worker 一个房间，你也在里面）
Worker Alice (OpenClaw)    Worker Bob (Hermes)
  ↕                           ↕
Higress AI Gateway ← 统一管理所有 API Key / GitHub PAT
  ↕
LLM API / GitHub API / MCP Servers
```

| 组件 | 作用 |
|------|------|
| **Higress AI Gateway** | 凭证网关——Worker 只拿 consumer token，真密钥不暴露给 agent |
| **Tuwunel** | 自建 Matrix IM 服务器 |
| **Element Web** | 浏览器端 Matrix 客户端，零配置 |
| **MinIO** | Agent 间共享文件系统，Worker 无状态 |
| **hiclaw-controller** | Go 写的 K8s 原生编排器（Helm + CRD） |

### 关键特性

| 特性 | 说明 |
|------|------|
| **Manager-Workers 架构** | Manager agent 负责理解需求、创建 Worker、分配任务 |
| **聊天室透明** | 所有 agent 间对话都在 Matrix 房间里，人类随时可见可介入 |
| **凭证隔离** | Worker 只持有 consumer token，真密钥锁在 Higress 网关里 |
| **多 Worker runtime** | OpenClaw / CoPaw / Hermes / NanoClaw / ZeroClaw，按需选择 |
| **K8s 原生** | Helm chart + CRD，生产级部署 |
| **一条命令部署** | `curl \| bash` 启动全套（网关 + IM + MinIO + Agent） |

### 快速上手

```bash
# 安装（需要 Docker Desktop）
# macOS / Linux
bash <(curl -sSL https://higress.ai/hiclaw/install.sh)

# 打开浏览器访问 Element Web
open http://127.0.0.1:18088
# Manager 会在聊天中引导你创建第一个 Worker
```

### 适用场景

- 偏好聊天式工作方式，习惯 Slack/Teams 风格的协作
- 需要强凭证隔离（企业安全合规要求）
- 已有 K8s 基础设施，需要生产级多 agent 部署
- 移动端访问需求（任意 Matrix 客户端即可接入）
- 需要随时观察和介入 agent 的工作过程

---

## 横向对比

| 维度 | Multica | HiClaw |
|------|---------|--------|
| **交互隐喻** | 看板（Jira / Linear） | 聊天室（Slack / Discord） |
| **Agent 发现** | Daemon 自动检测本机已装的 CLI | Manager 对话式创建 Worker |
| **凭证管理** | 未明确 | Higress 网关隔离，Worker 只见 consumer token |
| **通信协议** | 自有 WebSocket | Matrix 开放协议（可联邦、可桥接） |
| **部署形态** | CLI + Cloud / Docker 自部署 | Docker 全家桶一键部署 |
| **编排能力** | Squads（小队路由） | Manager-Workers（对话式调度） |
| **支持 Agent** | Claude Code, Codex, Copilot CLI, Gemini, Kimi 等 11 种 | OpenClaw, CoPaw, Hermes, NanoClaw, ZeroClaw |
| **文件共享** | 未明确 | MinIO 共享文件系统 |
| **后端语言** | Go | Go（controller）+ Python（agent） |
| **数据存储** | PostgreSQL + pgvector | MinIO + Matrix 状态 |
| **移动端** | Web 响应式 | 原生 Matrix 客户端支持 |
| **License** | Apache 2.0 | Apache 2.0 |

### 共同点

1. **Agent 是一级团队成员**，不是被调用的工具
2. **人类随时可介入**，不是全自动黑箱
3. **可自部署**，不锁定云服务
4. **关注凭证安全**，不让 agent 直接持有敏感密钥
5. **任务生命周期管理**，从分配到完成有完整的状态跟踪

### 核心差异

**交互模式**是最根本的差异——决定了你和 AI 团队的日常协作方式：

- **Multica**：你把任务写在看板上，Agent 自己去认领和完成。适合"异步协作"风格，信任 agent 自主工作，偶尔检查进度。
- **HiClaw**：你在聊天室里直接对话，实时观察每个 agent 的思考和行动。适合"实时协作"风格，想要全程可见可控。

这不是谁好谁坏的问题，而是**工作风格的偏好**。

---

## 与本实验的关系

本实验测试的工具（Superpowers / Spec-Kit / OpenSpec / GSD）和这两个平台解决的是**不同层级的问题**：

| 层级 | 解决什么 | 代表产品 |
|------|---------|---------|
| **工作流插件** | 单 agent 写代码时的流程纪律 | Superpowers, Spec-Kit, OpenSpec, GSD（本实验） |
| **Agent Runtime** | 单个 agent 的运行环境 | Claude Code, Codex, Copilot CLI |
| **多 Agent 编排** | 一个人指挥多个 agent 协作 | Multica, HiClaw（本文） |

一个可能的未来是三层叠加：用 Multica/HiClaw 编排多个 agent，每个 agent 用 Claude Code/Codex 运行，运行时加上 Superpowers/Spec-Kit 的工作流纪律。

但这也意味着**复杂性爆炸**——本实验中单 agent + 工作流插件就出现了各种质量问题（需求自降级、前端功能缺失），多 agent 编排的协调成本会更高。

---

## 链接

- **Multica**：[GitHub](https://github.com/multica-ai/multica) · [官网](https://multica.ai)
- **HiClaw**：[GitHub](https://github.com/agentscope-ai/HiClaw)

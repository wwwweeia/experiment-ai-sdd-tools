# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AI 编程工具对比实验工作区

## 这是什么

这是一个 AI 编程工具的实战对比实验。用**同一个需求、同一套基础项目**，分别用不同的 AI 工具来完成开发，然后横向对比各工具的实际表现。

## 实验方法

1. **基础项目**：`base/` — FastAPI + Vue 3 + SQLite 的 AI 智能体管理平台，已有 Model/Prompt CRUD，Agent 只有数据模型没有 API
2. **需求**：`requirement.md` — Agent 激活/停用功能（5 条业务规则、5 个 API 端点、前端管理页面）
3. **每轮实验**：复制 base 到 `0N-工具名/`，在该目录用 Claude Code + 待测工具完成开发
4. **复盘**：用 `notes/post-round-prompt.md` 的模板让 AI 自我分析，结合代码 diff 和状态栏数据整理观察笔记
5. **对比**：汇总到 `notes/comparison.md`

## 目录结构

```
base/                  # 干净的基础项目（实验起点，不要修改）
01-superpowers/        # Round 1: Superpowers — 已完成
02-speckit/            # Round 2: Spec-Kit — 已完成
03-openspec/           # Round 3: OpenSpec — 已完成
04-get-shit-done/      # Round 4: get-shit-done (gsd-build/get-shit-done) — 待跑
05-gsd-2/              # Round 5: GSD-2 (gsd-build/gsd-2) — 待跑（独立 CLI，非 Claude Code 插件）
06-tool-tbd/           # Round 6: 待定
notes/                 # 实验笔记
├── round1-superpowers.md   # Round 1 观察笔记
├── round2-speckit.md       # Round 2 观察笔记
├── round3-openspec.md      # Round 3 观察笔记
├── comparison.md           # 对比报告（前三轮已写，待补 R4/R5）
└── post-round-prompt.md    # 每轮复盘用的提示词模板
PLAN.md            # 实验计划
requirement.md     # 共用需求文档
```

## 已完成/计划中的实验

| 轮次 | 工具 | 耗时 | Context | 评分 | 关键特征 |
|------|------|------|---------|------|---------|
| R1 | Superpowers | 1h 4m | 96.1k (48%) | 5/10 | 流程严谨（brainstorm→plan→subagent）、19 个测试、11 次提交，但前端功能缺失（无创建关联、无删除） |
| R2 | Spec-Kit | 44m | 123k (61%) | 8/10 | 文档驱动 5 阶段、功能最完整（有 is_active、时间戳），但有死代码、AI 自行降级需求 |
| R3 | OpenSpec | 24m | 91.9k (46%) | 8/10 | 最快、最省 token、状态机设计最好（TRANSITIONS 映射表）、joinedload 优化，但 Superpowers 全程未触发 |
| R4 | get-shit-done | — | — | — | Claude Code 插件；子 agent 并行执行；62k stars；安装：`npx get-shit-done-cc@latest` |
| R5 | GSD-2 | — | — | — | **独立 CLI**（非 Claude Code 插件）；有 TUI/SQLite/worktree；安装：`npm i -g gsd-pi@latest` |

> **R4 vs R5 架构差异**：R4（get-shit-done）是 Claude Code 的 slash command 框架（同类于前三轮），R5（GSD-2）是完全不同的独立 agent 系统，替代 Claude Code 本身作为 runner。

## 新一轮实验的操作流程

### 1. 准备

```bash
# 确定工具名后改名
mv 04-tool-tbd 04-工具名

# 进入项目目录初始化工具（如果需要）
cd 04-工具名
# 按工具文档进行初始化...
```

### 2. 执行实验

- `cd 04-工具名 && claude` 启动新的 Claude Code session
- 把 `requirement.md` 内容发给 AI，让工具按自己的流程完成开发
- 用户尽量不干预，只在工具要求时做最少量的交互
- 记录状态栏数据（耗时、token 消耗）

### 3. 复盘

开发完成后，在同一 session 中用 `notes/post-round-prompt.md` 的模板让 AI 回顾对话，整理观察笔记。然后在外部 session（即本目录）中结合以下信息产出最终笔记：

- AI 自我分析的观察笔记（在 `0N-工具名/` 项目内）
- `git diff` 查看代码变更
- 状态栏的 token/耗时数据
- 用户的主观感受和评分

### 4. 笔记产出

产出 `notes/roundN-工具名.md`，结构与前几轮一致：
- 基本信息（耗时、context、技能使用）
- 需求理解（5 条业务规则逐条检查）
- 开发过程（工作流、人工干预、关键决策）
- 产出质量（后端/前端/文档）
- 工具体验（流畅度/自然度/安心感）
- 上下文使用分析

### 5. 更新对比报告

将新轮次数据补充到 `notes/comparison.md`。

## 注意事项

- **base/ 不要修改** — 它是所有轮次的起点
- **每轮独立 session** — 不同轮次之间不共享上下文
- **三轮已完成的项目不要动** — 保留原始代码用于对比
- **需求不变** — 所有轮次用同一份 `requirement.md`

---

## 开发命令

每个实验子目录（`0N-工具名/`）都有相同的目录结构，命令格式统一：

```bash
# 启动后端（任意一轮）
cd {round}/backend && pip install -r requirements.txt && uvicorn app.main:app --reload
# API 文档: http://localhost:8000/docs

# 启动前端
cd {round}/frontend && npm install && npm run dev
# 前端: http://localhost:5173

# 运行后端测试
cd {round}/backend && pytest

# 运行单个测试文件
cd {round}/backend && pytest tests/test_agent_api.py -v

# 比较两轮后端代码差异
diff -r 01-superpowers/backend 02-speckit/backend --exclude="*.pyc" --exclude="*.db"

# 比较两轮前端代码差异
diff -r 01-superpowers/frontend/src 02-speckit/frontend/src
```

---

## Base 项目架构

`base/` 是所有轮次的起点。了解其模式对阅读各轮产出很重要。

### 后端分层（FastAPI + SQLAlchemy 2.x）

```
app/
├── main.py              # FastAPI 入口，建表 + 注册路由 + CORS
├── core/
│   ├── database.py      # SQLite engine + SessionLocal + get_db 依赖
│   └── config.py        # 常量（PROJECT_NAME, API_PREFIX 等）
├── models/entity.py     # SQLAlchemy ORM 模型（Model, Prompt, Agent, Skill）
├── schemas/schema.py    # Pydantic v2 schemas + 通用响应包装
├── services/            # 业务逻辑层（XxxService(db) 构造函数模式）
└── api/v1/
    ├── endpoints.py     # 路由处理函数（每个实体一个 APIRouter）
    └── router.py        # 汇总注册所有路由
```

**关键模式：**

- **统一响应体**：所有端点返回 `Response[T]`（`code=0`, `data`, `message="success"`），定义在 `schemas/schema.py`
- **Service 层**：`XxxService(db)` 接收 Session，封装所有 DB 操作；端点层只负责 HTTP 层转换
- **路由注册**：新增实体需在 `endpoints.py` 创建 `xxx_router = APIRouter()`，并在 `router.py` 用 `include_router` 注册

### Agent 数据模型（base 里已有，无 API）

`AgentStatus` 枚举：`DRAFT / ACTIVE / INACTIVE`（值为小写字符串）  
`Agent` 模型：关联 `model_id → Model`、`prompt_id → Prompt`、反向关联 `skills → Skill[]`

### 前端分层（Vue 3 + Pinia + Element Plus）

```
src/
├── api/          # axios 封装（prompts.js 是参考模式，返回 response.data.data）
├── stores/       # Pinia stores（prompt.js 调用 api/ 并管理列表状态）
├── views/        # Vue 3 Composition API 页面组件
│   ├── PromptList.vue   # 参考模式：列表 + 创建表单 + 删除
│   └── AgentList.vue    # 各轮实验需完善的占位页面
└── router/index.js      # Agent 路由已注册（/agents）
```

**参考模式**：`PromptList.vue` + `stores/prompt.js` + `api/prompts.js` 是三层联动的完整示例，AI 工具应以此作为 Agent 功能的实现参考。

# 三工具实战体验计划：Spec-Kit / OpenSpec / Superpowers

## Context

阿威已经了解了三个 AI 编程工具（Spec-Kit、OpenSpec、Superpowers）的概念，但缺乏亲手实践的经验。希望通过在 demo 项目中用同一个功能需求分别跑三轮，从"无约束"到"严格规范"渐进体验，内化方法论并产出对比报告，同时为 h-codeflow-framework 寻找设计灵感。

## 需求场景：Agent 激活/停用

**当前状态**：Agent 模型已有 status 枚举（DRAFT/ACTIVE/INACTIVE），但没有激活/停用的业务逻辑、API 和前端 UI。已有 Prompt CRUD API 和前端对接作为参考模式。

**功能需求**：
- 后端：Agent 状态切换 API + 业务规则验证
- 前端：Agent 管理页面，含状态切换操作和规则提示

**业务规则**：
1. DRAFT → ACTIVE：必须已关联 Model 和 Prompt
2. ACTIVE → INACTIVE：直接切换，关联的 Skill 标记为不可用
3. INACTIVE → ACTIVE：重新检查 Model 和 Prompt 是否仍有效
4. ACTIVE 状态的 Agent 不能被删除
5. 状态变更记录操作时间和原因（可选）

---

## 阶段 1：准备实验基地 ✅ 已完成

### 1.1 从 demo 抽离基础项目 ✅

从 `demo/` 复制出一份干净的 FastAPI + Vue 3 项目，目录 `~/experiment-ai-tools/base/`。

### 1.2 复制三份实验项目 ✅

- `01-superpowers/` — Superpowers 单独
- `02-speckit/` — Spec-Kit + Superpowers
- `03-openspec/` — OpenSpec + Superpowers

### 1.3 写中立的需求文档 ✅

`~/experiment-ai-tools/requirement.md`，三轮共用。

### 1.4 安装工具 ✅

- Spec-Kit（Python）：`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- OpenSpec（Node.js）：`npm install -g @fission-ai/openspec@latest`
- Superpowers：Claude Code 插件，已安装

### 1.5 各项目初始化工具 ✅

- `01-superpowers/`：无额外初始化，Superpowers 通过插件自动生效
- `02-speckit/`：`specify init . --integration claude`（注意：`--ai` 参数已废弃）
- `03-openspec/`：`openspec init --tools claude`（注意：必须指定 `--tools`）

### 1.6 创建笔记目录 ✅

`~/experiment-ai-tools/notes/`

### 1.7 补强基础项目 ✅

为三个实验项目补充了必要的基础设施，确保实验公平性：

- **后端**：实现 Prompt CRUD API（PromptService + 端点 + 路由注册），作为 Agent 激活时的前置依赖
- **前端**：Prompt store 从 mock 改为真实 API 调用，修正前后端对接的参考模式
- **前端**：路由和导航添加 Agent 管理入口（最小占位页面），给 AI 提示页面位置

### 1.8 各项目 CLAUDE.md ✅

每个实验项目的 CLAUDE.md 包含：项目结构、启动命令、已实现功能、业务规则。02-speckit 额外包含 Spec-Kit 的 header block。

### 1.9 Git 初始化 ✅

四个项目各自有独立 git 仓库和初始提交，便于审计和回溯。

---

## 阶段 2：三轮实验（各自独立的 Claude Code session）

> **重要**：每轮开一个新的 Claude Code 窗口，互不干扰。每轮结束后立刻记录感受。

### 每轮开始前检查清单

1. 确认目录正确：`cd ~/experiment-ai-tools/0X-xxx`
2. 启动后端：`cd backend && uvicorn app.main:app --reload`
3. 启动前端：`cd frontend && npm run dev`
4. 确认基础功能正常（首页统计、Prompt 列表页、Agent 导航可见）
5. 打开 `requirement.md`，准备发送给 AI

---

### 第 1 轮：Superpowers 单独（01-superpowers/）

**启动**：`cd ~/experiment-ai-tools/01-superpowers && claude`

**目标**：体验没有规范约束时，AI 靠执行方法论能做到什么程度。

**步骤**：
1. 打开 Claude Code，进入 `01-superpowers/` 目录
2. 把 `requirement.md` 的内容作为自然语言需求发给 AI
3. 让 Superpowers 自动选择技能（预期触发 brainstorming → TDD / subagent-driven-development）
4. 中途允许参考文档（遇到卡点可以查 Superpowers 文档）
5. 跑到功能完成为止

**观察记录**：
- AI 是否遗漏了业务规则？哪些规则被漏掉了？
- 是否出现了"vibe coding"（凭感觉写）？
- 代码质量如何？测试覆盖如何？
- 过程中需要人工干预几次？干预的是什么？
- 从开始到完成的总耗时

**关注点**：自由度最高，但也最容易跑偏。重点体验"没有规范护栏"时 AI 的实际表现。

---

### 第 2 轮：Spec-Kit + Superpowers（02-speckit/）

**启动**：`cd ~/experiment-ai-tools/02-speckit && claude`

**目标**：体验严格分阶段规范 + TDD 执行。

**步骤**：
1. 进入 `02-speckit/`，确认 `.specify/` 目录已生成
2. Spec-Kit 分阶段流程：
   ```
   /speckit.constitution → 项目宪法（代码质量、测试标准、安全约束）
   /speckit.specify      → Agent 激活/停用的功能规范（what & why）
   /speckit.plan         → 技术方案（API 设计、状态机、数据模型变更）
   /speckit.tasks        → 任务分解
   /speckit.implement    → Superpowers TDD 执行
   ```
3. 每个阶段完成后，观察 AI 的产出质量
4. 可以尝试 `/speckit.clarify` 和 `/speckit.analyze` 看看效果

**观察记录**：
- constitution 阶段是否真的有价值？还是走过场？
- specify 和 plan 的产出质量如何？是否帮助 AI 更好理解需求？
- 严格阶段流程是否拖慢了节奏？
- 相比第 1 轮，最终代码质量差异有多大？
- 从开始到完成的总耗时

**关注点**：规范最严格。重点体验"先想清楚再动手"的实际体感 — 是安心还是繁琐？

---

### 第 3 轮：OpenSpec + Superpowers（03-openspec/）

**启动**：`cd ~/experiment-ai-tools/03-openspec && claude`

**目标**：体验轻量灵活的规范 + TDD 执行。

**步骤**：
1. 进入 `03-openspec/`，确认 `openspec/` 目录已生成
2. OpenSpec 流程（4 个核心命令）：
   ```
   /opsx:explore   → 探索模式 — 纯思考，不写代码，讨论想法、分析问题（可选前置）
   /opsx:propose   → 提变更 — 描述需求，自动生成 proposal.md → design.md → tasks.md 全套制品
   /opsx:apply     → 执行实现 — 按 tasks.md 逐条完成编码任务
   /opsx:archive   → 归档 — 完成后归档变更，可选同步 delta specs 到主规格
   ```
3. 典型流程：`/opsx:explore`（想清楚）→ `/opsx:propose`（生成制品）→ `/opsx:apply`（实现）→ `/opsx:archive`（归档）

**观察记录**：
- 相比 Spec-Kit，少了哪些环节？省下来的时间值得吗？
- propose 一步生成全套制品 vs Spec-Kit 的分阶段，哪个更高效？
- proposal + design + tasks 三文件 vs Spec-Kit 的 9 份文档，哪个更好维护？
- 归档功能对知识沉淀的价值？
- explore 模式是否有实际价值，还是直接 propose 更快？
- 从开始到完成的总耗时

**关注点**：灵活与规范的平衡。重点对比跟第 2 轮的差异 — 省了什么、缺了什么。

---

## 阶段 3：复盘与产出

### 对比维度

| 维度 | 关注点 |
|------|--------|
| 安装体验 | 哪个最顺畅？踩了什么坑？ |
| 工作流体感 | 哪个最自然？哪个最别扭？ |
| 需求理解质量 | 哪个让 AI 最准确地理解了业务规则？ |
| 产出质量 | 最终代码、测试覆盖、文档完整度 |
| 时间投入 | ROI 如何？多花的时间值不值？ |
| 适用场景 | 各自适合什么样的项目/团队？ |
| 框架灵感 | 哪些设计可以借鉴到 h-codeflow-framework？ |

### 产出物

```
~/experiment-ai-tools/
├── notes/
│   ├── round1-superpowers.md      # 第 1 轮观察笔记
│   ├── round2-speckit.md          # 第 2 轮观察笔记
│   ├── round3-openspec.md         # 第 3 轮观察笔记
│   └── comparison.md              # 最终对比总结
├── requirement.md                  # 共用需求文档
├── PLAN.md                         # 本计划
├── base/                           # 基础项目（备份）
├── 01-superpowers/                 # 第 1 轮代码（保留）
├── 02-speckit/                     # 第 2 轮代码（保留）
└── 03-openspec/                    # 第 3 轮代码（保留）
```

### 对比方法

三轮跑完后，可以：
- `diff -r 01-superpowers/backend 02-speckit/backend` 看代码差异
- `diff -r 01-superpowers/backend 03-openspec/backend` 看代码差异
- 对比三份 .specify/ 和 .openspec/ 里的规范文档，看哪个对需求理解最准确

---

## 注意事项

1. **不用 h-codeflow-framework 的 Agent 流程**：三个实验项目中没有我们的 PM/Arch/Dev 角色。注意 02-speckit 和 03-openspec 的 `.claude/skills/` 是工具自带的（Spec-Kit/OpenSpec 的 Claude 集成），不是我们的框架
2. **允许中途参考文档**：遇到卡点可以查工具官方文档或 GitHub README
3. **每轮独立 session**：不共享上下文，避免"剧透"
4. **记录当下的感受**：不要等全部跑完再回忆，每轮结束立刻写笔记
5. **保持同一份需求**：三轮用完全相同的需求描述，只改工具组合
6. **不强求一轮跑完**：每轮可以跨多个 session，累了就休息

## 当前项目参考文件

| 文件 | 作用 |
|------|------|
| `base/backend/app/models/entity.py` | 数据模型定义（Agent 含 status 枚举） |
| `base/backend/app/api/v1/endpoints.py` | API 端点（Model + Prompt CRUD 参考） |
| `base/backend/app/services/` | 业务逻辑层（ModelService + PromptService 参考） |
| `base/backend/app/schemas/schema.py` | Pydantic schemas（含 AgentCreate/AgentRead） |
| `base/frontend/src/views/` | Vue 页面组件（PromptList 参考模式） |
| `base/frontend/src/stores/` | Pinia stores（prompt.js 对接 API 参考） |
| `base/frontend/src/api/` | HTTP 客户端（prompts.js 参考） |
| `base/frontend/src/views/AgentList.vue` | Agent 最小占位页面（待 AI 完善） |

## 验证方式

- 每轮完成后，启动 backend 和 frontend，手动验证 Agent 状态切换功能
- 后端：`curl -X PATCH localhost:8000/api/v1/agents/{id}/status` 测试 API
- 前端：浏览器访问 Agent 管理页面，测试 UI 交互
- E2E：如果 AI 写了 Playwright 测试，运行验证
    
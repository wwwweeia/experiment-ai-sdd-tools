# 复现指南：自己跑一轮实验

这份指南告诉你怎么用本仓库的素材**自己亲手跑一遍**。"纸上得来终觉浅，绝知此事要躬行" —— 看笔记和亲手跑过的差距，比想象中大。

> 适合谁看：想验证三轮笔记的结论、想自己感受一下这些工具、想给团队选型前先试一下、或者想给本仓库补一轮新工具的人。

---

## 前置条件

| 需要什么 | 怎么装 |
|---------|--------|
| **Claude Code** | https://docs.claude.com/en/docs/claude-code/quickstart |
| **Python ≥ 3.10** + **pip** | macOS 自带或 `brew install python` |
| **Node.js ≥ 18** + **npm** | https://nodejs.org 或 `brew install node` |
| **uv**（仅 Spec-Kit 需要） | `pip install uv` 或 `brew install uv` |

---

## 准备实验环境

### 1. 克隆仓库

```bash
git clone https://github.com/<your-account>/experiment-ai-sdd-tools.git
cd experiment-ai-sdd-tools
```

### 2. 选一个空闲的轮次目录

仓库里有 3 个占位：`04-tool-tbd/`、`05-tool-tbd/`、`06-tool-tbd/`。它们都是从 `base/` 复制的干净副本。

```bash
# 假设你要跑第 4 轮，工具叫 mytool
mv 04-tool-tbd 04-mytool
cd 04-mytool
```

> 如果占位都用完了，可以再复制一份：`cp -r base 04-mytool`

### 3. 验证基础项目能跑起来

在 `04-mytool/` 里启动后端和前端，确认 base 状态正常：

```bash
# 终端 1：后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# API 文档: http://localhost:8000/docs

# 终端 2：前端
cd frontend
npm install
npm run dev
# 前端: http://localhost:5173
```

打开浏览器访问 `http://localhost:5173`，确认能看到首页统计、Prompt 列表、Agent 占位页面。

---

## 安装工具

按你要测的工具选其一（或都装）：

### Superpowers（Claude Code 插件）

在 Claude Code 中安装 Superpowers 插件。本实验中它**通过 `using-superpowers` skill 自动加载**，无需额外初始化。

### Spec-Kit

```bash
# 全局安装
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 在轮次目录里初始化
cd 04-mytool
specify init . --integration claude
```

> 注意：`--ai` 参数已废弃，必须用 `--integration claude`。

### OpenSpec

```bash
# 全局安装
npm install -g @fission-ai/openspec@latest

# 在轮次目录里初始化
cd 04-mytool
openspec init --tools claude
```

> 注意：`--tools` 是必填参数。

### 其他你想测的工具

照该工具的官方文档装。建议挑"规范驱动"或"AI 编程辅助"类工具，跟现有三轮可比性强。

---

## 执行实验

### 1. 启动一个全新的 Claude Code session

**关键**：必须是独立的新 session，**不能复用之前的对话上下文**。否则会"剧透"。

```bash
cd 04-mytool
claude
```

### 2. 把需求文档发给 AI

打开 [`requirement.md`](../requirement.md)，把完整内容复制给 AI。**只发需求文本，不要告诉它任何"工具该怎么用"** —— 让工具/AI 按自己的流程走。

如果工具有特定 slash command（如 `/speckit.constitution`），可以手动触发。但**不要主动指导 AI 怎么做**。

### 3. 让 AI 跑完整个需求

- 用户尽量不干预
- 工具需要决策时（比如方案选择、需求澄清），如实回答，不要替它做技术选择
- 记录下：
  - **从第一句对话到功能完成的 wall time**
  - **Claude Code 状态栏的 token 消耗**（实验过程中观察并记录最终值）
  - **每次手动触发的 slash command**
  - **每次主动干预的内容**（不算"OK/继续"的纯确认）

### 4. 完成后手动验证

启动后端和前端，按 `requirement.md` 的 5 条业务规则逐条手测：

```bash
# 后端 API 测试
curl -X PATCH http://localhost:8000/api/v1/agents/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE", "reason": "测试激活"}'

# 浏览器：http://localhost:5173/agents 手测 UI
```

如果 AI 写了测试，跑一下：

```bash
cd backend && pytest
```

---

## 复盘与笔记

### 1. 在同一 session 里让 AI 自我回顾

把 [`notes/post-round-prompt.md`](../notes/post-round-prompt.md) 的完整内容粘贴给 AI（替换 `[第 N 轮]` 和 `[工具名称]`）。

AI 会基于完整对话历史，按统一模板产出一份观察笔记（含基本信息、需求覆盖、工作流、决策点、上下文使用、主观评分等）。

**把 AI 自评的笔记保存在该轮次目录内**（比如 `04-mytool/observation-notes.md`），这是宝贵素材，跟"人评笔记"对照看很有意思。

### 2. 在外部 session（仓库根目录）里写最终笔记

退出实验 session，另开一个 Claude Code 在仓库根目录运行：

```bash
cd experiment-ai-sdd-tools
claude
```

让 AI 帮你结合以下材料整理最终笔记：

- AI 自评笔记（在轮次目录里）
- 代码 diff：`git diff base/ 04-mytool/`
- 你记录的状态栏数据（耗时、token）
- 你的主观感受和评分

参考前三轮的笔记结构（`notes/roundN-工具名.md`），保持一致性。

### 3. 推荐保存路径

```
notes/round4-mytool.md              # 最终观察笔记
04-mytool/observation-notes.md       # AI 自评原始记录
04-mytool/docs/images/               # 过程截图（建议命名 04-mytool-NN.png）
```

### 4. 更新对比报告

把新一轮的数据补到 [`notes/comparison.md`](../notes/comparison.md) 的概览表里，并视情况扩展其他对比维度。

---

## 注意事项

### 公平性
- **base/ 不要修改** —— 它是所有轮次的起点，污染了会破坏对比
- **三轮已完成的项目不要动**（`01-superpowers/`、`02-speckit/`、`03-openspec/`）—— 保留原始代码用于对比
- **需求不变** —— 用同一份 `requirement.md`，不要"按需调整"

### 客观性
- 第一次跑某工具难免不熟悉，**至少跑 2 次取后者** 可以减少学习成本干扰（但本仓库的三轮原始数据就是首次跑的，没做这个矫正）
- 记录工具版本号（在笔记顶部速览盒子里写清楚）
- 承认主观成分，不要假装在做"评测"

### 当心 AI 自评的偏差
AI 自评虽然有 post-round-prompt 模板约束，但 AI 倾向于：
- 美化自己的产出（比如把"AI 自行降级需求"说成"合理的简化决策"）
- 漏报失败的尝试
- 给自己的评分偏高

所以**人评是必须的**，AI 自评只是辅助素材。

---

## 想做更深入的对比？

可以参考 [`notes/comparison.md`](../notes/comparison.md) 的对比维度：

- 状态机实现差异
- 错误处理模式
- 数据加载策略（N+1 查询）
- Schema 设计模式
- 任务分解粒度
- 检查点设计 vs 实际执行
- Token 效率分解（系统开销 / 制品生成 / 子代理 / 实际编码）
- 自主决策质量

每个维度都可以单独写一篇深度对比。

---

跑完了？欢迎把笔记 PR 回本仓库 —— 看 [CONTRIBUTING.md](../CONTRIBUTING.md)。

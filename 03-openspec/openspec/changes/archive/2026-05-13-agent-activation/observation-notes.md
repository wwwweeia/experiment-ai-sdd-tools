# 第 3 轮实验观察：OpenSpec + Superpowers（Superpowers 未实际触发）

## 基本信息
- **工具组合**：OpenSpec（主导）+ Claude Code 内置 TaskCreate/TaskUpdate + Superpowers（已安装但未触发任何 skill）
- **开发耗时**：约 10-15 分钟（从用户发出 `/opsx:propose` 到 archive 完成）
- **使用的技能/命令**：
  1. `/opsx:propose`（用户手动调用）— 触发 OpenSpec propose 流程，生成 proposal → design → specs → tasks 四类制品
  2. `/opsx:apply`（用户手动调用）— 触发 OpenSpec apply 流程，按 tasks.md 逐条实现
  3. `/opsx:archive`（用户手动调用）— 归档变更，同步 delta specs 到主目录
  4. Superpowers skills：**全部未触发**（brainstorming、TDD、code-review、verification 等均未使用）

## 需求理解

### 业务规则覆盖
原始需求有 5 条业务规则：

1. **DRAFT → ACTIVE 必须已关联 Model 和 Prompt**：已实现。`agent_service.py:62-73` 完整校验 model_id/prompt_id 非空且对应记录存在，缺失时返回具体错误信息（如"未关联有效的 Model"）。后端验证测试通过。

2. **ACTIVE → INACTIVE 直接切换，关联 Skill 标记不可用**：部分实现。状态切换本身已实现（`TRANSITIONS` 映射表正确），但 Skill 不可用的处理采用了"间接判断"策略（design.md 中写明"Agent 为 INACTIVE 时 Skill 自然不可用"），实际上没有在代码层面做任何标记或检查。这是一个**设计决策**而非遗漏——design.md 中有明确记录——但严格来说，"标记为不可用"的需求被简化为了"逻辑上不可用"。

3. **INACTIVE → ACTIVE 重新检查 Model/Prompt 有效性**：已实现。`change_status` 方法对任何目标为 ACTIVE 的转换统一执行校验，不区分来源是 DRAFT 还是 INACTIVE。

4. **ACTIVE 状态 Agent 不能被删除**：已实现。`delete_agent` 方法在 `agent_service.py:37-38` 检查，返回 422 + 明确错误信息。

5. **状态变更记录操作时间和原因**：标记为可选跳过。需求原文是"可选：记录变更时间和原因"，AI 在 proposal.md 和 design.md 中均未纳入此条，属于**合理判断**（需求自身标注了"可选"）。但 `AgentStatusChange` schema 的 `reason` 字段在 API 层接收了，只是没有持久化存储——属于"接了参数但没用"的半成品状态。

### 遗漏分析
- Skill 标记不可用：AI 在 design 阶段主动做出了简化决策，理由是"通过 Agent 状态间接判断"。这**并非遗漏**而是有意的 scope 缩减，但用户并未被询问是否同意此简化。
- 状态变更历史：需求标注"可选"，AI 直接跳过，未征求用户意见。属于边界情况处理合理但沟通不足。

## 开发过程

### 工作流程
AI 严格遵循了 OpenSpec 的 **spec-driven** 工作流：

```
openspec new change → proposal → design + specs（并行）→ tasks → 编码实现 → 归档
```

- **策略**：先分析再动手。先读了所有现有代码（entity.py、endpoints.py、schema.py、service、前端文件），再写制品，最后编码。
- **未使用 subagent 或并行任务**：所有工作在主对话中串行完成。TaskCreate/TaskUpdate 仅用于跟踪制品创建进度（4 个 task 对应 4 类制品），不是 superpowers 的 skill。
- **OpenSpec 流程执行质量**：
  - `openspec new change`、`openspec status --json`、`openspec instructions` 等命令使用正确
  - 制品间的依赖关系（proposal → design/specs → tasks）被正确遵守
  - 每完成一个制品都重新检查 status，流程控制严谨
  - **但**：制品内容质量参差不齐（见下方分析）

### 技能使用详情

| # | 技能名称 | 触发方式 | 做了什么 | 质量评价 |
|---|---------|---------|---------|---------|
| 1 | `/opsx:propose` | 用户手动 | 读取 openspec instructions，生成 proposal/design/specs/tasks 共 6 个文件 | 流程执行准确，制品结构完整 |
| 2 | `/opsx:apply` | 用户手动 | 读取 tasks.md，逐条实现 22 个任务，每完成一个标记 [x] | 执行高效，一次性连续完成无中断 |
| 3 | `/opsx:archive` | 用户手动 | 检查完成状态、同步 specs、移动到 archive | 标准化归档流程 |
| 4 | TaskCreate/TaskUpdate | AI 自动 | 创建 4 个 task 跟踪制品进度 | 使用合理但粒度偏粗（仅跟踪制品类型） |
| 5 | Superpowers skills | **未触发** | — | brainstorming、TDD、code-review、verification 等均未调用 |

**关于 Superpowers 未触发的说明**：尽管系统提示中强调"1% 可能性就应触发"，但整个开发过程中 AI 没有调用任何 Superpowers skill。原因可能是 OpenSpec 的 propose→apply→archive 流程已经足够结构化，AI 判断不需要额外的 brainstorming 或 plan。这导致了一些本应由 skill 覆盖的质量保证环节缺失（如 code review、TDD）。

### 人工干预
整个过程中 **0 次人工干预**。

- 用户只发了 4 条指令：介绍项目、`/opsx:propose`（附需求文档）、`/opsx:apply`、`/opsx:archive`
- 每一步 AI 都自主完成，包括 archive 时的 AskUserQuestion（用户选择了"Sync now"）
- **潜在问题**：零干预不代表零问题。Skill 可用性标记的简化、状态变更历史的跳过，都是在用户不知情的情况下由 AI 自行决策的

### 关键决策点

1. **Skill 不可用 = 间接判断** — 有争议。需求明确说"标记为不可用"，AI 自行简化为"通过 Agent 状态隐含判断"，未给 Skill 添加字段或逻辑。节省了工作量，但降低了可追溯性。

2. **创建 Agent 时 Model/Prompt 为可选** — 合理。与 DRAFT 状态的设计一致，降低创建门槛。design.md 中有明确说明。

3. **查询参数不用单独 Schema** — 合理。FastAPI 的 Query 参数直接传参比定义额外的 Pydantic 模型更简洁，符合项目现有风格。Task 1.3 标注了"改用 FastAPI Query 参数，无需单独 Schema"。

4. **`_agent_to_read` 辅助函数放在 endpoints.py** — 有争议。这个函数负责 ORM 对象到响应模型的转换，逻辑上属于 Service 层或 Schema 层的职责。放在端点文件中增加了 API 层的厚度，与项目其他端点的简洁风格不一致。

5. **`reason` 字段接收但不持久化** — 不合理。API 接收了 `reason` 参数但没有存储，属于"半成品"设计。要么完整实现，要么从 schema 中移除。

## 产出质量

### 后端代码
- **API 设计**：基本 RESTful。5 个端点命名合理，状态切换用 `PATCH /agents/{id}/status` 而非通用 PATCH，是好的设计。状态码使用正确（201 创建、422 业务校验失败、404 未找到）。
- **分层模式**：Service 层封装了所有业务逻辑（状态机、校验），端点层轻薄。符合项目已有的 ModelService/PromptService 模式。
- **数据模型**：无变更。Agent 和 Skill 模型原有定义已满足需求，只扩展了 Pydantic Schema。
- **错误处理**：`delete_agent` 返回元组 `(bool, str)` 的模式比抛异常更简洁，但与 FastAPI 的异常风格不太一致（其他端点用 HTTPException）。
- **测试**：无 pytest 测试文件。后端验证是通过 TestClient 在一行脚本中完成的临时测试，不是持久化的测试套件。这直接导致规则 2（Skill 标记不可用）的遗漏无法被自动发现。

### 前端代码
- **模式一致性**：api/agents.js 沿用 prompts.js 的风格；store 使用 Composition API；页面使用 Element Plus 组件。与项目现有代码一致。
- **UI 完整度**：列表 + 筛选 + 操作按钮 + 确认对话框 + 创建表单，需求中的前端功能全部覆盖。
- **错误处理**：激活失败的错误信息通过 `e?.response?.data?.detail` 提取并 ElMessage.error 展示，覆盖到位。
- **不足**：未启动 dev server 做实际 UI 验证。Task 7.2 标记为"前端验证"但实际只做了 `npm run build`（编译检查），没有浏览器中实际操作确认。

### 文档与规范
- OpenSpec 生成了 6 个制品文件（proposal、design、3 个 spec、tasks），结构完整、格式规范。
- Spec 文件使用了标准的 `### Requirement` + `#### Scenario: WHEN/THEN` 格式，可测试性好。
- 代码注释：极少，只有 `_agent_to_read` 有一行 docstring。符合"注释解释为什么"的原则。
- **但**：制品之间存在一些"模板痕迹"——proposal 和 design 的部分内容像是在填模板而非深入思考（如 design.md 的 Risks 部分较短）。

## 工具体验

### 工作流体感（1-5 分）
- **流畅度**：4 分 — propose → apply → archive 三步走，几乎无卡顿。唯一的小摩擦是 `openspec` CLI 需要在项目根目录运行（第一次在 backend 目录执行报错）。
- **自然度**：3 分 — OpenSpec 的流程感很强，但"按模板填制品"的感觉也比较明显。AI 更像是在执行一个固定的流水线，而非在思考中自然产出文档。
- **安心感**：3 分 — 代码一次通过了后端验证，但缺少 code review、TDD、前端真实验证等质量保障环节。作为开发者，对"零干预即完成"的产出既惊喜又有些不安。

### 工具特有价值
- **最大亮点**：OpenSpec 的结构化流程让"需求→设计→实现→归档"全程可追溯。每个阶段都有制品产出，状态机（proposal → design/specs → tasks）确保了依赖关系的正确性。
- **节省了什么**：不需要手动规划任务拆分，tasks.md 由 openspec instructions + AI 自动生成。归档流程（sync specs → mv to archive）完全自动化。
- **增加了什么负担**：制品撰写消耗了相当的上下文（proposal + design + 3 个 spec + tasks = 约 6 个文件的写入），对于这个规模的变更来说，文档量与代码量的比例偏高。

### 痛点与不足
1. **制品"填充感"**：proposal 和 design 的部分内容像是在走流程而非深入分析。例如 design.md 的"Decisions"部分，4 个决策中有 2 个是显而易见的（独立文件、保持现有模式），真正有价值的只有 2 个。
2. **Superpowers 未触发**：尽管安装了 brainstorming、TDD、code-review 等 skill，AI 在 OpenSpec 流程中完全没有调用它们。两个工具之间缺乏"钩子"——OpenSpec 流程没有触发 Superpowers skill 的机制。
3. **前端验证不够真实**：只做了编译检查，没有在浏览器中实际操作。对比后端用 TestClient 做了完整的状态机流程测试，前端的验证明显不足。

## 上下文使用分析

- **总 token 消耗**：76.6k / 200k（38%）
- **是否发生 context 压缩**：否
- **上下文中占比最大的内容类型**：对话历史（Messages: 49.5k, 24.8%），其次是系统工具定义（9.8k, 4.9%）和 Skills 列表（6.8k, 3.4%）
- **上下文压力是否影响工作质量**：否。38% 使用率充足，后期工作质量未下降。

### 上下文效率评估
- **单位上下文产出比**：偏低。76.6k tokens 中，制品生成和 OpenSpec 命令交互消耗了大量空间。实际有效代码（后端 ~80 行 service + ~70 行 endpoints，前端 ~200 行 Vue）约 350 行，加上 ~6 个制品文件。上下文消耗与产出比约为 220 tokens/行代码。
- **与预期对比**：偏高。OpenSpec 的多轮 `openspec status --json` + `openspec instructions --json` 调用产生了大量重复的 JSON 输出（每次 status 都返回完整的 artifacts 数组），加上制品文件的读写，上下文开销显著高于"直接编码"模式。

## 总结

### 一句话评价
OpenSpec 提供了清晰的结构化流程和全程可追溯性，但制品撰写增加了显著的上下文开销，且 Superpowers skills 在流程中完全"悬空"——两个工具之间缺少联动机制，导致质量保障环节（brainstorming、TDD、code review）集体缺席。

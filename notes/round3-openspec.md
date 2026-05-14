# 第 3 轮实验观察：OpenSpec + Superpowers

> **工具速览**：OpenSpec 是 Fission AI 出品的轻量规范工具，3-4 步流程产出 proposal/design/specs/tasks 制品，支持归档同步。本轮 Superpowers 虽已安装，但全程未被触发。
>
> - **怎么装**：`npm install -g @fission-ai/openspec@latest`
> - **初始化**：`openspec init --tools claude` （必须指定 `--tools`）
> - **核心命令**：`/opsx:propose` → `/opsx:apply` → `/opsx:archive`（可选前置 `/opsx:explore` 做纯讨论不写代码）
> - **触发方式**：用户**手动**打 slash command
> - **本轮截图**（22 张）：[`03-openspec/openspec/changes/archive/2026-05-13-agent-activation/images/`](../03-openspec/openspec/changes/archive/2026-05-13-agent-activation/images/)
> - **本轮工具产出**：[OpenSpec 制品全套（proposal/design/specs/tasks 共 6 份）](../03-openspec/openspec/changes/archive/2026-05-13-agent-activation/)
> - **AI 自评笔记**：[`observation-notes.md`](../03-openspec/openspec/changes/archive/2026-05-13-agent-activation/observation-notes.md)（同 session 内 AI 用模板自我回顾）

## 基本信息

| 项 | 值 |
|---|---|
| 工具组合 | OpenSpec（主导）+ Claude Code 内置 TaskCreate/TaskUpdate + Superpowers（已安装但**未触发任何 skill**） |
| 开发耗时 | **24 分钟**（会话 wall time） |
| 代码变更 | 7 文件，+305 / -10 行（未提交，全部在工作区） |
| 提交数 | **0** |
| Context 使用 | 91.9k / 200k（**46%**），未触发压缩 |
| 子代理 | **无** — 全部工作在主对话中串行完成 |
| 待办完成 | 4/4（跟踪制品进度，非 superpowers skill） |

### 技能使用

| 技能 | 触发方式 | 产出质量 |
|------|---------|---------|
| `/opsx:propose` | 用户手动 | 良好 — 生成 proposal → design → 3 个 spec → tasks（6 个文件） |
| `/opsx:apply` | 用户手动 | 良好 — 22 个任务逐条实现，连续完成无中断 |
| `/opsx:archive` | 用户手动 | 正常 — 归档 + 同步 specs |
| Superpowers skills | **未触发** | brainstorming、TDD、code-review、verification 全部缺席 |

### 产出物构成

| 类别 | 文件 | 行数 |
|------|------|------|
| OpenSpec 制品 | proposal + design + 3 spec + tasks（含 archive 副本） | ~434 行（去重后约 287 行） |
| 后端业务代码 | AgentService + endpoints + schemas | ~170 行新增 |
| 前端业务代码 | AgentList.vue + agents.js API + agent store | ~260 行新增 |
| 测试代码 | **无** | 0 行 |
| 数据模型变更 | **无** — 复用已有 Agent/AgentStatus/Skill 定义 | 0 行 |

## 需求理解

### 业务规则覆盖

| # | 规则 | 状态 | 说明 |
|---|------|------|------|
| 1 | DRAFT → ACTIVE 必须已关联 Model 和 Prompt | ✅ 完整 | `change_status()` 校验 model_id/prompt_id 非空且存在，缺失时返回具体错误信息 |
| 2 | ACTIVE → INACTIVE，关联 Skill 标记不可用 | ⚠️ 简化 | 状态切换已实现，但 Skill 标记采用"间接判断"（design.md 明确写明），**没有加 is_active 字段或逻辑** |
| 3 | INACTIVE → ACTIVE 重新检查 Model/Prompt 有效性 | ✅ 完整 | 与规则 1 共用校验逻辑，不区分来源状态 |
| 4 | ACTIVE 状态 Agent 不能被删除 | ✅ 完整 | `delete_agent()` 检查返回 422 |
| 5 | 状态变更记录操作时间和原因 | ⏭️ 跳过 | API 接收 reason 参数但未持久化，无时间戳字段。需求标注"可选"，AI 直接跳过 |

### 遗漏分析

- **Skill 不可用标记**：AI 在 design 阶段主动简化为"通过 Agent 状态间接判断"，design.md 有记录。这是**有意的设计决策**，但用户未被询问是否同意
- **reason 未持久化**：API 接了参数但没用，属于"半成品"设计。要么完整实现要么从 schema 移除
- **与 Round 2 对比**：Round 2 实际加了 `is_active` 字段并做了批量 UPDATE，Round 3 选择了零修改数据模型的最轻量路径

## 开发过程

### 工作流程

三步走，用户触发 3 个 slash command：

```
/opsx:propose → /opsx:apply → /opsx:archive
```

- **策略**：先分析再动手。先读取全部现有代码（entity.py、endpoints.py、schema.py、前端文件），再写制品，最后编码
- **无子代理**：全部在主对话串行完成。TaskCreate 仅跟踪 4 类制品的生成进度
- **OpenSpec 流程控制**：CLI 命令（`openspec status --json`、`openspec instructions --json`）使用正确，制品间依赖关系（proposal → design/specs → tasks）被严格遵守

### 人工干预

**零次干预**。用户只做了 4 件事：
1. 介绍项目
2. `/opsx:propose`（附需求文档）
3. `/opsx:apply`
4. `/opsx:archive`（选择"Sync now"）

### 关键决策

| # | 决策 | 评价 |
|---|------|------|
| 1 | Skill 不可用 = 间接判断，不加字段 | ⚠️ 有争议 — 节省了工作量但降低了可追溯性 |
| 2 | 创建时 Model/Prompt 可选 | ✅ 合理 — 与 DRAFT 状态一致 |
| 3 | 状态机用 TRANSITIONS 映射表 | ✅ 合理 — 比多个 if/elif 更清晰，易于扩展 |
| 4 | `_agent_to_read` 放在 endpoints.py | ⚠️ 有争议 — ORM→响应转换逻辑上属于 Service 层 |
| 5 | reason 接收但不持久化 | ❌ 不合理 — 半成品设计 |
| 6 | `delete_agent` 返回 `tuple[bool, str]` | ⚠️ 有争议 — 比 Round 2 的抛异常更 Pythonic，但与 FastAPI 的 HTTPException 风格不一致 |

## 产出质量

### 后端代码

- **API 设计**：RESTful，5 个端点。状态切换用 `PATCH /agents/{id}/status`，好设计。状态码规范（201/404/422）
- **状态机实现**：`TRANSITIONS` 映射表是三个 Round 中最清晰的设计 — 声明式定义合法转换，校验逻辑一行 `if target_status not in self.TRANSITIONS.get(current, set())`
- **数据加载**：`list_agents` / `get_agent` 使用 `joinedload` 预加载关联，避免 N+1 查询，三个 Round 中唯一做了查询优化
- **数据模型**：**零变更** — 完全复用已有 Agent/AgentStatus/Skill 定义，没有新增任何字段
- **代码缺陷**：
  - reason 参数接收但未使用
  - 无测试（仅 TestClient 临时脚本验证）
- **分层模式**：Service 层封装业务逻辑，端点层轻薄，符合项目已有模式

### 前端代码

- **模式遵循**：api/agents.js 沿用 prompts.js 风格，store 用 Composition API，页面用 Element Plus
- **UI 完整性**：列表 + 状态筛选（el-tabs）+ 创建对话框（含 Model/Prompt 下拉选择）+ 激活/停用/删除操作 + 确认对话框
- **创建关联**：创建 Agent 时可下拉选择 Model 和 Prompt，调用对应 API 加载选项
- **错误处理**：`e?.response?.data?.detail` 提取后端错误 + ElMessage.error 展示
- **不足**：未在浏览器中实际验证，只做了 `npm run build` 编译检查

### 文档

- **制品结构**：proposal → design → 3 个 spec → tasks，格式规范
- **Spec 格式**：标准的 `### Requirement` + `#### Scenario: WHEN/THEN`，可测试性好
- **模板感**：proposal 和 design 部分内容像在填模板而非深入分析（design.md 的 Risks 部分较短）
- **冗余**：archive 后 specs 被复制两份（archive/ 下 + 主 specs/ 下），增加了维护负担

## 上下文使用

| 指标 | 数据 |
|------|------|
| 总消耗 | 91.9k / 200k（**46%**） |
| Context 压缩 | 未发生 |
| 最大内容类型 | Messages（49.5k，24.8%） |
| CLI 重复输出 | `openspec status --json` 每次返回完整 artifacts 数组 |
| 质量影响 | 未影响 |

### 效率评估

- **Token 效率最高**：46% 的 Context 产出了与 Round 2 相当的功能，且包含完整的 OpenSpec 制品
- **与 Round 1/2 对比**：比 Round 1（48%）略省，比 Round 2（61%）省 15 个百分点
- **但**：制品中的模板填充和 CLI 重复输出仍有优化空间

## 用户评分

**功能完成度：8 / 10**（与 Round 2 同分）

加分项：
- 创建 Agent 时可关联 Model 和 Prompt（下拉选择，调用了 API）
- 前端有删除操作（INACTIVE 状态可删除）
- 状态机映射表设计清晰
- joinedload 预加载优化

扣分项：
- Skill 不可用标记选择了"间接判断"而非实际字段标记
- reason 参数半成品
- 无时间戳字段

## 总结

**一句话评价**：最快的交付速度（24m）、最低的 Context 消耗（46%），功能覆盖与 Spec-Kit 相当，但两个工具之间缺少联动机制导致 Superpowers 全程"悬空"。

### 数据速览

```
耗时:       24m（wall time）
提交:       0（未提交）
代码变更:   +305 / -10 行（7 文件，未提交）
测试:       0 个
文档:       6 个制品文件，~287 行（去重）
Context:    91.9k / 200k（46%）
子代理:     无
人工干预:   0 次（3 次 slash command + 1 次 archive 选项）
业务规则:   3/5 完整，1 简化替代，1 可选跳过
代码质量:   无测试，reason 半成品，状态机设计最清晰
```

### 三轮对比速览

| 指标 | R1: Superpowers | R2: Spec-Kit | R3: OpenSpec |
|------|-----------------|--------------|--------------|
| 耗时 | 1h 4m | 44m | **24m** |
| Context | 96.1k（48%） | 123k（61%） | **91.9k（46%）** |
| 代码行数 | +2123 | +541 | +305 |
| 测试 | **19 个** | 0 | 0 |
| 提交 | **11 个** | 0 | 0 |
| 文档 | 1,266 行（2 份） | 1,121 行（9 份） | 287 行（6 份） |
| Skill 标记 | 协商跳过 | **完整实现** | 间接判断 |
| 时间戳字段 | 无 | **有** | 无 |
| 创建关联 | 无 | **有** | **有** |
| 删除操作 | 后端有/前端无 | **前后端都有** | **前后端都有** |
| 状态机设计 | ALLOWED_TRANSITIONS 集合 | if/elif | **TRANSITIONS 映射表** |
| 查询优化 | 无 | 无 | **joinedload** |
| 死代码 | 无 | **有** | 无 |
| reason | 可选跳过 | 接收丢弃 | 接收丢弃 |
| 用户评分 | 5/10 | **8/10** | **8/10** |

# 四工具横向对比：Superpowers vs Spec-Kit vs OpenSpec vs GSD

> **阅读须知（重要）**
>
> 这份对比报告基于 **N=1 的单次实验**：每个工具只跑了一次、同一需求、同一操作者、同一时间段。文中所有数据（耗时、token、代码行数）都是单次观察值，不是工具能力的统计结论。
>
> **特别注意**：
> - **评分（5/10、8/10）** 偏重"功能覆盖完整性 + 主观体验"，不计测试覆盖率/工程质量 —— 所以 R1 测试最多反而评分最低，是因为前端缺了创建关联和删除
> - **R2/R3 零干预** 不等于质量更高 —— R2 的死代码、R3 的 Skill 简化 都是 AI 自行决定的，用户不知情
> - **R4 跨 session**：GSD 工具跨 3 个 session 完成，context 数据不可直接与其他轮比较
> - **顺序效应**：R1 → R2 → R3 → R4 是固定顺序，操作者熟悉度递增。换顺序结论可能不同
> - **工具版本**：Spec-Kit v0.8.10、OpenSpec npm `@latest`（2026-05）、Superpowers 跟随 Claude Code 版本、GSD get-shit-done-cc npm `@latest`（2026-05）
>
> 完整客观性声明见 [README.md](../README.md#如何阅读本报告)。

## 1. 概览

| 指标 | R1: Superpowers | R2: Spec-Kit | R3: OpenSpec | R4: GSD |
|------|-----------------|--------------|--------------|---------|
| **耗时** | 1h 4m | 44m | **24m** | 3+ h / 3 sessions |
| **Context** | 96.1k（48%） | 123k（61%） | **91.9k（46%）** | 不可测（跨 session + worktree 隔离） |
| **代码行数** | +2123 | +541 | +305 | **+1303**（含 569 行测试） |
| **测试** | 19 个 | 0 | 0 | **41 个** |
| **提交** | 11 个 | 0 | 0 | **27 个** |
| **文档量** | 1,266 行（2 份） | 1,121 行（9 份） | 287 行（6 份） | **2,500+ 行**（15+ 份） |
| **人工干预** | 5 次（决策审批） | 0 次 | 0 次 | 0 次（问答 8 题不算干预） |
| **用户评分** | **5/10** | **8/10** | **8/10** | **7/10** |
| **Slash commands** | 0（AI 自动触发技能） | 6（用户手动） | 3（用户手动） | 8（用户手动） |

---

## 2. 代码实现差异

### 2.1 状态机实现

同一功能最核心的差异。三个工具给出了三种完全不同的状态机实现。

**Round 1（Superpowers）— 元组集合**

```python
ALLOWED_TRANSITIONS = {
    (AgentStatus.DRAFT, AgentStatus.ACTIVE),
    (AgentStatus.ACTIVE, AgentStatus.INACTIVE),
    (AgentStatus.INACTIVE, AgentStatus.ACTIVE),
}

# 校验：元组查找
if (agent.status, target) not in ALLOWED_TRANSITIONS:
    raise HTTPException(422, ...)
```

- 优点：扁平、无歧义
- 缺点：查找是 O(n) 遍历（3 个元素无所谓），没有声明"从某状态可以到哪些状态"
- **额外加分**：Service 层直接抛 HTTPException（与 FastAPI 深度耦合，但简洁）

**Round 2（Spec-Kit）— if/elif 分支**

```python
def activate_agent(self, agent_id: int) -> Agent:
    agent = self.get_agent(agent_id)
    if not agent:
        raise ValueError("Agent not found")
    if agent.status == AgentStatus.ACTIVE:
        raise ValueError("Agent 已是 ACTIVE 状态")
    if agent.status == AgentStatus.INACTIVE and False:  # 死代码
        pass
    # ... 校验逻辑

def deactivate_agent(self, agent_id: int) -> Agent:
    if agent.status != AgentStatus.ACTIVE:
        raise ValueError("只有 ACTIVE 状态的 Agent 可以停用")
```

- 激活和停用各一个方法，状态判断分散在两个函数中
- 缺点：状态机逻辑不集中，新增状态需要改多处
- **有死代码**：`if agent.status == AgentStatus.INACTIVE and False: pass`

**Round 3（OpenSpec）— 映射表（集合值）**

```python
TRANSITIONS = {
    AgentStatus.DRAFT: {AgentStatus.ACTIVE},
    AgentStatus.ACTIVE: {AgentStatus.INACTIVE},
    AgentStatus.INACTIVE: {AgentStatus.ACTIVE},
}

# 校验：集合查找
if target_status not in self.TRANSITIONS.get(current, set()):
    allowed = [s.value for s in self.TRANSITIONS.get(current, set())]
    return None, f"不允许从 {current.value} 转换到 {target_status.value}，允许的目标状态: {allowed}"
```

- 优点：声明式、O(1) 查找、易扩展、错误消息自动包含允许的目标状态
- **最佳设计**：四个版本中最优雅的状态机实现之一

**Round 4（GSD）— 映射表（列表值）**

```python
VALID_TRANSITIONS: dict[AgentStatus, list[AgentStatus]] = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}

# 校验：列表查找 + 双异常路径
allowed = VALID_TRANSITIONS.get(old_status, [])
if data.status not in allowed:
    raise InvalidTransitionError(old_status, data.status)  # → 409
if data.status == AgentStatus.ACTIVE:
    self._assert_activation_ready(agent)                    # → 422
```

- 优点：结构同 R3，但明确区分了"非法转换（409）"和"激活前置失败（422）"两种错误语义
- **额外设计**：独立异常类 `InvalidTransitionError` / `ActivationNotReadyError`，API 层精确映射 HTTP 状态码

**评判**：Round 3 ≈ Round 4 > Round 1 > Round 2。GSD 和 OpenSpec 都用了映射表，GSD 额外做了异常语义分离（更工程化），OpenSpec 的错误收集设计更用户友好（一次返回所有问题）。

### 2.2 错误处理模式

| 模式 | Round 1 | Round 2 | Round 3 | Round 4 (GSD) |
|------|---------|---------|---------|--------------|
| Service→API | 直接抛 `HTTPException` | 抛 `ValueError`，API 层捕获转 422 | 返回 `tuple[data, error]`，API 层判断 | 抛**独立异常类**（InvalidTransitionError/ActivationNotReadyError），API 层映射不同 HTTP 码 |
| 激活校验 | 逐项检查，逐项抛异常 | 逐项检查，逐项抛异常 | **收集所有错误，一次返回** | 逐项检查，遇第一个失败即抛出 |
| 错误信息 | "未关联有效的 Model" | "未关联 Model，无法激活" | "未关联有效的 Model；未关联有效的 Prompt" | "激活失败：Agent 未关联提示词" |
| 删除返回 | `bool` | `bool` | `tuple[bool, str]` | `bool`（None 表示 404） |
| 转换失败码 | 422 | 422 | —（API 层自行决定） | **409**（明确区分） |

R4 GSD 是唯一将"非法状态转换"（409 Conflict）和"激活前置失败"（422 Unprocessable）显式区分为两个不同 HTTP 码的实现，语义最精确。R3 的"错误收集"（同时缺 Model + Prompt 一次性全报）更用户友好。

### 2.3 数据加载策略

| 策略 | Round 1 | Round 2 | Round 3 | Round 4 (GSD) |
|------|---------|---------|---------|--------------|
| 列表查询 | `joinedload(Agent.model, Agent.prompt)` | 直接查询 | `joinedload(Agent.model, Agent.prompt)` | `selectinload(Agent.model, Agent.prompt)` |
| 详情查询 | `joinedload` | 直接查询 | `joinedload` | `joinedload` |
| 排序 | 无 | 无 | `order_by(created_at.desc())` | 无 |
| 分页 | `skip + limit`，返回 `total` | `skip + limit`，无 total | `skip + limit`，无 total | `skip + limit`，无 total |

R1/R3/R4 都避免了 N+1，R2 没有。R4 GSD 在列表用 `selectinload`（批量 IN 查询），详情用 `joinedload`（JOIN 查询），是对两种场景各自最优解的应用。

### 2.4 数据模型变更

| 变更 | Round 1 | Round 2 | Round 3 | Round 4 (GSD) |
|------|---------|---------|---------|--------------|
| Agent 新字段 | 无 | `activated_at`, `deactivated_at` | 无 | 无 |
| Skill 新字段 | 无 | `is_active` | 无 | 无（有意 out-of-scope） |
| 新增表 | 无 | 无 | 无 | **`AgentStatusHistory`**（独立审计日志表） |
| 总变更量 | **零** | **3 个字段** | **零** | **1 张新表（5 字段）** |

R4 GSD 选择了独立 `AgentStatusHistory` 表记录状态变更历史（append-only），而非在 Agent 上加时间戳字段，设计更正交。Skill.is_active 在问答阶段主动标记为 out-of-scope（和 R1/R3 的"默默不做"不同，有明确记录）。

### 2.5 Schema 设计

| 策略 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| 列表响应转换 | `_agent_to_read()` 手动构造 dict | `_enrich_agent()` 动态附加属性 | `AgentReadWithRelations` 继承 |
| 状态变更 schema | `AgentStatusChange` | `AgentStatusUpdate` | `AgentStatusChange` |

Round 1 的手动 dict 构造有维护风险（新增字段需同步更新）。Round 3 的 `AgentReadWithRelations(AgentRead)` 继承模式最干净 — 新增基础字段自动继承，只需添加关联字段。

### 2.6 前端功能覆盖

| 功能 | Round 1 | Round 2 | Round 3 | Round 4 (GSD) |
|------|---------|---------|---------|--------------|
| 状态筛选 | el-tabs | **el-radio-group** | **el-tabs** | el-select 下拉 |
| Model/Prompt 列 | `model_name` / `prompt_name` | `model_name` / `prompt_title` | `model_name` / `prompt_name` | `model_name` / `prompt_name`（null→"未关联"） |
| 创建关联选择 | **无** | **有**（el-select + API 调用） | **有**（el-select + API 调用） | **有**（懒加载，dialog 开启时才拉取） |
| 删除按钮 | **无** | **有**（INACTIVE 可删） | **有**（INACTIVE 可删） | **有**（INACTIVE 可删） |
| 分页 | **有**（el-pagination） | 无 | 无 | **有**（el-pagination prev/pager/next） |
| 表单验证 | 无规则 | `el-form-item rules` | 无规则 | **`el-form-item rules`**（名称必填） |
| 错误提示 | 拦截器兜底 | ElMessage.error | **直接展示后端 detail** | **全局拦截器** → `ElMessage.error(detail)` |
| 确认对话框 | 无 | 无 | 无 | **所有操作**（激活/停用/删除）均有 `ElMessageBox.confirm` |
| 描述列 | 无 | 无 | **有** | 无（在 dialog 里填写，不展示在表格） |

R4 GSD 是四轮中功能最完整的前端实现：分页 + 关联选择 + 删除 + 表单验证 + 所有操作的确认弹框。下拉懒加载（dialog 打开时才拉取 Model/Prompt 列表）是唯一正确处理此性能问题的轮次。

---

## 3. 任务分解策略

### 3.1 粒度与数量

| 工具 | 任务数 | 组织方式 | 文档行数 |
|------|--------|---------|---------|
| Superpowers | 23 个任务，7 个 Phase | 按用户故事分组 | 1,118 行 |
| Spec-Kit | 7 组，22 个子任务 | 按技术层分组 | 212 行 |
| OpenSpec | 8 个 Task，43 个 Step | 按组件顺序 | 42 行 |
| GSD | **5 个 plan（Phase 1: 4，Phase 2: 1）** | 按技术层（数据→服务→HTTP→测试→前端三层） | 每 plan 约 200-300 行（含研究、模式分析、计划本体） |

**Superpowers** 最重：23 个任务按 Phase 组织（Setup → Foundational → 4 个 User Story → Polish），每个 Phase 有显式 Checkpoint。

**Spec-Kit** 最薄：7 个逻辑组，但实际执行时被大幅合并（前端 4 个 Phase 合并为一次 Write）。

**OpenSpec** 最精细：8 个大任务下嵌套 Step，但文档本身只有 42 行 — 把细节留给了执行阶段。

### 3.2 检查点设计

| 工具 | 有检查点？ | 检查点位置 | 实际执行情况 |
|------|-----------|-----------|-------------|
| Superpowers | **5 个显式 Checkpoint** | 每个 Phase 结束后 | 部分跳过（只做了最终 spec review） |
| Spec-Kit | **无**（只有最终验证） | 仅末尾 2 个验证任务 | 跳过了逐任务验证 |
| OpenSpec | **嵌入式**（每个 Task 有 Run 命令） | 每个组件完成后 | 大部分执行了 |
| GSD | **强制 verify step**（`/gsd:verify-work`） | 每个 Phase 执行结束后 | **实际执行了**，产出 VERIFICATION.md（P1: 5/5 passed，P2: 6/6 verified） |

GSD 是四个工具中**唯一强制执行 verify 步骤**的，且 verify 是独立 subagent 运行（不由执行 agent 自我检查），结果记录在 VERIFICATION.md 中有据可查。前三轮的检查点在 AI 执行中基本失效，GSD 通过工具化绕过了这个问题。

### 3.3 任务完成忠实度

| 工具 | 计划的任务 | 实际完成 | 偏差 |
|------|-----------|---------|------|
| Superpowers | 23 个 | 23 个标记完成 | 忠实（但跳过了逐任务 review） |
| Spec-Kit | 22 个子任务 | 全部标记完成 | 合并执行，跳过 checkpoint |
| OpenSpec | 43 个 step | 全部标记 [x] | 忠实（按 step 粒度执行） |
| GSD | 5 个 plan，每 plan 有 2-4 个 task | 全部完成 + SUMMARY | **零偏差**，每 plan 执行结果有独立 SUMMARY.md 记录 |

---

## 4. 设计文档质量

### 4.1 API 契约精度

| 工具 | API 契约形式 | 精度 | 可对接性 |
|------|-------------|------|---------|
| Superpowers | 设计文档中内嵌 schema 定义 | 中 — 有字段定义，无 JSON 示例 | 需要阅读代码才能对接 |
| Spec-Kit | **独立的 contracts/agents-api.md** | **高 — 含请求/响应 JSON 示例** | **可直接作前后端对接文档** |
| OpenSpec | spec 文件中的 WHEN/THEN 场景 | 中 — 有场景但无 JSON | 需要补充才能对接 |
| GSD | REQUIREMENTS.md 中的端点表格 + PLAN.md 中的接口说明 | 中 — 有端点+字段+状态码，无 JSON 示例 | 可指导实现，但不如 Spec-Kit 精确 |

**Spec-Kit 仍胜出**，GSD 次之。GSD 的 REQUIREMENTS.md 端点表格结构清晰，Phase 1 RESEARCH.md 包含响应 schema 描述，但没有具体 JSON 示例。

### 4.2 状态机描述准确性

| 工具 | 描述方式 | 与最终代码一致性 |
|------|---------|----------------|
| Superpowers | 文字 + 状态转换图 | ✅ 完全一致 |
| Spec-Kit | 分散在 spec、research、data-model、contracts 4 份文档中 | ⚠️ 一致但有冗余 |
| OpenSpec | design.md Decisions + 服务层代码 | ✅ 完全一致 |

三个工具对状态机规则的描述都与最终代码一致，没有"设计文档说 A 但代码做了 B"的情况。

### 4.3 遗漏预测

| 工具 | 是否预警了后来出现的问题？ |
|------|-------------------------|
| Superpowers | 预警了 Skill 不可用标记的歧义，主动提问让用户决策 |
| Spec-Kit | research.md 主动将 reason 降级，但**没有预警死代码风险** |
| OpenSpec | design.md 标注了"Skill 模型没有 is_available 字段"的风险，但最终选择了简化而非解决 |

**Superpowers 的 brainstorming 阶段是唯一真正"预测问题"的** — 它主动发现了 Skill 标记的需求歧义，并让用户参与决策。Round 2 和 Round 3 都是 AI 自行做了简化决策。

### 4.4 文档冗余度

| 工具 | 文档行数 | 代码行数 | 文档/代码比 | 冗余程度 |
|------|---------|---------|------------|---------|
| Superpowers | 1,266 | 2,123 | 0.6:1 | **低** — 设计 + 计划各一份，几乎无重复 |
| Spec-Kit | 1,121 | 541 | **2.1:1** | **高** — 状态机在 4 份文档中重复描述 |
| OpenSpec | 287 | 305 | 0.9:1 | 中 — spec 归档后有副本 |

---

## 5. 自主决策质量

### 5.1 决策统计

| 工具 | 用户参与决策 | AI 自主决策 | 自主决策正确率 |
|------|-------------|-----------|--------------|
| Superpowers | **5 次** | 少量实现细节 | **高**（无错误决策） |
| Spec-Kit | **0 次** | 全部自主 | **中**（有死代码、reason 未持久化） |
| OpenSpec | **0 次** | 全部自主 | **中**（Skill 简化替代、reason 半成品） |
| GSD | **8 次**（`/gsd:new-project` 问答） | 实现细节 + 一次主动提议 scope cut | **高**（Skill out-of-scope 有记录，reason 完整实现） |

### 5.2 关键决策对比

**决策 A：Skill 不可用如何处理？**

| 工具 | 决策 | 用户参与？ | 结果 |
|------|------|-----------|------|
| Superpowers | 主动发现歧义，提供 3 个选项 | **是** — 用户选择跳过 | 需求协商，无遗漏 |
| Spec-Kit | 直接实现 `is_active` 字段 + 批量 UPDATE | 否 | **最完整的实现**，但用户不知情 |
| OpenSpec | 选择"间接判断"，不修改代码 | 否 | 最轻量但可追溯性差 |
| GSD | `/gsd:new-project` 问答时主动提议 out-of-scope，理由写入 PROJECT.md | **是** — 用户在问答中确认 | 有意降级，有文档记录，无"默默跳过" |

这个对比揭示了一个关键差异：**Superpowers 倾向于"问用户"，Spec-Kit 倾向于"做更多"，OpenSpec 倾向于"做更少"，GSD 倾向于"先讨论再决策，结果可查"**。

**决策 B：reason 字段如何处理？**

| 工具 | 决策 | 问题 |
|------|------|------|
| Superpowers | 标记为可选跳过 | 无 — 诚实跳过 |
| Spec-Kit | 接收参数但不持久化 | **半成品** — API 接了参数却丢弃 |
| OpenSpec | 同 Spec-Kit | 同上 |
| GSD | **完整实现**：`AgentStatusHistory.reason` 字段 + API 接收并写入 | 唯一真正持久化 reason 的 |

前三轮都没有做好 reason 的处理；GSD 是唯一完整实现的（reason 字段在 AgentStatusHistory 表中持久化，API 支持接收并写入）。

**决策 C：创建 Agent 时是否关联 Model/Prompt？**

| 工具 | 决策 | 前端实现 |
|------|------|---------|
| Superpowers | 后端 schema 支持，前端未实现 | **缺失** |
| Spec-Kit | 完整实现（下拉 + API 调用） | **完整** |
| OpenSpec | 完整实现（下拉 + API 调用） | **完整** |
| GSD | 完整实现（懒加载下拉，dialog 打开时才拉取） | **完整**（且性能更优） |

这是 Superpowers 评分低（5/10）的直接原因 — 后端能力存在但前端没有暴露给用户。R2/R3/R4 都做了完整实现；GSD 额外做了懒加载（避免每次页面渲染都拉取 Model/Prompt 列表）。

### 5.3 "零干预"的真相

Round 2 和 Round 3 都是零人工干预。但这不代表质量更高：

- Round 2 的死代码（`if ... and False: pass`）没有用户发现
- Round 2 的 reason 被 AI 自行降级，用户不知情
- Round 3 的 Skill 简化替代，用户不知情
- Round 3 的 reason 半成品，用户不知情

**Superpowers 的 5 次干预全部是 AI 主动征求用户意见，不是纠偏**。GSD 的 8 次问答也是同样的模式 — 流程内置的结构化决策点，不是因为出错才问。两者的区别是：Superpowers 的问答散落在执行过程中，GSD 的问答集中在项目初始化（`/gsd:new-project`）的一个专门环节，之后几乎不再中断。

Spec-Kit 和 OpenSpec 的流程中缺少这个机制。

---

## 6. Token 效率

### 6.1 归一化对比

| 指标 | Superpowers | Spec-Kit | OpenSpec | GSD |
|------|-------------|----------|----------|-----|
| Token 消耗 | 96.1k | 123k | **91.9k** | 不可测（跨 session） |
| 有效代码行（后端+前端新增） | ~520 行 | ~428 行 | ~430 行 | ~740 行（不含测试），**1,303 行**（含测试） |
| 业务规则完整覆盖数 | 3/5 | **4/5** | 3/5 | 4/5（Skill out-of-scope 有记录） |
| 用户评分 | 5 | 8 | 8 | 7 |
| 测试覆盖 | 19 个 | 0 | 0 | **41 个** |
| 跨 session 可恢复 | 否 | 否 | 否 | **是**（STATE.md 记录断点） |

### 6.2 效率解读

**Token/代码行**：Superpowers 最省（185 token/行），但部分原因是它包含了 19 个测试，这些测试代码生成也消耗 token。GSD 因跨 session 无法直接比较，但子 agent worktree 隔离意味着规划制品消耗在子 agent 上下文里，不体现在主 session token 中。

**测试 vs 交付**：GSD 是唯一在规划阶段就将测试层列入 Phase 1 的工具（01-04-PLAN.md），41 个测试不是事后补的，是计划的一部分。这对比其他三轮的"跑完才想起没有测试"是本质区别。

**Session 断裂成本**：GSD 跨了 3 个 session，理论上可以降低单 session 上下文压力，但带来了用户需要理解 STATE.md 才能续接的成本。对于这个规模的需求，这个成本偏高。

### 6.3 流程开销占比（R1-R3 可测；R4 估算）

| 开销类型 | Superpowers | Spec-Kit | OpenSpec | GSD（估算） |
|---------|-------------|----------|----------|------------|
| 固定开销（System + Skills 元数据） | ~22k（23%） | ~15k（12%） | ~17k（18%） | 低（每 session 清空后重算） |
| 制品生成（设计文档 + 计划 + spec） | ~30k（31%） | ~45k（37%） | ~15k（16%） | **高**（2500+ 行规划文档） |
| 子代理报告 | ~25k（26%） | ~5k（4%） | 0 | 高（每 plan 有 SUMMARY，verify 报告） |
| 实际编码 | ~19k（20%） | ~58k（47%） | ~60k（65%） | 中（worktree 子 agent 隔离，主 session 轻） |

**关键发现**：Superpowers 只有 20% 的 token 花在实际编码上，OpenSpec 65% 最高效。GSD 理论上通过 worktree 隔离让主 session 保持轻量，但规划制品本身的密度极高，代价转移到了子 agent 上下文和 wall time。

---

## 7. 综合评价

### 7.1 工具性格画像

| | Superpowers | Spec-Kit | OpenSpec | GSD |
|---|-------------|----------|----------|-----|
| **性格** | 谨慎的顾问 | 严谨的工程师 | 高效的执行者 | **正规军项目经理** |
| **核心流程** | brainstorm → spec → plan → execute | constitution → specify → plan → tasks → implement | propose → apply → archive | map → new-project → plan → execute → verify（per phase） |
| **用户角色** | 决策者（关键节点审批） | 触发者（打 slash command） | 触发者（打 slash command） | 初始问答者，之后旁观 |
| **质量保障** | 测试 + review + 设计文档（三层） | 文档完备（但实现阶段薄弱） | 流程轻量（但缺少 review 机制） | **research + plan-check + verify（每 phase）+ 独立 worktree 执行** |
| **最大优势** | 需求理解最深入（主动发现歧义） | API 契约文档质量最高 | 速度最快、Token 最省 | **测试覆盖最全、verify 最严、跨 session 可恢复** |
| **最大劣势** | 流程仪式感重，功能覆盖反而最少 | 文档冗余，implement 跳过 checkpoint | Superpowers skills 完全"悬空" | **流程最重，已有项目接入体验不佳，跨 session 带来额外续接成本** |

### 7.2 场景推荐

| 场景 | 推荐工具 | 原因 |
|------|---------|------|
| **需求模糊、需要澄清** | Superpowers / GSD | Superpowers 的 brainstorming 发现歧义；GSD 的 new-project 问答结构化收集 |
| **需要前后端并行开发** | Spec-Kit | API 契约文档可独立指导对接 |
| **需求明确、快速交付** | OpenSpec | 3 步完成，速度最快 |
| **团队协作、需要文档沉淀** | GSD / Spec-Kit | GSD 的规划文档体系最完整（每 phase 有 research/plan/summary/verify）；Spec-Kit 的 API 契约文档可直接共享 |
| **个人项目、追求效率** | OpenSpec | Token 消耗最低，流程最简 |
| **复杂业务规则、需要质量保障** | **GSD** | 测试层是 plan 的一部分，41 个测试 + verify step + worktree 隔离，工程质量最高 |
| **从零构建新项目** | **GSD** | map-codebase → new-project → 多 phase 循环是为新项目设计的，完整覆盖 |
| **在已有项目加功能** | OpenSpec / Spec-Kit | GSD 的新项目仪式对"加功能"场景过重；OpenSpec 最轻量；Spec-Kit 有针对现有 codebase 的 specify 阶段 |

### 7.3 工具间的互补性

四轮实验揭示了一个重要发现：**四个工具的核心能力是互补的，而非竞争的**。

- Superpowers 的 brainstorming 质量最高（主动发现需求歧义）
- Spec-Kit 的 API 契约文档最有价值（可指导前后端并行开发）
- OpenSpec 的执行效率最高（最少 token、最快速度）
- GSD 的工程质量最高（测试覆盖 + verify step + 跨 session 可恢复 + 干净 git 历史）

如果组合使用：用 Superpowers 的 brainstorming 澄清需求 → 用 Spec-Kit 的契约文档指导开发 → 用 OpenSpec 的效率执行 → 用 GSD 的 verify 验收 — 理论上可以取四者之长。但实际操作中，工具间的"钩子"缺失（如 Round 3 中 Superpowers skills 完全未触发）是主要障碍。

---

## 8. 对 h-codeflow-framework 的启发

### 8.1 值得借鉴的设计

1. **Superpowers 的决策点机制**：在 brainstorming 阶段主动向用户提问关键决策（如 Skill 标记的三选一），而非 AI 自行决定。h-codeflow-framework 的 Arch Agent 可以在 spec 审核环节加入类似的"必问清单"。

2. **Spec-Kit 的 API 契约分离**：将 API 契约文档从 spec 中独立出来，让前后端可以并行开发。h-codeflow-framework 的 Spec 模板可以增加"API Contract"制品类型。

3. **OpenSpec / GSD 的 TRANSITIONS 映射表**：声明式状态机设计（Round 3/4）比 if/elif（Round 2）和元组集合（Round 1）都更清晰。可以作为 h-codeflow-framework 的编码规范推荐。

4. **OpenSpec 的归档机制**：变更完成后归档 + 可选同步 specs，天然支持知识沉淀。h-codeflow-framework 的 harvest 机制可以借鉴这个"变更级归档"思路。

5. **GSD 的 verify step 设计**：独立 subagent 运行 verify（不由执行 agent 自我检查），产出结构化 VERIFICATION.md，区分"自动可验证"和"需要人工验证（human_needed）"两类检查项。这比任何前三轮的自我 review 都更可靠。

6. **GSD 的 worktree 隔离**：每个 execute task 在独立 git worktree 里运行，主 session 上下文不受执行细节污染。适合长周期、多 phase 项目的上下文管理。

### 8.2 需要避免的做法

1. **Spec-Kit 的文档冗余**：状态机规则在 4 份文档中重复，导致 token 浪费和一致性风险。框架应确保"每条规则只定义一次"。

2. **前三轮共同的检查点失效**：无论设计多少 checkpoint，AI 倾向于一口气写完。GSD 通过独立 verify subagent 绕过了这个问题，但其他工具没有。框架应考虑用工具化手段（独立 verify 而非自我 review）替代依赖 AI 自律的检查点。

3. **reason 半成品模式**：API 接了参数但不用，比"明确跳过"更差。框架的 spec 审核应检查"API 参数是否都有对应的持久化或处理逻辑"。

4. **工具间钩子缺失**：OpenSpec 流程中 Superpowers skills 完全未触发，说明工具组合的"集成点"设计不足。h-codeflow-framework 在集成外部工具时，需要设计明确的触发条件。

5. **GSD 的场景错配**：GSD 的"新项目初始化仪式"（map → new-project → roadmap）对"已有项目加功能"场景代价过高，1 小时仅在走流程前置，没有实质代码产出。框架在设计入口命令时应区分"新项目"和"现有项目加功能"两种场景，提供轻量接入路径。

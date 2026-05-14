# 三工具横向对比：Superpowers vs Spec-Kit vs OpenSpec

> **阅读须知（重要）**
>
> 这份对比报告基于 **N=1 的单次实验**：每个工具只跑了一次、同一需求、同一操作者、同一时间段。文中所有数据（耗时、token、代码行数）都是单次观察值，不是工具能力的统计结论。
>
> **特别注意**：
> - **评分（5/10、8/10）** 偏重"功能覆盖完整性 + 主观体验"，不计测试覆盖率/工程质量 —— 所以 R1 测试最多反而评分最低，是因为前端缺了创建关联和删除
> - **R2/R3 零干预** 不等于质量更高 —— R2 的死代码、R3 的 Skill 简化 都是 AI 自行决定的，用户不知情
> - **顺序效应**：R1 → R2 → R3 是固定顺序，操作者熟悉度递增。换顺序结论可能不同
> - **工具版本**：Spec-Kit v0.8.10、OpenSpec npm `@latest`（2026-05）、Superpowers 跟随 Claude Code 版本
>
> 完整客观性声明见 [README.md](../README.md#如何阅读本报告)。

## 1. 概览

| 指标 | R1: Superpowers | R2: Spec-Kit | R3: OpenSpec |
|------|-----------------|--------------|--------------|
| **耗时** | 1h 4m | 44m | **24m** |
| **Context** | 96.1k（48%） | 123k（61%） | **91.9k（46%）** |
| **代码行数** | +2123 | +541 | +305 |
| **测试** | **19 个** | 0 | 0 |
| **提交** | **11 个** | 0 | 0 |
| **文档量** | 1,266 行（2 份） | 1,121 行（9 份） | 287 行（6 份） |
| **人工干预** | 5 次（决策审批） | 0 次 | 0 次 |
| **用户评分** | **5/10** | **8/10** | **8/10** |
| **Slash commands** | 0（AI 自动触发技能） | 6（用户手动） | 3（用户手动） |

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

**Round 3（OpenSpec）— 映射表**

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
- **最佳设计**：三个版本中最优雅的状态机实现

**评判**：Round 3 > Round 1 > Round 2。映射表在可读性、可扩展性和错误信息质量上全面胜出。

### 2.2 错误处理模式

| 模式 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| Service→API | 直接抛 `HTTPException` | 抛 `ValueError`，API 层捕获转 422 | 返回 `tuple[data, error]`，API 层判断 |
| 激活校验 | 逐项检查，逐项抛异常 | 逐项检查，逐项抛异常 | **收集所有错误，一次返回** |
| 错误信息 | "未关联有效的 Model" | "未关联 Model，无法激活" | "未关联有效的 Model；未关联有效的 Prompt" |
| 删除返回 | `bool` | `bool` | `tuple[bool, str]` |

Round 3 的"错误收集"模式最用户友好 — 如果同时缺 Model 和 Prompt，一次性告知而非只报第一个。Round 2 的删除返回 `bool` 无法区分 404 和 422，Round 3 用 `tuple` 解决了这个问题。

### 2.3 数据加载策略

| 策略 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| 列表查询 | `joinedload(Agent.model, Agent.prompt)` | 直接查询 | `joinedload(Agent.model, Agent.prompt)` |
| 详情查询 | `joinedload` | 直接查询 | `joinedload` |
| 排序 | 无 | 无 | `order_by(created_at.desc())` |
| 分页 | `skip + limit`，返回 `total` | `skip + limit`，无 total | `skip + limit`，无 total |

Round 1 和 Round 3 都用了 `joinedload` 避免 N+1 查询，Round 2 没有。Round 1 额外返回了 `total` 用于分页。

### 2.4 数据模型变更

| 变更 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| Agent 新字段 | 无 | `activated_at`, `deactivated_at` | 无 |
| Skill 新字段 | 无 | `is_active` | 无 |
| 总变更量 | **零** | **3 个字段** | **零** |

Round 2 是唯一修改了数据模型的 — 加了时间戳和 Skill 可用性字段。Round 1 和 Round 3 选择了"零模型变更"的轻量路径。

### 2.5 Schema 设计

| 策略 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| 列表响应转换 | `_agent_to_read()` 手动构造 dict | `_enrich_agent()` 动态附加属性 | `AgentReadWithRelations` 继承 |
| 状态变更 schema | `AgentStatusChange` | `AgentStatusUpdate` | `AgentStatusChange` |

Round 1 的手动 dict 构造有维护风险（新增字段需同步更新）。Round 3 的 `AgentReadWithRelations(AgentRead)` 继承模式最干净 — 新增基础字段自动继承，只需添加关联字段。

### 2.6 前端功能覆盖

| 功能 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| 状态筛选 | el-tabs | **el-radio-group** | **el-tabs** |
| Model/Prompt 列 | `model_name` / `prompt_name` | `model_name` / `prompt_title` | `model_name` / `prompt_name` |
| 创建关联选择 | **无** | **有**（el-select + API 调用） | **有**（el-select + API 调用） |
| 删除按钮 | **无** | **有**（INACTIVE 可删） | **有**（INACTIVE 可删） |
| 分页 | **有**（el-pagination） | 无 | 无 |
| 表单验证 | 无规则 | `el-form-item rules` | 无规则 |
| 错误提示 | 拦截器兜底 | ElMessage.error | **直接展示后端 detail** |
| 描述列 | 无 | 无 | **有** |

Round 2 和 Round 3 在功能覆盖上相当，都有创建关联和删除。Round 1 独有分页但缺关联选择和删除。Round 3 独有描述列展示。

---

## 3. 任务分解策略

### 3.1 粒度与数量

| 工具 | 任务数 | 组织方式 | 文档行数 |
|------|--------|---------|---------|
| Superpowers | 23 个任务，7 个 Phase | 按用户故事分组 | 1,118 行 |
| Spec-Kit | 7 组，22 个子任务 | 按技术层分组 | 212 行 |
| OpenSpec | 8 个 Task，43 个 Step | 按组件顺序 | 42 行 |

**Superpowers** 最重：23 个任务按 Phase 组织（Setup → Foundational → 4 个 User Story → Polish），每个 Phase 有显式 Checkpoint。

**Spec-Kit** 最薄：7 个逻辑组，但实际执行时被大幅合并（前端 4 个 Phase 合并为一次 Write）。

**OpenSpec** 最精细：8 个大任务下嵌套 Step，但文档本身只有 42 行 — 把细节留给了执行阶段。

### 3.2 检查点设计

| 工具 | 有检查点？ | 检查点位置 | 实际执行情况 |
|------|-----------|-----------|-------------|
| Superpowers | **5 个显式 Checkpoint** | 每个 Phase 结束后 | 部分跳过（只做了最终 spec review） |
| Spec-Kit | **无**（只有最终验证） | 仅末尾 2 个验证任务 | 跳过了逐任务验证 |
| OpenSpec | **嵌入式**（每个 Task 有 Run 命令） | 每个组件完成后 | 大部分执行了 |

三个工具的检查点都没被严格执行。Superpowers 设计了 5 个但只做了最终 1 个；Spec-Kit 设计了 0 个；OpenSpec 嵌入了验证命令但也不是每个都跑了。

**结论**：检查点设计在 AI 执行中基本失效 — AI 倾向于一口气写完，不愿中途停下来验证。

### 3.3 任务完成忠实度

| 工具 | 计划的任务 | 实际完成 | 偏差 |
|------|-----------|---------|------|
| Superpowers | 23 个 | 23 个标记完成 | 忠实（但跳过了逐任务 review） |
| Spec-Kit | 22 个子任务 | 全部标记完成 | 合并执行，跳过 checkpoint |
| OpenSpec | 43 个 step | 全部标记 [x] | 忠实（按 step 粒度执行） |

---

## 4. 设计文档质量

### 4.1 API 契约精度

| 工具 | API 契约形式 | 精度 | 可对接性 |
|------|-------------|------|---------|
| Superpowers | 设计文档中内嵌 schema 定义 | 中 — 有字段定义，无 JSON 示例 | 需要阅读代码才能对接 |
| Spec-Kit | **独立的 contracts/agents-api.md** | **高 — 含请求/响应 JSON 示例** | **可直接作前后端对接文档** |
| OpenSpec | spec 文件中的 WHEN/THEN 场景 | 中 — 有场景但无 JSON | 需要补充才能对接 |

**Spec-Kit 胜出**：258 行的独立 API 契约文档，精确到每个端点的请求体和响应体 JSON 示例，是三个工具中唯一能直接指导前后端并行开发的文档。

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

### 5.2 关键决策对比

**决策 A：Skill 不可用如何处理？**

| 工具 | 决策 | 用户参与？ | 结果 |
|------|------|-----------|------|
| Superpowers | 主动发现歧义，提供 3 个选项 | **是** — 用户选择跳过 | 需求协商，无遗漏 |
| Spec-Kit | 直接实现 `is_active` 字段 + 批量 UPDATE | 否 | **最完整的实现**，但用户不知情 |
| OpenSpec | 选择"间接判断"，不修改代码 | 否 | 最轻量但可追溯性差 |

这个对比揭示了一个关键差异：**Superpowers 倾向于"问用户"，Spec-Kit 倾向于"做更多"，OpenSpec 倾向于"做更少"**。

**决策 B：reason 字段如何处理？**

| 工具 | 决策 | 问题 |
|------|------|------|
| Superpowers | 标记为可选跳过 | 无 — 诚实跳过 |
| Spec-Kit | 接收参数但不持久化 | **半成品** — API 接了参数却丢弃 |
| OpenSpec | 同 Spec-Kit | 同上 |

三个工具都没有做好 reason 的处理。Superpowers 的"诚实跳过"比 Spec-Kit/OpenSpec 的"接了不用"更干净。

**决策 C：创建 Agent 时是否关联 Model/Prompt？**

| 工具 | 决策 | 前端实现 |
|------|------|---------|
| Superpowers | 后端 schema 支持，前端未实现 | **缺失** |
| Spec-Kit | 完整实现（下拉 + API 调用） | **完整** |
| OpenSpec | 完整实现（下拉 + API 调用） | **完整** |

这是 Superpowers 评分低（5/10）的直接原因 — 后端能力存在但前端没有暴露给用户。

### 5.3 "零干预"的真相

Round 2 和 Round 3 都是零人工干预。但这不代表质量更高：

- Round 2 的死代码（`if ... and False: pass`）没有用户发现
- Round 2 的 reason 被 AI 自行降级，用户不知情
- Round 3 的 Skill 简化替代，用户不知情
- Round 3 的 reason 半成品，用户不知情

**Superpowers 的 5 次干预全部是 AI 主动征求用户意见，不是纠偏**。这意味着 Superpowers 的流程设计中内置了"关键决策点必须用户确认"的机制，而 Spec-Kit 和 OpenSpec 的流程中缺少这个机制。

---

## 6. Token 效率

### 6.1 归一化对比

| 指标 | Superpowers | Spec-Kit | OpenSpec |
|------|-------------|----------|----------|
| Token 消耗 | 96.1k | 123k | **91.9k** |
| 有效代码行（后端+前端新增） | ~520 行 | ~428 行 | ~430 行 |
| Token / 代码行 | **185** | 287 | **214** |
| 业务规则完整覆盖数 | 3/5 | **4/5** | 3/5 |
| Token / 覆盖规则 | 32k | 31k | **31k** |
| 用户评分 | 5 | 8 | 8 |
| Token / 评分点 | **19.2k** | 15.4k | **11.5k** |

### 6.2 效率解读

**Token/代码行**：Superpowers 最省（185 token/行），但部分原因是它包含了 19 个测试（278 行测试代码），这些测试代码的生成也需要 token。

**Token/覆盖规则**：三个工具几乎相同（31-32k/规则），说明"理解一条业务规则"的成本是稳定的，差异主要在流程开销。

**Token/评分点**：OpenSpec 最优（11.5k/分），Superpowers 最差（19.2k/分）。这反映了 Superpowers 的流程开销（brainstorming + 设计文档 + 实施计划 + 子代理报告）占用了大量 token，但最终功能覆盖反而最少。

### 6.3 流程开销占比

| 开销类型 | Superpowers | Spec-Kit | OpenSpec |
|---------|-------------|----------|----------|
| 固定开销（System + Skills 元数据） | ~22k（23%） | ~15k（12%） | ~17k（18%） |
| 制品生成（设计文档 + 计划 + spec） | ~30k（31%） | ~45k（37%） | ~15k（16%） |
| 子代理报告 | ~25k（26%） | ~5k（4%） | 0 |
| 实际编码 | ~19k（20%） | ~58k（47%） | ~60k（65%） |

**关键发现**：Superpowers 只有 20% 的 token 花在实际编码上，80% 花在流程上。OpenSpec 65% 的 token 用于编码，是最"高效"的。Spec-Kit 47% 用于编码但 37% 用于制品生成（且有大量冗余）。

---

## 7. 综合评价

### 7.1 工具性格画像

| | Superpowers | Spec-Kit | OpenSpec |
|---|-------------|----------|----------|
| **性格** | 谨慎的顾问 | 严谨的工程师 | 高效的执行者 |
| **核心流程** | brainstorm → spec → plan → execute | constitution → specify → plan → tasks → implement | propose → apply → archive |
| **用户角色** | 决策者（关键节点审批） | 触发者（打 slash command） | 触发者（打 slash command） |
| **质量保障** | 测试 + review + 设计文档（三层） | 文档完备（但实现阶段薄弱） | 流程轻量（但缺少 review 机制） |
| **最大优势** | 需求理解最深入（主动发现歧义） | API 契约文档质量最高 | 速度最快、Token 最省 |
| **最大劣势** | 流程仪式感重，功能覆盖反而最少 | 文档冗余，implement 跳过 checkpoint | Superpowers skills 完全"悬空" |

### 7.2 场景推荐

| 场景 | 推荐工具 | 原因 |
|------|---------|------|
| **需求模糊、需要澄清** | Superpowers | brainstorming 阶段能主动发现歧义 |
| **需要前后端并行开发** | Spec-Kit | API 契约文档可独立指导对接 |
| **需求明确、快速交付** | OpenSpec | 3 步完成，速度最快 |
| **团队协作、需要文档沉淀** | Spec-Kit | 多份文档结构清晰，归档体系完善 |
| **个人项目、追求效率** | OpenSpec | Token 消耗最低，流程最简 |
| **复杂业务规则、需要质量保障** | Superpowers | 测试覆盖 + spec review + 子代理执行 |

### 7.3 工具间的互补性

三轮实验揭示了一个重要发现：**三个工具的核心能力是互补的，而非竞争的**。

- Superpowers 的 brainstorming 质量最高（主动发现需求歧义）
- Spec-Kit 的 API 契约文档最有价值（可指导前后端并行开发）
- OpenSpec 的执行效率最高（最少 token、最快速度）

如果组合使用：用 Superpowers 的 brainstorming 澄清需求 → 用 Spec-Kit 的契约文档指导开发 → 用 OpenSpec 的效率执行 — 理论上可以取三者之长。但实际操作中，工具间的"钩子"缺失（如 Round 3 中 Superpowers skills 完全未触发）是主要障碍。

---

## 8. 对 h-codeflow-framework 的启发

### 8.1 值得借鉴的设计

1. **Superpowers 的决策点机制**：在 brainstorming 阶段主动向用户提问关键决策（如 Skill 标记的三选一），而非 AI 自行决定。h-codeflow-framework 的 Arch Agent 可以在 spec 审核环节加入类似的"必问清单"。

2. **Spec-Kit 的 API 契约分离**：将 API 契约文档从 spec 中独立出来，让前后端可以并行开发。h-codeflow-framework 的 Spec 模板可以增加"API Contract"制品类型。

3. **OpenSpec 的 TRANSITIONS 映射表**：声明式状态机设计（Round 3）比 if/elif（Round 2）和元组集合（Round 1）都更清晰。可以作为 h-codeflow-framework 的编码规范推荐。

4. **OpenSpec 的归档机制**：变更完成后归档 + 可选同步 specs，天然支持知识沉淀。h-codeflow-framework 的 harvest 机制可以借鉴这个"变更级归档"思路。

### 8.2 需要避免的做法

1. **Spec-Kit 的文档冗余**：状态机规则在 4 份文档中重复，导致 token 浪费和一致性风险。框架应确保"每条规则只定义一次"。

2. **三工具共同的检查点失效**：无论设计多少 checkpoint，AI 倾向于一口气写完。框架应考虑用自动化手段（如 CI 检查、测试覆盖率门禁）替代依赖 AI 自律的检查点。

3. **reason 半成品模式**：API 接了参数但不用，比"明确跳过"更差。框架的 spec 审核应检查"API 参数是否都有对应的持久化或处理逻辑"。

4. **工具间钩子缺失**：OpenSpec 流程中 Superpowers skills 完全未触发，说明工具组合的"集成点"设计不足。h-codeflow-framework 在集成外部工具时，需要设计明确的触发条件。

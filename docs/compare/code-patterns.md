# 代码模式对比

> 状态机之外，四轮在错误处理、数据加载、数据模型变更、Schema 设计、前端功能覆盖上各有取舍。

## 错误处理模式

| 模式 | Round 1 | Round 2 | Round 3 | Round 4 |
|------|---------|---------|---------|---------|
| Service→API | 直接抛 `HTTPException` | 抛 `ValueError`，API 层捕获转 422 | 返回 `tuple[data, error]`，API 层判断 | 抛**独立异常类**（InvalidTransitionError/ActivationNotReadyError），API 层映射不同 HTTP 码 |
| 激活校验 | 逐项检查，逐项抛异常 | 逐项检查，逐项抛异常 | **收集所有错误，一次返回** | 逐项检查，遇第一个失败即抛出 |
| 错误信息 | "未关联有效的 Model" | "未关联 Model，无法激活" | "未关联有效的 Model；未关联有效的 Prompt" | "激活失败：Agent 未关联提示词" |
| 删除返回 | `bool` | `bool` | `tuple[bool, str]` | `bool`（None 表示 404） |
| 转换失败码 | 422 | 422 | 422 | **409**（明确区分） |

**Round 3 的"错误收集"模式最用户友好** —— 如果同时缺 Model 和 Prompt，一次性告知而非只报第一个。**R4 是唯一将"非法状态转换"（409）和"激活前置失败"（422）显式区分为两个不同 HTTP 码的实现，语义最精确。**

## 数据加载策略

| 策略 | Round 1 | Round 2 | Round 3 | Round 4 |
|------|---------|---------|---------|---------|
| 列表查询 | `joinedload(Agent.model, Agent.prompt)` | 直接查询 | `joinedload(Agent.model, Agent.prompt)` | `selectinload(Agent.model, Agent.prompt)` |
| 详情查询 | `joinedload` | 直接查询 | `joinedload` | `joinedload` |
| 排序 | 无 | 无 | `order_by(created_at.desc())` | 无 |
| 分页 | `skip + limit`，返回 `total` | `skip + limit`，无 total | `skip + limit`，无 total | `skip + limit`，无 total |

**Round 1 和 Round 3 都用了 `joinedload` 避免 N+1 查询**，Round 2 没有。**R4 GSD 在列表用 `selectinload`（批量 IN 查询），详情用 `joinedload`（JOIN 查询），是对两种场景各自最优解的应用。**

## 数据模型变更

| 变更 | Round 1 | Round 2 | Round 3 | Round 4 |
|------|---------|---------|---------|---------|
| Agent 新字段 | 无 | `activated_at`, `deactivated_at` | 无 | 无 |
| Skill 新字段 | 无 | `is_active` | 无 | 无（有意 out-of-scope） |
| 新增表 | 无 | 无 | 无 | **`AgentStatusHistory`**（独立审计日志表） |
| 总变更量 | **零** | **3 个字段** | **零** | **1 张新表（5 字段）** |

**Round 2** 是唯一修改了现有模型字段的 —— 加了时间戳和 Skill 可用性字段。**R4 选择了独立 `AgentStatusHistory` 表（append-only）而非在 Agent 上加时间戳字段，设计更正交。**

## Schema 设计

| 策略 | Round 1 | Round 2 | Round 3 | Round 4 |
|------|---------|---------|---------|---------|
| 列表响应转换 | `_agent_to_read()` 手动构造 dict | `_enrich_agent()` 动态附加属性 | `AgentReadWithRelations` 继承 | `AgentReadWithRelations` 继承（同 R3） |
| 状态变更 schema | `AgentStatusChange` | `AgentStatusUpdate` | `AgentStatusChange` | `AgentStatusChange` + 新增 `AgentStatusHistoryRead`（历史记录查询） |

Round 1 的手动 dict 构造有维护风险（新增字段需同步更新）。**Round 3 / Round 4 的 `AgentReadWithRelations(AgentRead)` 继承模式最干净** —— 新增基础字段自动继承，只需添加关联字段。

## 前端功能覆盖

| 功能 | Round 1 | Round 2 | Round 3 | Round 4 |
|------|---------|---------|---------|---------|
| 状态筛选 | el-tabs | **el-radio-group** | **el-tabs** | `el-select` 下拉 |
| Model/Prompt 列 | `model_name` / `prompt_name` | `model_name` / `prompt_title` | `model_name` / `prompt_name` | `model_name` / `prompt_name`（null→"未关联"） |
| 创建关联选择 | **无** | **有**（el-select + API 调用） | **有**（el-select + API 调用） | **有**（懒加载，dialog 开启时才拉取） |
| 删除按钮 | **无** | **有**（INACTIVE 可删） | **有**（INACTIVE 可删） | **有**（INACTIVE 可删） |
| 分页 | **有**（el-pagination） | 无 | 无 | **有**（el-pagination） |
| 表单验证 | 无规则 | `el-form-item rules` | 无规则 | **`el-form-item rules`**（名称必填） |
| 错误提示 | 拦截器兜底 | ElMessage.error | **直接展示后端 detail** | **全局拦截器** → `ElMessage.error(detail)` |
| 确认对话框 | 部分 | 部分 | 部分 | **所有操作均有** `ElMessageBox.confirm` |
| 描述列 | 无 | 无 | **有** | 无（在 dialog 填写，不展示在表格） |

**R4 是四轮中功能最完整的前端实现**。懒加载（dialog 打开时才拉取 Model/Prompt 列表）是唯一正确处理此性能问题的轮次。所有操作均有确认弹框也是 R4 独有的。

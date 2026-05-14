# 代码模式对比

> 状态机之外，三轮在错误处理、数据加载、数据模型变更、Schema 设计、前端功能覆盖上各有取舍。

## 错误处理模式

| 模式 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| Service→API | 直接抛 `HTTPException` | 抛 `ValueError`，API 层捕获转 422 | 返回 `tuple[data, error]`，API 层判断 |
| 激活校验 | 逐项检查，逐项抛异常 | 逐项检查，逐项抛异常 | **收集所有错误，一次返回** |
| 错误信息 | "未关联有效的 Model" | "未关联 Model，无法激活" | "未关联有效的 Model；未关联有效的 Prompt" |
| 删除返回 | `bool` | `bool` | `tuple[bool, str]` |

**Round 3 的"错误收集"模式最用户友好** —— 如果同时缺 Model 和 Prompt，一次性告知而非只报第一个。Round 2 的删除返回 `bool` 无法区分 404 和 422，Round 3 用 `tuple` 解决了这个问题。

## 数据加载策略

| 策略 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| 列表查询 | `joinedload(Agent.model, Agent.prompt)` | 直接查询 | `joinedload(Agent.model, Agent.prompt)` |
| 详情查询 | `joinedload` | 直接查询 | `joinedload` |
| 排序 | 无 | 无 | `order_by(created_at.desc())` |
| 分页 | `skip + limit`，返回 `total` | `skip + limit`，无 total | `skip + limit`，无 total |

**Round 1 和 Round 3 都用了 `joinedload` 避免 N+1 查询**，Round 2 没有。Round 1 额外返回了 `total` 用于分页。

## 数据模型变更

| 变更 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| Agent 新字段 | 无 | `activated_at`, `deactivated_at` | 无 |
| Skill 新字段 | 无 | `is_active` | 无 |
| 总变更量 | **零** | **3 个字段** | **零** |

**Round 2 是唯一修改了数据模型的** —— 加了时间戳和 Skill 可用性字段。Round 1 和 Round 3 选择了"零模型变更"的轻量路径。

这是一把双刃剑：Round 2 的实现最完整（业务规则 5 的时间戳是它独有的），但也带来了数据迁移的成本和复杂度。

## Schema 设计

| 策略 | Round 1 | Round 2 | Round 3 |
|------|---------|---------|---------|
| 列表响应转换 | `_agent_to_read()` 手动构造 dict | `_enrich_agent()` 动态附加属性 | `AgentReadWithRelations` 继承 |
| 状态变更 schema | `AgentStatusChange` | `AgentStatusUpdate` | `AgentStatusChange` |

Round 1 的手动 dict 构造有维护风险（新增字段需同步更新）。**Round 3 的 `AgentReadWithRelations(AgentRead)` 继承模式最干净** —— 新增基础字段自动继承，只需添加关联字段。

## 前端功能覆盖

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

**Round 2 和 Round 3 在功能覆盖上相当**，都有创建关联和删除。Round 1 独有分页但缺关联选择和删除——这是 Round 1 评分仅 5/10 的直接原因。Round 3 独有描述列展示。

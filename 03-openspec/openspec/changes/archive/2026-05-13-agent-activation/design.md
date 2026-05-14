## Context

当前项目已有 Agent 数据模型（含 `AgentStatus` 枚举：DRAFT/ACTIVE/INACTIVE）和基础的 Pydantic Schema（`AgentCreate`、`AgentRead`）。前端有路由 `/agents` 和占位页面 `AgentList.vue`，以及一个简单的 Pinia store。

后端已有 Model 和 Prompt 的完整 CRUD 实现作为参考模式：`endpoints.py` 中按路由分组定义端点，`services/` 中按实体拆分 Service 类，`schemas/schema.py` 集中管理 Pydantic 模型。

**现有模式总结：**
- 路由注册：`router.py` 中 `include_router` + prefix
- 端点风格：函数式，`Depends(get_db)` 注入 Session，手动实例化 Service
- 响应格式：统一 `Response[T]` 包装（`{code, data, message}`）
- 错误处理：`HTTPException` 抛出，由 FastAPI 统一处理

## Goals / Non-Goals

**Goals:**
- 实现 Agent CRUD + 状态切换的完整后端 API
- 状态机规则和前置条件校验在服务层实现，保持端点层轻薄
- 前端 Agent 管理页面包含列表、状态操作、创建表单
- 激活失败时返回清晰的错误信息，前端能展示给用户

**Non-Goals:**
- 状态变更历史记录（本次不实现审计日志）
- Skill 可用性标记的具体展示逻辑（停用时仅标记，不深入 Skill 管理）
- Agent 编辑功能（修改名称、关联等），留后续迭代

## Decisions

### 1. 状态切换用独立端点 `PATCH /agents/{id}/status`

**选择**：单独的状态切换端点，而非通用 `PATCH /agents/{id}`

**理由**：状态变更涉及复杂的业务规则（前置条件、删除保护），与普通字段更新逻辑差异大。独立端点让校验逻辑清晰、错误信息精准，也便于后续添加审计。

**替代方案**：通用 PATCH 端点 + 条件分支。风险是逻辑混杂，且通用更新需要处理更多边界情况。

### 2. 服务层集中状态机逻辑

**选择**：在 `AgentService` 中封装状态机转换规则和校验

**理由**：业务规则（状态转换合法性、关联校验）集中在一处，端点只做参数解析和结果返回。与现有 ModelService/PromptService 模式一致。

### 3. 前端 API 调用用独立文件

**选择**：新建 `frontend/src/api/agents.js`，与 `prompts.js` 模式一致

**理由**：保持项目现有组织方式，Store 通过 api 模块调用。

### 4. 创建表单中 Model/Prompt 为可选

**选择**：创建时不强制选择 Model 和 Prompt，可在创建后通过激活前关联

**理由**：Agent 初始为 DRAFT 状态，激活才校验关联。创建阶段允许空关联降低使用门槛。

## Risks / Trade-offs

- **[Skill 停用标记]** → 当前 Skill 模型没有 `is_available` 字段，需求说停用时标记 Skill 不可用。本次通过 Agent 状态间接判断即可——Agent 为 INACTIVE 时，其 Skill 自然不可用。不需要给 Skill 加字段。
- **[并发状态切换]** → 同一 Agent 短时间内多次状态切换，SQLite 单写者模式下风险较低。如需更强保障后续可加乐观锁（version 字段）。
- **[删除级联]** → 删除 Agent 时关联的 Skill 如何处理？当前 Skill 有 `agent_id` 外键但未设 cascade。应在删除前检查并提示，或由 SQLite 约束处理。

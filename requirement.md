# Agent 激活/停用功能需求

## 背景

AI Prompt Lab 是一个 AI 智能体管理平台。系统中有 4 个核心实体：Model（模型）、Prompt（提示词模板）、Agent（智能体）、Skill（工具能力）。

Agent 是核心实体，它将 Model 和 Prompt 组合在一起形成一个可运行的智能体。Agent 当前有 3 种状态：DRAFT（草稿）、ACTIVE（已激活）、INACTIVE（已停用）。

目前 Agent 只有数据模型定义，没有激活/停用的业务逻辑、API 端点和前端管理页面。

## 功能目标

实现 Agent 的状态管理功能，包括：激活、停用操作，配套的业务规则验证，以及前端管理页面。

## 业务规则

### 状态转换规则

```
DRAFT ──激活──▶ ACTIVE
ACTIVE ──停用──▶ INACTIVE
INACTIVE ──激活──▶ ACTIVE
```

- DRAFT 不能直接转为 INACTIVE（没有意义，草稿就是未激活的）
- 不允许跳级转换

### 激活前置条件

将 Agent 从 DRAFT 或 INACTIVE 激活为 ACTIVE 时，必须满足：
1. 已关联有效的 Model（model_id 不为空，且对应的 Model 存在）
2. 已关联有效的 Prompt（prompt_id 不为空，且对应的 Prompt 存在）

### 停用处理

将 Agent 从 ACTIVE 停用为 INACTIVE 时：
1. 直接允许停用，无需额外条件
2. 关联该 Agent 的所有 Skill 应标记为不可用（不影响 Skill 本身，只是表示"该 Agent 的工具当前不可用"）

### 删除保护

- ACTIVE 状态的 Agent 不允许被删除
- 必须先停用为 INACTIVE，才能删除

## 后端需求

### API 端点

1. **GET /api/v1/agents/** — 获取 Agent 列表（分页，支持按状态筛选）
2. **GET /api/v1/agents/{id}** — 获取单个 Agent 详情
3. **POST /api/v1/agents/** — 创建 Agent（默认 DRAFT 状态）
4. **PATCH /api/v1/agents/{id}/status** — 切换 Agent 状态
   - 请求体：`{"status": "ACTIVE", "reason": "准备上线"}`
   - 需执行业务规则验证
   - 验证失败返回 422 + 具体错误信息
5. **DELETE /api/v1/agents/{id}** — 删除 Agent（仅 INACTIVE 和 DRAFT 可删）

### 服务层

- AgentService：状态切换的业务逻辑和规则验证
- 与 Model 和 Prompt 的关联校验
- 状态变更记录（可选：记录变更时间和原因）

## 前端需求

### Agent 管理页面

1. **Agent 列表**：
   - 显示所有 Agent，包含名称、状态标签、关联的 Model 和 Prompt 名称
   - 支持按状态筛选（全部 / 草稿 / 已激活 / 已停用）
   - 分页

2. **状态切换操作**：
   - 每个 Agent 行上有操作按钮：
     - DRAFT 状态：显示"激活"按钮
     - ACTIVE 状态：显示"停用"按钮
     - INACTIVE 状态：显示"激活"和"删除"按钮
   - 点击操作后弹出确认对话框，显示操作影响说明
   - 激活失败时显示具体原因（如"未关联 Model"）

3. **创建 Agent 表单**：
   - 名称、描述
   - 选择关联的 Model（下拉列表）
   - 选择关联的 Prompt（下拉列表）
   - 创建后为 DRAFT 状态

## 技术约束

- 后端：FastAPI + SQLAlchemy 2.x + SQLite
- 前端：Vue 3 + Element Plus + Pinia
- 测试：后端 pytest，前端可选手动验证
- 遵循项目现有的代码风格和目录结构

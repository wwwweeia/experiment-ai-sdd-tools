# Agent 状态管理功能设计

## 概述

为 AI Prompt Lab 平台实现 Agent 的完整生命周期管理：创建、激活、停用、删除，包含业务规则验证和前端管理页面。

## 业务规则

### 状态机

```
DRAFT ──激活──▶ ACTIVE
ACTIVE ──停用──▶ INACTIVE
INACTIVE ──激活──▶ ACTIVE
```

- DRAFT 不能直接转为 INACTIVE
- 不允许跳级转换

### 激活前置条件

从 DRAFT 或 INACTIVE 激活为 ACTIVE 时：
1. model_id 不为空，且对应 Model 存在
2. prompt_id 不为空，且对应 Prompt 存在

### 停用处理

ACTIVE → INACTIVE 直接允许，无需额外条件。Skill 停用标记本期跳过（Skill 功能未实现）。

### 删除保护

ACTIVE 状态不允许删除，必须先停用。

## API 设计

### 方案：专用状态端点

状态变更是有业务语义的操作，与普通字段更新本质不同，使用独立端点。

### 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/agents/` | 列表，支持 `?status=active&skip=0&limit=20` |
| GET | `/api/v1/agents/{id}` | 详情 |
| POST | `/api/v1/agents/` | 创建，默认 DRAFT |
| PATCH | `/api/v1/agents/{id}/status` | 状态变更 |
| DELETE | `/api/v1/agents/{id}` | 删除，ACTIVE 拒绝 |

### Schemas

```python
class AgentCreate(BaseModel):
    name: str
    description: str | None = None
    model_id: int | None = None
    prompt_id: int | None = None

class AgentRead(BaseModel):
    id: int
    name: str
    description: str | None
    model_id: int | None
    prompt_id: int | None
    status: AgentStatus
    created_at: datetime
    model_name: str | None = None
    prompt_name: str | None = None

class AgentStatusChange(BaseModel):
    status: AgentStatus
    reason: str | None = None

class AgentQuery(BaseModel):
    status: AgentStatus | None = None
    skip: int = 0
    limit: int = 20
```

### 状态机逻辑

```
change_status(agent_id, target, reason):
    1. 查 agent，不存在 → 404
    2. 校验转换合法性（DRAFT→ACTIVE, ACTIVE→INACTIVE, INACTIVE→ACTIVE）
       非法 → 422 "不允许从 {current} 转换为 {target}"
    3. 若目标是 ACTIVE：
       - model_id 为空或 Model 不存在 → 422 "未关联有效的 Model"
       - prompt_id 为空或 Prompt 不存在 → 422 "未关联有效的 Prompt"
    4. 更新状态，commit
```

### 列表查询

使用 joinedload 一次性加载关联的 Model/Prompt，避免 N+1。

## 前端设计

### 文件

| 文件 | 用途 |
|------|------|
| `frontend/src/api/agent.js` | Agent HTTP 客户端 |
| `frontend/src/stores/agent.js` | Agent Pinia Store |
| `frontend/src/views/AgentList.vue` | Agent 管理页面 |

### 页面结构

- 顶部：标题 + "新建 Agent" 按钮
- 筛选栏：状态 Tab（全部 / 草稿 / 已激活 / 已停用）
- 表格：名称、描述、关联模型、关联提示词、状态标签、操作按钮
- 底部：分页

### 操作按钮

| 状态 | 按钮 |
|------|------|
| DRAFT | 激活 |
| ACTIVE | 停用 |
| INACTIVE | 激活、删除 |

### 交互

- 激活/停用：confirm 确认 → PATCH status → 刷新 / 错误提示
- 删除：confirm 二次确认 → DELETE → 刷新
- 新建：dialog 弹窗表单 → POST → 刷新

### 状态标签

- DRAFT → el-tag info（灰色）
- ACTIVE → el-tag success（绿色）
- INACTIVE → el-tag danger（红色）

### Store

```javascript
useAgentStore:
  state: agents[], loading, pagination{skip,limit,total}, filterStatus
  actions: fetchAgents(), changeStatus(id, status, reason), deleteAgent(id), createAgent(data)
```

新建表单的 Model/Prompt 下拉：组件 onMounted 时单独调用对应 API 填充。

## 技术约束

- 后端：FastAPI + SQLAlchemy 2.x + SQLite
- 前端：Vue 3 + Element Plus + Pinia
- 遵循项目现有代码模式和目录结构

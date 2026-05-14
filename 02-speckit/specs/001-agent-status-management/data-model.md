# Data Model: Agent 状态管理

**Feature**: Agent 激活/停用功能
**Date**: 2026-05-13

## Entity Changes

### Agent（修改现有模型）

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| id | Integer | PK, auto-increment | - | 主键 |
| name | String(100) | NOT NULL | - | Agent 名称 |
| description | Text | NULL | - | 描述 |
| model_id | Integer (FK → models.id) | NULL | - | 关联模型 |
| prompt_id | Integer (FK → prompts.id) | NULL | - | 关联提示词 |
| status | Enum(draft/active/inactive) | NOT NULL | draft | 状态 |
| activated_at | DateTime | NULL | - | 最近激活时间 |
| deactivated_at | DateTime | NULL | - | 最近停用时间 |
| created_at | DateTime | NOT NULL | now | 创建时间 |

**Changes from current model**:
- 新增 `activated_at: DateTime | None` 字段
- 新增 `deactivated_at: DateTime | None` 字段
- 其余字段保持不变

### AgentStatus Enum（保持不变）

```
DRAFT = "draft"
ACTIVE = "active"
INACTIVE = "inactive"
```

### Skill（修改现有模型）

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| id | Integer | PK, auto-increment | - | 主键 |
| name | String(100) | NOT NULL | - | 技能名称 |
| description | Text | NULL | - | 描述 |
| endpoint_url | String(500) | NULL | - | 接口地址 |
| agent_id | Integer (FK → agents.id) | NULL | - | 所属 Agent |
| is_active | Boolean | NOT NULL | True | 是否可用 |
| created_at | DateTime | NOT NULL | now | 创建时间 |

**Changes from current model**:
- 新增 `is_active: Boolean` 字段，默认 True
- 停用 Agent 时批量设为 False
- 激活 Agent 时批量恢复为 True

## State Machine

```
         activate()            deactivate()
DRAFT ──────────────▶ ACTIVE ──────────────▶ INACTIVE
                          │                       │
                          │    activate()         │
                          └───────────────────────┘

无效转换：
  DRAFT → INACTIVE  (无意义)
  DRAFT → DRAFT     (无操作)
  ACTIVE → DRAFT    (不允许回退)
  ACTIVE → ACTIVE   (无操作)
  INACTIVE → DRAFT  (不允许)
  INACTIVE → INACTIVE (无操作)
```

## Validation Rules

### 激活校验 (DRAFT/INACTIVE → ACTIVE)

1. `model_id` 不为空
2. `model_id` 对应的 Model 记录存在
3. `prompt_id` 不为空
4. `prompt_id` 对应的 Prompt 记录存在

校验失败返回 422 + 具体错误消息。

### 停用 (ACTIVE → INACTIVE)

1. 无前置条件
2. 批量更新关联 Skill 的 `is_active = False`
3. 记录 `deactivated_at`

### 删除保护

1. `status == ACTIVE` 时拒绝删除，返回 422
2. DRAFT / INACTIVE 状态允许删除

## Relationships

```text
Model  1──N Agent     (model.agents ↔ agent.model)
Prompt 1──N Agent     (agent.prompt)
Agent  1──N Skill     (agent.skills ↔ skill.agent)
```

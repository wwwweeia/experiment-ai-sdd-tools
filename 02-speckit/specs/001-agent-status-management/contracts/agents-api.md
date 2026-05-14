# API Contract: Agent Management

**Base Path**: `/api/v1/agents`
**Response Format**: `{"code": 0, "data": <payload>, "message": "success"}`

---

## GET /api/v1/agents/

获取 Agent 列表（分页 + 状态筛选）

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| skip | int | No | 0 | 跳过记录数 |
| limit | int | No | 100 | 返回记录数上限 |
| status | string | No | - | 按状态筛选 (draft/active/inactive) |

### Response 200

```json
{
  "code": 0,
  "data": [
    {
      "id": 1,
      "name": "客服助手",
      "description": "处理客户咨询",
      "model_id": 1,
      "prompt_id": 2,
      "status": "draft",
      "model_name": "GPT-4",
      "prompt_title": "客服回复模板",
      "activated_at": null,
      "deactivated_at": null,
      "created_at": "2026-05-13T10:00:00"
    }
  ],
  "message": "success"
}
```

---

## GET /api/v1/agents/{agent_id}

获取单个 Agent 详情

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| agent_id | int | Agent ID |

### Response 200

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "name": "客服助手",
    "description": "处理客户咨询",
    "model_id": 1,
    "prompt_id": 2,
    "status": "active",
    "model_name": "GPT-4",
    "prompt_title": "客服回复模板",
    "activated_at": "2026-05-13T12:00:00",
    "deactivated_at": null,
    "created_at": "2026-05-13T10:00:00"
  },
  "message": "success"
}
```

### Response 404

```json
{
  "code": 1,
  "data": null,
  "message": "Agent not found"
}
```

---

## POST /api/v1/agents/

创建 Agent（默认 DRAFT 状态）

### Request Body

```json
{
  "name": "客服助手",
  "description": "处理客户咨询",
  "model_id": 1,
  "prompt_id": 2
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Agent 名称 |
| description | string | No | 描述 |
| model_id | int | No | 关联 Model ID |
| prompt_id | int | No | 关联 Prompt ID |

### Response 201

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "name": "客服助手",
    "description": "处理客户咨询",
    "model_id": 1,
    "prompt_id": 2,
    "status": "draft",
    "model_name": "GPT-4",
    "prompt_title": "客服回复模板",
    "activated_at": null,
    "deactivated_at": null,
    "created_at": "2026-05-13T10:00:00"
  },
  "message": "success"
}
```

---

## PATCH /api/v1/agents/{agent_id}/status

切换 Agent 状态

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| agent_id | int | Agent ID |

### Request Body

```json
{
  "status": "active",
  "reason": "准备上线"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | string | Yes | 目标状态 (active/inactive) |
| reason | string | No | 变更原因 |

### Response 200 (激活成功)

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "name": "客服助手",
    "status": "active",
    "activated_at": "2026-05-13T12:00:00"
  },
  "message": "success"
}
```

### Response 200 (停用成功)

```json
{
  "code": 0,
  "data": {
    "id": 1,
    "name": "客服助手",
    "status": "inactive",
    "deactivated_at": "2026-05-13T14:00:00"
  },
  "message": "success"
}
```

### Response 422 (校验失败)

```json
{
  "code": 422,
  "data": null,
  "message": "未关联 Model，无法激活"
}
```

可能的错误消息：
- "未关联 Model，无法激活"
- "关联的 Model 不存在，无法激活"
- "未关联 Prompt，无法激活"
- "关联的 Prompt 不存在，无法激活"
- "DRAFT 状态不能直接转为 INACTIVE"
- "当前状态不允许此操作"

---

## DELETE /api/v1/agents/{agent_id}

删除 Agent

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| agent_id | int | Agent ID |

### Response 200

```json
{
  "code": 0,
  "data": null,
  "message": "Deleted"
}
```

### Response 404

```json
{
  "code": 1,
  "data": null,
  "message": "Agent not found"
}
```

### Response 422 (ACTIVE 状态拒绝删除)

```json
{
  "code": 422,
  "data": null,
  "message": "ACTIVE 状态的 Agent 不能删除，请先停用"
}
```

---

## GET /api/v1/models/

（已实现，用于前端 Agent 创建表单的 Model 下拉列表）

## GET /api/v1/prompts/

（已实现，用于前端 Agent 创建表单的 Prompt 下拉列表）

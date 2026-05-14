# Quickstart: Agent 状态管理

## 验证步骤

### 1. 启动服务

```bash
# 后端
cd backend && uvicorn app.main:app --reload

# 前端
cd frontend && npm run dev
```

### 2. 后端验证

```bash
# 创建 Agent
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{"name": "测试助手", "description": "测试用", "model_id": 1, "prompt_id": 1}'

# 激活 Agent（需先确认 model_id=1 和 prompt_id=1 存在）
curl -X PATCH http://localhost:8000/api/v1/agents/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active", "reason": "测试激活"}'

# 查看 Agent 列表
curl http://localhost:8000/api/v1/agents/

# 按状态筛选
curl "http://localhost:8000/api/v1/agents/?status=active"

# 停用 Agent
curl -X PATCH http://localhost:8000/api/v1/agents/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive", "reason": "测试停用"}'

# 删除 Agent
curl -X DELETE http://localhost:8000/api/v1/agents/1

# 验证删除保护（先激活再尝试删除）
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{"name": "删除保护测试"}'
curl -X PATCH http://localhost:8000/api/v1/agents/2/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
curl -X DELETE http://localhost:8000/api/v1/agents/2
# 期望返回 422: "ACTIVE 状态的 Agent 不能删除，请先停用"
```

### 3. 前端验证

1. 打开 http://localhost:5173/agents
2. 点击"创建 Agent"按钮
3. 填写名称，选择 Model 和 Prompt，提交
4. 在列表中找到新建的 Agent，点击"激活"
5. 确认激活成功，状态标签变为绿色 "已激活"
6. 点击"停用"，确认后状态变为灰色 "已停用"
7. 停用状态下点击"删除"，确认删除
8. 测试状态筛选功能（全部/草稿/已激活/已停用）
9. 测试不关联 Model 直接激活，确认显示错误提示

"""Agent HTTP API 集成测试 — 通过 FastAPI TestClient 验证所有 5 个端点。

所有断言通过 Response[T] 响应包装（res.json()["data"], ["code"], ["message"]）。
状态码断言格式统一为 assert res.status_code == X, res.text，失败时显示响应体。

覆盖范围：
- AGENT-01: 列表分页 + status 筛选 + 422 on invalid enum
- AGENT-02: 创建 Agent（默认 DRAFT，关联 Model/Prompt）
- AGENT-03: 状态切换（200/409/422 路径）
- AGENT-04: 删除（200/409/404 路径）
- STATE-02: 关联名称映射（model_name / prompt_name）
"""

import pytest
from app.models.entity import AgentStatus


# ─── TestListAgents ───────────────────────────────────────────────────────────


class TestListAgents:
    def test_list_empty_returns_envelope(self, client):
        """空库查询应返回标准响应包装，data 为空列表。"""
        res = client.get("/api/v1/agents/")
        assert res.status_code == 200, res.text
        assert res.json() == {"code": 0, "data": [], "message": "success"}

    def test_list_with_agents(self, client, seed_agent):
        """库中有 Agent 时，列表应返回该条记录。"""
        res = client.get("/api/v1/agents/")
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == seed_agent["name"]

    def test_list_includes_relation_names(self, client, seed_agent, seed_model, seed_prompt):
        """列表响应必须包含 model_name 和 prompt_name（避免 N+1 查询，AGENT-01）。

        prompt_name 取自 Prompt.title（不是 name 字段），已在 _agent_to_read 中映射。
        """
        res = client.get("/api/v1/agents/")
        assert res.status_code == 200, res.text
        item = res.json()["data"][0]
        assert item["model_name"] == seed_model["name"], f"got: {item['model_name']}"
        assert item["prompt_name"] == seed_prompt["title"], f"got: {item['prompt_name']}"

    def test_list_filter_by_status_draft(self, client, seed_agent):
        """?status=draft 应只返回 DRAFT 状态的 Agent（AGENT-01 状态筛选）。"""
        res = client.get("/api/v1/agents/", params={"status": "draft"})
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        assert len(data) >= 1
        assert all(item["status"] == AgentStatus.DRAFT.value for item in data)

    def test_list_filter_by_status_active(self, client, seed_agent):
        """激活后按 active 筛选应返回 1 条；按 draft 筛选应返回 0 条。"""
        agent_id = seed_agent["id"]
        # 激活
        patch_res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert patch_res.status_code == 200, patch_res.text
        # active 筛选
        res_active = client.get("/api/v1/agents/", params={"status": "active"})
        assert res_active.status_code == 200, res_active.text
        assert len(res_active.json()["data"]) == 1
        # draft 筛选——已激活，不应出现
        res_draft = client.get("/api/v1/agents/", params={"status": "draft"})
        assert res_draft.status_code == 200, res_draft.text
        assert len(res_draft.json()["data"]) == 0

    def test_list_invalid_status_returns_422(self, client):
        """?status=garbage 应被 FastAPI 枚举校验拦截，返回 422（AGENT-01）。"""
        res = client.get("/api/v1/agents/", params={"status": "garbage"})
        assert res.status_code == 422, res.text

    def test_list_pagination(self, client, seed_model, seed_prompt):
        """分页参数 limit=2&skip=1 应返回准确数量（AGENT-01 分页）。"""
        for i in range(5):
            client.post(
                "/api/v1/agents/",
                json={
                    "name": f"Agent {i}",
                    "model_id": seed_model["id"],
                    "prompt_id": seed_prompt["id"],
                },
            )
        res = client.get("/api/v1/agents/", params={"limit": 2, "skip": 1})
        assert res.status_code == 200, res.text
        assert len(res.json()["data"]) == 2


# ─── TestGetAgent ─────────────────────────────────────────────────────────────


class TestGetAgent:
    def test_get_returns_relation_names(self, client, seed_agent, seed_model, seed_prompt):
        """单 Agent 详情应包含 model_name / prompt_name（关联名称映射验证）。"""
        agent_id = seed_agent["id"]
        res = client.get(f"/api/v1/agents/{agent_id}")
        assert res.status_code == 200, res.text
        data = res.json()["data"]
        assert data["model_name"] == seed_model["name"]
        assert data["prompt_name"] == seed_prompt["title"]

    def test_get_nonexistent_returns_404(self, client):
        """不存在的 Agent ID 应返回 404。"""
        res = client.get("/api/v1/agents/9999")
        assert res.status_code == 404, res.text


# ─── TestCreateAgent ──────────────────────────────────────────────────────────


class TestCreateAgent:
    def test_create_returns_201_default_draft(self, client):
        """POST 创建应返回 201，status 默认为 draft（AGENT-03）。"""
        res = client.post("/api/v1/agents/", json={"name": "Test Agent"})
        assert res.status_code == 201, res.text
        assert res.json()["data"]["status"] == AgentStatus.DRAFT.value

    def test_create_ignores_status_in_body(self, client):
        """即使请求体中传入 status=active，创建后的状态也必须是 draft（AGENT-03 防御）。

        Schema 中 AgentCreate 不含 status 字段，FastAPI 会自动忽略多余字段。
        服务层也有防御性强制赋值，双重保险。
        """
        res = client.post("/api/v1/agents/", json={"name": "X", "status": "active"})
        assert res.status_code == 201, res.text
        assert res.json()["data"]["status"] == AgentStatus.DRAFT.value

    def test_create_with_relations(self, client, seed_model, seed_prompt):
        """创建时传入 model_id / prompt_id，响应中应原样返回这些 ID。"""
        res = client.post(
            "/api/v1/agents/",
            json={
                "name": "关联 Agent",
                "model_id": seed_model["id"],
                "prompt_id": seed_prompt["id"],
            },
        )
        assert res.status_code == 201, res.text
        data = res.json()["data"]
        assert data["model_id"] == seed_model["id"]
        assert data["prompt_id"] == seed_prompt["id"]


# ─── TestStatusTransitions ────────────────────────────────────────────────────


class TestStatusTransitions:
    def test_draft_to_active_returns_200(self, client, seed_agent):
        """DRAFT → ACTIVE：有效依赖存在，应返回 200，status 更新为 active。"""
        agent_id = seed_agent["id"]
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 200, res.text
        assert res.json()["data"]["status"] == AgentStatus.ACTIVE.value

    def test_invalid_transition_returns_409(self, client, seed_agent):
        """DRAFT → INACTIVE：不合法转换应返回 409 Conflict（InvalidTransitionError → 409）。"""
        agent_id = seed_agent["id"]
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        assert res.status_code == 409, res.text
        detail = res.json()["detail"]
        # 错误消息应提及状态名称
        assert any(word in detail.lower() for word in ["draft", "inactive", "无法"]), detail

    def test_active_to_draft_returns_409(self, client, seed_agent):
        """ACTIVE → DRAFT：不合法转换应返回 409。"""
        agent_id = seed_agent["id"]
        # 先激活
        activate_res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert activate_res.status_code == 200, activate_res.text
        # 尝试回退到 DRAFT
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.DRAFT.value},
        )
        assert res.status_code == 409, res.text

    def test_activate_without_model_returns_422(self, client, seed_prompt):
        """创建仅有 prompt 的 Agent，激活时应返回 422（缺少 model，AGENT-03）。"""
        create_res = client.post(
            "/api/v1/agents/",
            json={"name": "无模型 Agent", "prompt_id": seed_prompt["id"]},
        )
        assert create_res.status_code == 201, create_res.text
        agent_id = create_res.json()["data"]["id"]
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422, res.text
        detail = res.json()["detail"]
        assert any(word in detail.lower() for word in ["model", "模型"]), detail

    def test_activate_without_prompt_returns_422(self, client, seed_model):
        """创建仅有 model 的 Agent，激活时应返回 422（缺少 prompt，AGENT-03）。"""
        create_res = client.post(
            "/api/v1/agents/",
            json={"name": "无提示词 Agent", "model_id": seed_model["id"]},
        )
        assert create_res.status_code == 201, create_res.text
        agent_id = create_res.json()["data"]["id"]
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422, res.text
        detail = res.json()["detail"]
        assert any(word in detail.lower() for word in ["prompt", "提示词"]), detail

    def test_status_change_nonexistent_returns_404(self, client):
        """不存在的 Agent ID 发起状态切换应返回 404。"""
        res = client.patch(
            "/api/v1/agents/9999/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 404, res.text

    def test_invalid_status_value_returns_422(self, client, seed_agent):
        """发送无效的 status 字符串（不在枚举范围内）应被 Pydantic 拦截，返回 422。"""
        agent_id = seed_agent["id"]
        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": "garbage"},
        )
        assert res.status_code == 422, res.text


# ─── TestDeleteAgent ──────────────────────────────────────────────────────────


class TestDeleteAgent:
    def test_delete_draft_returns_200(self, client, seed_agent):
        """DELETE DRAFT Agent 应返回 200，随后 GET 应返回 404（AGENT-04）。"""
        agent_id = seed_agent["id"]
        res = client.delete(f"/api/v1/agents/{agent_id}")
        assert res.status_code == 200, res.text
        assert res.json()["message"] == "Deleted"
        # 验证确实已删除
        get_res = client.get(f"/api/v1/agents/{agent_id}")
        assert get_res.status_code == 404, get_res.text

    def test_delete_inactive_returns_200(self, client, seed_agent):
        """INACTIVE 状态 Agent 可删除（AGENT-04）。完整路径：DRAFT → ACTIVE → INACTIVE → DELETE。"""
        agent_id = seed_agent["id"]
        client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        res = client.delete(f"/api/v1/agents/{agent_id}")
        assert res.status_code == 200, res.text

    def test_delete_active_returns_409(self, client, seed_agent):
        """DELETE ACTIVE Agent 应返回 409，且 Agent 仍然存在（AGENT-04）。"""
        agent_id = seed_agent["id"]
        # 先激活
        client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        # 尝试删除
        res = client.delete(f"/api/v1/agents/{agent_id}")
        assert res.status_code == 409, res.text
        # 确认 Agent 仍然存在
        get_res = client.get(f"/api/v1/agents/{agent_id}")
        assert get_res.status_code == 200, get_res.text

    def test_delete_nonexistent_returns_404(self, client):
        """删除不存在的 Agent 应返回 404。"""
        res = client.delete("/api/v1/agents/9999")
        assert res.status_code == 404, res.text

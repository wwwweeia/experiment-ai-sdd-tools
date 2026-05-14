from app.models.entity import AgentStatus


class TestAgentCRUD:
    """Agent 基础 CRUD 测试"""

    def test_create_agent_default_draft(self, client):
        res = client.post("/api/v1/agents/", json={
            "name": "Test Agent",
        })
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["name"] == "Test Agent"
        assert data["status"] == AgentStatus.DRAFT.value

    def test_create_agent_with_relations(self, client, seed_model, seed_prompt):
        res = client.post("/api/v1/agents/", json={
            "name": "Linked Agent",
            "model_id": seed_model["id"],
            "prompt_id": seed_prompt["id"],
        })
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["model_id"] == seed_model["id"]
        assert data["prompt_id"] == seed_prompt["id"]

    def test_list_agents(self, client, seed_agent):
        res = client.get("/api/v1/agents/")
        assert res.status_code == 200
        body = res.json()["data"]
        assert body["total"] >= 1
        assert len(body["items"]) >= 1

    def test_list_agents_filter_by_status(self, client, seed_agent):
        res = client.get("/api/v1/agents/", params={"status": "draft"})
        assert res.status_code == 200
        body = res.json()["data"]
        assert body["total"] >= 1

        res2 = client.get("/api/v1/agents/", params={"status": "active"})
        assert res2.status_code == 200
        assert res2.json()["data"]["total"] == 0

    def test_get_agent_with_relation_names(self, client, seed_agent, seed_model, seed_prompt):
        res = client.get(f"/api/v1/agents/{seed_agent['id']}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["model_name"] == seed_model["name"]
        assert data["prompt_name"] == seed_prompt["title"]

    def test_get_agent_not_found(self, client):
        res = client.get("/api/v1/agents/9999")
        assert res.status_code == 404

    def test_delete_draft_agent(self, client):
        res = client.post("/api/v1/agents/", json={"name": "To Delete"})
        agent_id = res.json()["data"]["id"]
        res = client.delete(f"/api/v1/agents/{agent_id}")
        assert res.status_code == 200

    def test_delete_nonexistent_agent(self, client):
        res = client.delete("/api/v1/agents/9999")
        assert res.status_code == 404


class TestAgentStatusMachine:
    """Agent 状态机测试"""

    def test_activate_draft_success(self, client, seed_agent):
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == AgentStatus.ACTIVE.value

    def test_activate_without_model(self, client, seed_prompt):
        res = client.post("/api/v1/agents/", json={
            "name": "No Model",
            "prompt_id": seed_prompt["id"],
        })
        agent_id = res.json()["data"]["id"]

        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422
        assert "Model" in res.json()["detail"]

    def test_activate_without_prompt(self, client, seed_model):
        res = client.post("/api/v1/agents/", json={
            "name": "No Prompt",
            "model_id": seed_model["id"],
        })
        agent_id = res.json()["data"]["id"]

        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422
        assert "Prompt" in res.json()["detail"]

    def test_activate_with_nonexistent_model(self, client, seed_prompt):
        res = client.post("/api/v1/agents/", json={
            "name": "Bad Model Ref",
            "model_id": 9999,
            "prompt_id": seed_prompt["id"],
        })
        agent_id = res.json()["data"]["id"]

        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422
        assert "Model" in res.json()["detail"]

    def test_deactivate_active_agent(self, client, seed_agent):
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == AgentStatus.INACTIVE.value

    def test_reactivate_inactive_agent(self, client, seed_agent):
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == AgentStatus.ACTIVE.value

    def test_draft_to_inactive_forbidden(self, client):
        res = client.post("/api/v1/agents/", json={"name": "Draft"})
        agent_id = res.json()["data"]["id"]

        res = client.patch(
            f"/api/v1/agents/{agent_id}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        assert res.status_code == 422
        assert "不允许" in res.json()["detail"]

    def test_active_to_active_forbidden(self, client, seed_agent):
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 422

    def test_delete_active_agent_forbidden(self, client, seed_agent):
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        res = client.delete(f"/api/v1/agents/{seed_agent['id']}")
        assert res.status_code == 422
        assert "停用" in res.json()["detail"]

    def test_delete_inactive_agent_allowed(self, client, seed_agent):
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        res = client.delete(f"/api/v1/agents/{seed_agent['id']}")
        assert res.status_code == 200

    def test_status_change_nonexistent_agent(self, client):
        res = client.patch(
            "/api/v1/agents/9999/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        assert res.status_code == 404

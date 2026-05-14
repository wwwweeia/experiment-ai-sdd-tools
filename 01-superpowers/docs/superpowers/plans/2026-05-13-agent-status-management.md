# Agent 状态管理功能实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Agent 完整生命周期管理（CRUD + 状态机 + 前端管理页面）

**Architecture:** 后端三层架构（Schema → Service → Endpoint），状态变更通过专用 PATCH 端点实现，前端 Vue 3 + Element Plus 管理页面

**Tech Stack:** FastAPI, SQLAlchemy 2.x, SQLite, Pydantic, pytest / Vue 3, Pinia, Element Plus, Axios

---

## File Structure

| 操作 | 文件 | 职责 |
|------|------|------|
| 修改 | `backend/requirements.txt` | 添加 pytest + httpx 依赖 |
| 修改 | `backend/app/schemas/schema.py` | 添加 AgentStatusChange / AgentQuery，更新 AgentCreate / AgentRead |
| 修改 | `backend/app/schemas/__init__.py` | 导出新 schemas |
| 创建 | `backend/app/services/agent_service.py` | Agent CRUD + 状态机业务逻辑 |
| 修改 | `backend/app/services/__init__.py` | 导出 AgentService |
| 修改 | `backend/app/api/v1/endpoints.py` | 添加 agent_router |
| 修改 | `backend/app/api/v1/router.py` | 注册 agent_router |
| 创建 | `backend/tests/__init__.py` | 测试包 |
| 创建 | `backend/tests/conftest.py` | 测试 fixtures（内存数据库 + 测试客户端） |
| 创建 | `backend/tests/test_agent_api.py` | Agent API 集成测试 |
| 创建 | `frontend/src/api/agent.js` | Agent HTTP 客户端 |
| 修改 | `frontend/src/stores/agent.js` | 重写 Agent Pinia Store |
| 修改 | `frontend/src/views/AgentList.vue` | 重写 Agent 管理页面 |

---

### Task 1: 测试基础设施

**Files:**
- 修改: `backend/requirements.txt`
- 创建: `backend/tests/__init__.py`
- 创建: `backend/tests/conftest.py`

- [ ] **Step 1: 添加测试依赖**

修改 `backend/requirements.txt`，在末尾添加：

```
pytest==8.3.4
httpx==0.28.1
```

最终文件内容：

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
pydantic==2.10.4
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 2: 安装依赖**

Run: `cd backend && pip install pytest httpx`

- [ ] **Step 3: 创建测试包和 fixtures**

创建 `backend/tests/__init__.py`（空文件）。

创建 `backend/tests/conftest.py`：

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.entity import AgentStatus


TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def db_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed_model(client):
    """创建一个 Model 并返回其数据"""
    res = client.post("/api/v1/models/", json={
        "name": "GPT-4o",
        "provider": "OpenAI",
        "model_type": "chat",
        "version": "2024-08-06",
    })
    return res.json()["data"]


@pytest.fixture
def seed_prompt(client):
    """创建一个 Prompt 并返回其数据"""
    res = client.post("/api/v1/prompts/", json={
        "title": "翻译助手",
        "content": "将以下内容翻译为{language}: {text}",
    })
    return res.json()["data"]


@pytest.fixture
def seed_agent(client, seed_model, seed_prompt):
    """创建一个关联了 Model 和 Prompt 的 DRAFT Agent"""
    res = client.post("/api/v1/agents/", json={
        "name": "翻译智能体",
        "description": "多语言翻译",
        "model_id": seed_model["id"],
        "prompt_id": seed_prompt["id"],
    })
    return res.json()["data"]
```

- [ ] **Step 4: 验证测试环境**

Run: `cd backend && python -m pytest tests/ -v --co`
Expected: 无报错，显示收集到 0 个测试（尚未编写测试）

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/tests/__init__.py backend/tests/conftest.py
git commit -m "chore: set up pytest infrastructure for backend tests"
```

---

### Task 2: 更新 Agent Schemas

**Files:**
- 修改: `backend/app/schemas/schema.py`
- 修改: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 更新 schema.py 中的 Agent 相关 schemas**

在 `backend/app/schemas/schema.py` 顶部的 import 区域添加：

```python
from app.models.entity import AgentStatus
```

将 `Agent` 部分替换为：

```python
# ─── Agent ──────────────────────────────────────────────────────

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

    model_config = ConfigDict(from_attributes=True)


class AgentStatusChange(BaseModel):
    status: AgentStatus
    reason: str | None = None
```

关键变更：
- `AgentCreate` 移除了 `status` 字段（创建时固定为 DRAFT）
- `AgentRead` 的 `status` 类型改为 `AgentStatus`，新增 `model_name` 和 `prompt_name`
- 新增 `AgentStatusChange` schema

- [ ] **Step 2: 更新 schemas/__init__.py 导出**

将 `backend/app/schemas/__init__.py` 修改为：

```python
from .schema import (
    ModelCreate, ModelRead,
    PromptCreate, PromptRead,
    AgentCreate, AgentRead, AgentStatusChange,
    SkillCreate, SkillRead,
    Response,
)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/schema.py backend/app/schemas/__init__.py
git commit -m "feat: update Agent schemas with status change and richer read model"
```

---

### Task 3: Agent Service

**Files:**
- 创建: `backend/app/services/agent_service.py`
- 修改: `backend/app/services/__init__.py`

- [ ] **Step 1: 创建 AgentService**

创建 `backend/app/services/agent_service.py`：

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.entity import Agent, AgentStatus, Model, Prompt
from app.schemas.schema import AgentCreate


ALLOWED_TRANSITIONS = {
    (AgentStatus.DRAFT, AgentStatus.ACTIVE),
    (AgentStatus.ACTIVE, AgentStatus.INACTIVE),
    (AgentStatus.INACTIVE, AgentStatus.ACTIVE),
}


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def list_agents(
        self, skip: int = 0, limit: int = 20, status: AgentStatus | None = None
    ) -> tuple[list[Agent], int]:
        query = self.db.query(Agent).options(
            joinedload(Agent.model), joinedload(Agent.prompt)
        )
        if status:
            query = query.filter(Agent.status == status)
        total = query.count()
        agents = query.offset(skip).limit(limit).all()
        return agents, total

    def get_agent(self, agent_id: int) -> Agent | None:
        return (
            self.db.query(Agent)
            .options(joinedload(Agent.model), joinedload(Agent.prompt))
            .filter(Agent.id == agent_id)
            .first()
        )

    def create_agent(self, data: AgentCreate) -> Agent:
        agent = Agent(**data.model_dump(), status=AgentStatus.DRAFT)
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def change_status(
        self, agent_id: int, target: AgentStatus, reason: str | None = None
    ) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if (agent.status, target) not in ALLOWED_TRANSITIONS:
            raise HTTPException(
                status_code=422,
                detail=f"不允许从 {agent.status.value} 转换为 {target.value}",
            )

        if target == AgentStatus.ACTIVE:
            if not agent.model_id or not self.db.query(Model).filter(Model.id == agent.model_id).first():
                raise HTTPException(status_code=422, detail="未关联有效的 Model")
            if not agent.prompt_id or not self.db.query(Prompt).filter(Prompt.id == agent.prompt_id).first():
                raise HTTPException(status_code=422, detail="未关联有效的 Prompt")

        agent.status = target
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        if agent.status == AgentStatus.ACTIVE:
            raise HTTPException(status_code=422, detail="ACTIVE 状态的 Agent 不允许删除，请先停用")
        self.db.delete(agent)
        self.db.commit()
        return True
```

关键设计：
- `list_agents` 返回 `(agents, total)` 元组以支持分页
- `ALLOWED_TRANSITIONS` 集合定义合法状态转换，新增状态只需添加一个元组
- `change_status` 先校验转换合法性，再校验激活前置条件
- `delete_agent` 拒绝 ACTIVE 状态的删除

- [ ] **Step 2: 更新 services/__init__.py**

将 `backend/app/services/__init__.py` 修改为：

```python
from .model_service import ModelService
from .agent_service import AgentService
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/agent_service.py backend/app/services/__init__.py
git commit -m "feat: add AgentService with status machine and business rules"
```

---

### Task 4: Agent API 端点

**Files:**
- 修改: `backend/app/api/v1/endpoints.py`
- 修改: `backend/app/api/v1/router.py`

- [ ] **Step 1: 在 endpoints.py 添加 agent_router**

在 `backend/app/api/v1/endpoints.py` 顶部的 import 区域，追加导入：

```python
from app.models.entity import AgentStatus
from app.schemas.schema import (
    ModelCreate, ModelRead, PromptCreate, PromptRead,
    AgentCreate, AgentRead, AgentStatusChange, Response,
)
from app.services.agent_service import AgentService
```

在文件末尾添加：

```python
# ─── Agent ────────────────────────────────────────────────────

agents_router = APIRouter()


@agents_router.get("/", response_model=Response)
def list_agents(
    skip: int = 0, limit: int = 20, status: AgentStatus | None = None,
    db: Session = Depends(get_db),
):
    service = AgentService(db)
    agents, total = service.list_agents(skip=skip, limit=limit, status=status)
    return Response(data={
        "items": [_agent_to_read(a) for a in agents],
        "total": total,
        "skip": skip,
        "limit": limit,
    })


@agents_router.get("/{agent_id}", response_model=Response[AgentRead])
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return Response(data=_agent_to_read(agent))


@agents_router.post("/", response_model=Response[AgentRead], status_code=201)
def create_agent(body: AgentCreate, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.create_agent(body)
    return Response(data=_agent_to_read(agent))


@agents_router.patch("/{agent_id}/status", response_model=Response[AgentRead])
def change_agent_status(
    agent_id: int, body: AgentStatusChange, db: Session = Depends(get_db),
):
    service = AgentService(db)
    agent = service.change_status(agent_id, body.status, body.reason)
    return Response(data=_agent_to_read(agent))


@agents_router.delete("/{agent_id}", response_model=Response[None])
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    if not service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    return Response(message="Deleted")


def _agent_to_read(agent) -> dict:
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "model_id": agent.model_id,
        "prompt_id": agent.prompt_id,
        "status": agent.status,
        "created_at": agent.created_at,
        "model_name": agent.model.name if agent.model else None,
        "prompt_name": agent.prompt.title if agent.prompt else None,
    }
```

注意：
- 列表接口返回分页结构 `{items, total, skip, limit}` 而不是裸数组
- `_agent_to_read` 辅助函数从 ORM 对象提取关联名称，避免在 schema 层处理懒加载问题

- [ ] **Step 2: 注册 agent_router**

将 `backend/app/api/v1/router.py` 修改为：

```python
from fastapi import APIRouter
from .endpoints import models_router, prompts_router, agents_router

router = APIRouter()
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
router.include_router(agents_router, prefix="/agents", tags=["agents"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/endpoints.py backend/app/api/v1/router.py
git commit -m "feat: add Agent CRUD + status change API endpoints"
```

---

### Task 5: 后端集成测试

**Files:**
- 创建: `backend/tests/test_agent_api.py`

- [ ] **Step 1: 编写集成测试**

创建 `backend/tests/test_agent_api.py`：

```python
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
        # 先激活
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        # 再停用
        res = client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == AgentStatus.INACTIVE.value

    def test_reactivate_inactive_agent(self, client, seed_agent):
        # draft -> active -> inactive
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.ACTIVE.value},
        )
        client.patch(
            f"/api/v1/agents/{seed_agent['id']}/status",
            json={"status": AgentStatus.INACTIVE.value},
        )
        # inactive -> active
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
        # draft -> active -> inactive
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
```

- [ ] **Step 2: 运行测试验证全部通过**

Run: `cd backend && python -m pytest tests/test_agent_api.py -v`
Expected: 全部 PASS（约 16 个测试）

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_agent_api.py
git commit -m "test: add Agent API integration tests covering CRUD and status machine"
```

---

### Task 6: 前端 API 客户端

**Files:**
- 创建: `frontend/src/api/agent.js`

- [ ] **Step 1: 创建 Agent API 文件**

创建 `frontend/src/api/agent.js`：

```javascript
import api from './index'

export function fetchAgents(params = {}) {
  return api.get('/api/v1/agents/', { params })
}

export function fetchAgent(id) {
  return api.get(`/api/v1/agents/${id}`)
}

export function createAgent(data) {
  return api.post('/api/v1/agents/', data)
}

export function changeAgentStatus(id, status, reason = '') {
  return api.patch(`/api/v1/agents/${id}/status`, { status, reason })
}

export function deleteAgent(id) {
  return api.delete(`/api/v1/agents/${id}`)
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/agent.js
git commit -m "feat: add Agent API client functions"
```

---

### Task 7: 前端 Agent Store

**Files:**
- 修改: `frontend/src/stores/agent.js`

- [ ] **Step 1: 重写 Agent Store**

将 `frontend/src/stores/agent.js` 替换为：

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  fetchAgents as fetchAgentsApi,
  createAgent as createAgentApi,
  changeAgentStatus as changeAgentStatusApi,
  deleteAgent as deleteAgentApi,
} from '../api/agent'

export const useAgentStore = defineStore('agent', () => {
  const agents = ref([])
  const loading = ref(false)
  const pagination = ref({ skip: 0, limit: 20, total: 0 })
  const filterStatus = ref('')

  const statusLabel = { draft: '草稿', active: '已激活', inactive: '已停用' }
  const statusTagType = { draft: 'info', active: 'success', inactive: 'danger' }

  async function fetchAgents() {
    loading.value = true
    try {
      const params = { skip: pagination.value.skip, limit: pagination.value.limit }
      if (filterStatus.value) params.status = filterStatus.value
      const res = await fetchAgentsApi(params)
      const body = res.data
      agents.value = body.items || []
      pagination.value.total = body.total || 0
    } catch {
      agents.value = []
    } finally {
      loading.value = false
    }
  }

  async function createAgent(data) {
    await createAgentApi(data)
    await fetchAgents()
  }

  async function changeStatus(id, status, reason = '') {
    await changeAgentStatusApi(id, status, reason)
    await fetchAgents()
  }

  async function deleteAgent(id) {
    await deleteAgentApi(id)
    await fetchAgents()
  }

  function setFilter(status) {
    filterStatus.value = status
    pagination.value.skip = 0
  }

  function setPage(skip) {
    pagination.value.skip = skip
  }

  return {
    agents,
    loading,
    pagination,
    filterStatus,
    statusLabel,
    statusTagType,
    fetchAgents,
    createAgent,
    changeStatus,
    deleteAgent,
    setFilter,
    setPage,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/agent.js
git commit -m "feat: rewrite Agent Pinia store with CRUD, status, and pagination"
```

---

### Task 8: 前端 Agent 管理页面

**Files:**
- 修改: `frontend/src/views/AgentList.vue`

- [ ] **Step 1: 重写 AgentList.vue**

将 `frontend/src/views/AgentList.vue` 替换为：

```vue
<template>
  <div class="agent-list">
    <div class="header">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">新建 Agent</el-button>
    </div>

    <!-- 状态筛选 -->
    <el-tabs v-model="activeTab" class="status-tabs" @tab-change="handleFilterChange">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="草稿" name="draft" />
      <el-tab-pane label="已激活" name="active" />
      <el-tab-pane label="已停用" name="inactive" />
    </el-tabs>

    <!-- Agent 表格 -->
    <el-table v-loading="agentStore.loading" :data="agentStore.agents" style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
      <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
      <el-table-column label="关联模型" width="120">
        <template #default="{ row }">
          {{ row.model_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="关联提示词" width="140">
        <template #default="{ row }">
          {{ row.prompt_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="agentStore.statusTagType[row.status]" size="small">
            {{ agentStore.statusLabel[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'draft' || row.status === 'inactive'"
            type="success"
            size="small"
            @click="handleActivate(row)"
          >
            激活
          </el-button>
          <el-button
            v-if="row.status === 'active'"
            type="warning"
            size="small"
            @click="handleDeactivate(row)"
          >
            停用
          </el-button>
          <el-button
            v-if="row.status === 'inactive'"
            type="danger"
            size="small"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="agentStore.pagination.limit"
        :total="agentStore.pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 新建 Agent 弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建 Agent" width="500px" @close="resetForm">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="关联模型">
          <el-select v-model="createForm.model_id" placeholder="选择模型（激活前必选）" clearable style="width: 100%">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联提示词">
          <el-select v-model="createForm.prompt_id" placeholder="选择提示词（激活前必选）" clearable style="width: 100%">
            <el-option v-for="p in promptOptions" :key="p.id" :label="p.title" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAgentStore } from '../stores/agent'
import { fetchPrompts } from '../api/prompts'
import api from '../api'

const agentStore = useAgentStore()

const activeTab = ref('')
const showCreateDialog = ref(false)
const submitting = ref(false)
const modelOptions = ref([])
const promptOptions = ref([])

const createForm = ref({
  name: '',
  description: '',
  model_id: null,
  prompt_id: null,
})

const currentPage = computed({
  get: () => Math.floor(agentStore.pagination.skip / agentStore.pagination.limit) + 1,
  set: () => {},
})

async function loadOptions() {
  const [modelRes, promptRes] = await Promise.all([
    api.get('/api/v1/models/'),
    fetchPrompts(),
  ])
  modelOptions.value = modelRes.data || []
  promptOptions.value = promptRes.data || []
}

function handleFilterChange(status) {
  agentStore.setFilter(status)
  agentStore.fetchAgents()
}

function handlePageChange(page) {
  agentStore.setPage((page - 1) * agentStore.pagination.limit)
  agentStore.fetchAgents()
}

function handleActivate(row) {
  ElMessageBox.confirm(
    `确定要激活 Agent「${row.name}」吗？激活后将可被系统调用。`,
    '激活确认',
    { type: 'info', confirmButtonText: '确定激活', cancelButtonText: '取消' },
  ).then(() => {
    agentStore.changeStatus(row.id, 'active').catch(() => {})
  }).catch(() => {})
}

function handleDeactivate(row) {
  ElMessageBox.confirm(
    `确定要停用 Agent「${row.name}」吗？停用后该 Agent 将不再接受请求。`,
    '停用确认',
    { type: 'warning', confirmButtonText: '确定停用', cancelButtonText: '取消' },
  ).then(() => {
    agentStore.changeStatus(row.id, 'inactive').catch(() => {})
  }).catch(() => {})
}

function handleDelete(row) {
  ElMessageBox.confirm(
    `确定要删除 Agent「${row.name}」吗？此操作不可恢复。`,
    '删除确认',
    { type: 'error', confirmButtonText: '确定删除', cancelButtonText: '取消' },
  ).then(() => {
    agentStore.deleteAgent(row.id).then(() => {
      ElMessage.success('删除成功')
    }).catch(() => {})
  }).catch(() => {})
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入 Agent 名称')
    return
  }
  submitting.value = true
  try {
    await agentStore.createAgent(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
  } catch {
    // 错误由拦截器处理
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  createForm.value = { name: '', description: '', model_id: null, prompt_id: null }
}

onMounted(() => {
  agentStore.fetchAgents()
  loadOptions()
})
</script>

<style scoped>
.agent-list {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 60px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
}

.status-tabs {
  margin-bottom: 16px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
```

- [ ] **Step 2: 启动前后端验证页面可访问**

Run: `cd backend && uvicorn app.main:app --reload &`
Run: `cd frontend && npm run dev &`

验证：
1. 打开 http://localhost:5173/agents
2. 页面正常渲染，显示表格和筛选 Tab
3. 点击"新建 Agent"弹窗正常弹出
4. 填写名称，选择模型和提示词，点击创建
5. 列表出现新 Agent，状态为"草稿"
6. 点击"激活"，确认后状态变为"已激活"
7. 点击"停用"，确认后状态变为"已停用"
8. 停用状态下显示"激活"和"删除"按钮

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/AgentList.vue
git commit -m "feat: implement Agent management page with CRUD, status toggle, and filtering"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: 每条设计需求都有对应 Task
  - 状态机转换 → Task 3 (AgentService) + Task 5 (测试)
  - 激活前置条件 → Task 3 + Task 5
  - 删除保护 → Task 3 + Task 5
  - 5 个 API 端点 → Task 4
  - 前端列表/筛选/分页 → Task 8
  - 前端状态操作 → Task 8
  - 前端创建表单 → Task 8
- [x] **Placeholder scan**: 无 TBD/TODO，所有步骤含完整代码
- [x] **Type consistency**: Schema 字段名、API 路径、Store 属性名全部一致

"""AgentService 单元测试 — 直接调用服务层，不经过 HTTP 边界。

目的：最快速地验证状态机业务规则。测试失败时直接指向具体的规则违反，
而不是被 HTTP 层噪音掩盖。全文件运行 < 5s。

覆盖范围：AGENT-01~04, STATE-01, STATE-02
"""

import pytest
from app.models.entity import Agent, AgentStatus, AgentStatusHistory, Model, Prompt
from app.schemas.schema import AgentCreate, StatusChangeRequest
from app.services.agent_service import (
    AgentService,
    VALID_TRANSITIONS,
    InvalidTransitionError,
    ActivationNotReadyError,
)


# ─── 本地 seed fixture（直接操作 db_session，不走 HTTP，更快）─────────────────


@pytest.fixture
def seed_model_and_prompt(db_session):
    """直接向数据库插入 Model + Prompt，返回 (model, prompt) 元组。

    避免走 HTTP client，让 TestStateMachineTransitions 测试专注于服务层逻辑。
    """
    m = Model(name="gpt-4o", provider="openai", model_type="chat", version="1")
    p = Prompt(title="t", content="c")
    db_session.add_all([m, p])
    db_session.commit()
    db_session.refresh(m)
    db_session.refresh(p)
    return m, p


# ─── 辅助函数 ─────────────────────────────────────────────────────────────────


def make_agent(db_session, model=None, prompt=None) -> Agent:
    """创建 Agent 并返回，前置条件可选传入 Model/Prompt。"""
    svc = AgentService(db_session)
    data = AgentCreate(
        name="测试 Agent",
        model_id=model.id if model else None,
        prompt_id=prompt.id if prompt else None,
    )
    return svc.create_agent(data)


def activate(db_session, agent: Agent) -> Agent:
    """快捷激活 Agent（DRAFT → ACTIVE）。"""
    svc = AgentService(db_session)
    return svc.change_status(agent.id, StatusChangeRequest(status=AgentStatus.ACTIVE))


def deactivate(db_session, agent: Agent) -> Agent:
    """快捷停用 Agent（ACTIVE → INACTIVE）。"""
    svc = AgentService(db_session)
    return svc.change_status(agent.id, StatusChangeRequest(status=AgentStatus.INACTIVE))


# ─── TestValidTransitions ─────────────────────────────────────────────────────


class TestValidTransitions:
    def test_valid_transitions_shape(self):
        """VALID_TRANSITIONS 映射表结构必须精确匹配需求文档中的状态机定义。"""
        assert VALID_TRANSITIONS == {
            AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
            AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
            AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
        }


# ─── TestCreateAgent ──────────────────────────────────────────────────────────


class TestCreateAgent:
    def test_create_defaults_to_draft(self, db_session, seed_model_and_prompt):
        """新创建的 Agent 无论传入什么，状态必须是 DRAFT（AGENT-03）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        assert agent.status == AgentStatus.DRAFT

    def test_create_writes_initial_history_row(self, db_session, seed_model_and_prompt):
        """创建 Agent 时必须写入初始 history 行（STATE-02）。

        from_status 必须是 None（初始创建，无前驱状态），to_status 必须是 DRAFT。
        """
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        rows = db_session.query(AgentStatusHistory).filter_by(agent_id=agent.id).all()
        assert len(rows) == 1, "初始创建应写入恰好 1 行 history"
        row = rows[0]
        assert row.from_status is None, "首次创建 from_status 必须为 None"
        assert row.to_status == AgentStatus.DRAFT


# ─── TestStateMachineTransitions ──────────────────────────────────────────────


class TestStateMachineTransitions:
    def test_draft_to_active_with_valid_deps(self, db_session, seed_model_and_prompt):
        """DRAFT → ACTIVE：有效的 Model + Prompt，应成功并写入 history 行。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        updated = activate(db_session, agent)
        assert updated.status == AgentStatus.ACTIVE

        rows = db_session.query(AgentStatusHistory).filter_by(agent_id=agent.id).all()
        assert len(rows) == 2
        transition_row = rows[1]
        assert transition_row.from_status == AgentStatus.DRAFT
        assert transition_row.to_status == AgentStatus.ACTIVE

    def test_draft_to_active_without_model_raises_422(self, db_session, seed_model_and_prompt):
        """DRAFT → ACTIVE：缺失 model_id，应抛出 ActivationNotReadyError（→ HTTP 422）。"""
        _, prompt = seed_model_and_prompt
        agent = make_agent(db_session, prompt=prompt)  # 没有 model
        with pytest.raises(ActivationNotReadyError):
            activate(db_session, agent)

    def test_draft_to_active_without_prompt_raises_422(self, db_session, seed_model_and_prompt):
        """DRAFT → ACTIVE：缺失 prompt_id，应抛出 ActivationNotReadyError（→ HTTP 422）。"""
        model, _ = seed_model_and_prompt
        agent = make_agent(db_session, model=model)  # 没有 prompt
        with pytest.raises(ActivationNotReadyError):
            activate(db_session, agent)

    def test_draft_to_active_with_deleted_model_raises_422(self, db_session, seed_model_and_prompt):
        """DRAFT → ACTIVE：model_id 存在但模型已被删除，应抛出 ActivationNotReadyError。

        防御 Pitfall #6：关联实体被外部删除后重新激活时的幽灵 FK。
        """
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        # 删除模型，模拟外部清理场景
        db_session.delete(model)
        db_session.commit()
        with pytest.raises(ActivationNotReadyError):
            activate(db_session, agent)

    def test_active_to_inactive_succeeds(self, db_session, seed_model_and_prompt):
        """DRAFT → ACTIVE → INACTIVE：完整路径，history 共 3 行（初始 + 2 次转换）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        agent = activate(db_session, agent)
        agent = deactivate(db_session, agent)
        assert agent.status == AgentStatus.INACTIVE

        rows = db_session.query(AgentStatusHistory).filter_by(agent_id=agent.id).all()
        assert len(rows) == 3, "初始创建 + 2 次状态转换 = 3 行"

    def test_inactive_to_active_revalidates_dependencies(self, db_session, seed_model_and_prompt):
        """INACTIVE → ACTIVE：重新激活时必须重新校验依赖（防御 Pitfall #6）。

        Prompt 在停用后被删除，再次激活应抛出 ActivationNotReadyError，
        而不是静默地让 Agent 进入 ACTIVE 状态。
        """
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        agent = activate(db_session, agent)
        agent = deactivate(db_session, agent)
        # 删除 Prompt，模拟停用期间关联资源被清理
        db_session.delete(prompt)
        db_session.commit()
        with pytest.raises(ActivationNotReadyError):
            activate(db_session, agent)

    def test_active_to_draft_raises_409(self, db_session, seed_model_and_prompt):
        """ACTIVE → DRAFT：不合法转换，应抛出 InvalidTransitionError（→ HTTP 409）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        activate(db_session, agent)
        with pytest.raises(InvalidTransitionError):
            svc = AgentService(db_session)
            svc.change_status(agent.id, StatusChangeRequest(status=AgentStatus.DRAFT))

    def test_draft_to_inactive_raises_409(self, db_session, seed_model_and_prompt):
        """DRAFT → INACTIVE：不合法转换，应抛出 InvalidTransitionError（→ HTTP 409）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        with pytest.raises(InvalidTransitionError):
            svc = AgentService(db_session)
            svc.change_status(agent.id, StatusChangeRequest(status=AgentStatus.INACTIVE))


# ─── TestStatusHistory ────────────────────────────────────────────────────────


class TestStatusHistory:
    def test_every_transition_creates_history_row(self, db_session, seed_model_and_prompt):
        """每次合法的状态转换都必须产生一行 history（STATE-02 核心验证）。

        做 3 次转换（DRAFT→ACTIVE→INACTIVE→ACTIVE），加上初始创建行，共 4 行。
        """
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        agent = activate(db_session, agent)
        agent = deactivate(db_session, agent)
        agent = activate(db_session, agent)  # 第三次转换

        rows = db_session.query(AgentStatusHistory).filter_by(agent_id=agent.id).all()
        assert len(rows) == 4, "初始创建(1) + 3 次转换 = 4 行"

    def test_history_records_reason(self, db_session, seed_model_and_prompt):
        """change_status 传入 reason 时，history 行应记录该原因（STATE-02 reason 字段）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        svc = AgentService(db_session)
        svc.change_status(
            agent.id,
            StatusChangeRequest(status=AgentStatus.ACTIVE, reason="manual activation"),
        )
        rows = (
            db_session.query(AgentStatusHistory)
            .filter_by(agent_id=agent.id)
            .order_by(AgentStatusHistory.changed_at)
            .all()
        )
        # rows[0] 是初始创建行，rows[1] 是本次转换行
        assert rows[1].reason == "manual activation"


# ─── TestDeleteAgent ──────────────────────────────────────────────────────────


class TestDeleteAgent:
    def test_delete_draft_agent_returns_true(self, db_session, seed_model_and_prompt):
        """DRAFT 状态 Agent 可直接删除，返回 True（AGENT-04）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        svc = AgentService(db_session)
        result = svc.delete_agent(agent.id)
        assert result is True
        assert svc.get_agent(agent.id) is None

    def test_delete_inactive_agent_returns_true(self, db_session, seed_model_and_prompt):
        """INACTIVE 状态 Agent 可删除，返回 True（AGENT-04）。"""
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        agent = activate(db_session, agent)
        agent = deactivate(db_session, agent)
        svc = AgentService(db_session)
        result = svc.delete_agent(agent.id)
        assert result is True

    def test_delete_active_agent_raises_valueerror(self, db_session, seed_model_and_prompt):
        """ACTIVE 状态 Agent 禁止删除，必须抛出 ValueError（→ HTTP 409，AGENT-04）。

        注意：抛出的是基础 ValueError，不是子类，与 agent_service.py 的设计一致。
        """
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        activate(db_session, agent)
        svc = AgentService(db_session)
        with pytest.raises(ValueError):
            svc.delete_agent(agent.id)

    def test_delete_nonexistent_agent_returns_false(self, db_session):
        """删除不存在的 Agent，返回 False（不应抛出异常）。"""
        svc = AgentService(db_session)
        assert svc.delete_agent(9999) is False

    def test_cascade_deletes_history(self, db_session, seed_model_and_prompt):
        """删除 Agent 时，AgentStatusHistory 记录应通过 FK CASCADE 自动清理。

        验证 entity.py 中 cascade="all, delete-orphan" 的 ORM 配置实际生效。
        """
        model, prompt = seed_model_and_prompt
        agent = make_agent(db_session, model=model, prompt=prompt)
        agent_id = agent.id
        agent = activate(db_session, agent)
        agent = deactivate(db_session, agent)
        # 删除 agent
        svc = AgentService(db_session)
        svc.delete_agent(agent_id)
        # history 行应随 agent 一起被清理
        remaining = db_session.query(AgentStatusHistory).filter_by(agent_id=agent_id).all()
        assert len(remaining) == 0, "Agent 删除后 history 行应级联清理"

"""Agent 服务层 — 拥有状态机和所有业务规则。

注意：本模块使用 SQLAlchemy 2.x 的 select() + session.execute() 风格，
不使用旧的 db.query()，与 prompt_service.py 有意不同。
这是有意为之的设计选择，以符合 SQLAlchemy 2.x 最佳实践。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, joinedload

from app.models.entity import Agent, AgentStatus, AgentStatusHistory, Model, Prompt
from app.schemas.schema import AgentCreate, StatusChangeRequest


# ─── 状态机定义 ──────────────────────────────────────────────────

VALID_TRANSITIONS: dict[AgentStatus, list[AgentStatus]] = {
    AgentStatus.DRAFT:    [AgentStatus.ACTIVE],
    AgentStatus.ACTIVE:   [AgentStatus.INACTIVE],
    AgentStatus.INACTIVE: [AgentStatus.ACTIVE],
}
"""合法的状态转换映射表。

DRAFT → ACTIVE：需要关联有效的 Model 和 Prompt（激活前置校验）。
ACTIVE → INACTIVE：直接允许，记录变更历史。
INACTIVE → ACTIVE：重新激活，同样需要通过激活前置校验。
"""


# ─── 领域异常 ──────────────────────────────────────────────────

class InvalidTransitionError(ValueError):
    """状态转换不合法 — 路由层映射为 HTTP 409 Conflict。

    例如：尝试从 ACTIVE 直接切换到 DRAFT。
    """


class ActivationNotReadyError(ValueError):
    """激活前置条件不满足 — 路由层映射为 HTTP 422 Unprocessable Entity。

    例如：Agent 未关联模型或提示词，无法激活。
    """


# ─── AgentService ──────────────────────────────────────────────

class AgentService:
    """Agent 业务逻辑服务。

    通过构造函数注入 SQLAlchemy Session，与 prompt_service.py 保持一致的构造模式。
    所有数据库操作使用 SQLAlchemy 2.x 风格（select() + execute()）。
    """

    def __init__(self, db: Session):
        self.db = db

    def list_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: AgentStatus | None = None,
    ) -> list[Agent]:
        """返回 Agent 列表，支持分页和状态筛选。

        使用 selectinload 避免 N+1 问题：无论返回多少条记录，
        始终只额外发出 2 条 IN-clause 查询（一条加载 model，一条加载 prompt）。
        """
        stmt = select(Agent).options(
            selectinload(Agent.model),
            selectinload(Agent.prompt),
        )
        if status is not None:
            stmt = stmt.where(Agent.status == status)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def get_agent(self, agent_id: int) -> Agent | None:
        """按 ID 获取单个 Agent，使用 joinedload 单查询加载关联关系。

        使用 .unique() 消除 joinedload 产生的笛卡尔积重复行警告。
        """
        stmt = (
            select(Agent)
            .options(
                joinedload(Agent.model),
                joinedload(Agent.prompt),
            )
            .where(Agent.id == agent_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create_agent(self, data: AgentCreate) -> Agent:
        """创建新 Agent，始终强制 status=DRAFT（忽略任何外部输入）。

        写入初始 AgentStatusHistory 行（from_status=None, to_status=DRAFT），
        确保从创建时刻起就有完整的审计追踪。

        防御性设计：即使 AgentCreate 将来意外新增了 status 字段，
        显式赋值也会强制覆盖为 DRAFT，满足 AGENT-03 要求。
        """
        agent = Agent(**data.model_dump())
        # 防御性强制 DRAFT——即使 AgentCreate 将来新增 status 字段也能保证语义正确
        agent.status = AgentStatus.DRAFT
        self.db.add(agent)
        # flush 使 agent.id 可用，避免在 history 行中写入 None
        self.db.flush()
        self.db.add(AgentStatusHistory(
            agent_id=agent.id,
            from_status=None,
            to_status=AgentStatus.DRAFT,
            reason="初始创建",
        ))
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def _assert_activation_ready(self, agent: Agent) -> None:
        """校验激活前置条件：Agent 必须已关联有效的 Model 和 Prompt。

        对 DRAFT→ACTIVE 和 INACTIVE→ACTIVE 两条路径都执行此校验，
        防止重新激活时依赖的 Model/Prompt 已被删除的情况（Pitfall #6）。

        Raises:
            ActivationNotReadyError: 当任一前置条件不满足时，路由层映射为 HTTP 422。
        """
        if not agent.model_id:
            raise ActivationNotReadyError("激活失败：Agent 未关联模型")
        if not agent.prompt_id:
            raise ActivationNotReadyError("激活失败：Agent 未关联提示词")

        # 验证关联实体是否仍然存在于数据库（可能已被外部删除）
        model = self.db.get(Model, agent.model_id)
        if not model:
            raise ActivationNotReadyError(
                f"激活失败：关联模型 (id={agent.model_id}) 已不存在"
            )
        prompt = self.db.get(Prompt, agent.prompt_id)
        if not prompt:
            raise ActivationNotReadyError(
                f"激活失败：关联提示词 (id={agent.prompt_id}) 已不存在"
            )

    def change_status(self, agent_id: int, data: StatusChangeRequest) -> Agent:
        """执行状态切换，遵循校验顺序：存在性 → 转换合法性 → 激活前置 → 原子写入。

        校验顺序确保：
        1. 404 before 409（先确认 agent 存在，再检查转换是否合法）
        2. 409 before 422（先检查转换规则，再检查前置条件）
        3. 状态更新和 history 行在同一个 commit 中原子写入（STATE-01 + STATE-02）

        Raises:
            ValueError: Agent 不存在（路由层转换为 404）
            InvalidTransitionError: 转换不合法（路由层转换为 409）
            ActivationNotReadyError: 激活前置条件不满足（路由层转换为 422）
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} 不存在")

        old_status = agent.status
        allowed = VALID_TRANSITIONS.get(old_status, [])

        if data.status not in allowed:
            raise InvalidTransitionError(
                f"无法从 {old_status.value} 切换到 {data.status.value}"
            )

        # 对任何目标为 ACTIVE 的转换都执行激活前置校验
        if data.status == AgentStatus.ACTIVE:
            self._assert_activation_ready(agent)

        # 原子写入：状态更新 + 审计日志在同一个事务中提交
        agent.status = data.status
        self.db.add(AgentStatusHistory(
            agent_id=agent.id,
            from_status=old_status,
            to_status=data.status,
            reason=data.reason,
        ))
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete_agent(self, agent_id: int) -> bool:
        """删除 Agent，ACTIVE 状态不允许删除。

        ACTIVE 状态禁止删除（AGENT-04）：必须先停用才能删除。
        历史记录通过 ORM 级联（cascade="all, delete-orphan"）自动清理。

        Returns:
            True：删除成功（DRAFT 或 INACTIVE 状态）
            False：Agent 不存在

        Raises:
            ValueError: Agent 处于 ACTIVE 状态，禁止删除（路由层映射为 409）
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        if agent.status == AgentStatus.ACTIVE:
            raise ValueError("无法删除：Agent 正处于激活状态，请先停用")

        self.db.delete(agent)
        self.db.commit()
        return True

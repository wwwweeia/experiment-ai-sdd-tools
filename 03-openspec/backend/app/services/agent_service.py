from sqlalchemy.orm import Session, joinedload
from app.models.entity import Agent, AgentStatus, Model, Prompt
from app.schemas.schema import AgentCreate


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def list_agents(self, skip: int = 0, limit: int = 100, status: str | None = None) -> list[Agent]:
        query = self.db.query(Agent).options(
            joinedload(Agent.model), joinedload(Agent.prompt)
        )
        if status:
            query = query.filter(Agent.status == status)
        return query.order_by(Agent.created_at.desc()).offset(skip).limit(limit).all()

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

    def delete_agent(self, agent_id: int) -> tuple[bool, str]:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return False, "Agent not found"
        if agent.status == AgentStatus.ACTIVE:
            return False, "ACTIVE 状态的 Agent 不允许删除，请先停用"
        self.db.delete(agent)
        self.db.commit()
        return True, ""

    # 状态机：合法转换映射
    TRANSITIONS = {
        AgentStatus.DRAFT: {AgentStatus.ACTIVE},
        AgentStatus.ACTIVE: {AgentStatus.INACTIVE},
        AgentStatus.INACTIVE: {AgentStatus.ACTIVE},
    }

    def change_status(self, agent_id: int, target_status: AgentStatus, reason: str | None = None) -> tuple[Agent | None, str]:
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None, "Agent not found"

        current = AgentStatus(agent.status) if isinstance(agent.status, str) else agent.status

        if target_status not in self.TRANSITIONS.get(current, set()):
            allowed = [s.value for s in self.TRANSITIONS.get(current, set())]
            return None, f"不允许从 {current.value} 转换到 {target_status.value}，允许的目标状态: {allowed or '无'}"

        # 激活前置校验
        if target_status == AgentStatus.ACTIVE:
            errors = []
            if not agent.model_id:
                errors.append("未关联有效的 Model")
            elif not self.db.query(Model).filter(Model.id == agent.model_id).first():
                errors.append("未关联有效的 Model")
            if not agent.prompt_id:
                errors.append("未关联有效的 Prompt")
            elif not self.db.query(Prompt).filter(Prompt.id == agent.prompt_id).first():
                errors.append("未关联有效的 Prompt")
            if errors:
                return None, "；".join(errors)

        agent.status = target_status
        self.db.commit()
        self.db.refresh(agent)
        return agent, ""

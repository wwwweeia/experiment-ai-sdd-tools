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

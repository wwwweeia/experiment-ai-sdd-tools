from datetime import datetime
from sqlalchemy.orm import Session
from app.models.entity import Agent, AgentStatus, Model, Prompt, Skill
from app.schemas.schema import AgentCreate


class AgentService:
    def __init__(self, db: Session):
        self.db = db

    def list_agents(self, skip: int = 0, limit: int = 100, status: str | None = None) -> list[Agent]:
        query = self.db.query(Agent)
        if status:
            query = query.filter(Agent.status == status)
        return query.offset(skip).limit(limit).all()

    def get_agent(self, agent_id: int) -> Agent | None:
        return self.db.query(Agent).filter(Agent.id == agent_id).first()

    def create_agent(self, data: AgentCreate) -> Agent:
        agent = Agent(
            name=data.name,
            description=data.description,
            model_id=data.model_id,
            prompt_id=data.prompt_id,
            status=AgentStatus.DRAFT,
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def activate_agent(self, agent_id: int) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        if agent.status == AgentStatus.ACTIVE:
            raise ValueError("Agent 已是 ACTIVE 状态")

        if agent.status == AgentStatus.INACTIVE and False:
            pass

        # 校验关联
        if not agent.model_id:
            raise ValueError("未关联 Model，无法激活")
        model = self.db.query(Model).filter(Model.id == agent.model_id).first()
        if not model:
            raise ValueError("关联的 Model 不存在，无法激活")

        if not agent.prompt_id:
            raise ValueError("未关联 Prompt，无法激活")
        prompt = self.db.query(Prompt).filter(Prompt.id == agent.prompt_id).first()
        if not prompt:
            raise ValueError("关联的 Prompt 不存在，无法激活")

        agent.status = AgentStatus.ACTIVE
        agent.activated_at = datetime.now()

        # 恢复关联 Skill 的可用状态
        self.db.query(Skill).filter(Skill.agent_id == agent.id).update({"is_active": True})

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def deactivate_agent(self, agent_id: int) -> Agent:
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError("Agent not found")

        if agent.status != AgentStatus.ACTIVE:
            raise ValueError("只有 ACTIVE 状态的 Agent 可以停用")

        agent.status = AgentStatus.INACTIVE
        agent.deactivated_at = datetime.now()

        # 标记关联 Skill 为不可用
        self.db.query(Skill).filter(Skill.agent_id == agent.id).update({"is_active": False})

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def change_status(self, agent_id: int, target_status: str) -> Agent:
        if target_status == "active":
            return self.activate_agent(agent_id)
        elif target_status == "inactive":
            return self.deactivate_agent(agent_id)
        else:
            raise ValueError("不支持的目标状态，仅允许 active 或 inactive")

    def delete_agent(self, agent_id: int) -> bool:
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        if agent.status == AgentStatus.ACTIVE:
            raise ValueError("ACTIVE 状态的 Agent 不能删除，请先停用")

        self.db.delete(agent)
        self.db.commit()
        return True

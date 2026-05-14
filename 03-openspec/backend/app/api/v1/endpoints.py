from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schema import (
    AgentCreate, AgentRead, AgentReadWithRelations, AgentStatusChange,
    ModelCreate, ModelRead, PromptCreate, PromptRead, Response,
)
from app.models.entity import AgentStatus
from app.services.model_service import ModelService
from app.services.prompt_service import PromptService
from app.services.agent_service import AgentService

models_router = APIRouter()


@models_router.get("/", response_model=Response[list[ModelRead]])
def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    service = ModelService(db)
    data = service.list_models(skip=skip, limit=limit)
    return Response(data=data)


@models_router.get("/{model_id}", response_model=Response[ModelRead])
def get_model(model_id: int, db: Session = Depends(get_db)):
    service = ModelService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return Response(data=model)


@models_router.post("/", response_model=Response[ModelRead], status_code=201)
def create_model(body: ModelCreate, db: Session = Depends(get_db)):
    service = ModelService(db)
    model = service.create_model(body)
    return Response(data=model)


@models_router.delete("/{model_id}", response_model=Response[None])
def delete_model(model_id: int, db: Session = Depends(get_db)):
    service = ModelService(db)
    if not service.delete_model(model_id):
        raise HTTPException(status_code=404, detail="Model not found")
    return Response(message="Deleted")


prompts_router = APIRouter()


@prompts_router.get("/", response_model=Response[list[PromptRead]])
def list_prompts(skip: int = 0, limit: int = 100, keyword: str | None = None, tag: str | None = None, db: Session = Depends(get_db)):
    service = PromptService(db)
    data = service.list_prompts(skip=skip, limit=limit, keyword=keyword, tag=tag)
    return Response(data=data)


@prompts_router.get("/{prompt_id}", response_model=Response[PromptRead])
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    service = PromptService(db)
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return Response(data=prompt)


@prompts_router.post("/", response_model=Response[PromptRead], status_code=201)
def create_prompt(body: PromptCreate, db: Session = Depends(get_db)):
    service = PromptService(db)
    prompt = service.create_prompt(body)
    return Response(data=prompt)


@prompts_router.delete("/{prompt_id}", response_model=Response[None])
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    service = PromptService(db)
    if not service.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return Response(message="Deleted")


agents_router = APIRouter()


def _agent_to_read(agent):
    """将 ORM Agent 转为 AgentReadWithRelations"""
    return AgentReadWithRelations(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model_id=agent.model_id,
        prompt_id=agent.prompt_id,
        status=agent.status.value if isinstance(agent.status, AgentStatus) else agent.status,
        created_at=agent.created_at,
        model_name=agent.model.name if agent.model else None,
        prompt_name=agent.prompt.title if agent.prompt else None,
    )


@agents_router.get("/", response_model=Response[list[AgentReadWithRelations]])
def list_agents(skip: int = 0, limit: int = 100, status: str | None = None, db: Session = Depends(get_db)):
    service = AgentService(db)
    agents = service.list_agents(skip=skip, limit=limit, status=status)
    return Response(data=[_agent_to_read(a) for a in agents])


@agents_router.get("/{agent_id}", response_model=Response[AgentReadWithRelations])
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
    return Response(data=agent)


@agents_router.patch("/{agent_id}/status", response_model=Response[AgentRead])
def change_agent_status(agent_id: int, body: AgentStatusChange, db: Session = Depends(get_db)):
    service = AgentService(db)
    try:
        target = AgentStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"无效的状态值: {body.status}")
    agent, error = service.change_status(agent_id, target, body.reason)
    if error:
        raise HTTPException(status_code=422, detail=error)
    return Response(data=agent)


@agents_router.delete("/{agent_id}", response_model=Response[None])
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    ok, error = service.delete_agent(agent_id)
    if not ok:
        status_code = 422 if "不允许删除" in error else 404
        raise HTTPException(status_code=status_code, detail=error)
    return Response(message="Deleted")

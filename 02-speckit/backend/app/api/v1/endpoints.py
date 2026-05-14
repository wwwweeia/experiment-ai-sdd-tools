from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schema import (
    AgentCreate, AgentRead, AgentStatusUpdate, AgentStatusResult,
    ModelCreate, ModelRead, PromptCreate, PromptRead, Response,
)
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


def _enrich_agent(agent):
    """为 Agent 附加 model_name 和 prompt_title"""
    agent.model_name = agent.model.name if agent.model else None
    agent.prompt_title = agent.prompt.title if agent.prompt else None
    return agent


@agents_router.get("/", response_model=Response[list[AgentRead]])
def list_agents(skip: int = 0, limit: int = 100, status: str | None = None, db: Session = Depends(get_db)):
    service = AgentService(db)
    data = service.list_agents(skip=skip, limit=limit, status=status)
    return Response(data=[_enrich_agent(a) for a in data])


@agents_router.get("/{agent_id}", response_model=Response[AgentRead])
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return Response(data=_enrich_agent(agent))


@agents_router.post("/", response_model=Response[AgentRead], status_code=201)
def create_agent(body: AgentCreate, db: Session = Depends(get_db)):
    service = AgentService(db)
    agent = service.create_agent(body)
    return Response(data=_enrich_agent(agent))


@agents_router.patch("/{agent_id}/status", response_model=Response[AgentStatusResult])
def change_agent_status(agent_id: int, body: AgentStatusUpdate, db: Session = Depends(get_db)):
    service = AgentService(db)
    try:
        agent = service.change_status(agent_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return Response(data=agent)


@agents_router.delete("/{agent_id}", response_model=Response[None])
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    service = AgentService(db)
    try:
        if not service.delete_agent(agent_id):
            raise HTTPException(status_code=404, detail="Agent not found")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return Response(message="Deleted")

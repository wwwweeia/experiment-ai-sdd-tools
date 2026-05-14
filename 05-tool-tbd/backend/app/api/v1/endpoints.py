from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schema import ModelCreate, ModelRead, PromptCreate, PromptRead, Response
from app.services.model_service import ModelService
from app.services.prompt_service import PromptService

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

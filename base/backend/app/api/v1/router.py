from fastapi import APIRouter
from .endpoints import models_router, prompts_router

router = APIRouter()
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])

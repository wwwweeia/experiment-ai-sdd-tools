from fastapi import APIRouter
from .endpoints import models_router, prompts_router, agents_router

router = APIRouter()
router.include_router(models_router, prefix="/models", tags=["models"])
router.include_router(prompts_router, prefix="/prompts", tags=["prompts"])
router.include_router(agents_router, prefix="/agents", tags=["agents"])

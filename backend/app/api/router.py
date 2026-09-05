from fastapi import APIRouter
from app.api.endpoints.health import router as health_router
from app.api.endpoints.models import router as models_router
from app.api.endpoints.sessions import router as sessions_router
from app.api.endpoints.chat import router as chat_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(sessions_router)
api_router.include_router(chat_router)

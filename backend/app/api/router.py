from fastapi import APIRouter

from backend.app.api.v1.admin_config import router as admin_config_router
from backend.app.api.v1.admin_clientes import router as admin_clientes_router
from backend.app.api.v1.avaliacoes import router as avaliacoes_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admin_clientes_router)
api_router.include_router(admin_config_router)
api_router.include_router(avaliacoes_router)

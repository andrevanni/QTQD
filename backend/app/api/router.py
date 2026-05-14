from fastapi import APIRouter

from backend.app.api.v1.admin_clientes import router as admin_clientes_router
from backend.app.api.v1.admin_config import router as admin_config_router
from backend.app.api.v1.admin_logins import router as admin_logins_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.avaliacoes import router as avaliacoes_router
from backend.app.api.v1.cliente_config import router as cliente_config_router
from backend.app.api.v1.importacao import router as importacao_router
from backend.app.api.v1.cron import router as cron_router

api_router = APIRouter(prefix="/api/v1")

# Autenticação do cliente (sem auth obrigatório)
api_router.include_router(auth_router)

# Rotas do cliente (exigem JWT Supabase Auth)
api_router.include_router(avaliacoes_router)
api_router.include_router(cliente_config_router)

# Rotas administrativas (exigem X-Admin-Token)
api_router.include_router(admin_clientes_router)
api_router.include_router(admin_config_router)
api_router.include_router(admin_logins_router)
api_router.include_router(importacao_router)
api_router.include_router(cron_router)

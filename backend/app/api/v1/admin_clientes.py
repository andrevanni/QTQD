from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.admin_auth import require_admin_token
from backend.app.db.client import get_supabase
from backend.app.schemas.admin_clientes import (
    ClienteAdminCreateRequest,
    ClienteAdminResumo,
    ClienteAdminUpdateRequest,
)

router = APIRouter(prefix="/admin/clientes", tags=["admin-clientes"], dependencies=[Depends(require_admin_token)])

_COLS = "id, nome, slug, status, plano, contato_nome, contato_email, observacoes, created_at, updated_at"


@router.get("", response_model=list[ClienteAdminResumo])
def listar_clientes() -> list[ClienteAdminResumo]:
    result = get_supabase().table("tenants").select(_COLS).order("created_at", desc=True).execute()
    return [ClienteAdminResumo(**row) for row in result.data]


@router.post("", response_model=ClienteAdminResumo, status_code=201)
def criar_cliente(payload: ClienteAdminCreateRequest) -> ClienteAdminResumo:
    result = get_supabase().table("tenants").insert(payload.model_dump()).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar cliente.")
    return ClienteAdminResumo(**result.data[0])


@router.patch("/{tenant_id}", response_model=ClienteAdminResumo)
def atualizar_cliente(tenant_id: UUID, payload: ClienteAdminUpdateRequest) -> ClienteAdminResumo:
    values = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not values:
        raise HTTPException(status_code=400, detail="Nenhum campo enviado para atualizacao.")
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = get_supabase().table("tenants").update(values).eq("id", str(tenant_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    return ClienteAdminResumo(**result.data[0])

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.auth import get_current_tenant
from backend.app.db.client import get_supabase
from backend.app.schemas.avaliacoes import (
    AvaliacaoCreateRequest,
    AvaliacaoResponse,
    AvaliacaoUpdateRequest,
    AvaliacaoValores,
)
from backend.app.services.calculos_qtqd import calcular_indicadores

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])

_COLS = "id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at"


def _serialize(row: dict) -> AvaliacaoResponse:
    valores = AvaliacaoValores(**(row.get("valores") or {}))
    return AvaliacaoResponse(
        id=row["id"],
        tenant_id=row["tenant_id"],
        semana_referencia=row["semana_referencia"],
        status=row["status"],
        observacoes=row.get("observacoes"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        valores=valores,
        indicadores=calcular_indicadores(valores),
    )


@router.get("", response_model=list[AvaliacaoResponse])
def listar(tenant_id: UUID = Depends(get_current_tenant)) -> list[AvaliacaoResponse]:
    result = (
        get_supabase()
        .table("avaliacoes_semanais")
        .select(_COLS)
        .eq("tenant_id", str(tenant_id))
        .order("semana_referencia", desc=True)
        .execute()
    )
    return [_serialize(row) for row in result.data]


@router.get("/{avaliacao_id}", response_model=AvaliacaoResponse)
def obter(avaliacao_id: UUID, tenant_id: UUID = Depends(get_current_tenant)) -> AvaliacaoResponse:
    result = (
        get_supabase()
        .table("avaliacoes_semanais")
        .select(_COLS)
        .eq("id", str(avaliacao_id))
        .eq("tenant_id", str(tenant_id))
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    return _serialize(result.data[0])


@router.post("", response_model=AvaliacaoResponse, status_code=201)
def criar(payload: AvaliacaoCreateRequest, tenant_id: UUID = Depends(get_current_tenant)) -> AvaliacaoResponse:
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_id do payload nao confere com o token.")
    valores = AvaliacaoValores(**payload.model_dump(exclude={"tenant_id", "semana_referencia", "status", "observacoes"}))
    data = {
        "tenant_id": str(tenant_id),
        "semana_referencia": str(payload.semana_referencia),
        "status": payload.status,
        "observacoes": payload.observacoes,
        "valores": valores.model_dump(),
    }
    result = get_supabase().table("avaliacoes_semanais").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar avaliacao.")
    return _serialize(result.data[0])


@router.patch("/{avaliacao_id}", response_model=AvaliacaoResponse)
def atualizar(
    avaliacao_id: UUID,
    payload: AvaliacaoUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant),
) -> AvaliacaoResponse:
    sb = get_supabase()
    current = sb.table("avaliacoes_semanais").select(_COLS).eq("id", str(avaliacao_id)).eq("tenant_id", str(tenant_id)).limit(1).execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    row = current.data[0]
    next_valores = AvaliacaoValores(**(payload.valores.model_dump() if payload.valores else row.get("valores") or {}))
    update_data = {
        "status": payload.status or row["status"],
        "observacoes": payload.observacoes if payload.observacoes is not None else row.get("observacoes"),
        "valores": next_valores.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = sb.table("avaliacoes_semanais").update(update_data).eq("id", str(avaliacao_id)).eq("tenant_id", str(tenant_id)).execute()
    return _serialize(result.data[0])


@router.post("/{avaliacao_id}/fechar", response_model=AvaliacaoResponse)
def fechar(avaliacao_id: UUID, tenant_id: UUID = Depends(get_current_tenant)) -> AvaliacaoResponse:
    update_data = {
        "status": "fechada",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = (
        get_supabase()
        .table("avaliacoes_semanais")
        .update(update_data)
        .eq("id", str(avaliacao_id))
        .eq("tenant_id", str(tenant_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    return _serialize(result.data[0])


@router.delete("/{avaliacao_id}", status_code=204)
def excluir(avaliacao_id: UUID, tenant_id: UUID = Depends(get_current_tenant)) -> None:
    result = (
        get_supabase()
        .table("avaliacoes_semanais")
        .delete()
        .eq("id", str(avaliacao_id))
        .eq("tenant_id", str(tenant_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")

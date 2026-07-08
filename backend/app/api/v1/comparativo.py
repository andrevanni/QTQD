from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.core.auth import get_current_tenant
from backend.app.db.client import get_supabase
from backend.app.services.series_service import (
    build_comparativo_snapshot,
    build_comparativo_evolucao,
)

router = APIRouter(prefix="/me", tags=["comparativo"])


def _carregar(tenant_id: UUID):
    sb = get_supabase()
    avals = (
        sb.table("avaliacoes_semanais")
        .select("semana_referencia, grupo_id, loja_id, valores")
        .eq("tenant_id", str(tenant_id))
        .execute()
        .data
    )
    grupos = (
        sb.table("grupos_economicos")
        .select("id, nome, nivel_preenchimento")
        .eq("tenant_id", str(tenant_id))
        .execute()
        .data
    )
    lojas = (
        sb.table("lojas")
        .select("id, grupo_id, nome")
        .eq("tenant_id", str(tenant_id))
        .execute()
        .data
    )
    return avals, grupos, lojas


@router.get("/comparativo")
def comparativo(
    tenant_id: UUID = Depends(get_current_tenant),
    nivel: str = "rede",
    grupo_id: UUID | None = None,
    modo: str = "snapshot",
    semana: str | None = None,
) -> dict:
    avals, grupos, lojas = _carregar(tenant_id)
    ref = str(grupo_id) if grupo_id else None
    if modo == "evolucao":
        return build_comparativo_evolucao(avals, grupos, lojas, nivel, ref)
    if not semana:
        semanas = sorted({a["semana_referencia"] for a in avals}, reverse=True)
        if not semanas:
            return {"semana": None, "unidades": [], "total": None}
        semana = semanas[0]
    return build_comparativo_snapshot(avals, grupos, lojas, nivel, ref, semana)

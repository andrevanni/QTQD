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
    from backend.app.services.relatorio_service import enviar_relatorio_para_tenant

    sb = get_supabase()
    result = (
        sb.table("avaliacoes_semanais")
        .update({"status": "fechada", "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", str(avaliacao_id))
        .eq("tenant_id", str(tenant_id))
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")

    cfg_res = sb.table("tenant_pdf_config").select("ativo").eq("tenant_id", str(tenant_id)).limit(1).execute()
    envio_ativo = (cfg_res.data[0].get("ativo", True) if cfg_res.data else True)
    if envio_ativo:
        try:
            enviar_relatorio_para_tenant(str(tenant_id), sb, avaliacao_id=str(avaliacao_id), origem="fechar")
        except Exception:
            pass  # Não bloqueia o fechamento se o envio falhar

    return _serialize(result.data[0])


@router.post("/{avaliacao_id}/finalizar")
def finalizar(avaliacao_id: UUID, tenant_id: UUID = Depends(get_current_tenant)) -> dict:
    """Marca a semana como finalizada e dispara o e-mail automático para todos os usuários."""
    from backend.app.services.relatorio_service import enviar_relatorio_para_tenant

    sb = get_supabase()
    check = sb.table("avaliacoes_semanais").select("id,status").eq("id", str(avaliacao_id)).eq("tenant_id", str(tenant_id)).limit(1).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")

    sb.table("avaliacoes_semanais").update(
        {"status": "finalizado", "updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", str(avaliacao_id)).eq("tenant_id", str(tenant_id)).execute()

    final = sb.table("avaliacoes_semanais").select(_COLS).eq("id", str(avaliacao_id)).limit(1).execute()
    avaliacao = _serialize(final.data[0])

    try:
        destinatarios = enviar_relatorio_para_tenant(str(tenant_id), sb, avaliacao_id=str(avaliacao_id), origem="finalizar")
    except Exception:
        destinatarios = []

    return {
        "avaliacao": avaliacao.model_dump(),
        "enviado_para": destinatarios,
        "n_destinatarios": len(destinatarios),
    }


@router.post("/{avaliacao_id}/reenviar-relatorio")
def reenviar_relatorio(
    avaliacao_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    email_teste: str | None = None,
) -> dict:
    """Reenvia o e-mail de relatório sem alterar o status da avaliação.
    Passar email_teste=addr@x.com restringe o envio a esse endereço apenas.
    """
    from backend.app.services.relatorio_service import enviar_relatorio_para_tenant

    sb = get_supabase()
    if not sb.table("avaliacoes_semanais").select("id").eq("id", str(avaliacao_id)).eq("tenant_id", str(tenant_id)).limit(1).execute().data:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")

    try:
        destinatarios = enviar_relatorio_para_tenant(str(tenant_id), sb, email_teste=email_teste, avaliacao_id=str(avaliacao_id), origem="reenviar")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar relatorio: {e}")

    return {"enviado_para": destinatarios, "n_destinatarios": len(destinatarios)}


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

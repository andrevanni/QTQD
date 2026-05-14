"""
Endpoints de Cron — chamados pelo Vercel Cron (sem autenticação de usuário,
protegidos pelo cabeçalho X-Vercel-Cron ou pela variável CRON_SECRET).
"""
from __future__ import annotations
import os
from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/cron", tags=["cron"])

CRON_SECRET = os.getenv("CRON_SECRET", "")


def _check_cron_auth(x_vercel_cron: str | None, authorization: str | None) -> None:
    """Aceita requisições do Vercel Cron (x-vercel-cron: 1) ou com CRON_SECRET."""
    if x_vercel_cron == "1":
        return  # Chamada legítima do Vercel Cron
    if CRON_SECRET and authorization == f"Bearer {CRON_SECRET}":
        return
    raise HTTPException(status_code=401, detail="Acesso nao autorizado ao endpoint de cron.")


@router.get("/acompanhamento-semanal")
def cron_acompanhamento_semanal(
    x_vercel_cron: str | None = Header(default=None, alias="x-vercel-cron"),
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Cron semanal: envia o relatório de acompanhamento de rascunhos para todos os
    tenants com rascunhos_ativo=True na config de PDF.
    Vercel Cron schedule: toda segunda-feira às 09:00 UTC (0 9 * * 1).
    """
    _check_cron_auth(x_vercel_cron, authorization)

    from backend.app.db.client import get_supabase
    from backend.app.services.relatorio_rascunhos_service import enviar_acompanhamento_rascunhos
    from datetime import date

    sb = get_supabase()

    # Busca tenants com acompanhamento ativo
    configs = (
        sb.table("tenant_pdf_config")
        .select("tenant_id,rascunhos_dia_semana")
        .eq("rascunhos_ativo", True)
        .execute()
        .data or []
    )

    hoje_weekday = date.today().isoweekday()  # 1=Seg … 7=Dom
    enviados: list[str] = []
    erros: list[str]   = []

    for cfg in configs:
        dia = int(cfg.get("rascunhos_dia_semana") or 1)
        if dia != hoje_weekday:
            continue  # Não é o dia configurado para este tenant
        tid = str(cfg["tenant_id"])
        try:
            destinatarios = enviar_acompanhamento_rascunhos(
                tid, sb, origem="cron_semanal"
            )
            enviados.extend(destinatarios)
        except Exception as e:
            erros.append(f"{tid}: {e}")

    return {
        "ok":     True,
        "data":   date.today().isoformat(),
        "enviados": len(enviados),
        "erros":  erros,
    }

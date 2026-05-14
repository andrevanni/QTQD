"""
Serviço de Acompanhamento de Rascunhos QTQD.
Envia e-mail semanal com o status dos lançamentos dos últimos meses.
"""
from __future__ import annotations
from datetime import date, timedelta


def enviar_acompanhamento_rascunhos(
    tenant_id: str,
    sb,
    email_teste: str | None = None,
    origem: str = "acompanhamento",
    meses: int = 3,
) -> list[str]:
    """
    Busca os lançamentos dos últimos `meses` meses, monta o e-mail de
    acompanhamento de rascunhos e envia para os usuários ativos do tenant.
    Retorna a lista de e-mails que receberam.
    """
    from backend.app.services.relatorio_rascunhos_html import build_acompanhamento_html
    from backend.app.services.email_service import send_html
    from backend.app.schemas.avaliacoes import AvaliacaoValores
    from backend.app.services.calculos_qtqd import calcular_indicadores

    hoje    = date.today()
    cutoff  = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
    # cutoff = primeiro dia do mês que começa `meses` meses atrás
    ano, mes = cutoff.year, cutoff.month
    mes -= (meses - 1)
    while mes <= 0:
        mes += 12; ano -= 1
    data_inicio = date(ano, mes, 1).isoformat()

    # Nome e branding do tenant
    tenant_res = sb.table("tenants").select("nome").eq("id", tenant_id).limit(1).execute()
    tenant_nome = tenant_res.data[0]["nome"] if tenant_res.data else "Cliente"

    brand_res = (
        sb.table("tenant_branding")
        .select("logo_cliente_url")
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    logo_url = (brand_res.data[0].get("logo_cliente_url") if brand_res.data else None)

    # Lançamentos do período (todos os status)
    avals = (
        sb.table("avaliacoes_semanais")
        .select("semana_referencia,status,valores")
        .eq("tenant_id", tenant_id)
        .gte("semana_referencia", data_inicio)
        .order("semana_referencia", desc=True)
        .execute()
        .data or []
    )

    registros: list[dict] = []
    for av in avals:
        raw    = av.get("valores") or {}
        status = av.get("status", "rascunho")
        qt_total    = None
        qd_total    = None
        saldo       = None
        try:
            valores     = AvaliacaoValores(**raw)
            indicadores = calcular_indicadores(valores)
            def _ind(cod: str) -> float | None:
                for i in indicadores:
                    if i.codigo == cod:
                        return i.valor
                return None
            qt_total = _ind("qt_total")
            qd_total = _ind("qd_total")
            saldo    = _ind("saldo_qt_qd")
        except Exception:
            pass
        registros.append({
            "semana_referencia": av["semana_referencia"],
            "status":  status,
            "qt_total": qt_total,
            "qd_total": qd_total,
            "saldo":    saldo,
        })

    html = build_acompanhamento_html(
        tenant_nome=tenant_nome,
        portal_url="https://qtqd-vt2a.vercel.app/cliente",
        registros=registros,
        logo_cliente_url=logo_url,
        meses=meses,
    )

    # Destinatários
    usuarios_res = (
        sb.table("tenant_usuarios")
        .select("email,nome")
        .eq("tenant_id", tenant_id)
        .eq("ativo", True)
        .execute()
    )
    if email_teste:
        destinatarios = [email_teste]
    else:
        destinatarios = [u["email"] for u in (usuarios_res.data or []) if u.get("email")]
    if not destinatarios:
        return []

    n_rasc  = sum(1 for r in registros if r["status"] == "rascunho")
    subject = (
        f"QTQD — Acompanhamento de Rascunhos — {tenant_nome} — "
        + hoje.strftime("%d/%m/%Y")
        + (f" ({n_rasc} pendente{'s' if n_rasc != 1 else ''})" if n_rasc else " ✅ Tudo confirmado")
    )

    status_log = "success"
    erro_log: str | None = None
    try:
        send_html(destinatarios, subject, html)
    except Exception as e:
        status_log = "error"
        erro_log   = str(e)
        raise
    finally:
        try:
            sb.table("email_log").insert({
                "tenant_id":      tenant_id,
                "destinatarios":  destinatarios,
                "status":         status_log,
                "n_destinatarios": len(destinatarios),
                "origem":         origem,
                **({"erro": erro_log} if erro_log else {}),
            }).execute()
        except Exception:
            pass

    return destinatarios

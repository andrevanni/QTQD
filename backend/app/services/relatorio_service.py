"""
Lógica compartilhada de envio de relatório semanal.
Usada pelo endpoint admin (manual) e pelo endpoint de finalização (automático).
"""
from datetime import date


def enviar_relatorio_para_tenant(tenant_id: str, sb) -> list[str]:
    """
    Monta e envia o relatório semanal para todos os usuários ativos do tenant.
    Retorna lista de e-mails que receberam.
    Lança exceção se o envio falhar.
    """
    from backend.app.schemas.avaliacoes import AvaliacaoValores
    from backend.app.services.calculos_qtqd import calcular_indicadores
    from backend.app.services.relatorio_html import build_relatorio_html
    from backend.app.services.email_service import send_html

    # Config PDF do tenant
    cfg_res = sb.table("tenant_pdf_config").select("*").eq("tenant_id", tenant_id).limit(1).execute()
    cfg = cfg_res.data[0] if cfg_res.data else {}
    n_retratos       = int(cfg.get("n_retratos", 8))
    incluir_inspetor = bool(cfg.get("incluir_inspetor", False))
    incluir_graficos  = bool(cfg.get("incluir_graficos", False))

    # Nome do tenant
    tenant_res = sb.table("tenants").select("nome").eq("id", tenant_id).limit(1).execute()
    tenant_nome = tenant_res.data[0]["nome"] if tenant_res.data else "Cliente"

    # Últimas N avaliações
    avals = (
        sb.table("avaliacoes_semanais")
        .select("semana_referencia,valores")
        .eq("tenant_id", tenant_id)
        .order("semana_referencia", desc=True)
        .limit(n_retratos)
        .execute()
        .data
    )
    if not avals:
        return []

    avals_sorted = sorted(avals, key=lambda x: x["semana_referencia"])
    periodos = []
    for av in avals_sorted:
        try:
            d = date.fromisoformat(av["semana_referencia"])
            data_fmt = d.strftime("%d/%m/%Y")
        except Exception:
            data_fmt = av["semana_referencia"]
        valores = AvaliacaoValores(**(av.get("valores") or {}))
        periodos.append({"data": data_fmt, "indicadores": calcular_indicadores(valores)})

    # Branding
    brand_res = (
        sb.table("tenant_branding")
        .select("nome_portal,logo_cliente_url")
        .eq("tenant_id", tenant_id)
        .limit(1)
        .execute()
    )
    brand = brand_res.data[0] if brand_res.data else {}
    logo_cliente_url = brand.get("logo_cliente_url") or None

    html = build_relatorio_html(
        tenant_nome=tenant_nome,
        portal_url="https://qtqd-vt2a.vercel.app/cliente",
        periodos=periodos,
        incluir_inspetor=incluir_inspetor,
        incluir_graficos=incluir_graficos,
        logo_cliente_url=logo_cliente_url,
    )

    from backend.app.services.relatorio_pdf import build_relatorio_pdf
    pdf_bytes = build_relatorio_pdf(tenant_nome=tenant_nome, periodos=periodos)

    # Destinatários — todos os usuários ativos com e-mail
    usuarios_res = (
        sb.table("tenant_usuarios")
        .select("email,nome")
        .eq("tenant_id", tenant_id)
        .eq("ativo", True)
        .execute()
    )
    destinatarios = [u["email"] for u in (usuarios_res.data or []) if u.get("email")]
    if not destinatarios:
        return []

    today = date.today().strftime("%d/%m/%Y")
    today_file = date.today().strftime("%Y%m%d")
    subject = f"QTQD Atualizado — {tenant_nome} — {today}"
    pdf_filename = f"relatorio_qtqd_{today_file}.pdf"
    send_html(destinatarios, subject, html, pdf_bytes=pdf_bytes, pdf_filename=pdf_filename)
    return destinatarios

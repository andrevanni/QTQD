"""
Lógica compartilhada de envio de relatório semanal.
Usada pelo endpoint admin (manual) e pelo endpoint de finalização (automático).
"""
from datetime import date


def montar_avals_por_nivel(all_avals: list[dict], grupos: list[dict], modo_rede: bool, nivel: str, ref: str | None) -> list[dict]:
    """Devolve [{semana_referencia, valores}] no nível pedido, ordenado desc.
    Sem modo_rede: usa as avals como estão (comportamento atual)."""
    if not modo_rede or nivel not in ("loja", "grupo", "rede"):
        return sorted(all_avals, key=lambda x: x["semana_referencia"], reverse=True)
    from backend.app.services.series_service import build_series
    serie = build_series(all_avals, grupos, nivel, ref)  # já desc
    return serie


def enviar_relatorio_para_tenant(
    tenant_id: str,
    sb,
    email_teste: str | None = None,
    avaliacao_id: str | None = None,
    origem: str = "manual",
) -> list[str]:
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

    # Nível do relatório (loja/grupo/rede) — só relevante quando o tenant está em modo_rede
    modo_rede_res = sb.table("tenants").select("modo_rede").eq("id", tenant_id).limit(1).execute()
    modo_rede = bool(modo_rede_res.data[0].get("modo_rede")) if modo_rede_res.data else False
    nivel_relatorio = cfg.get("nivel_relatorio") or "loja"

    # Todas as avaliações publicadas (sem rascunhos) — a consolidação por nível precisa de todas as lojas
    all_avals = (
        sb.table("avaliacoes_semanais")
        .select("semana_referencia,grupo_id,loja_id,valores")
        .eq("tenant_id", tenant_id)
        .neq("status", "rascunho")
        .execute()
        .data
    ) or []
    if not all_avals:
        return []
    grupos = sb.table("grupos_economicos").select("id,nivel_preenchimento").eq("tenant_id", tenant_id).execute().data or []

    ref = None
    if modo_rede and avaliacao_id:
        av_ref = sb.table("avaliacoes_semanais").select("grupo_id,loja_id").eq("id", avaliacao_id).limit(1).execute()
        if av_ref.data:
            if nivel_relatorio == "loja":
                ref = av_ref.data[0].get("loja_id")
            elif nivel_relatorio == "grupo":
                ref = av_ref.data[0].get("grupo_id")

    nivel_efetivo = nivel_relatorio
    if modo_rede and nivel_relatorio in ("loja", "grupo") and ref is None:
        nivel_efetivo = "rede"  # envio manual sem contexto de loja -> consolidado da rede (evita relatório vazio)

    serie = montar_avals_por_nivel(all_avals, grupos, modo_rede, nivel_efetivo, ref)[:n_retratos]

    avals_sorted = sorted(serie, key=lambda x: x["semana_referencia"])
    periodos = []
    for av in avals_sorted:
        try:
            d = date.fromisoformat(av["semana_referencia"])
            data_fmt = d.strftime("%d/%m/%Y")
        except Exception:
            data_fmt = av["semana_referencia"]
        raw_valores = av.get("valores") or {}
        valores = AvaliacaoValores(**raw_valores)
        periodos.append({
            "data": data_fmt,
            "indicadores": calcular_indicadores(valores),
            "valores": raw_valores,
        })

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

    # Destinatários — todos os usuários ativos com e-mail
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

    today = date.today().strftime("%d/%m/%Y")
    subject = f"QTQD Atualizado — {tenant_nome} — {today}"

    status_log = "success"
    erro_log: str | None = None
    try:
        send_html(destinatarios, subject, html)
    except Exception as e:
        status_log = "error"
        erro_log = str(e)
        raise
    finally:
        try:
            log_row: dict = {
                "tenant_id": tenant_id,
                "destinatarios": destinatarios,
                "status": status_log,
                "n_destinatarios": len(destinatarios),
                "origem": origem,
            }
            if avaliacao_id:
                log_row["avaliacao_id"] = avaliacao_id
            if erro_log:
                log_row["erro"] = erro_log
            sb.table("email_log").insert(log_row).execute()
        except Exception:
            pass  # log nunca pode quebrar o fluxo principal

    return destinatarios

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.admin_auth import require_admin_token
from backend.app.db.client import get_supabase
from backend.app.schemas.admin_config import (
    BrandingAdminResponse,
    BrandingAdminUpsertRequest,
    ComponenteConfigResponse,
    ComponentesConfigUpsertRequest,
    ImportacaoAdminCreateRequest,
    ImportacaoAdminResponse,
    LicencaAdminCreateRequest,
    LicencaAdminResponse,
    LicencaAdminUpdateRequest,
    PdfConfigRequest,
    PdfConfigResponse,
    UsuarioAdminCreateRequest,
    UsuarioAdminResponse,
    UsuarioAdminUpdateRequest,
)

router = APIRouter(prefix="/admin", tags=["admin-config"], dependencies=[Depends(require_admin_token)])


@router.get("/licencas", response_model=list[LicencaAdminResponse])
def listar_licencas(tenant_id: UUID | None = None) -> list[LicencaAdminResponse]:
    query = get_supabase().table("tenant_licencas").select("*")
    if tenant_id:
        query = query.eq("tenant_id", str(tenant_id))
    result = query.order("inicio_vigencia", desc=True).execute()
    return [LicencaAdminResponse(**row) for row in result.data]


@router.delete("/licencas/{licenca_id}", status_code=204)
def excluir_licenca(licenca_id: UUID) -> None:
    result = get_supabase().table("tenant_licencas").delete().eq("id", str(licenca_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vigencia nao encontrada.")


@router.patch("/licencas/{licenca_id}", response_model=LicencaAdminResponse)
def atualizar_licenca(licenca_id: UUID, payload: LicencaAdminUpdateRequest) -> LicencaAdminResponse:
    values = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not values:
        raise HTTPException(status_code=400, detail="Nenhum campo enviado para atualizacao.")
    if "inicio_vigencia" in values:
        values["inicio_vigencia"] = str(values["inicio_vigencia"])
    if "fim_vigencia" in values:
        values["fim_vigencia"] = str(values["fim_vigencia"])
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = get_supabase().table("tenant_licencas").update(values).eq("id", str(licenca_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Vigencia nao encontrada.")
    return LicencaAdminResponse(**result.data[0])


@router.post("/licencas", response_model=LicencaAdminResponse, status_code=201)
def criar_licenca(payload: LicencaAdminCreateRequest) -> LicencaAdminResponse:
    data = payload.model_dump()
    data["tenant_id"] = str(data["tenant_id"])
    if data.get("inicio_vigencia"):
        data["inicio_vigencia"] = str(data["inicio_vigencia"])
    if data.get("fim_vigencia"):
        data["fim_vigencia"] = str(data["fim_vigencia"])
    result = get_supabase().table("tenant_licencas").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar licenca.")
    return LicencaAdminResponse(**result.data[0])


@router.get("/branding/{tenant_id}", response_model=BrandingAdminResponse | None)
def obter_branding(tenant_id: UUID) -> BrandingAdminResponse | None:
    result = get_supabase().table("tenant_branding").select("*").eq("tenant_id", str(tenant_id)).limit(1).execute()
    return BrandingAdminResponse(**result.data[0]) if result.data else None


@router.put("/branding/{tenant_id}", response_model=BrandingAdminResponse)
def salvar_branding(tenant_id: UUID, payload: BrandingAdminUpsertRequest) -> BrandingAdminResponse:
    data = {"tenant_id": str(tenant_id), **payload.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}
    result = get_supabase().table("tenant_branding").upsert(data, on_conflict="tenant_id").execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao salvar branding.")
    return BrandingAdminResponse(**result.data[0])


@router.get("/componentes-config/{tenant_id}", response_model=list[ComponenteConfigResponse])
def listar_componentes_config(tenant_id: UUID) -> list[ComponenteConfigResponse]:
    result = (
        get_supabase()
        .table("tenant_componentes_config")
        .select("*")
        .eq("tenant_id", str(tenant_id))
        .order("ordem_exibicao")
        .order("codigo_componente")
        .execute()
    )
    return [ComponenteConfigResponse(**row) for row in result.data]


@router.put("/componentes-config/{tenant_id}", response_model=list[ComponenteConfigResponse])
def salvar_componentes_config(tenant_id: UUID, payload: ComponentesConfigUpsertRequest) -> list[ComponenteConfigResponse]:
    sb = get_supabase()
    rows = []
    for item in payload.itens:
        data = {
            "tenant_id": str(tenant_id),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **item.model_dump(),
        }
        result = sb.table("tenant_componentes_config").upsert(data, on_conflict="tenant_id,codigo_componente").execute()
        if result.data:
            rows.append(ComponenteConfigResponse(**result.data[0]))
    return rows


@router.get("/pdf-config/{tenant_id}", response_model=PdfConfigResponse | None)
def obter_pdf_config(tenant_id: UUID) -> PdfConfigResponse | None:
    result = get_supabase().table("tenant_pdf_config").select("*").eq("tenant_id", str(tenant_id)).limit(1).execute()
    return PdfConfigResponse(**result.data[0]) if result.data else None


@router.put("/pdf-config/{tenant_id}", response_model=PdfConfigResponse)
def salvar_pdf_config(tenant_id: UUID, payload: PdfConfigRequest) -> PdfConfigResponse:
    data = {"tenant_id": str(tenant_id), "updated_at": datetime.now(timezone.utc).isoformat(), **payload.model_dump()}
    result = get_supabase().table("tenant_pdf_config").upsert(data, on_conflict="tenant_id").execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao salvar configuracao de PDF.")
    return PdfConfigResponse(**result.data[0])


@router.post("/enviar-relatorio/{tenant_id}", status_code=200)
def enviar_relatorio(tenant_id: UUID) -> dict:
    from backend.app.schemas.avaliacoes import AvaliacaoValores
    from backend.app.services.calculos_qtqd import calcular_indicadores
    from backend.app.services.relatorio_html import build_relatorio_html
    from backend.app.services.email_service import send_html

    sb = get_supabase()

    # Busca config PDF
    cfg_res = sb.table("tenant_pdf_config").select("*").eq("tenant_id", str(tenant_id)).limit(1).execute()
    cfg = cfg_res.data[0] if cfg_res.data else {}
    n_retratos       = int(cfg.get("n_retratos", 8))
    incluir_inspetor = bool(cfg.get("incluir_inspetor", False))
    incluir_graficos  = bool(cfg.get("incluir_graficos", False))

    # Busca nome do tenant
    tenant_res = sb.table("tenants").select("nome").eq("id", str(tenant_id)).limit(1).execute()
    tenant_nome = tenant_res.data[0]["nome"] if tenant_res.data else "Cliente"

    # Busca últimas N avaliações
    avals = sb.table("avaliacoes_semanais")\
        .select("semana_referencia,valores")\
        .eq("tenant_id", str(tenant_id))\
        .order("semana_referencia", desc=True)\
        .limit(n_retratos)\
        .execute().data

    if not avals:
        raise HTTPException(status_code=404, detail="Nenhuma avaliacao encontrada para este tenant.")

    avals_sorted = sorted(avals, key=lambda x: x["semana_referencia"])
    periodos = []
    for av in avals_sorted:
        from datetime import date
        try:
            d = date.fromisoformat(av["semana_referencia"])
            data_fmt = d.strftime("%d/%m/%Y")
        except Exception:
            data_fmt = av["semana_referencia"]
        valores = AvaliacaoValores(**(av.get("valores") or {}))
        periodos.append({"data": data_fmt, "indicadores": calcular_indicadores(valores)})

    # Busca destinatários
    usuarios_res = sb.table("tenant_usuarios")\
        .select("email,nome")\
        .eq("tenant_id", str(tenant_id))\
        .eq("ativo", True)\
        .execute()
    destinatarios = [u["email"] for u in (usuarios_res.data or []) if u.get("email")]

    if not destinatarios:
        raise HTTPException(status_code=400, detail="Nenhum usuario ativo com e-mail encontrado para este tenant.")

    # Busca branding para URL do portal
    brand_res = sb.table("tenant_branding").select("nome_portal").eq("tenant_id", str(tenant_id)).limit(1).execute()
    portal_url = "https://qtqd-vt2a.vercel.app/cliente"

    html = build_relatorio_html(
        tenant_nome=tenant_nome,
        portal_url=portal_url,
        periodos=periodos,
        incluir_inspetor=incluir_inspetor,
        incluir_graficos=incluir_graficos,
    )

    from datetime import date
    today = date.today().strftime("%d/%m/%Y")
    subject = f"Relatório QTQD — {tenant_nome} — {today}"

    try:
        send_html(destinatarios, subject, html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {e}")

    return {"ok": True, "enviado_para": destinatarios, "n_periodos": len(periodos)}


@router.get("/usuarios", response_model=list[UsuarioAdminResponse])
def listar_usuarios(tenant_id: UUID | None = None) -> list[UsuarioAdminResponse]:
    query = get_supabase().table("tenant_usuarios").select("*")
    if tenant_id:
        query = query.eq("tenant_id", str(tenant_id))
    result = query.order("nome").execute()
    return [UsuarioAdminResponse(**r) for r in result.data]


@router.post("/usuarios", response_model=UsuarioAdminResponse, status_code=201)
def criar_usuario(payload: UsuarioAdminCreateRequest) -> UsuarioAdminResponse:
    data = payload.model_dump()
    data["tenant_id"] = str(data["tenant_id"])
    result = get_supabase().table("tenant_usuarios").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar usuario.")
    return UsuarioAdminResponse(**result.data[0])


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioAdminResponse)
def atualizar_usuario(usuario_id: UUID, payload: UsuarioAdminUpdateRequest) -> UsuarioAdminResponse:
    values = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not values:
        raise HTTPException(status_code=400, detail="Nenhum campo enviado.")
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = get_supabase().table("tenant_usuarios").update(values).eq("id", str(usuario_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    return UsuarioAdminResponse(**result.data[0])


@router.delete("/usuarios/{usuario_id}", status_code=204)
def excluir_usuario(usuario_id: UUID) -> None:
    result = get_supabase().table("tenant_usuarios").delete().eq("id", str(usuario_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")


@router.get("/importacoes", response_model=list[ImportacaoAdminResponse])
def listar_importacoes(tenant_id: UUID | None = None) -> list[ImportacaoAdminResponse]:
    query = get_supabase().table("tenant_importacoes").select("*")
    if tenant_id:
        query = query.eq("tenant_id", str(tenant_id))
    result = query.order("created_at", desc=True).execute()
    return [ImportacaoAdminResponse(**row) for row in result.data]


@router.post("/importacoes", response_model=ImportacaoAdminResponse, status_code=201)
def criar_importacao(payload: ImportacaoAdminCreateRequest) -> ImportacaoAdminResponse:
    data = payload.model_dump()
    data["tenant_id"] = str(data["tenant_id"])
    result = get_supabase().table("tenant_importacoes").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar importacao.")
    return ImportacaoAdminResponse(**result.data[0])

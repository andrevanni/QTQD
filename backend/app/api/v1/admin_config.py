from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

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


@router.post("/branding/{tenant_id}/logo")
async def upload_logo_cliente(tenant_id: UUID, arquivo: UploadFile = File(...)) -> dict:
    if arquivo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Use JPG, PNG ou WebP.")
    content = await arquivo.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Máximo 2 MB.")
    ext = (arquivo.filename or "logo.jpg").rsplit(".", 1)[-1].lower()
    path = f"{tenant_id}/logo.{ext}"
    sb = get_supabase()
    try:
        sb.storage.from_("logos").remove([path])
    except Exception:
        pass
    sb.storage.from_("logos").upload(path, content, {"content-type": arquivo.content_type})
    url = sb.storage.from_("logos").get_public_url(path)
    return {"url": url}


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
    now = datetime.now(timezone.utc).isoformat()
    rows_data = [
        {"tenant_id": str(tenant_id), "updated_at": now, **item.model_dump()}
        for item in payload.itens
    ]
    if not rows_data:
        return []
    result = sb.table("tenant_componentes_config").upsert(
        rows_data, on_conflict="tenant_id,codigo_componente"
    ).execute()
    return [ComponenteConfigResponse(**row) for row in (result.data or [])]


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
    from backend.app.services.relatorio_service import enviar_relatorio_para_tenant
    sb = get_supabase()
    try:
        destinatarios = enviar_relatorio_para_tenant(str(tenant_id), sb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar relatorio: {e}")
    if not destinatarios:
        raise HTTPException(status_code=400, detail="Nenhum usuario ativo com e-mail ou nenhuma avaliacao encontrada.")
    return {"ok": True, "enviado_para": destinatarios}


@router.get("/usuarios", response_model=list[UsuarioAdminResponse])
def listar_usuarios(tenant_id: UUID | None = None) -> list[UsuarioAdminResponse]:
    query = get_supabase().table("tenant_usuarios").select("*")
    if tenant_id:
        query = query.eq("tenant_id", str(tenant_id))
    result = query.order("nome").execute()
    return [UsuarioAdminResponse(**r) for r in result.data]


@router.post("/usuarios", response_model=UsuarioAdminResponse, status_code=201)
def criar_usuario(payload: UsuarioAdminCreateRequest) -> UsuarioAdminResponse:
    sb = get_supabase()
    data = payload.model_dump()
    data["tenant_id"] = str(data["tenant_id"])
    data["email"] = data["email"].lower().strip()

    # Cria (ou convida) o usuário no Supabase Auth e obtém o user_id
    instalar_url = "https://qtqd-vt2a.vercel.app/instalar"
    for link_type in ("invite", "recovery"):
        try:
            link_resp = sb.auth.admin.generate_link({
                "type": link_type,
                "email": payload.email,
                "redirect_to": instalar_url,
            })
            auth_user = getattr(link_resp, "user", None)
            if auth_user and getattr(auth_user, "id", None):
                data["user_id"] = str(auth_user.id)
            break
        except Exception:
            continue  # usuário pode já existir no Auth; tenta próximo tipo

    result = sb.table("tenant_usuarios").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar usuario.")
    return UsuarioAdminResponse(**result.data[0])


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioAdminResponse)
def atualizar_usuario(usuario_id: UUID, payload: UsuarioAdminUpdateRequest) -> UsuarioAdminResponse:
    sb = get_supabase()
    check = sb.table("tenant_usuarios").select("id").eq("id", str(usuario_id)).limit(1).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    values = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not values:
        raise HTTPException(status_code=400, detail="Nenhum campo enviado.")
    values["updated_at"] = datetime.now(timezone.utc).isoformat()
    sb.table("tenant_usuarios").update(values).eq("id", str(usuario_id)).execute()
    final = sb.table("tenant_usuarios").select("*").eq("id", str(usuario_id)).limit(1).execute()
    return UsuarioAdminResponse(**final.data[0])


@router.post("/usuarios/{usuario_id}/enviar-convite", status_code=200)
def enviar_convite_usuario(usuario_id: UUID) -> dict:
    from backend.app.services.email_service import send_html

    sb = get_supabase()

    u_res = sb.table("tenant_usuarios").select("*").eq("id", str(usuario_id)).limit(1).execute()
    if not u_res.data:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")
    u = u_res.data[0]

    t_res = sb.table("tenants").select("nome").eq("id", str(u["tenant_id"])).limit(1).execute()
    tenant_nome = t_res.data[0]["nome"] if t_res.data else "Service Farma"
    b_res = sb.table("tenant_branding").select("nome_portal").eq("tenant_id", str(u["tenant_id"])).limit(1).execute()
    portal_nome = (b_res.data[0].get("nome_portal") or tenant_nome) if b_res.data else tenant_nome

    # Gera link de acesso via Supabase Auth
    # Tenta "invite" (para novos usuários); se falhar (usuário já confirmado), usa "recovery"
    instalar_url = "https://qtqd-vt2a.vercel.app/instalar"
    setup_link = None
    last_error = None

    for link_type in ("invite", "recovery"):
        try:
            link_resp = sb.auth.admin.generate_link({
                "type": link_type,
                "email": u["email"],
                "redirect_to": instalar_url,
            })
            props = getattr(link_resp, "properties", None)
            action = getattr(props, "action_link", None) if props else None
            if action:
                setup_link = action
                auth_user = getattr(link_resp, "user", None)
                if auth_user and getattr(auth_user, "id", None):
                    auth_uid = str(auth_user.id)
                    # Sincroniza user_id na tabela
                    sb.table("tenant_usuarios").update({"user_id": auth_uid}).eq("id", str(usuario_id)).execute()
                    # Grava referência no app_metadata do Auth — usado pelo definir-senha
                    try:
                        sb.auth.admin.update_user_by_id(auth_uid, {
                            "app_metadata": {
                                "qtqd_usuario_id": str(usuario_id),
                                "qtqd_tenant_id": str(u["tenant_id"]),
                            }
                        })
                    except Exception:
                        pass
                break
        except Exception as e:
            last_error = str(e)
            continue

    if not setup_link:
        raise HTTPException(
            status_code=500,
            detail=f"Nao foi possivel gerar o link de acesso para {u['email']}. Erro: {last_error}",
        )

    perm_label = {"edita": "Edição", "visualiza": "Somente leitura", "relatorio": "Somente relatórios"}.get(u.get("permissao", ""), "Acesso")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Convite QTQD</title></head>
<body style="margin:0;padding:20px;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:600px;margin:0 auto;">

  <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#2563eb 100%);border-radius:12px 12px 0 0;padding:28px 32px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#93c5fd;">QTQD — Saúde Financeira</p>
    <h1 style="margin:0 0 6px;font-size:22px;font-weight:700;color:#ffffff;">Você foi convidado!</h1>
    <p style="margin:0;font-size:14px;color:#bfdbfe;">{portal_nome}</p>
  </div>

  <div style="background:#ffffff;padding:28px 32px;border-radius:0 0 12px 12px;box-shadow:0 4px 6px rgba(0,0,0,0.07);">
    <p style="margin:0 0 16px;font-size:15px;color:#374151;">Olá, <strong>{u['nome']}</strong>!</p>

    <p style="margin:0 0 20px;font-size:14px;color:#374151;line-height:1.6;">
      Você foi cadastrado no sistema <strong>QTQD — Quanto Tenho, Quanto Devo</strong>
      da <strong>{tenant_nome}</strong> pela equipe <strong>Service Farma</strong>.
      Clique no botão abaixo para criar sua senha e instalar o aplicativo.
    </p>

    <div style="text-align:center;margin:0 0 28px;">
      <a href="{setup_link}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:16px 36px;border-radius:10px;font-size:16px;font-weight:700;letter-spacing:0.01em;">
        🔑 Criar minha senha e instalar o app →
      </a>
      <p style="margin:10px 0 0;font-size:12px;color:#94a3b8;">Este link expira em 24 horas.</p>
    </div>

    <div style="background:#f8fafc;border-radius:8px;padding:16px 20px;margin:0 0 24px;border:1px solid #e2e8f0;">
      <p style="margin:0 0 6px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#64748b;">Seus dados de acesso</p>
      <p style="margin:0 0 4px;font-size:14px;color:#374151;">📧 <strong>E-mail:</strong> {u['email']}</p>
      <p style="margin:0 0 4px;font-size:14px;color:#374151;">🔑 <strong>Permissão:</strong> {perm_label}</p>
      {f'<p style="margin:0;font-size:14px;color:#374151;">💼 <strong>Função:</strong> {u["funcao"]}</p>' if u.get("funcao") else ''}
    </div>

    <p style="margin:24px 0 0;font-size:13px;color:#94a3b8;border-top:1px solid #f1f5f9;padding-top:16px;">
      Em caso de dúvidas, entre em contato com a equipe Service Farma.<br>
      Não responda a este e-mail.
    </p>
  </div>

</div>
</body>
</html>"""

    try:
        send_html(to=[u["email"]], subject=f"Convite QTQD — {portal_nome}", html=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {e}")

    return {"ok": True, "enviado_para": u["email"]}


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


@router.post("/abrir-portal/{tenant_id}")
def abrir_portal(tenant_id: UUID) -> dict:
    """Gera um token de acesso para o portal do cliente do tenant informado."""
    import json, urllib.request as urlreq
    from backend.app.core.config import settings

    if not settings.portal_admin_password:
        raise HTTPException(status_code=503, detail="PORTAL_ADMIN_PASSWORD nao configurado.")

    url = f"{settings.supabase_url}/auth/v1/token?grant_type=password"
    body = json.dumps({"email": settings.portal_admin_email, "password": settings.portal_admin_password}).encode()
    req = urlreq.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "apikey": settings.supabase_service_role_key or "",
    }, method="POST")
    try:
        with urlreq.urlopen(req, timeout=15) as r:
            session = json.loads(r.read())
    except urlreq.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Falha ao autenticar: {e.read().decode()}")

    return {
        "access_token": session.get("access_token"),
        "tenant_id": str(tenant_id),
        "expires_in": session.get("expires_in", 3600),
    }

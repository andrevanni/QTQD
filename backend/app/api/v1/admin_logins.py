from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.core.admin_auth import require_admin_token
from backend.app.db.client import get_supabase
from backend.app.core.config import settings

router = APIRouter(prefix="/admin/admins", tags=["admin-logins"], dependencies=[Depends(require_admin_token)])

MASTER_EMAIL = settings.portal_admin_email


class AdminLoginResponse(BaseModel):
    id: UUID
    email: str
    nome: str | None = None
    ativo: bool
    is_master: bool
    created_at: datetime


class ConvidarAdminRequest(BaseModel):
    email: str
    nome: str | None = None


@router.get("", response_model=list[AdminLoginResponse])
def listar_admins() -> list[AdminLoginResponse]:
    result = get_supabase().table("admin_logins").select("*").order("created_at").execute()
    return [AdminLoginResponse(**r) for r in result.data]


@router.post("", response_model=AdminLoginResponse, status_code=201)
def convidar_admin(payload: ConvidarAdminRequest) -> AdminLoginResponse:
    from backend.app.services.email_service import send_html

    sb = get_supabase()
    email = payload.email.lower().strip()

    existing = sb.table("admin_logins").select("id").eq("email", email).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Já existe um admin com esse e-mail.")

    data = {
        "email": email,
        "nome": payload.nome or None,
        "ativo": True,
        "is_master": False,
    }
    result = sb.table("admin_logins").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Falha ao criar admin.")

    portal_url = "https://qtqd-vt2a.vercel.app/admin"
    token = settings.admin_token
    nome_display = payload.nome or email

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#1e293b">
      <div style="background:#0f1621;padding:28px 24px 20px;border-radius:8px 8px 0 0;text-align:center">
        <div style="color:#f1f5f9;font-size:18px;font-weight:700">QTQD — Painel Admin</div>
        <div style="color:#94a3b8;font-size:12px;margin-top:4px">Service Farma</div>
      </div>
      <div style="background:#f8fafc;padding:32px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0">
        <h2 style="margin:0 0 12px;font-size:20px">Bem-vindo, {nome_display}!</h2>
        <p style="color:#475569;margin:0 0 24px;line-height:1.6">
          Você foi convidado a acessar o painel administrativo do <strong>QTQD</strong>.<br>
          Use as credenciais abaixo para entrar:
        </p>
        <div style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:6px;padding:16px;margin-bottom:24px;font-family:monospace;font-size:13px">
          <div style="margin-bottom:8px"><strong>URL:</strong> <a href="{portal_url}" style="color:#2563eb">{portal_url}</a></div>
          <div><strong>Token de acesso:</strong> {token}</div>
        </div>
        <div style="text-align:center;margin-bottom:24px">
          <a href="{portal_url}"
             style="display:inline-block;background:#2563eb;color:#fff;padding:14px 36px;
                    border-radius:6px;text-decoration:none;font-weight:bold;font-size:15px">
            Acessar o Painel Admin
          </a>
        </div>
        <p style="color:#94a3b8;font-size:12px;margin:0;text-align:center">
          Powered by Grupo A3 · Service Farma
        </p>
      </div>
    </div>
    """

    try:
        send_html([email], "Convite — Painel Admin QTQD", html)
    except Exception:
        pass

    return AdminLoginResponse(**result.data[0])


@router.patch("/{admin_id}/revogar", response_model=AdminLoginResponse)
def revogar_admin(admin_id: UUID) -> AdminLoginResponse:
    sb = get_supabase()
    check = sb.table("admin_logins").select("*").eq("id", str(admin_id)).limit(1).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Admin não encontrado.")
    if check.data[0].get("is_master"):
        raise HTTPException(status_code=400, detail="Não é possível revogar o admin master.")
    result = sb.table("admin_logins").update({"ativo": False}).eq("id", str(admin_id)).execute()
    return AdminLoginResponse(**result.data[0])


@router.patch("/{admin_id}/reativar", response_model=AdminLoginResponse)
def reativar_admin(admin_id: UUID) -> AdminLoginResponse:
    sb = get_supabase()
    check = sb.table("admin_logins").select("*").eq("id", str(admin_id)).limit(1).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Admin não encontrado.")
    result = sb.table("admin_logins").update({"ativo": True}).eq("id", str(admin_id)).execute()
    return AdminLoginResponse(**result.data[0])


@router.delete("/{admin_id}", status_code=204)
def excluir_admin(admin_id: UUID) -> None:
    sb = get_supabase()
    check = sb.table("admin_logins").select("*").eq("id", str(admin_id)).limit(1).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Admin não encontrado.")
    if check.data[0].get("is_master"):
        raise HTTPException(status_code=400, detail="Não é possível excluir o admin master.")
    sb.table("admin_logins").delete().eq("id", str(admin_id)).execute()

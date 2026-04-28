from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.db.client import get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])

PORTAL_URL = "https://qtqd-vt2a.vercel.app/cliente"


class LoginRequest(BaseModel):
    email: str
    password: str


class DefinirSenhaRequest(BaseModel):
    access_token: str
    nova_senha: str


def _tenant_para_usuario(sb, email: str, user_id: str | None = None) -> dict:
    """Busca o tenant_usuario por user_id (UUID) ou email. Retorna o registro ou lança 403."""

    # 1. Por user_id do Supabase Auth (mais confiável)
    if user_id:
        res = (
            sb.table("tenant_usuarios")
            .select("tenant_id,permissao,nome,ativo")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if res.data:
            row = res.data[0]
            if not row.get("ativo"):
                raise HTTPException(status_code=403, detail="Usuário inativo. Reative o acesso no painel admin.")
            return row

    # 2. Por e-mail em lowercase (fallback)
    email_lower = email.lower().strip()
    res = (
        sb.table("tenant_usuarios")
        .select("tenant_id,permissao,nome,ativo")
        .eq("email", email_lower)
        .limit(1)
        .execute()
    )
    if res.data:
        row = res.data[0]
        if not row.get("ativo"):
            raise HTTPException(status_code=403, detail=f"Usuário '{email_lower}' está inativo. Reative no painel admin.")
        return row

    raise HTTPException(
        status_code=403,
        detail=f"Usuário '{email_lower}' não encontrado. Cadastre-o no painel admin antes de enviar o convite.",
    )


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    sb = get_supabase()
    try:
        resp = sb.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    if not resp.session:
        raise HTTPException(status_code=401, detail="Falha na autenticação.")

    tu = _tenant_para_usuario(sb, resp.user.email, str(resp.user.id))
    return {
        "access_token": resp.session.access_token,
        "tenant_id": str(tu["tenant_id"]),
        "nome": tu.get("nome"),
        "permissao": tu.get("permissao"),
    }


@router.post("/definir-senha")
def definir_senha(payload: DefinirSenhaRequest) -> dict:
    sb = get_supabase()

    try:
        user_resp = sb.auth.get_user(payload.access_token)
        user = user_resp.user
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Link expirado ou inválido. Solicite um novo convite ao administrador.",
        )

    if len(payload.nova_senha) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter ao menos 6 caracteres.")

    try:
        sb.auth.admin.update_user_by_id(str(user.id), {"password": payload.nova_senha})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao definir senha: {e}")

    try:
        sign_resp = sb.auth.sign_in_with_password(
            {"email": user.email, "password": payload.nova_senha}
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Senha definida com sucesso. Acesse o portal com seu e-mail e senha.",
        )

    # Tenta lookup pelo app_metadata gravado no envio do convite (mais confiável)
    app_meta = getattr(user, "app_metadata", None) or {}
    qtqd_usuario_id = app_meta.get("qtqd_usuario_id")
    if qtqd_usuario_id:
        res = sb.table("tenant_usuarios").select("tenant_id,permissao,nome,ativo").eq("id", qtqd_usuario_id).limit(1).execute()
        if res.data and res.data[0].get("ativo"):
            tu = res.data[0]
        else:
            tu = _tenant_para_usuario(sb, user.email, str(user.id))
    else:
        tu = _tenant_para_usuario(sb, user.email, str(user.id))
    return {
        "access_token": sign_resp.session.access_token,
        "tenant_id": str(tu["tenant_id"]),
        "nome": tu.get("nome"),
        "permissao": tu.get("permissao"),
    }

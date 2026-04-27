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


def _tenant_para_usuario(sb, email: str) -> dict:
    res = (
        sb.table("tenant_usuarios")
        .select("tenant_id,permissao,nome")
        .eq("email", email)
        .eq("ativo", True)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(
            status_code=403,
            detail="Usuário sem acesso configurado. Contate o administrador.",
        )
    return res.data[0]


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

    tu = _tenant_para_usuario(sb, resp.user.email)
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

    tu = _tenant_para_usuario(sb, user.email)
    return {
        "access_token": sign_resp.session.access_token,
        "tenant_id": str(tu["tenant_id"]),
        "nome": tu.get("nome"),
        "permissao": tu.get("permissao"),
    }

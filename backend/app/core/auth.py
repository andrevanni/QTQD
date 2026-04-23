"""
Autenticação via JWT do Supabase.

Fluxo:
  1. Frontend autentica o usuário no Supabase Auth e obtém um JWT.
  2. Frontend envia o JWT no header: Authorization: Bearer <token>
  3. Este módulo valida o JWT com SUPABASE_JWT_SECRET e extrai o user_id (sub).
  4. O user_id é usado para resolver o tenant_id na tabela tenant_users.
"""
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db_session


def _verify_jwt(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization ausente ou mal formatado. Use: Bearer <token>",
        )
    token = authorization[7:]
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SUPABASE_JWT_SECRET nao configurado no servidor.",
        )
    try:
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.")


def get_current_tenant(
    payload: dict = Depends(_verify_jwt),
    db: Session = Depends(get_db_session),
) -> UUID:
    """Retorna o tenant_id do usuário autenticado."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificacao de usuario (sub).",
        )
    row = db.execute(
        text(
            """
            SELECT tenant_id
              FROM tenant_users
             WHERE user_id = :uid
               AND ativo = true
             LIMIT 1
            """
        ),
        {"uid": user_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem acesso a nenhum tenant ativo.",
        )
    return UUID(str(row["tenant_id"]))

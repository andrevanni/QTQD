"""
Autenticação via JWT do Supabase — suporte a ECC (P-256 / ES256).

Usa o endpoint JWKS do Supabase para buscar a chave pública e validar
tokens de forma automática, sem necessidade de configurar um segredo manualmente.

Endpoint JWKS: {SUPABASE_URL}/auth/v1/.well-known/jwks.json
"""
from uuid import UUID

import jwt
from jwt import PyJWKClient
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db_session

# Cliente JWKS — inicializado uma vez, faz cache das chaves automaticamente
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.supabase_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SUPABASE_URL nao configurado no servidor.",
            )
        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
    return _jwks_client


def _verify_jwt(authorization: str | None = Header(default=None)) -> dict:
    """Valida o JWT do Supabase Auth (ES256 ou HS256 legado)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header Authorization ausente. Use: Bearer <token>",
        )
    token = authorization[7:]
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Falha na validacao do token: {e}",
        )


def get_current_tenant(
    payload: dict = Depends(_verify_jwt),
    db: Session = Depends(get_db_session),
) -> UUID:
    """Resolve o tenant_id do usuário autenticado via JWT."""
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

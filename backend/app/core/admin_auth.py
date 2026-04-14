from fastapi import Header, HTTPException, status

from backend.app.core.config import settings


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> str:
    if x_admin_token != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token administrativo invalido.",
        )
    return x_admin_token

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClienteAdminBase(BaseModel):
    nome: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=160)
    status: str = Field(default="implantacao")
    plano: str = Field(default="basico")
    contato_nome: str | None = None
    contato_email: EmailStr | None = None
    observacoes: str | None = None


class ClienteAdminCreateRequest(ClienteAdminBase):
    pass


class ClienteAdminUpdateRequest(BaseModel):
    nome: str | None = None
    slug: str | None = None
    status: str | None = None
    plano: str | None = None
    contato_nome: str | None = None
    contato_email: EmailStr | None = None
    observacoes: str | None = None


class ClienteAdminResumo(ClienteAdminBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

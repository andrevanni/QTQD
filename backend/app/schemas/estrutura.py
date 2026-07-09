from uuid import UUID

from pydantic import BaseModel


class GrupoCreate(BaseModel):
    nome: str
    nivel_preenchimento: str = "loja"  # 'loja' | 'grupo'
    ordem: int = 0


class GrupoUpdate(BaseModel):
    nome: str | None = None
    nivel_preenchimento: str | None = None
    ordem: int | None = None
    ativo: bool | None = None


class GrupoResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nome: str
    nivel_preenchimento: str
    ordem: int
    ativo: bool


class LojaCreate(BaseModel):
    grupo_id: UUID
    nome: str
    cnpj: str | None = None
    filial_excel: int | None = None
    ordem: int = 0


class LojaUpdate(BaseModel):
    grupo_id: UUID | None = None
    nome: str | None = None
    cnpj: str | None = None
    filial_excel: int | None = None
    ordem: int | None = None
    ativo: bool | None = None


class LojaResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    grupo_id: UUID
    nome: str
    cnpj: str | None = None
    filial_excel: int | None = None
    ordem: int
    ativo: bool


class GrupoComLojas(GrupoResponse):
    lojas: list[LojaResponse] = []


class LojasArvoreResponse(BaseModel):
    modo_rede: bool
    grupos: list[GrupoComLojas]

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LicencaAdminBase(BaseModel):
    tenant_id: UUID
    plano: str = Field(default="basico")
    status: str = Field(default="ativo")
    inicio_vigencia: date
    fim_vigencia: date | None = None
    limite_usuarios: int | None = None
    limite_avaliacoes_mes: int | None = None
    observacoes: str | None = None


class LicencaAdminCreateRequest(LicencaAdminBase):
    pass


class LicencaAdminUpdateRequest(BaseModel):
    plano: str | None = None
    status: str | None = None
    inicio_vigencia: date | None = None
    fim_vigencia: date | None = None
    limite_usuarios: int | None = None
    limite_avaliacoes_mes: int | None = None
    observacoes: str | None = None


class LicencaAdminResponse(LicencaAdminBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BrandingAdminUpsertRequest(BaseModel):
    nome_portal: str | None = None
    logo_cliente_url: str | None = None
    tema: str = Field(default="dark")
    cor_primaria: str | None = None
    cor_secundaria: str | None = None
    powered_by_label: str = Field(default="Powered by Service Farma")


class BrandingAdminResponse(BrandingAdminUpsertRequest):
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class ComponenteConfigItem(BaseModel):
    codigo_componente: str
    label_customizado: str | None = None
    visivel: bool = True
    obrigatorio: bool = False
    ordem_exibicao: int | None = None


class ComponentesConfigUpsertRequest(BaseModel):
    itens: list[ComponenteConfigItem]


class ComponenteConfigResponse(ComponenteConfigItem):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


class PdfConfigRequest(BaseModel):
    n_retratos:       int  = 8
    incluir_inspetor: bool = False
    incluir_graficos: bool = False
    ativo:            bool = True


class PdfConfigResponse(PdfConfigRequest):
    id:         UUID
    tenant_id:  UUID
    created_at: datetime
    updated_at: datetime


class UsuarioAdminCreateRequest(BaseModel):
    tenant_id: UUID
    nome: str
    funcao: str | None = None
    email: str
    permissao: str = "visualiza"  # edita | visualiza | relatorio
    ativo: bool = True


class UsuarioAdminUpdateRequest(BaseModel):
    nome: str | None = None
    funcao: str | None = None
    permissao: str | None = None
    ativo: bool | None = None


class UsuarioAdminResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nome: str
    funcao: str | None = None
    email: str
    permissao: str
    ativo: bool
    user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ImportacaoAdminCreateRequest(BaseModel):
    tenant_id: UUID
    tipo: str = Field(default="primeira_carga")
    origem_arquivo_nome: str
    origem_arquivo_url: str | None = None
    status: str = Field(default="recebido")
    observacoes: str | None = None
    registros_processados: int = 0
    registros_com_erro: int = 0
    payload_resumo: dict = Field(default_factory=dict)


class ImportacaoAdminResponse(ImportacaoAdminCreateRequest):
    id: UUID
    created_at: datetime
    updated_at: datetime
    finished_at: datetime | None = None

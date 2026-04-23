from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

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
)

router = APIRouter(prefix="/admin", tags=["admin-config"], dependencies=[Depends(require_admin_token)])


@router.get("/licencas", response_model=list[LicencaAdminResponse])
def listar_licencas(tenant_id: UUID | None = None) -> list[LicencaAdminResponse]:
    query = get_supabase().table("tenant_licencas").select("*")
    if tenant_id:
        query = query.eq("tenant_id", str(tenant_id))
    result = query.order("inicio_vigencia", desc=True).execute()
    return [LicencaAdminResponse(**row) for row in result.data]


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
    rows = []
    for item in payload.itens:
        data = {
            "tenant_id": str(tenant_id),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **item.model_dump(),
        }
        result = sb.table("tenant_componentes_config").upsert(data, on_conflict="tenant_id,codigo_componente").execute()
        if result.data:
            rows.append(ComponenteConfigResponse(**result.data[0]))
    return rows


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

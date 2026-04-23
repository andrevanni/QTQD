from uuid import UUID

from fastapi import APIRouter, Depends

from backend.app.core.auth import get_current_tenant
from backend.app.db.client import get_supabase
from backend.app.schemas.admin_config import BrandingAdminResponse, ComponenteConfigResponse

router = APIRouter(prefix="/me", tags=["cliente-config"])


@router.get("/branding", response_model=BrandingAdminResponse | None)
def obter_branding(tenant_id: UUID = Depends(get_current_tenant)) -> BrandingAdminResponse | None:
    result = get_supabase().table("tenant_branding").select("*").eq("tenant_id", str(tenant_id)).limit(1).execute()
    return BrandingAdminResponse(**result.data[0]) if result.data else None


@router.get("/componentes-config", response_model=list[ComponenteConfigResponse])
def obter_componentes_config(tenant_id: UUID = Depends(get_current_tenant)) -> list[ComponenteConfigResponse]:
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

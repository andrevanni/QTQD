from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends

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


@router.get("/charts-config")
def get_charts_config(tenant_id: UUID = Depends(get_current_tenant)) -> dict:
    row = get_supabase().table("tenants").select("charts_config").eq("id", str(tenant_id)).limit(1).execute()
    cfg = row.data[0].get("charts_config") if row.data else []
    return {"charts_config": cfg or []}


@router.put("/charts-config")
def put_charts_config(
    charts_config: list = Body(default=[], embed=True),
    tenant_id: UUID = Depends(get_current_tenant),
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    get_supabase().table("tenants").update({"charts_config": charts_config, "updated_at": now}).eq("id", str(tenant_id)).execute()
    return {"ok": True}

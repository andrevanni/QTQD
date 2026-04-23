"""
Endpoints para o frontend do cliente obter sua própria configuração.
Todos exigem JWT válido do Supabase Auth.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_tenant
from backend.app.db.session import get_db_session
from backend.app.schemas.admin_config import BrandingAdminResponse, ComponenteConfigResponse

router = APIRouter(prefix="/me", tags=["cliente-config"])


@router.get("/branding", response_model=BrandingAdminResponse | None)
def obter_branding(
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> BrandingAdminResponse | None:
    """Retorna o branding configurado para o tenant do usuário autenticado."""
    row = db.execute(
        text(
            """
            SELECT tenant_id, nome_portal, logo_cliente_url, tema, cor_primaria,
                   cor_secundaria, powered_by_label, created_at, updated_at
              FROM tenant_branding
             WHERE tenant_id = :tid
            """
        ),
        {"tid": tenant_id},
    ).mappings().first()
    return BrandingAdminResponse(**row) if row else None


@router.get("/componentes-config", response_model=list[ComponenteConfigResponse])
def obter_componentes_config(
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> list[ComponenteConfigResponse]:
    """Retorna a configuração de campos do tenant do usuário autenticado."""
    rows = db.execute(
        text(
            """
            SELECT id, tenant_id, codigo_componente, label_customizado,
                   visivel, obrigatorio, ordem_exibicao, created_at, updated_at
              FROM tenant_componentes_config
             WHERE tenant_id = :tid
             ORDER BY coalesce(ordem_exibicao, 999999), codigo_componente
            """
        ),
        {"tid": tenant_id},
    ).mappings().all()
    return [ComponenteConfigResponse(**row) for row in rows]

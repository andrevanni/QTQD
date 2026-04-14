import json
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.admin_auth import require_admin_token
from backend.app.db.session import get_db_session
from backend.app.schemas.admin_config import (
    BrandingAdminResponse,
    BrandingAdminUpsertRequest,
    ComponentesConfigUpsertRequest,
    ComponenteConfigResponse,
    ImportacaoAdminCreateRequest,
    ImportacaoAdminResponse,
    LicencaAdminCreateRequest,
    LicencaAdminResponse,
)

router = APIRouter(prefix="/admin", tags=["admin-config"], dependencies=[Depends(require_admin_token)])


@router.get("/licencas", response_model=list[LicencaAdminResponse])
def listar_licencas(tenant_id: UUID | None = None, db: Session = Depends(get_db_session)) -> list[LicencaAdminResponse]:
    sql = """
        select id, tenant_id, plano, status, inicio_vigencia, fim_vigencia, limite_usuarios,
               limite_avaliacoes_mes, observacoes, created_at, updated_at
        from tenant_licencas
    """
    params: dict[str, UUID] = {}
    if tenant_id:
        sql += " where tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id
    sql += " order by inicio_vigencia desc, created_at desc"
    rows = db.execute(text(sql), params).mappings().all()
    return [LicencaAdminResponse(**row) for row in rows]


@router.post("/licencas", response_model=LicencaAdminResponse)
def criar_licenca(payload: LicencaAdminCreateRequest, db: Session = Depends(get_db_session)) -> LicencaAdminResponse:
    row = db.execute(
        text(
            """
            insert into tenant_licencas (
              tenant_id, plano, status, inicio_vigencia, fim_vigencia,
              limite_usuarios, limite_avaliacoes_mes, observacoes
            )
            values (
              :tenant_id, :plano, :status, :inicio_vigencia, :fim_vigencia,
              :limite_usuarios, :limite_avaliacoes_mes, :observacoes
            )
            returning id, tenant_id, plano, status, inicio_vigencia, fim_vigencia,
                      limite_usuarios, limite_avaliacoes_mes, observacoes, created_at, updated_at
            """
        ),
        payload.model_dump(),
    ).mappings().one()
    db.commit()
    return LicencaAdminResponse(**row)


@router.get("/branding/{tenant_id}", response_model=BrandingAdminResponse | None)
def obter_branding(tenant_id: UUID, db: Session = Depends(get_db_session)) -> BrandingAdminResponse | None:
    row = db.execute(
        text(
            """
            select tenant_id, nome_portal, logo_cliente_url, tema, cor_primaria, cor_secundaria,
                   powered_by_label, created_at, updated_at
            from tenant_branding
            where tenant_id = :tenant_id
            """
        ),
        {"tenant_id": tenant_id},
    ).mappings().first()
    return BrandingAdminResponse(**row) if row else None


@router.put("/branding/{tenant_id}", response_model=BrandingAdminResponse)
def salvar_branding(
    tenant_id: UUID,
    payload: BrandingAdminUpsertRequest,
    db: Session = Depends(get_db_session),
) -> BrandingAdminResponse:
    row = db.execute(
        text(
            """
            insert into tenant_branding (
              tenant_id, nome_portal, logo_cliente_url, tema, cor_primaria, cor_secundaria, powered_by_label
            )
            values (
              :tenant_id, :nome_portal, :logo_cliente_url, :tema, :cor_primaria, :cor_secundaria, :powered_by_label
            )
            on conflict (tenant_id) do update
               set nome_portal = excluded.nome_portal,
                   logo_cliente_url = excluded.logo_cliente_url,
                   tema = excluded.tema,
                   cor_primaria = excluded.cor_primaria,
                   cor_secundaria = excluded.cor_secundaria,
                   powered_by_label = excluded.powered_by_label,
                   updated_at = now()
            returning tenant_id, nome_portal, logo_cliente_url, tema, cor_primaria, cor_secundaria,
                      powered_by_label, created_at, updated_at
            """
        ),
        {"tenant_id": tenant_id, **payload.model_dump()},
    ).mappings().one()
    db.commit()
    return BrandingAdminResponse(**row)


@router.get("/componentes-config/{tenant_id}", response_model=list[ComponenteConfigResponse])
def listar_componentes_config(tenant_id: UUID, db: Session = Depends(get_db_session)) -> list[ComponenteConfigResponse]:
    rows = db.execute(
        text(
            """
            select id, tenant_id, codigo_componente, label_customizado, visivel, obrigatorio, ordem_exibicao,
                   created_at, updated_at
            from tenant_componentes_config
            where tenant_id = :tenant_id
            order by coalesce(ordem_exibicao, 999999), codigo_componente
            """
        ),
        {"tenant_id": tenant_id},
    ).mappings().all()
    return [ComponenteConfigResponse(**row) for row in rows]


@router.put("/componentes-config/{tenant_id}", response_model=list[ComponenteConfigResponse])
def salvar_componentes_config(
    tenant_id: UUID,
    payload: ComponentesConfigUpsertRequest,
    db: Session = Depends(get_db_session),
) -> list[ComponenteConfigResponse]:
    saved_rows = []
    for item in payload.itens:
        row = db.execute(
            text(
                """
                insert into tenant_componentes_config (
                  tenant_id, codigo_componente, label_customizado, visivel, obrigatorio, ordem_exibicao
                )
                values (
                  :tenant_id, :codigo_componente, :label_customizado, :visivel, :obrigatorio, :ordem_exibicao
                )
                on conflict (tenant_id, codigo_componente) do update
                   set label_customizado = excluded.label_customizado,
                       visivel = excluded.visivel,
                       obrigatorio = excluded.obrigatorio,
                       ordem_exibicao = excluded.ordem_exibicao,
                       updated_at = now()
                returning id, tenant_id, codigo_componente, label_customizado, visivel, obrigatorio,
                          ordem_exibicao, created_at, updated_at
                """
            ),
            {"tenant_id": tenant_id, **item.model_dump()},
        ).mappings().one()
        saved_rows.append(ComponenteConfigResponse(**row))
    db.commit()
    return saved_rows


@router.get("/importacoes", response_model=list[ImportacaoAdminResponse])
def listar_importacoes(
    tenant_id: UUID | None = None,
    db: Session = Depends(get_db_session),
) -> list[ImportacaoAdminResponse]:
    sql = """
        select id, tenant_id, tipo, origem_arquivo_nome, origem_arquivo_url, status, observacoes,
               registros_processados, registros_com_erro, payload_resumo, created_at, updated_at, finished_at
        from tenant_importacoes
    """
    params: dict[str, UUID] = {}
    if tenant_id:
        sql += " where tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id
    sql += " order by created_at desc"
    rows = db.execute(text(sql), params).mappings().all()
    return [ImportacaoAdminResponse(**row) for row in rows]


@router.post("/importacoes", response_model=ImportacaoAdminResponse)
def criar_importacao(
    payload: ImportacaoAdminCreateRequest,
    db: Session = Depends(get_db_session),
) -> ImportacaoAdminResponse:
    row = db.execute(
        text(
            """
            insert into tenant_importacoes (
              tenant_id, tipo, origem_arquivo_nome, origem_arquivo_url, status, observacoes,
              registros_processados, registros_com_erro, payload_resumo
            )
            values (
              :tenant_id, :tipo, :origem_arquivo_nome, :origem_arquivo_url, :status, :observacoes,
              :registros_processados, :registros_com_erro, cast(:payload_resumo as jsonb)
            )
            returning id, tenant_id, tipo, origem_arquivo_nome, origem_arquivo_url, status, observacoes,
                      registros_processados, registros_com_erro, payload_resumo, created_at, updated_at, finished_at
            """
        ),
        {
            **payload.model_dump(exclude={"payload_resumo"}),
            "payload_resumo": json.dumps(payload.payload_resumo),
        },
    ).mappings().one()
    db.commit()
    return ImportacaoAdminResponse(**row)

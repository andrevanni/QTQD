from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.admin_auth import require_admin_token
from backend.app.db.session import get_db_session
from backend.app.schemas.admin_clientes import (
    ClienteAdminCreateRequest,
    ClienteAdminResumo,
    ClienteAdminUpdateRequest,
)

router = APIRouter(prefix="/admin/clientes", tags=["admin-clientes"], dependencies=[Depends(require_admin_token)])


@router.get("", response_model=list[ClienteAdminResumo])
def listar_clientes(db: Session = Depends(get_db_session)) -> list[ClienteAdminResumo]:
    rows = db.execute(
        text(
            """
            select id, nome, slug, status, plano, contato_nome, contato_email, observacoes, created_at, updated_at
            from tenants
            order by created_at desc
            """
        )
    ).mappings().all()
    return [ClienteAdminResumo(**row) for row in rows]


@router.post("", response_model=ClienteAdminResumo)
def criar_cliente(payload: ClienteAdminCreateRequest, db: Session = Depends(get_db_session)) -> ClienteAdminResumo:
    row = db.execute(
        text(
            """
            insert into tenants (nome, slug, status, plano, contato_nome, contato_email, observacoes)
            values (:nome, :slug, :status, :plano, :contato_nome, :contato_email, :observacoes)
            returning id, nome, slug, status, plano, contato_nome, contato_email, observacoes, created_at, updated_at
            """
        ),
        payload.model_dump(),
    ).mappings().one()
    db.commit()
    return ClienteAdminResumo(**row)


@router.patch("/{tenant_id}", response_model=ClienteAdminResumo)
def atualizar_cliente(
    tenant_id: UUID,
    payload: ClienteAdminUpdateRequest,
    db: Session = Depends(get_db_session),
) -> ClienteAdminResumo:
    values = {key: value for key, value in payload.model_dump().items() if value is not None}
    if not values:
        raise HTTPException(status_code=400, detail="Nenhum campo enviado para atualizacao.")
    values["tenant_id"] = tenant_id
    set_clause = ", ".join(f"{column} = :{column}" for column in values if column != "tenant_id")
    row = db.execute(
        text(
            f"""
            update tenants
               set {set_clause},
                   updated_at = now()
             where id = :tenant_id
         returning id, nome, slug, status, plano, contato_nome, contato_email, observacoes, created_at, updated_at
            """
        ),
        values,
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado.")
    db.commit()
    return ClienteAdminResumo(**row)

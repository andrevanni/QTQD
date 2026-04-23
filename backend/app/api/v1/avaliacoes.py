from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_tenant
from backend.app.db.session import get_db_session
from backend.app.schemas.avaliacoes import (
    AvaliacaoCreateRequest,
    AvaliacaoResponse,
    AvaliacaoUpdateRequest,
    AvaliacaoValores,
)
from backend.app.services.calculos_qtqd import calcular_indicadores

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])


def _serialize(row: dict) -> AvaliacaoResponse:
    valores = AvaliacaoValores(**(row["valores"] or {}))
    return AvaliacaoResponse(
        id=row["id"],
        tenant_id=row["tenant_id"],
        semana_referencia=row["semana_referencia"],
        status=row["status"],
        observacoes=row["observacoes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        valores=valores,
        indicadores=calcular_indicadores(valores),
    )


_SELECT = """
    SELECT id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
      FROM avaliacoes_semanais
"""


@router.get("", response_model=list[AvaliacaoResponse])
def listar(
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> list[AvaliacaoResponse]:
    rows = db.execute(
        text(_SELECT + " WHERE tenant_id = :tid ORDER BY semana_referencia DESC"),
        {"tid": tenant_id},
    ).mappings().all()
    return [_serialize(row) for row in rows]


@router.get("/{avaliacao_id}", response_model=AvaliacaoResponse)
def obter(
    avaliacao_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> AvaliacaoResponse:
    row = db.execute(
        text(_SELECT + " WHERE id = :id AND tenant_id = :tid"),
        {"id": avaliacao_id, "tid": tenant_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    return _serialize(row)


@router.post("", response_model=AvaliacaoResponse, status_code=201)
def criar(
    payload: AvaliacaoCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> AvaliacaoResponse:
    # Garante que o tenant_id do payload bate com o do JWT
    if payload.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="tenant_id do payload nao confere com o token.")
    valores = AvaliacaoValores(**payload.model_dump(exclude={"tenant_id", "semana_referencia", "status", "observacoes"}))
    row = db.execute(
        text(
            """
            INSERT INTO avaliacoes_semanais (tenant_id, semana_referencia, status, observacoes, valores)
            VALUES (:tid, :semana, :status, :obs, cast(:valores AS jsonb))
            RETURNING id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            """
        ),
        {
            "tid": tenant_id,
            "semana": payload.semana_referencia,
            "status": payload.status,
            "obs": payload.observacoes,
            "valores": valores.model_dump_json(),
        },
    ).mappings().one()
    db.commit()
    return _serialize(row)


@router.patch("/{avaliacao_id}", response_model=AvaliacaoResponse)
def atualizar(
    avaliacao_id: UUID,
    payload: AvaliacaoUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> AvaliacaoResponse:
    current = db.execute(
        text(_SELECT + " WHERE id = :id AND tenant_id = :tid"),
        {"id": avaliacao_id, "tid": tenant_id},
    ).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")

    next_status = payload.status or current["status"]
    next_obs = payload.observacoes if payload.observacoes is not None else current["observacoes"]
    next_valores = AvaliacaoValores(**(payload.valores.model_dump() if payload.valores else current["valores"] or {}))

    row = db.execute(
        text(
            """
            UPDATE avaliacoes_semanais
               SET status      = :status,
                   observacoes = :obs,
                   valores     = cast(:valores AS jsonb),
                   updated_at  = now()
             WHERE id = :id AND tenant_id = :tid
            RETURNING id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            """
        ),
        {
            "id": avaliacao_id,
            "tid": tenant_id,
            "status": next_status,
            "obs": next_obs,
            "valores": next_valores.model_dump_json(),
        },
    ).mappings().one()
    db.commit()
    return _serialize(row)


@router.post("/{avaliacao_id}/fechar", response_model=AvaliacaoResponse)
def fechar(
    avaliacao_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> AvaliacaoResponse:
    row = db.execute(
        text(
            """
            UPDATE avaliacoes_semanais
               SET status       = 'fechada',
                   updated_at   = now(),
                   published_at = now()
             WHERE id = :id AND tenant_id = :tid
            RETURNING id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            """
        ),
        {"id": avaliacao_id, "tid": tenant_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    db.commit()
    return _serialize(row)


@router.delete("/{avaliacao_id}", status_code=204)
def excluir(
    avaliacao_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db_session),
) -> None:
    result = db.execute(
        text("DELETE FROM avaliacoes_semanais WHERE id = :id AND tenant_id = :tid"),
        {"id": avaliacao_id, "tid": tenant_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    db.commit()

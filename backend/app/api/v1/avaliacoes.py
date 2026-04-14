from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db.session import get_db_session
from backend.app.schemas.avaliacoes import (
    AvaliacaoCreateRequest,
    AvaliacaoResponse,
    AvaliacaoUpdateRequest,
    AvaliacaoValores,
)
from backend.app.services.calculos_qtqd import calcular_indicadores

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])


def _serializar_avaliacao(row: dict) -> AvaliacaoResponse:
    valores = AvaliacaoValores(**(row["valores"] or {}))
    indicadores = calcular_indicadores(valores)
    return AvaliacaoResponse(
        id=row["id"],
        tenant_id=row["tenant_id"],
        semana_referencia=row["semana_referencia"],
        status=row["status"],
        observacoes=row["observacoes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        valores=valores,
        indicadores=indicadores,
    )


@router.get("", response_model=list[AvaliacaoResponse])
def listar_avaliacoes(tenant_id: UUID, db: Session = Depends(get_db_session)) -> list[AvaliacaoResponse]:
    rows = db.execute(
        text(
            """
            select id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            from avaliacoes_semanais
            where tenant_id = :tenant_id
            order by semana_referencia desc
            """
        ),
        {"tenant_id": tenant_id},
    ).mappings().all()
    return [_serializar_avaliacao(row) for row in rows]


@router.get("/{avaliacao_id}", response_model=AvaliacaoResponse)
def obter_avaliacao(avaliacao_id: UUID, db: Session = Depends(get_db_session)) -> AvaliacaoResponse:
    row = db.execute(
        text(
            """
            select id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            from avaliacoes_semanais
            where id = :avaliacao_id
            """
        ),
        {"avaliacao_id": avaliacao_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    return _serializar_avaliacao(row)


@router.post("", response_model=AvaliacaoResponse)
def criar_avaliacao(payload: AvaliacaoCreateRequest, db: Session = Depends(get_db_session)) -> AvaliacaoResponse:
    valores = AvaliacaoValores(**payload.model_dump())
    row = db.execute(
        text(
            """
            insert into avaliacoes_semanais (tenant_id, semana_referencia, status, observacoes, valores)
            values (:tenant_id, :semana_referencia, :status, :observacoes, cast(:valores as jsonb))
            returning id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            """
        ),
        {
            "tenant_id": payload.tenant_id,
            "semana_referencia": payload.semana_referencia,
            "status": payload.status,
            "observacoes": payload.observacoes,
            "valores": valores.model_dump_json(),
        },
    ).mappings().one()
    db.commit()
    return _serializar_avaliacao(row)


@router.patch("/{avaliacao_id}", response_model=AvaliacaoResponse)
def atualizar_avaliacao(
    avaliacao_id: UUID,
    payload: AvaliacaoUpdateRequest,
    db: Session = Depends(get_db_session),
) -> AvaliacaoResponse:
    current = db.execute(
        text(
            """
            select id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            from avaliacoes_semanais
            where id = :avaliacao_id
            """
        ),
        {"avaliacao_id": avaliacao_id},
    ).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")

    next_status = payload.status or current["status"]
    next_observacoes = payload.observacoes if payload.observacoes is not None else current["observacoes"]
    next_valores = payload.valores.model_dump() if payload.valores else current["valores"]

    row = db.execute(
        text(
            """
            update avaliacoes_semanais
               set status = :status,
                   observacoes = :observacoes,
                   valores = cast(:valores as jsonb),
                   updated_at = now()
             where id = :avaliacao_id
         returning id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            """
        ),
        {
            "avaliacao_id": avaliacao_id,
            "status": next_status,
            "observacoes": next_observacoes,
            "valores": AvaliacaoValores(**next_valores).model_dump_json(),
        },
    ).mappings().one()
    db.commit()
    return _serializar_avaliacao(row)


@router.post("/{avaliacao_id}/fechar", response_model=AvaliacaoResponse)
def fechar_avaliacao(avaliacao_id: UUID, db: Session = Depends(get_db_session)) -> AvaliacaoResponse:
    row = db.execute(
        text(
            """
            update avaliacoes_semanais
               set status = 'fechada',
                   updated_at = now(),
                   published_at = now()
             where id = :avaliacao_id
         returning id, tenant_id, semana_referencia, status, observacoes, valores, created_at, updated_at
            """
        ),
        {"avaliacao_id": avaliacao_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    db.commit()
    return _serializar_avaliacao(row)


@router.delete("/{avaliacao_id}", status_code=204)
def excluir_avaliacao(avaliacao_id: UUID, db: Session = Depends(get_db_session)) -> None:
    result = db.execute(
        text(
            """
            delete from avaliacoes_semanais
            where id = :avaliacao_id
            """
        ),
        {"avaliacao_id": avaliacao_id},
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Avaliacao nao encontrada.")
    db.commit()

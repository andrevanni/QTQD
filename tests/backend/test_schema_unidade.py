from uuid import UUID
from datetime import date
from backend.app.schemas.avaliacoes import (
    AvaliacaoCreateRequest,
    AvaliacaoUpdateRequest,
)

TID = UUID("b2ce08a4-b1f9-4465-b162-9f5e9bb70092")
GID = UUID("11111111-1111-1111-1111-111111111111")
LID = UUID("22222222-2222-2222-2222-222222222222")


def test_create_default_unidade_none():
    req = AvaliacaoCreateRequest(tenant_id=TID, semana_referencia=date(2026, 7, 6))
    assert req.grupo_id is None
    assert req.loja_id is None


def test_create_aceita_unidade():
    req = AvaliacaoCreateRequest(
        tenant_id=TID, semana_referencia=date(2026, 7, 6), grupo_id=GID, loja_id=LID
    )
    assert req.grupo_id == GID
    assert req.loja_id == LID


def test_update_aceita_unidade():
    req = AvaliacaoUpdateRequest(grupo_id=GID, loja_id=LID)
    assert req.grupo_id == GID
    assert req.loja_id == LID

import pytest
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.series_service import (
    _normalizar_detalhe, build_series,
)


def _av(semana, valores, grupo_id=None, loja_id=None):
    return {"semana_referencia": semana, "grupo_id": grupo_id,
            "loja_id": loja_id, "valores": valores}


def test_normalizar_zera_total_quando_ha_subitens():
    v = {"contas_receber": 500.0, "cartoes": 300.0, "convenios": 100.0}
    out = _normalizar_detalhe(v)
    assert out["contas_receber"] == 0.0   # zerado: sub-itens presentes
    assert out["cartoes"] == 300.0


def test_normalizar_mantem_total_sem_subitens():
    v = {"contas_receber": 500.0}
    out = _normalizar_detalhe(v)
    assert out["contas_receber"] == 500.0


def test_series_nivel_loja_retorna_serie_crua():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-06-29", {"saldo_bancario": 90.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 999.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="loja", ref_id="l1")
    assert [s["semana_referencia"] for s in serie] == ["2026-07-06", "2026-06-29"]
    assert serie[0]["valores"]["saldo_bancario"] == 100.0


def test_series_nivel_grupo_soma_lojas():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="grupo", ref_id="g1")
    assert len(serie) == 1
    assert serie[0]["valores"]["saldo_bancario"] == 300.0


def test_series_nivel_grupo_direto_usa_lancamento_do_grupo():
    avals = [_av("2026-07-06", {"saldo_bancario": 500.0}, grupo_id="g2", loja_id=None)]
    grupos = [{"id": "g2", "nivel_preenchimento": "grupo"}]
    serie = build_series(avals, grupos, nivel="grupo", ref_id="g2")
    assert serie[0]["valores"]["saldo_bancario"] == 500.0


def test_series_nivel_rede_soma_todos_os_grupos():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
        _av("2026-07-06", {"saldo_bancario": 500.0}, grupo_id="g2", loja_id=None),
    ]
    grupos = [
        {"id": "g1", "nivel_preenchimento": "loja"},
        {"id": "g2", "nivel_preenchimento": "grupo"},
    ]
    serie = build_series(avals, grupos, nivel="rede", ref_id=None)
    assert serie[0]["valores"]["saldo_bancario"] == 800.0

import pytest
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.calculos_qtqd import calcular_indicadores
from backend.app.services.series_service import (
    build_series,
    build_comparativo_snapshot, build_comparativo_evolucao,
)


def _av(semana, valores, grupo_id=None, loja_id=None):
    return {"semana_referencia": semana, "grupo_id": grupo_id,
            "loja_id": loja_id, "valores": valores}


def _ind(indicadores, codigo):
    return next(i["valor"] for i in indicadores if i["codigo"] == codigo)


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


def test_comparativo_snapshot_rede_compara_grupos_e_total():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0, "contas_pagar": 50.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0, "contas_pagar": 50.0}, grupo_id="g2", loja_id=None),
    ]
    grupos = [
        {"id": "g1", "nivel_preenchimento": "loja", "nome": "Grupo 1"},
        {"id": "g2", "nivel_preenchimento": "grupo", "nome": "Grupo 2"},
    ]
    lojas = [{"id": "l1", "grupo_id": "g1", "nome": "Loja 1"}]
    snap = build_comparativo_snapshot(avals, grupos, lojas, nivel="rede", ref_id=None, semana="2026-07-06")
    nomes = {u["nome"] for u in snap["unidades"]}
    assert nomes == {"Grupo 1", "Grupo 2"}
    assert _ind(snap["total"]["indicadores"], "qt_total") == 300.0  # 100 + 200


def test_comparativo_snapshot_grupo_compara_lojas():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja", "nome": "Grupo 1"}]
    lojas = [{"id": "l1", "grupo_id": "g1", "nome": "Loja 1"},
             {"id": "l2", "grupo_id": "g1", "nome": "Loja 2"}]
    snap = build_comparativo_snapshot(avals, grupos, lojas, nivel="grupo", ref_id="g1", semana="2026-07-06")
    assert {u["nome"] for u in snap["unidades"]} == {"Loja 1", "Loja 2"}
    assert _ind(snap["total"]["indicadores"], "qt_total") == 300.0


def test_comparativo_evolucao_uma_serie_por_unidade():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-06-29", {"saldo_bancario": 90.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja", "nome": "Grupo 1"}]
    lojas = [{"id": "l1", "grupo_id": "g1", "nome": "Loja 1"},
             {"id": "l2", "grupo_id": "g1", "nome": "Loja 2"}]
    evo = build_comparativo_evolucao(avals, grupos, lojas, nivel="grupo", ref_id="g1")
    l1 = next(u for u in evo["unidades"] if u["nome"] == "Loja 1")
    assert [p["semana"] for p in l1["serie"]] == ["2026-07-06", "2026-06-29"]


def _qt(valores: dict) -> float:
    from backend.app.schemas.avaliacoes import AvaliacaoValores as AV
    from backend.app.services.calculos_qtqd import calcular_indicadores
    ind = calcular_indicadores(AV(**valores))
    return next(i.valor for i in ind if i.codigo == "qt_total")


def test_series_grupo_misto_detalhe_nao_perde_total():
    # Loja A detalha (cartoes=300), Loja B só total (contas_receber=500)
    avals = [
        _av("2026-07-06", {"cartoes": 300.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"contas_receber": 500.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="grupo", ref_id="g1")
    assert _qt(serie[0]["valores"]) == 800.0  # nada perdido (300 + 500)


def test_series_uniforme_detalhe_preserva_subitens():
    avals = [
        _av("2026-07-06", {"cartoes": 300.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"cartoes": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="grupo", ref_id="g1")
    v = serie[0]["valores"]
    assert v["cartoes"] == 500.0        # preservado (uniforme, não colapsa)
    assert v["contas_receber"] == 0.0


def test_series_rede_mista_grupo_direto_e_loja_nao_perde_total():
    # g1 (loja, detalha cartoes=300) + g2 (grupo direto, contas_receber=500)
    avals = [
        _av("2026-07-06", {"cartoes": 300.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"contas_receber": 500.0}, grupo_id="g2", loja_id=None),
    ]
    grupos = [
        {"id": "g1", "nivel_preenchimento": "loja"},
        {"id": "g2", "nivel_preenchimento": "grupo"},
    ]
    serie = build_series(avals, grupos, nivel="rede", ref_id=None)
    assert _qt(serie[0]["valores"]) == 800.0  # 300 + 500


def test_series_loja_e_crua_nao_normaliza():
    # nível loja deve devolver o dado cru: total preenchido permanece
    avals = [_av("2026-07-06", {"contas_receber": 500.0, "cartoes": 100.0}, grupo_id="g1", loja_id="l1")]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="loja", ref_id="l1")
    v = serie[0]["valores"]
    assert v["contas_receber"] == 500.0  # cru, não zerado
    assert v["cartoes"] == 100.0

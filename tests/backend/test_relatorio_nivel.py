from backend.app.services.relatorio_service import montar_avals_por_nivel


def _av(semana, valores, grupo_id=None, loja_id=None):
    return {"semana_referencia": semana, "grupo_id": grupo_id, "loja_id": loja_id, "valores": valores}


def test_sem_modo_rede_usa_todas_as_avals():
    avals = [_av("2026-07-06", {"saldo_bancario": 100.0}), _av("2026-06-29", {"saldo_bancario": 90.0})]
    out = montar_avals_por_nivel(avals, [], modo_rede=False, nivel="loja", ref=None)
    assert len(out) == 2
    assert out[0]["semana_referencia"] == "2026-07-06"  # desc


def test_modo_rede_nivel_loja_filtra_a_loja():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 999.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    out = montar_avals_por_nivel(avals, grupos, modo_rede=True, nivel="loja", ref="l1")
    assert len(out) == 1
    assert out[0]["valores"]["saldo_bancario"] == 100.0


def test_modo_rede_nivel_rede_soma():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    out = montar_avals_por_nivel(avals, grupos, modo_rede=True, nivel="rede", ref=None)
    assert out[0]["valores"]["saldo_bancario"] == 300.0


def test_nivel_rede_com_ref_none_consolida():
    """Fallback para rede quando é modo_rede + nivel loja/grupo mas ref=None (envio manual sem contexto)."""
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    out = montar_avals_por_nivel(avals, grupos, modo_rede=True, nivel="rede", ref=None)
    assert out[0]["valores"]["saldo_bancario"] == 300.0

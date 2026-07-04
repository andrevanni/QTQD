import pytest
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.api.v1.excesso_critico import _merge_aplicar_valores
from backend.app.api.v1.avaliacoes import _preserve_apply_only


def test_schema_tem_campo_com_default_zero():
    v = AvaliacaoValores()
    assert v.total_estoque_lancamentos == 0


def test_schema_aceita_valor():
    v = AvaliacaoValores(total_estoque_lancamentos=66232.77)
    assert v.total_estoque_lancamentos == 66232.77


def test_merge_grava_total_lancamentos_e_preserva_outros():
    valores = {"saldo_bancario": 100.0, "excesso_curva_a": 5.0}
    payload = {
        "excesso_curva_a": 11.0,
        "excesso_curva_b": 22.0,
        "excesso_curva_c": 33.0,
        "excesso_curva_d": 44.0,
        "total_estoque_lancamentos": 66232.77,
    }
    out = _merge_aplicar_valores(valores, payload)
    assert out["total_estoque_lancamentos"] == 66232.77
    assert out["excesso_curva_a"] == 11.0
    assert out["saldo_bancario"] == 100.0  # preservado


def test_merge_ignora_campo_ausente():
    valores = {"total_estoque_lancamentos": 10.0}
    out = _merge_aplicar_valores(valores, {"excesso_curva_a": 1.0})
    assert out["total_estoque_lancamentos"] == 10.0  # não sobrescrito


def test_merge_rejeita_nao_numerico():
    with pytest.raises(ValueError):
        _merge_aplicar_valores({}, {"total_estoque_lancamentos": "abc"})


def test_preserve_apply_only_mantem_valor_existente():
    old = {"total_estoque_lancamentos": 66232.77, "saldo_bancario": 5.0}
    new = {"total_estoque_lancamentos": 0, "saldo_bancario": 10.0}
    out = _preserve_apply_only(new, old)
    assert out["total_estoque_lancamentos"] == 66232.77  # preservado do antigo
    assert out["saldo_bancario"] == 10.0                 # do novo (formulário)


def test_preserve_apply_only_sem_antigo_nao_altera():
    new = {"total_estoque_lancamentos": 0}
    assert _preserve_apply_only(new, None)["total_estoque_lancamentos"] == 0


def test_preserve_apply_only_antigo_sem_campo():
    new = {"total_estoque_lancamentos": 0}
    out = _preserve_apply_only(new, {"saldo_bancario": 1.0})
    assert out["total_estoque_lancamentos"] == 0  # antigo não tinha → mantém novo

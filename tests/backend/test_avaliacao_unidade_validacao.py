import pytest
from backend.app.api.v1.avaliacoes import _validar_unidade


def test_sem_modo_rede_exige_unidade_nula():
    _validar_unidade(False, None, None, None)  # ok
    with pytest.raises(ValueError):
        _validar_unidade(False, None, "g1", None)
    with pytest.raises(ValueError):
        _validar_unidade(False, None, None, "l1")


def test_modo_rede_grupo_nivel_loja_exige_loja():
    _validar_unidade(True, "loja", "g1", "l1")  # ok
    with pytest.raises(ValueError):
        _validar_unidade(True, "loja", "g1", None)


def test_modo_rede_grupo_nivel_grupo_exige_grupo_sem_loja():
    _validar_unidade(True, "grupo", "g1", None)  # ok
    with pytest.raises(ValueError):
        _validar_unidade(True, "grupo", "g1", "l1")
    with pytest.raises(ValueError):
        _validar_unidade(True, "grupo", None, None)

import pytest
from backend.app.services.consolidacao_service import media_ponderada


def test_media_ponderada_basica():
    # (30*100 + 60*300) / (100+300) = 21000/400 = 52.5
    assert media_ponderada([30.0, 60.0], [100.0, 300.0]) == pytest.approx(52.5)


def test_peso_zero_cai_para_media_simples_dos_positivos():
    # pesos zerados -> média simples de [30, 50] (ignora o 0)
    assert media_ponderada([30.0, 0.0, 50.0], [0.0, 0.0, 0.0]) == pytest.approx(40.0)


def test_tudo_zero_retorna_zero():
    assert media_ponderada([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_nao_divide_por_zero():
    # não lança exceção mesmo com pesos zerados
    assert media_ponderada([10.0], [0.0]) == pytest.approx(10.0)

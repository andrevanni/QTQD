import pytest
from backend.app.services.consolidacao_service import media_ponderada
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.consolidacao_service import consolidar_valores


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


def test_consolidar_soma_aditivos():
    l1 = AvaliacaoValores(saldo_bancario=100.0, estoque_custo=1000.0, excesso_curva_d=50.0)
    l2 = AvaliacaoValores(saldo_bancario=200.0, estoque_custo=3000.0, excesso_curva_d=70.0)
    out = consolidar_valores([l1, l2])
    assert out.saldo_bancario == 300.0
    assert out.estoque_custo == 4000.0
    assert out.excesso_curva_d == 120.0


def test_consolidar_pondera_pmp_por_compras():
    # PMP ponderado por compras_mes: (30*100 + 60*300)/(400) = 52.5
    l1 = AvaliacaoValores(pmp=30.0, compras_mes=100.0)
    l2 = AvaliacaoValores(pmp=60.0, compras_mes=300.0)
    out = consolidar_valores([l1, l2])
    assert out.pmp == pytest.approx(52.5)
    assert out.compras_mes == 400.0  # aditivo


def test_consolidar_pondera_pmv_e_pme():
    l1 = AvaliacaoValores(pmv=40.0, venda_custo_mes=1000.0, pme_excel=25.0, estoque_custo=500.0)
    l2 = AvaliacaoValores(pmv=20.0, venda_custo_mes=1000.0, pme_excel=35.0, estoque_custo=1500.0)
    out = consolidar_valores([l1, l2])
    assert out.pmv == pytest.approx(30.0)                       # (40+20)/2 pesos iguais
    assert out.pme_excel == pytest.approx((25*500 + 35*1500)/2000)  # 32.5


def test_consolidar_lista_vazia_zero():
    out = consolidar_valores([])
    assert out.saldo_bancario == 0.0
    assert out.pmp == 0.0


def test_consolidar_aceita_dict():
    out = consolidar_valores([{"saldo_bancario": 10.0}, {"saldo_bancario": 5.0}])
    assert out.saldo_bancario == 15.0


def test_todos_os_campos_do_schema_tem_regra():
    from backend.app.services.consolidacao_service import ADITIVOS, PONDERADOS
    campos = set(AvaliacaoValores().model_dump().keys())
    cobertos = set(ADITIVOS) | set(PONDERADOS.keys())
    assert campos == cobertos, f"Sem regra: {campos - cobertos}; sobrando: {cobertos - campos}"


def test_item_unico_reproduz_valores():
    x = AvaliacaoValores(saldo_bancario=123.0, pmp=45.0, compras_mes=900.0)
    out = consolidar_valores([x])
    assert out.saldo_bancario == 123.0
    assert out.pmp == pytest.approx(45.0)
    assert out.compras_mes == 900.0


def test_associatividade_loja_grupo_rede():
    # 3 lojas com pesos > 0: consolidar em cascata == consolidar tudo de uma vez
    l1 = AvaliacaoValores(saldo_bancario=100.0, pmp=30.0, compras_mes=100.0,
                          pmv=40.0, venda_custo_mes=200.0)
    l2 = AvaliacaoValores(saldo_bancario=200.0, pmp=60.0, compras_mes=300.0,
                          pmv=20.0, venda_custo_mes=600.0)
    l3 = AvaliacaoValores(saldo_bancario=50.0, pmp=10.0, compras_mes=50.0,
                          pmv=90.0, venda_custo_mes=100.0)

    plano = consolidar_valores([l1, l2, l3])
    cascata = consolidar_valores([consolidar_valores([l1, l2]), consolidar_valores([l3])])

    assert cascata.saldo_bancario == pytest.approx(plano.saldo_bancario)
    assert cascata.pmp == pytest.approx(plano.pmp)
    assert cascata.pmv == pytest.approx(plano.pmv)
    assert cascata.compras_mes == pytest.approx(plano.compras_mes)

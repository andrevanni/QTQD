from backend.app.schemas.avaliacoes import AvaliacaoValores, IndicadorCalculado


def _safe_divide(left: float, right: float) -> float | None:
    if right == 0:
        return None
    return left / right


def calcular_indicadores(valores: AvaliacaoValores) -> list[IndicadorCalculado]:
    qt_total = (
        valores.saldo_bancario
        + valores.contas_receber
        + valores.cartoes
        + valores.convenios
        + valores.cheques
        + valores.trade_marketing
        + valores.outros_qt
        + valores.estoque_custo
    )
    qd_total = (
        valores.contas_pagar
        + valores.fornecedores
        + valores.investimentos_assumidos
        + valores.outras_despesas_assumidas
        + valores.dividas
        + valores.financiamentos
        + valores.tributos_atrasados
        + valores.acoes_processos
    )
    saldo_qt_qd = qt_total - qd_total
    indice_qt_qd = _safe_divide(qt_total, qd_total)
    saldo_sem_dividas = saldo_qt_qd + valores.dividas + valores.financiamentos + valores.tributos_atrasados + valores.acoes_processos
    indice_sem_dividas = _safe_divide(
        qt_total,
        qd_total - valores.dividas - valores.financiamentos - valores.tributos_atrasados - valores.acoes_processos,
    )
    saldo_sem_dividas_sem_estoque = saldo_sem_dividas - valores.estoque_custo
    pme = _safe_divide(valores.estoque_custo * 30, valores.venda_custo_mes)
    prazo_medio_compra = _safe_divide(valores.contas_pagar * 30, valores.compras_mes)
    prazo_venda = _safe_divide(valores.contas_receber * 30, valores.venda_cupom_mes)
    # Ciclo usa PMP e PMV como inputs do ERP quando fornecidos
    ciclo_financiamento = (pme or 0) + valores.pmv - valores.pmp if (valores.pmp > 0 or valores.pmv > 0) else None
    indice_compra_venda = _safe_divide(valores.compras_mes, valores.venda_custo_mes)
    margem_bruta = _safe_divide(valores.venda_cupom_mes - valores.venda_custo_mes, valores.venda_cupom_mes)
    excesso_total = valores.excesso_curva_a + valores.excesso_curva_b + valores.excesso_curva_c + valores.excesso_curva_d

    raw = [
        ("qt_total", "QT Total", qt_total, "currency"),
        ("qd_total", "QD Total", qd_total, "currency"),
        ("saldo_qt_qd", "Saldo QT/QD", saldo_qt_qd, "currency"),
        ("indice_qt_qd", "Indice QT/QD", indice_qt_qd, "ratio"),
        ("saldo_sem_dividas", "Saldo QT/QD sem dividas", saldo_sem_dividas, "currency"),
        ("indice_sem_dividas", "Indice QT/QD sem dividas", indice_sem_dividas, "ratio"),
        ("saldo_sem_dividas_sem_estoque", "Saldo QT/QD sem dividas e sem estoque", saldo_sem_dividas_sem_estoque, "currency"),
        ("pme", "Prazo medio de estoque", pme, "days"),
        ("prazo_medio_compra", "Prazo medio de compra", prazo_medio_compra, "days"),
        ("prazo_venda", "Prazo de venda", prazo_venda, "days"),
        ("ciclo_financiamento", "Ciclo de financiamento", ciclo_financiamento, "days"),
        ("indice_compra_venda", "Indice de compra/venda (custo)", indice_compra_venda, "number"),
        ("margem_bruta", "Margem bruta no mes", margem_bruta, "percent"),
        ("excesso_total", "Excesso critico total", excesso_total, "currency"),
    ]
    return [IndicadorCalculado(codigo=code, nome=name, valor=value, unidade=unit) for code, name, value, unit in raw]

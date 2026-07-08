from backend.app.schemas.avaliacoes import AvaliacaoValores


# Campos que somam diretamente na consolidação
ADITIVOS = [
    "saldo_bancario", "contas_receber", "cartoes", "convenios", "cheques",
    "trade_marketing", "outros_qt", "estoque_custo", "contas_pagar",
    "fornecedores", "investimentos_assumidos", "outras_despesas_assumidas",
    "dividas", "financiamentos", "tributos_atrasados", "acoes_processos",
    "faturamento_previsto_mes", "compras_mes", "entrada_mes",
    "venda_cupom_mes", "venda_custo_mes", "lucro_liquido_mes",
    "excesso_curva_a", "excesso_curva_b", "excesso_curva_c", "excesso_curva_d",
    "total_estoque_lancamentos",
]

# Campos ponderados: campo -> campo base do peso
PONDERADOS = {
    "pmp": "compras_mes",
    "pmv": "venda_custo_mes",
    "pmv_avista": "venda_custo_mes",
    "pmv_30": "venda_custo_mes",
    "pmv_60": "venda_custo_mes",
    "pmv_90": "venda_custo_mes",
    "pmv_120": "venda_custo_mes",
    "pmv_outros": "venda_custo_mes",
    "pme_excel": "estoque_custo",
    "cobertura_estoque_dia": "estoque_custo",
    "indice_faltas": "venda_custo_mes",
}


def _as_valores(item) -> AvaliacaoValores:
    if isinstance(item, AvaliacaoValores):
        return item
    return AvaliacaoValores(**item)


def media_ponderada(valores: list[float], pesos: list[float]) -> float:
    """Média ponderada com fallback seguro.

    Se a soma dos pesos for > 0, retorna Σ(v·p)/Σ(p).
    Se todos os pesos forem 0, retorna a média simples dos valores > 0.
    Se não houver valor > 0, retorna 0.0. Nunca divide por zero.
    """
    soma_pesos = sum(pesos)
    if soma_pesos > 0:
        return sum(v * p for v, p in zip(valores, pesos)) / soma_pesos
    positivos = [v for v in valores if v > 0]
    if positivos:
        return sum(positivos) / len(positivos)
    return 0.0


def consolidar_valores(itens: list[AvaliacaoValores | dict]) -> AvaliacaoValores:
    """Consolida uma lista de AvaliacaoValores numa só.

    Aditivos somam; prazos/índices são média ponderada pela sua base
    (ver PONDERADOS). Lista vazia -> AvaliacaoValores() (tudo zero).
    Os campos calculados NÃO são tratados aqui: quem precisar deles roda
    calcular_indicadores() sobre o resultado desta função.
    """
    registros = [_as_valores(i) for i in itens]
    if not registros:
        return AvaliacaoValores()
    out: dict = {}
    for campo in ADITIVOS:
        out[campo] = sum(getattr(r, campo) for r in registros)
    for campo, base in PONDERADOS.items():
        valores = [getattr(r, campo) for r in registros]
        pesos = [getattr(r, base) for r in registros]
        out[campo] = media_ponderada(valores, pesos)
    return AvaliacaoValores(**out)

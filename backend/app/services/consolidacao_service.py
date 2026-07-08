from backend.app.schemas.avaliacoes import AvaliacaoValores


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

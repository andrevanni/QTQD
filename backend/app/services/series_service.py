from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.consolidacao_service import consolidar_valores
from backend.app.services.calculos_qtqd import calcular_indicadores

# Total -> sub-itens que, se presentes (>0), tornam o total redundante
_GRUPOS_DETALHE = {
    "contas_receber": ("cartoes", "convenios", "cheques", "trade_marketing", "outros_qt"),
    "contas_pagar": ("fornecedores", "investimentos_assumidos", "outras_despesas_assumidas"),
    "dividas": ("financiamentos", "tributos_atrasados", "acoes_processos"),
}


def _normalizar_detalhe(valores: dict) -> dict:
    """Zera o campo-total quando há sub-itens > 0, para que a soma na consolidação
    não conflite com a prioridade 'ou-ou' de calcular_indicadores (evita descarte
    silencioso do total de uma loja quando outra detalha sub-itens)."""
    v = dict(valores)
    for total, subitens in _GRUPOS_DETALHE.items():
        if any(float(v.get(s) or 0) > 0 for s in subitens):
            v[total] = 0.0
    return v


def _valores_norm(av: dict) -> AvaliacaoValores:
    return AvaliacaoValores(**_normalizar_detalhe(av.get("valores") or {}))


def _semanas_desc(avals: list[dict]) -> list[str]:
    return sorted({a["semana_referencia"] for a in avals}, reverse=True)


def _consolidar_grupo(grupo: dict, avals_grupo: list[dict], semana: str) -> AvaliacaoValores | None:
    """Consolidado de um grupo numa semana. Grupo nivel='grupo': lançamento direto
    (loja_id None). Grupo nivel='loja': soma das lojas."""
    da_semana = [a for a in avals_grupo if a["semana_referencia"] == semana]
    if grupo["nivel_preenchimento"] == "grupo":
        diretos = [a for a in da_semana if a.get("loja_id") is None]
        if not diretos:
            return None
        return _valores_norm(diretos[0])
    lojas = [a for a in da_semana if a.get("loja_id") is not None]
    if not lojas:
        return None
    return consolidar_valores([_valores_norm(a) for a in lojas])


def build_series(avaliacoes: list[dict], grupos: list[dict], nivel: str, ref_id: str | None) -> list[dict]:
    """Série por nível: loja (crua), grupo (consolidado), rede (consolidado dos grupos)."""
    grupos_por_id = {g["id"]: g for g in grupos}

    if nivel == "loja":
        da_loja = [a for a in avaliacoes if a.get("loja_id") == ref_id]
        semanas = _semanas_desc(da_loja)
        out = []
        for s in semanas:
            regs = [a for a in da_loja if a["semana_referencia"] == s]
            valores = _valores_norm(regs[0])  # 1 registro por (loja, semana)
            out.append({"semana_referencia": s, "valores": valores.model_dump()})
        return out

    if nivel == "grupo":
        grupo = grupos_por_id.get(ref_id)
        if not grupo:
            return []
        da_grupo = [a for a in avaliacoes if a.get("grupo_id") == ref_id]
        out = []
        for s in _semanas_desc(da_grupo):
            cons = _consolidar_grupo(grupo, da_grupo, s)
            if cons is not None:
                out.append({"semana_referencia": s, "valores": cons.model_dump()})
        return out

    # nivel == "rede": soma dos consolidados de cada grupo, por semana
    out = []
    for s in _semanas_desc(avaliacoes):
        consolidados_grupo = []
        for gid, grupo in grupos_por_id.items():
            da_grupo = [a for a in avaliacoes if a.get("grupo_id") == gid]
            cons = _consolidar_grupo(grupo, da_grupo, s)
            if cons is not None:
                consolidados_grupo.append(cons)
        if consolidados_grupo:
            rede = consolidar_valores(consolidados_grupo)
            out.append({"semana_referencia": s, "valores": rede.model_dump()})
    return out


def _pacote(valores: AvaliacaoValores) -> dict:
    """Agrupa valores e indicadores calculados."""
    return {
        "valores": valores.model_dump(),
        "indicadores": [i.model_dump() for i in calcular_indicadores(valores)],
    }


def _unidades_filhas(grupos: list[dict], lojas: list[dict], nivel: str, ref_id: str | None):
    """Lista de (id, nome, tipo) das unidades comparáveis no nível pedido."""
    if nivel == "rede":
        return [(g["id"], g.get("nome", ""), "grupo") for g in grupos]
    # nivel == "grupo": compara as lojas daquele grupo
    return [(l["id"], l.get("nome", ""), "loja") for l in lojas if l.get("grupo_id") == ref_id]


def build_comparativo_snapshot(avaliacoes, grupos, lojas, nivel, ref_id, semana) -> dict:
    """Snapshot de comparativo: unidades filhas + total consolidado numa semana."""
    grupos_por_id = {g["id"]: g for g in grupos}
    unidades_out = []
    for uid, nome, tipo in _unidades_filhas(grupos, lojas, nivel, ref_id):
        if tipo == "grupo":
            da_grupo = [a for a in avaliacoes if a.get("grupo_id") == uid]
            cons = _consolidar_grupo(grupos_por_id[uid], da_grupo, semana)
        else:  # loja
            regs = [a for a in avaliacoes if a.get("loja_id") == uid and a["semana_referencia"] == semana]
            cons = _valores_norm(regs[0]) if regs else None
        if cons is not None:
            unidades_out.append({"id": uid, "nome": nome, "tipo": tipo, **_pacote(cons)})
    total_serie = build_series(avaliacoes, grupos, nivel, ref_id)
    total_v = next((s["valores"] for s in total_serie if s["semana_referencia"] == semana), None)
    total = _pacote(AvaliacaoValores(**total_v)) if total_v else _pacote(AvaliacaoValores())
    return {"semana": semana, "unidades": unidades_out, "total": total}


def build_comparativo_evolucao(avaliacoes, grupos, lojas, nivel, ref_id) -> dict:
    """Evolução de cada unidade filha: série com indicadores por semana."""
    unidades_out = []
    for uid, nome, tipo in _unidades_filhas(grupos, lojas, nivel, ref_id):
        sub_nivel = "grupo" if tipo == "grupo" else "loja"
        serie = build_series(avaliacoes, grupos, sub_nivel, uid)
        pontos = [{"semana": s["semana_referencia"],
                   "indicadores": [i.model_dump() for i in calcular_indicadores(AvaliacaoValores(**s["valores"]))]}
                  for s in serie]
        unidades_out.append({"id": uid, "nome": nome, "serie": pontos})
    return {"unidades": unidades_out}

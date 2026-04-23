"""Processa planilha Excel da primeira carga QTQD.

Formato esperado (gerado pelo template do admin):
  Coluna A: labels dos campos (linha 1 = "Campo", linha 2 = "Data (DD/MM/AAAA)", linhas 3+ = campos financeiros)
  Colunas B+: uma por semana (linha 1 = cabeçalho, linha 2 = data, linhas 3+ = valores numéricos)
"""
from __future__ import annotations
import io
from datetime import datetime
from typing import Any

import openpyxl

# Mapeamento label → código do campo (normalizado)
_LABEL_TO_KEY: dict[str, str] = {
    "saldo bancário": "saldo_bancario",
    "saldo bancario": "saldo_bancario",
    "contas a receber": "contas_receber",
    "cartões": "cartoes",
    "cartoes": "cartoes",
    "convênios": "convenios",
    "convenios": "convenios",
    "cheques": "cheques",
    "trade marketing": "trade_marketing",
    "outros qt": "outros_qt",
    "estoque (preço custo)": "estoque_custo",
    "estoque (preco custo)": "estoque_custo",
    "estoque custo": "estoque_custo",
    "contas a pagar": "contas_pagar",
    "fornecedores": "fornecedores",
    "investimentos assumidos": "investimentos_assumidos",
    "outras despesas assumidas": "outras_despesas_assumidas",
    "dívidas": "dividas",
    "dividas": "dividas",
    "financiamentos": "financiamentos",
    "tributos atrasados": "tributos_atrasados",
    "ações e processos": "acoes_processos",
    "acoes e processos": "acoes_processos",
    "faturamento previsto no mês": "faturamento_previsto_mes",
    "faturamento previsto no mes": "faturamento_previsto_mes",
    "compras no mês": "compras_mes",
    "compras no mes": "compras_mes",
    "entrada no mês": "entrada_mes",
    "entrada no mes": "entrada_mes",
    "venda cupom no mês": "venda_cupom_mes",
    "venda cupom no mes": "venda_cupom_mes",
    "venda custo no mês (cmv)": "venda_custo_mes",
    "venda custo no mes (cmv)": "venda_custo_mes",
    "venda custo no mês - cmv": "venda_custo_mes",
    "lucro líquido no mês": "lucro_liquido_mes",
    "lucro liquido no mes": "lucro_liquido_mes",
    "lucro líquido - mês": "lucro_liquido_mes",
}


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _parse_date(cell_value: Any) -> str | None:
    """Converte célula de data para ISO YYYY-MM-DD."""
    if not cell_value:
        return None
    if isinstance(cell_value, datetime):
        return cell_value.date().isoformat()
    s = str(cell_value).strip()
    # Tenta DD/MM/AAAA
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_num(cell_value: Any) -> float:
    if cell_value is None or cell_value == "":
        return 0.0
    try:
        return float(str(cell_value).replace("R$", "").replace(".", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return 0.0


def parse_excel(file_bytes: bytes) -> list[dict]:
    """
    Retorna lista de dicts prontos para inserir em avaliacoes_semanais.
    Cada dict: { semana_referencia: str, status: 'rascunho', valores: dict }
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Planilha vazia.")

    # Linha 1 = cabeçalhos das semanas (col B em diante)
    # Linha 2 = datas
    # Linhas 3+ = campos financeiros (col A = label, col B+ = valor)

    if len(rows) < 3:
        raise ValueError("Planilha deve ter pelo menos 3 linhas (cabeçalho, data, e campos).")

    date_row    = rows[1]   # índice 1 = linha 2
    field_rows  = rows[2:]  # a partir da linha 3

    # Quantas colunas de dados (B em diante = índices 1+)
    n_cols = len(date_row)

    # Mapeia cada linha a um campo
    field_map: list[str | None] = []
    for row in field_rows:
        label = _norm(str(row[0])) if row[0] else ""
        field_map.append(_LABEL_TO_KEY.get(label))

    semanas = []
    for col_idx in range(1, n_cols):
        date_val = date_row[col_idx] if col_idx < len(date_row) else None
        data_iso = _parse_date(date_val)
        if not data_iso:
            continue  # coluna sem data válida — pula

        valores: dict[str, float] = {}
        for row_idx, field_key in enumerate(field_map):
            if not field_key:
                continue
            raw = field_rows[row_idx][col_idx] if col_idx < len(field_rows[row_idx]) else None
            valores[field_key] = _parse_num(raw)

        semanas.append({
            "semana_referencia": data_iso,
            "status": "rascunho",
            "valores": valores,
        })

    if not semanas:
        raise ValueError("Nenhuma semana com data válida encontrada na planilha.")

    return semanas

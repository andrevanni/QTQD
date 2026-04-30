"""Gera o PDF do relatório QTQD para envio como anexo no e-mail."""
from __future__ import annotations
from datetime import date

from fpdf import FPDF


def _fmt_brl_curto(v: float | None) -> str:
    if v is None:
        return "-"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    if abs_v >= 1_000_000:
        return f"{prefix}R${abs_v / 1_000_000:.1f}M".replace(".", ",")
    if abs_v >= 1_000:
        return f"{prefix}R${abs_v / 1_000:.1f}K".replace(".", ",")
    return f"{prefix}R${abs_v:.0f}"


def _fmt_ratio(v: float | None) -> str:
    if v is None:
        return "-"
    return f"{v:.2f}x".replace(".", ",")


def _fmt_days(v: float | None) -> str:
    if v is None:
        return "-"
    return f"{v:.0f}d"


_INDICADORES = [
    ("qt_total",            "QT Total",           _fmt_brl_curto, "money"),
    ("qd_total",            "QD Total",            _fmt_brl_curto, "money"),
    ("saldo_qt_qd",         "Saldo QT/QD",         _fmt_brl_curto, "saldo"),
    ("indice_qt_qd",        "Indice QT/QD",        _fmt_ratio,     "indice"),
    ("saldo_sem_dividas",   "Saldo s/ Dividas",    _fmt_brl_curto, "saldo"),
    ("pme",                 "PME",                 _fmt_days,      None),
    ("prazo_venda",         "Prazo de Venda",      _fmt_days,      None),
    ("prazo_medio_compra",  "Prazo Medio Compra",  _fmt_days,      None),
    ("ciclo_financiamento", "Ciclo Financeiro",    _fmt_days,      None),
]


def _get_ind(indicadores: list, codigo: str) -> float | None:
    for i in indicadores:
        if i.codigo == codigo:
            return i.valor
    return None


def _text_color_for(color_type: str | None, v: float | None, pdf: FPDF) -> None:
    if color_type == "saldo":
        if v is None:
            pdf.set_text_color(55, 65, 81)
        elif v >= 0:
            pdf.set_text_color(22, 163, 74)
        else:
            pdf.set_text_color(220, 38, 38)
    elif color_type == "indice":
        if v is None:
            pdf.set_text_color(55, 65, 81)
        elif v >= 1.5:
            pdf.set_text_color(22, 163, 74)
        elif v >= 1.0:
            pdf.set_text_color(217, 119, 6)
        else:
            pdf.set_text_color(220, 38, 38)
    else:
        pdf.set_text_color(55, 65, 81)


def build_relatorio_pdf(tenant_nome: str, periodos: list[dict]) -> bytes:
    """
    Gera PDF do relatório QTQD e retorna os bytes do arquivo.

    periodos: lista de {"data": "dd/mm/yyyy", "indicadores": [IndicadorCalculado]}
    """
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    page_w = pdf.w - pdf.l_margin - pdf.r_margin  # 277mm em A4 landscape

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, pdf.w, 26, style="F")

    pdf.set_xy(pdf.l_margin, 5)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(page_w * 0.75, 8, f"Relatorio QTQD - {tenant_nome}", align="L")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(191, 219, 254)
    pdf.set_xy(pdf.l_margin, 14)
    pdf.cell(page_w, 7, f"Gerado em {date.today().strftime('%d/%m/%Y')}", align="L")

    pdf.ln(18)

    # ── Tabela ─────────────────────────────────────────────────────────────────
    n = len(periodos)
    label_w = 46.0
    data_w = (page_w - label_w) / max(n, 1)
    row_h = 7.5

    # Cabeçalho da tabela
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(71, 85, 105)
    pdf.set_draw_color(226, 232, 240)

    pdf.set_x(pdf.l_margin)
    pdf.cell(label_w, row_h, "Indicador", border="B", align="L", fill=True)
    for p in periodos:
        pdf.cell(data_w, row_h, p["data"], border="B", align="R", fill=True)
    pdf.ln()

    # Linhas de dados
    for i, (cod, nome, fmt_fn, color_type) in enumerate(_INDICADORES):
        even = i % 2 == 0
        pdf.set_fill_color(248, 250, 252 if even else 255, 252 if even else 255)
        if not even:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.set_x(pdf.l_margin)
        pdf.cell(label_w, row_h, nome, border="B", align="L", fill=True)

        for p in periodos:
            v = _get_ind(p["indicadores"], cod)
            _text_color_for(color_type, v, pdf)
            peso = "B" if color_type in ("saldo", "indice") else ""
            pdf.set_font("Helvetica", peso, 8)
            pdf.cell(data_w, row_h, fmt_fn(v), border="B", align="R", fill=True)

        pdf.set_text_color(55, 65, 81)
        pdf.ln()

    # ── Rodapé ─────────────────────────────────────────────────────────────────
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(
        0, 5,
        "Service Farma - Grupo A3 - Direitos Reservados  |  Enviado automaticamente pelo sistema QTQD",
        align="C",
    )

    return bytes(pdf.output())

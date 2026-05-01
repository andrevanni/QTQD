"""Gera o PDF do relatório QTQD — anexo do e-mail: tabela de indicadores por semana."""
from __future__ import annotations
from datetime import date

from fpdf import FPDF


# ── Formatadores ──────────────────────────────────────────────────────────────

def _fmt_brl(v: float | None) -> str:
    if v is None: return "-"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    if abs_v >= 1_000_000: return f"{prefix}R${abs_v/1_000_000:.1f}M".replace(".", ",")
    if abs_v >= 1_000:     return f"{prefix}R${abs_v/1_000:.1f}K".replace(".", ",")
    return f"{prefix}R${abs_v:.0f}"

def _fmt_ratio(v: float | None) -> str:
    return f"{v:.2f}x".replace(".", ",") if v is not None else "-"

def _fmt_days(v: float | None) -> str:
    return f"{v:.0f}d" if v is not None else "-"


# ── Lookup ────────────────────────────────────────────────────────────────────

def _get_ind(indicadores: list, codigo: str) -> float | None:
    for i in indicadores:
        if i.codigo == codigo:
            return i.valor
    return None

def _get_field(period: dict, key: str) -> float | None:
    """Busca em indicadores calculados e, para pmv/pmp/pme, nos valores raw."""
    if key == "_pme":
        raw = period.get("valores", {})
        pme_excel = float(raw.get("pme_excel") or 0)
        return pme_excel if pme_excel > 0 else _get_ind(period["indicadores"], "pme")
    v = _get_ind(period["indicadores"], key)
    if v is not None:
        return v
    raw = period.get("valores", {})
    val = raw.get(key)
    if val is None:
        return None
    f = float(val)
    return f if f > 0 else None


# ── Indicadores da tabela ─────────────────────────────────────────────────────

_INDICADORES = [
    ("qt_total",            "QT Total",          _fmt_brl,   "money"),
    ("qd_total",            "QD Total",          _fmt_brl,   "money"),
    ("saldo_qt_qd",         "Saldo QT/QD",       _fmt_brl,   "saldo"),
    ("indice_qt_qd",        "Indice QT/QD",      _fmt_ratio, "indice"),
    ("saldo_sem_dividas",   "Saldo s/ Dividas",  _fmt_brl,   "saldo"),
    ("_pme",                "PME",               _fmt_days,  None),
    ("pmp",                 "PMP",               _fmt_days,  None),
    ("pmv",                 "PMV",               _fmt_days,  None),
    ("ciclo_financiamento", "Ciclo Financeiro",  _fmt_days,  None),
]


def _text_color(color_type: str | None, v: float | None, pdf: FPDF) -> None:
    if color_type == "saldo":
        pdf.set_text_color(22, 163, 74) if (v is not None and v >= 0) else pdf.set_text_color(220, 38, 38)
    elif color_type == "indice":
        if v is None:          pdf.set_text_color(71, 85, 105)
        elif v >= 1.5:         pdf.set_text_color(22, 163, 74)
        elif v >= 1.0:         pdf.set_text_color(217, 119, 6)
        else:                  pdf.set_text_color(220, 38, 38)
    else:
        pdf.set_text_color(71, 85, 105)


# ── Gerador ───────────────────────────────────────────────────────────────────

def build_relatorio_pdf(
    tenant_nome: str,
    periodos: list[dict],
    charts_config: list[dict] | None = None,
) -> bytes:
    """
    Gera PDF do relatório QTQD (tabela de semanas) para envio como anexo.

    periodos: [{"data": "dd/mm/yyyy", "indicadores": [...], "valores": {...}}, ...]
    """
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()

    page_w = pdf.w - pdf.l_margin - pdf.r_margin  # ~273mm em A4 landscape

    # ── Cabecalho ────────────────────────────────────────────────────────────
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

    # ── Tabela de indicadores x semanas ─────────────────────────────────────
    n = len(periodos)
    label_w = 46.0
    data_w = (page_w - label_w) / max(n, 1)
    row_h = 7.5

    # Cabecalho da tabela
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
        pdf.set_fill_color(248, 250, 252) if even else pdf.set_fill_color(255, 255, 255)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(71, 85, 105)
        pdf.set_x(pdf.l_margin)
        pdf.cell(label_w, row_h, nome, border="B", align="L", fill=True)

        for p in periodos:
            v = _get_field(p, cod)
            _text_color(color_type, v, pdf)
            pdf.set_font("Helvetica", "B" if color_type in ("saldo", "indice") else "", 8)
            pdf.cell(data_w, row_h, fmt_fn(v), border="B", align="R", fill=True)

        pdf.set_text_color(55, 65, 81)
        pdf.ln()

    # ── Rodape ───────────────────────────────────────────────────────────────
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(
        0, 5,
        "Service Farma - Grupo A3 - Direitos Reservados  |  Enviado automaticamente pelo sistema QTQD",
        align="C",
    )

    return bytes(pdf.output())

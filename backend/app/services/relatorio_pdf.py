"""Gera o PDF do relatório QTQD — visual idêntico ao Inspetor IA do portal."""
from __future__ import annotations
from datetime import date
from io import BytesIO
import os

# Aponta o cache do matplotlib para /tmp (único diretório gravável no Lambda/Vercel)
os.environ.setdefault("MPLCONFIGDIR", "/tmp")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fpdf import FPDF

# ── Paleta de cores (igual ao portal) ─────────────────────────────────────────
C_DARK   = (15,  23,  42)    # #0f172a  — header escuro
C_BLUE   = (37,  99,  235)   # #2563eb  — accent
C_GOOD   = (22,  163, 74)    # #16a34a  — verde
C_WARN   = (217, 119, 6)     # #d97706  — âmbar
C_BAD    = (220, 38,  38)    # #dc2626  — vermelho
C_MUTED  = (100, 116, 139)   # #64748b
C_INK    = (15,  23,  42)    # #0f172a
C_SURF   = (248, 250, 252)   # #f8fafc
C_SURF2  = (241, 245, 249)   # #f1f5f9
C_BORDER = (226, 232, 240)   # #e2e8f0
C_WHITE  = (255, 255, 255)

_HEX = {
    "blue":  "#2563eb", "good":  "#16a34a", "warn":  "#d97706",
    "bad":   "#dc2626", "muted": "#64748b", "dark":  "#0f172a",
    "surf":  "#f8fafc", "surf2": "#f1f5f9", "border":"#e2e8f0",
}

_PALETTE_CHARTS = [
    "#2563eb", "#16a34a", "#dc2626", "#d97706",
    "#7c3aed", "#0891b2", "#be185d", "#65a30d",
]

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

def _fmt_pct(v: float | None) -> str:
    return f"{v*100:.1f}%".replace(".", ",") if v is not None else "-"

def _fmt_by(v: float | None, fmt: str) -> str:
    if   fmt == "ratio":    return _fmt_ratio(v)
    elif fmt == "days":     return _fmt_days(v)
    elif fmt == "percent":  return _fmt_pct(v)
    return _fmt_brl(v)

# ── Catálogo de campos ────────────────────────────────────────────────────────

_FIELD_FORMAT: dict[str, str] = {
    "qt_total": "currency", "qd_total": "currency",
    "saldo_qt_qd": "currency", "indice_qt_qd": "ratio",
    "saldo_sem_dividas": "currency", "indice_sem_dividas": "ratio",
    "saldo_sem_dividas_sem_estoque": "currency",
    "pme": "days", "prazo_medio_compra": "days", "prazo_venda": "days",
    "ciclo_financiamento": "days",
    "indice_compra_venda": "percent", "indice_entrada_venda": "percent",
    "margem_bruta": "percent", "excesso_total": "currency",
    "saldo_bancario": "currency", "contas_receber": "currency",
    "cartoes": "currency", "convenios": "currency", "cheques": "currency",
    "trade_marketing": "currency", "outros_qt": "currency", "estoque_custo": "currency",
    "contas_pagar": "currency", "fornecedores": "currency",
    "investimentos_assumidos": "currency", "outras_despesas_assumidas": "currency",
    "dividas": "currency", "financiamentos": "currency",
    "tributos_atrasados": "currency", "acoes_processos": "currency",
    "faturamento_previsto_mes": "currency", "compras_mes": "currency",
    "entrada_mes": "currency", "venda_cupom_mes": "currency",
    "venda_custo_mes": "currency", "lucro_liquido_mes": "currency",
    "pmp": "days", "pmv": "days", "pme_excel": "days",
    "indice_faltas": "percent",
    "pmv_avista": "currency", "pmv_30": "currency", "pmv_60": "currency",
    "pmv_90": "currency", "pmv_120": "currency", "pmv_outros": "currency",
    "excesso_curva_a": "currency", "excesso_curva_b": "currency",
    "excesso_curva_c": "currency", "excesso_curva_d": "currency",
}

_FIELD_LABEL: dict[str, str] = {
    "qt_total": "QT Total", "qd_total": "QD Total",
    "saldo_qt_qd": "Saldo QT/QD", "indice_qt_qd": "Índice QT/QD",
    "saldo_sem_dividas": "Saldo s/ Dívidas", "indice_sem_dividas": "Índice s/ Dívidas",
    "saldo_sem_dividas_sem_estoque": "Saldo s/ Div. e Estoque",
    "pme": "PME", "prazo_medio_compra": "Prazo Médio Compra", "prazo_venda": "Prazo de Venda",
    "ciclo_financiamento": "Ciclo Financeiro",
    "margem_bruta": "Margem Bruta", "excesso_total": "Excesso Total",
    "saldo_bancario": "Saldo Bancário", "estoque_custo": "Estoque (custo)",
    "contas_receber": "Contas a Receber", "fornecedores": "Fornecedores",
    "dividas": "Dívidas", "pmp": "PMP", "pmv": "PMV",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_ind(indicadores: list, codigo: str) -> float | None:
    for i in indicadores:
        if i.codigo == codigo:
            return i.valor
    return None

def _get_field(period: dict, key: str) -> float | None:
    v = _get_ind(period["indicadores"], key)
    if v is not None: return v
    raw = period.get("valores", {})
    val = raw.get(key)
    return float(val) if val is not None else None

def _rgb_f(rgb: tuple) -> tuple:
    """Convert (0-255) tuple to (0.0-1.0) for matplotlib."""
    return tuple(c / 255 for c in rgb)

def _semaforo_color(key: str, v: float | None) -> tuple[int,int,int]:
    if v is None: return C_MUTED
    if key == "indice_qt_qd":
        return C_GOOD if v >= 1.5 else (C_WARN if v >= 1.0 else C_BAD)
    if key == "saldo_qt_qd":
        return C_GOOD if v >= 0 else C_BAD
    if key == "pmp":
        return C_GOOD if v > 60 else (C_WARN if v > 30 else C_BAD)
    if key == "pmv":
        return C_GOOD if v < 60 else (C_WARN if v < 90 else C_BAD)
    if key == "pme":
        return C_GOOD if v < 90 else (C_WARN if v < 120 else C_BAD)
    if key == "ciclo_financiamento":
        return C_GOOD if v >= 10 else (C_WARN if v >= -10 else C_BAD)
    return C_MUTED

def _kpi_color(key: str, v: float | None) -> tuple[int,int,int]:
    if key == "indice_qt_qd":
        return C_GOOD if (v and v >= 1.5) else (C_WARN if (v and v >= 1.0) else C_BAD)
    if key in ("saldo_qt_qd", "saldo_sem_dividas"):
        return C_GOOD if (v is not None and v >= 0) else C_BAD
    if key == "ciclo_financiamento":
        return C_GOOD if (v and v >= 10) else (C_WARN if (v and v >= -10) else C_BAD)
    return C_BLUE

# ── FPDF helpers ──────────────────────────────────────────────────────────────

def _set_rgb(pdf: FPDF, rgb: tuple, what: str = "text") -> None:
    r, g, b = rgb
    if what == "text":   pdf.set_text_color(r, g, b)
    elif what == "fill": pdf.set_fill_color(r, g, b)
    elif what == "draw": pdf.set_draw_color(r, g, b)

def _page_header(pdf: FPDF, tenant_nome: str, subtitle: str, page_w: float) -> None:
    """Faixa de cabeçalho escura."""
    _set_rgb(pdf, C_DARK, "fill")
    pdf.rect(0, 0, pdf.w, 18, style="F")
    pdf.set_xy(pdf.l_margin, 3)
    pdf.set_font("Helvetica", "B", 13)
    _set_rgb(pdf, C_WHITE, "text")
    pdf.cell(page_w * 0.6, 7, f"QTQD | {tenant_nome}", align="L")
    pdf.set_font("Helvetica", "", 8)
    _set_rgb(pdf, (191, 219, 254), "text")
    pdf.cell(page_w * 0.4, 7, subtitle, align="R")
    pdf.ln(20)

def _section_title(pdf: FPDF, title: str, page_w: float) -> None:
    """Título de seção com sublinha azul."""
    _set_rgb(pdf, C_BLUE, "fill")
    pdf.rect(pdf.l_margin, pdf.get_y(), 3, 5, style="F")
    pdf.set_xy(pdf.l_margin + 5, pdf.get_y())
    pdf.set_font("Helvetica", "B", 9)
    _set_rgb(pdf, C_INK, "text")
    pdf.cell(page_w - 5, 5, title.upper(), align="L")
    pdf.ln(8)

# ── Gráficos matplotlib ───────────────────────────────────────────────────────

def _apply_style(ax, title: str = "", ylabel: str = "") -> None:
    ax.set_facecolor("#f8fafc")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#e2e8f0")
    ax.tick_params(colors="#64748b", labelsize=7)
    ax.yaxis.label.set_color("#64748b")
    ax.yaxis.label.set_size(7)
    if title:
        ax.set_title(title, fontsize=8, color="#0f172a", fontweight="bold", pad=6)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.5, linestyle="--")
    ax.set_axisbelow(True)

def _fmt_mpl_tick(x, _pos, fmt: str) -> str:
    if   fmt == "days":    return f"{x:.0f}d"
    elif fmt == "percent": return f"{x*100:.0f}%"
    elif fmt == "ratio":   return f"{x:.1f}x"
    abs_x = abs(x)
    prefix = "-" if x < 0 else ""
    if abs_x >= 1e6: return f"{prefix}{abs_x/1e6:.1f}M"
    if abs_x >= 1e3: return f"{prefix}{abs_x/1e3:.0f}K"
    return f"{prefix}{abs_x:.0f}"

def _chart_to_png(fig) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def _embed_png(pdf: FPDF, png_bytes: bytes, x: float, y: float, w: float, h: float) -> None:
    buf = BytesIO(png_bytes)
    pdf.image(buf, x=x, y=y, w=w, h=h, type="PNG")

def _build_evolution_chart(periodos: list[dict], width_mm: float) -> bytes:
    """Gráfico de evolução QT/QD/Saldo — linha dupla eixo."""
    labels = [p["data"][-5:] for p in periodos]  # dd/mm
    qt  = [_get_ind(p["indicadores"], "qt_total")     or 0 for p in periodos]
    qd  = [_get_ind(p["indicadores"], "qd_total")     or 0 for p in periodos]
    sal = [_get_ind(p["indicadores"], "saldo_qt_qd")  or 0 for p in periodos]
    idx = [_get_ind(p["indicadores"], "indice_qt_qd") or 0 for p in periodos]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(width_mm / 25.4, 2.8))
    fig.patch.set_facecolor("white")

    # — QT vs QD —
    x = range(len(labels))
    w = 0.35
    ax1.bar([i - w/2 for i in x], qt,  width=w, label="QT", color=_HEX["blue"],  alpha=0.85)
    ax1.bar([i + w/2 for i in x], qd,  width=w, label="QD", color=_HEX["bad"],   alpha=0.85)
    ax1.set_xticks(list(x)); ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=6)
    from matplotlib.ticker import FuncFormatter
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _fmt_mpl_tick(v, _, "currency")))
    _apply_style(ax1, "QT vs QD")
    ax1.legend(fontsize=6, framealpha=0.5, loc="upper left")

    # — Saldo + Índice —
    colors_sal = [_HEX["good"] if v >= 0 else _HEX["bad"] for v in sal]
    ax2.bar(list(x), sal, color=colors_sal, alpha=0.8, label="Saldo")
    ax2r = ax2.twinx()
    ax2r.plot(list(x), idx, color=_HEX["blue"], linewidth=1.5, marker="o",
              markersize=3, label="Índice", zorder=5)
    ax2r.axhline(1.0, color=_HEX["warn"], linewidth=0.8, linestyle="--", alpha=0.7)
    ax2.set_xticks(list(x)); ax2.set_xticklabels(labels, rotation=45, ha="right", fontsize=6)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _fmt_mpl_tick(v, _, "currency")))
    ax2r.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}x"))
    ax2r.tick_params(colors="#64748b", labelsize=6)
    ax2r.spines[["top"]].set_visible(False)
    _apply_style(ax2, "Saldo & Índice QT/QD")
    lines1, lbls1 = ax2.get_legend_handles_labels()
    lines2, lbls2 = ax2r.get_legend_handles_labels()
    ax2.legend(lines1+lines2, lbls1+lbls2, fontsize=6, framealpha=0.5, loc="upper left")

    fig.tight_layout(pad=0.8)
    return _chart_to_png(fig)

def _build_prazos_chart(periodos: list[dict], width_mm: float) -> bytes:
    """Gráfico de PMP / PMV / PME / Ciclo."""
    labels = [p["data"][-5:] for p in periodos]
    pmp  = [_get_field(p, "pmp")              or 0 for p in periodos]
    pmv  = [_get_field(p, "pmv")              or 0 for p in periodos]
    pme  = [_get_ind(p["indicadores"], "pme") or 0 for p in periodos]
    ciclo= [_get_ind(p["indicadores"], "ciclo_financiamento") for p in periodos]

    fig, ax = plt.subplots(figsize=(width_mm / 25.4, 2.6))
    fig.patch.set_facecolor("white")
    x = list(range(len(labels)))

    ax.plot(x, pmp,  color=_HEX["blue"],  linewidth=1.5, marker="o", markersize=3, label="PMP")
    ax.plot(x, pmv,  color=_HEX["warn"],  linewidth=1.5, marker="s", markersize=3, label="PMV")
    ax.plot(x, pme,  color=_HEX["good"],  linewidth=1.5, marker="^", markersize=3, label="PME")
    ciclo_vals = [c if c is not None else float("nan") for c in ciclo]
    ax.plot(x, ciclo_vals, color=_HEX["bad"], linewidth=1.2, marker="D",
            markersize=3, linestyle="--", label="Ciclo")
    ax.axhline(0, color="#e2e8f0", linewidth=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=6)
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}d"))
    _apply_style(ax, "Prazos Operacionais (dias)")
    ax.legend(fontsize=6, framealpha=0.5, ncol=4, loc="upper left")
    fig.tight_layout(pad=0.8)
    return _chart_to_png(fig)

def _build_custom_chart(cfg: dict, periodos: list[dict], width_mm: float) -> bytes | None:
    """Gráfico personalizado salvo pelo chart_builder."""
    field_keys: list[str] = cfg.get("fields", [])
    count = max(1, int(cfg.get("count", 12)))
    chart_type = cfg.get("type", "line")

    pts = periodos[-count:] if len(periodos) > count else periodos
    if not pts or not field_keys: return None

    labels = [p["data"][-5:] for p in pts]
    x = list(range(len(labels)))

    series = []
    for key in field_keys:
        vals = [_get_field(p, key) for p in pts]
        if all(v is None for v in vals): continue
        series.append({"key": key, "values": vals, "format": _FIELD_FORMAT.get(key, "currency"),
                       "color": _PALETTE_CHARTS[len(series) % len(_PALETTE_CHARTS)]})
    if not series: return None

    fig, ax = plt.subplots(figsize=(width_mm / 25.4, 2.6))
    fig.patch.set_facecolor("white")
    primary_fmt = series[0]["format"]

    for s in series:
        vals = [v if v is not None else float("nan") for v in s["values"]]
        label = _FIELD_LABEL.get(s["key"], s["key"].replace("_", " ").title())
        if chart_type == "bar":
            w = 0.6 / max(len(series), 1)
            offset = (series.index(s) - len(series) / 2 + 0.5) * w
            ax.bar([xi + offset for xi in x], vals, width=w, color=s["color"], alpha=0.85, label=label)
        else:
            ax.plot(x, vals, color=s["color"], linewidth=1.5, marker="o", markersize=3, label=label)

    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=6)
    from matplotlib.ticker import FuncFormatter
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _, f=primary_fmt: _fmt_mpl_tick(v, _, f)))
    _apply_style(ax, cfg.get("name", "Gráfico"))
    if len(series) > 1:
        ax.legend(fontsize=6, framealpha=0.5, loc="best", ncol=min(len(series), 3))
    fig.tight_layout(pad=0.8)
    return _chart_to_png(fig)

# ── Página 1: Dashboard / Inspetor ───────────────────────────────────────────

def _add_inspector_page(pdf: FPDF, tenant_nome: str, periodos: list[dict]) -> None:
    pdf.add_page()
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    latest = periodos[-1]

    _page_header(pdf, tenant_nome,
                 f"Semana de {latest['data']}  ·  Gerado em {date.today().strftime('%d/%m/%Y')}",
                 page_w)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    _section_title(pdf, "Inspetor IA Financeiro", page_w)

    kpis = [
        ("indice_qt_qd",        "ÍNDICE QT/QD",    _fmt_ratio),
        ("saldo_qt_qd",         "SALDO QT/QD",     _fmt_brl),
        ("saldo_sem_dividas",   "SALDO S/ DÍVIDAS", _fmt_brl),
        ("ciclo_financiamento", "CICLO FINANCEIRO", _fmt_days),
    ]
    box_w = (page_w - 9) / 4
    box_h = 22
    by = pdf.get_y()

    for idx, (key, label, fmt_fn) in enumerate(kpis):
        v = _get_field(latest, key)
        color = _kpi_color(key, v)
        bx = pdf.l_margin + idx * (box_w + 3)

        # Card background
        _set_rgb(pdf, C_SURF, "fill")
        _set_rgb(pdf, C_BORDER, "draw")
        pdf.set_line_width(0.3)
        pdf.rect(bx, by, box_w, box_h, style="FD")

        # Barra colorida esquerda
        _set_rgb(pdf, color, "fill")
        pdf.rect(bx, by, 2.5, box_h, style="F")

        # Label
        pdf.set_xy(bx + 5, by + 4)
        pdf.set_font("Helvetica", "B", 6)
        _set_rgb(pdf, C_MUTED, "text")
        pdf.cell(box_w - 7, 4, label, align="L")

        # Valor principal
        pdf.set_xy(bx + 5, by + 10)
        pdf.set_font("Helvetica", "B", 13)
        _set_rgb(pdf, color, "text")
        pdf.cell(box_w - 7, 8, fmt_fn(v) if v is not None else "-", align="L")

        # Variação vs anterior
        if len(periodos) >= 2:
            prev = _get_field(periodos[-2], key)
            if v is not None and prev is not None and prev != 0:
                delta = ((v - prev) / abs(prev)) * 100
                dcolor = C_GOOD if delta >= 0 else C_BAD
                dsign  = "+" if delta >= 0 else "-"
                pdf.set_xy(bx + 5, by + 17)
                pdf.set_font("Helvetica", "", 6)
                _set_rgb(pdf, dcolor, "text")
                pdf.cell(box_w - 7, 4, f"{dsign} {abs(delta):.1f}% vs anterior", align="L")

    pdf.set_y(by + box_h + 6)

    # ── Semáforo ──────────────────────────────────────────────────────────────
    _section_title(pdf, "Semáforo IA Financeiro", page_w)

    semaforo = [
        ("indice_qt_qd",        "LIQUIDEZ",   _fmt_ratio,  "Indice >= 1,5x"),
        ("saldo_qt_qd",         "SALDO",      _fmt_brl,    "Positivo"),
        ("pmp",                 "PMP",        _fmt_days,   "> 60 dias"),
        ("pmv",                 "PMV",        _fmt_days,   "< 60 dias"),
        ("pme",                 "PME",        _fmt_days,   "< 90 dias"),
        ("ciclo_financiamento", "CICLO",      _fmt_days,   ">= +10 dias"),
    ]
    col_w = page_w / len(semaforo)
    box_h_sem = 18
    sy = pdf.get_y()

    for i, (key, label, fmt_fn, meta) in enumerate(semaforo):
        v = _get_field(latest, key)
        color = _semaforo_color(key, v)
        bx = pdf.l_margin + i * col_w

        # Caixa com fundo levemente colorido
        soft = tuple(min(255, c + 200) for c in color)
        _set_rgb(pdf, soft, "fill")
        _set_rgb(pdf, color, "draw")
        pdf.set_line_width(0.5)
        pdf.rect(bx, sy, col_w - 1, box_h_sem, style="FD")

        # Label
        pdf.set_xy(bx, sy + 2)
        pdf.set_font("Helvetica", "B", 6)
        _set_rgb(pdf, C_MUTED, "text")
        pdf.cell(col_w - 1, 4, label, align="C")

        # Valor
        pdf.set_xy(bx, sy + 7)
        pdf.set_font("Helvetica", "B", 10)
        _set_rgb(pdf, color, "text")
        pdf.cell(col_w - 1, 6, fmt_fn(v) if v is not None else "-", align="C")

        # Meta
        pdf.set_xy(bx, sy + 13)
        pdf.set_font("Helvetica", "", 5.5)
        _set_rgb(pdf, C_MUTED, "text")
        pdf.cell(col_w - 1, 4, meta, align="C")

    pdf.set_y(sy + box_h_sem + 6)

    # ── Tabela histórica compacta ─────────────────────────────────────────────
    _section_title(pdf, "Evolução dos Indicadores", page_w)

    hist_keys = [
        ("qt_total",            "QT Total",    _fmt_brl,   "money"),
        ("qd_total",            "QD Total",    _fmt_brl,   "money"),
        ("saldo_qt_qd",         "Saldo",       _fmt_brl,   "saldo"),
        ("indice_qt_qd",        "Índice",      _fmt_ratio, "indice"),
        ("pmp",                 "PMP",         _fmt_days,  None),
        ("pmv",                 "PMV",         _fmt_days,  None),
        ("pme",                 "PME",         _fmt_days,  None),
        ("ciclo_financiamento", "Ciclo",       _fmt_days,  "ciclo"),
    ]
    recentes = periodos[-8:]
    lbl_w = 36.0
    hcol_w = (page_w - lbl_w) / max(len(recentes), 1)
    row_h = 6.5

    # Cabeçalho
    _set_rgb(pdf, C_SURF2, "fill")
    _set_rgb(pdf, C_BORDER, "draw")
    pdf.set_line_width(0.2)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 6.5)
    _set_rgb(pdf, C_MUTED, "text")
    pdf.cell(lbl_w, row_h, "Indicador", border="B", align="L", fill=True)
    for p in recentes:
        pdf.cell(hcol_w, row_h, p["data"][-5:], border="B", align="R", fill=True)
    pdf.ln()

    for i, (cod, nome, fmt_fn, ctype) in enumerate(hist_keys):
        _set_rgb(pdf, C_SURF if i % 2 == 0 else C_WHITE, "fill")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 6.5)
        _set_rgb(pdf, C_INK, "text")
        pdf.cell(lbl_w, row_h, nome, border="B", align="L", fill=True)

        for p in recentes:
            v = _get_field(p, cod)
            if ctype == "saldo":
                _set_rgb(pdf, C_GOOD if (v and v >= 0) else C_BAD, "text")
            elif ctype == "indice":
                _set_rgb(pdf, C_GOOD if (v and v >= 1.5) else (C_WARN if (v and v >= 1.0) else C_BAD), "text")
            elif ctype == "ciclo":
                _set_rgb(pdf, C_GOOD if (v and v >= 10) else (C_WARN if (v and v >= -10) else C_BAD), "text")
            else:
                _set_rgb(pdf, C_INK, "text")
            pdf.set_font("Helvetica", "B" if ctype in ("saldo","indice") else "", 6.5)
            pdf.cell(hcol_w, row_h, fmt_fn(v), border="B", align="R", fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    # Rodapé
    pdf.set_y(-10)
    pdf.set_font("Helvetica", "I", 6)
    _set_rgb(pdf, C_MUTED, "text")
    pdf.cell(0, 4, "Service Farma · Grupo A3 · Direitos Reservados  |  Enviado automaticamente pelo sistema QTQD", align="C")

# ── Página 2: Gráficos de Evolução ───────────────────────────────────────────

def _add_evolution_page(pdf: FPDF, tenant_nome: str, periodos: list[dict]) -> None:
    pdf.add_page()
    page_w = pdf.w - pdf.l_margin - pdf.r_margin

    _page_header(pdf, tenant_nome,
                 f"Evolucao: {periodos[0]['data']} a {periodos[-1]['data']}", page_w)

    _section_title(pdf, "Evolução QT, QD, Saldo e Índice", page_w)

    chart_h = 56.0
    png = _build_evolution_chart(periodos, page_w)
    _embed_png(pdf, png, pdf.l_margin, pdf.get_y(), page_w, chart_h)
    pdf.set_y(pdf.get_y() + chart_h + 6)

    _section_title(pdf, "Prazos Operacionais: PMP · PMV · PME · Ciclo", page_w)
    png2 = _build_prazos_chart(periodos, page_w)
    _embed_png(pdf, png2, pdf.l_margin, pdf.get_y(), page_w, 52)
    pdf.set_y(pdf.get_y() + 52 + 4)

    # Rodapé
    pdf.set_y(-10)
    pdf.set_font("Helvetica", "I", 6)
    _set_rgb(pdf, C_MUTED, "text")
    pdf.cell(0, 4, "Service Farma · Grupo A3 · Direitos Reservados", align="C")

# ── Página(s): Gráficos personalizados ───────────────────────────────────────

def _add_charts_pages(pdf: FPDF, tenant_nome: str, periodos: list[dict], charts_config: list[dict]) -> None:
    pdf_charts = [c for c in (charts_config or []) if c.get("includePdf")]
    if not pdf_charts: return

    pdf.add_page()
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    _page_header(pdf, tenant_nome, "Gráficos Personalizados", page_w)
    _section_title(pdf, "Gráficos configurados para o relatório", page_w)

    chart_h = 58.0
    first = True

    for cfg in pdf_charts:
        if not first:
            remaining = pdf.h - pdf.b_margin - pdf.get_y()
            if remaining < chart_h + 12:
                pdf.add_page()
                page_w = pdf.w - pdf.l_margin - pdf.r_margin
                _page_header(pdf, tenant_nome, "Gráficos Personalizados", page_w)
                pdf.ln(2)
        first = False

        png = _build_custom_chart(cfg, periodos, page_w)
        if png is None: continue

        _embed_png(pdf, png, pdf.l_margin, pdf.get_y(), page_w, chart_h)
        pdf.set_y(pdf.get_y() + chart_h + 8)

    # Rodapé
    pdf.set_y(-10)
    pdf.set_font("Helvetica", "I", 6)
    _set_rgb(pdf, C_MUTED, "text")
    pdf.cell(0, 4, "Service Farma · Grupo A3 · Direitos Reservados", align="C")

# ── Entry point ───────────────────────────────────────────────────────────────

def build_relatorio_pdf(
    tenant_nome: str,
    periodos: list[dict],
    charts_config: list[dict] | None = None,
) -> bytes:
    """
    Gera PDF do relatório QTQD.

    periodos: [{"data": "dd/mm/yyyy", "indicadores": [...], "valores": {...}}, ...]
    charts_config: lista de configs salvas pelo chart_builder (tenants.charts_config)
    """
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(12, 12, 12)

    _add_inspector_page(pdf, tenant_nome, periodos)
    _add_evolution_page(pdf, tenant_nome, periodos)
    _add_charts_pages(pdf, tenant_nome, periodos, charts_config or [])

    return bytes(pdf.output())

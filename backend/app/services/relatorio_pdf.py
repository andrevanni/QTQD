"""Gera o PDF do relatório QTQD para envio como anexo no e-mail."""
from __future__ import annotations
from datetime import date

from fpdf import FPDF

# ── Formatadores ──────────────────────────────────────────────────────────────

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


def _fmt_percent(v: float | None) -> str:
    if v is None:
        return "-"
    return f"{v * 100:.1f}%".replace(".", ",")


def _fmt_axis(v: float, fmt: str) -> str:
    if fmt == "days":
        return f"{v:.0f}d"
    if fmt == "percent":
        return f"{v * 100:.0f}%"
    if fmt == "ratio":
        return f"{v:.1f}x"
    abs_v = abs(v)
    prefix = "-" if v < 0 else ""
    if abs_v >= 1_000_000:
        return f"{prefix}{abs_v / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"{prefix}{abs_v / 1_000:.0f}K"
    return f"{prefix}{abs_v:.0f}"


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

_PALETTE = [
    (37, 99, 235), (22, 163, 74), (220, 38, 38), (217, 119, 6),
    (124, 58, 237), (8, 145, 178), (190, 24, 93), (101, 163, 13),
]

_INDICADORES_TABLE = [
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

_SEMAFORO_ITEMS = [
    ("indice_qt_qd",        "Liquidez",   _fmt_ratio),
    ("saldo_qt_qd",         "Saldo",      _fmt_brl_curto),
    ("pmp",                 "PMP",        _fmt_days),
    ("pmv",                 "PMV",        _fmt_days),
    ("pme",                 "PME",        _fmt_days),
    ("ciclo_financiamento", "Ciclo",      _fmt_days),
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_ind(indicadores: list, codigo: str) -> float | None:
    for i in indicadores:
        if i.codigo == codigo:
            return i.valor
    return None


def _get_field(period: dict, key: str) -> float | None:
    v = _get_ind(period["indicadores"], key)
    if v is not None:
        return v
    raw = period.get("valores", {})
    val = raw.get(key)
    return float(val) if val is not None else None


def _semaforo_color(key: str, v: float | None) -> tuple[int, int, int]:
    G, Y, R, X = (22, 163, 74), (217, 119, 6), (220, 38, 38), (148, 163, 184)
    if v is None:
        return X
    if key == "indice_qt_qd":
        return G if v >= 1.5 else (Y if v >= 1.0 else R)
    if key == "saldo_qt_qd":
        return G if v >= 0 else R
    if key == "pmp":
        return G if v > 60 else (Y if v > 30 else R)
    if key == "pmv":
        return G if v < 60 else (Y if v < 90 else R)
    if key == "pme":
        return G if v < 90 else (Y if v < 120 else R)
    if key == "ciclo_financiamento":
        return G if v >= 10 else (Y if v >= -10 else R)
    return X


def _text_color_for(color_type: str | None, v: float | None, pdf: FPDF) -> None:
    if color_type == "saldo":
        pdf.set_text_color(22, 163, 74) if (v is not None and v >= 0) else pdf.set_text_color(220, 38, 38)
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


# ── Página 1: tabela de indicadores ──────────────────────────────────────────

def _add_table_page(pdf: FPDF, tenant_nome: str, periodos: list[dict]) -> None:
    pdf.add_page()
    page_w = pdf.w - pdf.l_margin - pdf.r_margin

    # Cabeçalho
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

    for i, (cod, nome, fmt_fn, color_type) in enumerate(_INDICADORES_TABLE):
        pdf.set_fill_color(248, 250, 252) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
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

    # Rodapé
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, "Service Farma - Grupo A3 - Direitos Reservados  |  Enviado automaticamente pelo sistema QTQD", align="C")


# ── Página 2: Inspetor de Saúde ───────────────────────────────────────────────

def _add_inspector_page(pdf: FPDF, periodos: list[dict]) -> None:
    pdf.add_page()
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    latest = periodos[-1]

    # Título da seção
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, pdf.w, 16, style="F")
    pdf.set_xy(pdf.l_margin, 4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(page_w * 0.6, 8, "Inspetor de Saude", align="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(191, 219, 254)
    pdf.cell(page_w * 0.4, 8, f"Semana de {latest['data']}", align="R")
    pdf.ln(20)

    # ── 4 KPI boxes ──────────────────────────────────────────────────────────
    kpis = [
        ("indice_qt_qd",        "Indice QT/QD",      _fmt_ratio,     "indice"),
        ("saldo_qt_qd",         "Saldo QT/QD",       _fmt_brl_curto, "saldo"),
        ("saldo_sem_dividas",   "Saldo s/ Dividas",   _fmt_brl_curto, "saldo"),
        ("ciclo_financiamento", "Ciclo Financeiro",   _fmt_days,      "ciclo"),
    ]
    box_w = (page_w - 9) / 4
    box_h = 24
    by = pdf.get_y()

    for idx, (key, label, fmt_fn, ctype) in enumerate(kpis):
        v = _get_field(latest, key)
        if ctype == "indice":
            r, g, b = (22, 163, 74) if (v is not None and v >= 1.5) else \
                      ((217, 119, 6) if (v is not None and v >= 1.0) else (220, 38, 38))
        elif ctype == "saldo":
            r, g, b = (22, 163, 74) if (v is not None and v >= 0) else (220, 38, 38)
        elif ctype == "ciclo":
            r, g, b = (22, 163, 74) if (v is not None and v >= 10) else \
                      ((217, 119, 6) if (v is not None and v >= -10) else (220, 38, 38))
        else:
            r, g, b = (148, 163, 184)

        bx = pdf.l_margin + idx * (box_w + 3)

        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(r, g, b)
        pdf.set_line_width(0.6)
        pdf.rect(bx, by, box_w, box_h, style="FD")

        # barra lateral colorida
        pdf.set_fill_color(r, g, b)
        pdf.rect(bx, by, 2.5, box_h, style="F")

        pdf.set_xy(bx + 5, by + 4)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(box_w - 7, 4, label.upper(), align="L")

        pdf.set_xy(bx + 5, by + 10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(r, g, b)
        pdf.cell(box_w - 7, 9, fmt_fn(v) if v is not None else "-", align="L")

    pdf.set_y(by + box_h + 10)

    # ── Semáforo ──────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(page_w, 6, "Semaforo de Saude", align="L")
    pdf.ln(8)

    col_w = page_w / len(_SEMAFORO_ITEMS)
    sy = pdf.get_y()

    for idx, (key, label, fmt_fn) in enumerate(_SEMAFORO_ITEMS):
        v = _get_field(latest, key)
        cr, cg, cb = _semaforo_color(key, v)
        cx = pdf.l_margin + idx * col_w + col_w / 2

        # círculo
        pdf.set_fill_color(cr, cg, cb)
        pdf.ellipse(cx - 6, sy, 12, 12, style="F")

        # label
        pdf.set_xy(pdf.l_margin + idx * col_w, sy + 14)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(col_w, 5, label, align="C")

        # valor
        pdf.set_xy(pdf.l_margin + idx * col_w, sy + 19)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(cr, cg, cb)
        pdf.cell(col_w, 5, fmt_fn(v) if v is not None else "-", align="C")

    pdf.set_y(sy + 30)

    # ── Mini-tabela histórica (últimas 8 semanas, 4 indicadores) ─────────────
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(page_w, 6, "Evolucao Recente", align="L")
    pdf.ln(8)

    hist_keys = [
        ("indice_qt_qd",        "Idx QT/QD",  _fmt_ratio,     "indice"),
        ("saldo_qt_qd",         "Saldo",       _fmt_brl_curto, "saldo"),
        ("ciclo_financiamento", "Ciclo",       _fmt_days,      None),
        ("pme",                 "PME",         _fmt_days,      None),
    ]
    recentes = periodos[-8:]
    lbl_w = 38.0
    hcol_w = (page_w - lbl_w) / max(len(recentes), 1)
    row_h = 7.0

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_text_color(71, 85, 105)
    pdf.set_draw_color(226, 232, 240)
    pdf.set_x(pdf.l_margin)
    pdf.cell(lbl_w, row_h, "Indicador", border="B", align="L", fill=True)
    for p in recentes:
        pdf.cell(hcol_w, row_h, p["data"][-5:], border="B", align="R", fill=True)
    pdf.ln()

    for i, (cod, nome, fmt_fn, ct) in enumerate(hist_keys):
        pdf.set_fill_color(248, 250, 252) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(71, 85, 105)
        pdf.set_x(pdf.l_margin)
        pdf.cell(lbl_w, row_h, nome, border="B", align="L", fill=True)
        for p in recentes:
            v = _get_field(p, cod)
            _text_color_for(ct, v, pdf)
            pdf.set_font("Helvetica", "B" if ct in ("saldo", "indice") else "", 7)
            pdf.cell(hcol_w, row_h, fmt_fn(v), border="B", align="R", fill=True)
        pdf.set_text_color(55, 65, 81)
        pdf.ln()

    # Rodapé
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, "Service Farma - Grupo A3 - Direitos Reservados", align="C")


# ── Página(s) de Gráficos ────────────────────────────────────────────────────

def _draw_line_chart(pdf: FPDF, cfg: dict, periodos: list[dict],
                     cx: float, cy: float, cw: float, ch: float) -> None:
    field_keys: list[str] = cfg.get("fields", [])
    count = max(1, int(cfg.get("count", 12)))
    chart_type = cfg.get("type", "line")

    pts = periodos[-count:] if len(periodos) > count else periodos
    n = len(pts)
    if n == 0 or not field_keys:
        return

    # Coletar séries
    series = []
    for i, key in enumerate(field_keys):
        values = [_get_field(p, key) for p in pts]
        series.append({
            "key": key,
            "values": values,
            "color": _PALETTE[i % len(_PALETTE)],
            "format": _FIELD_FORMAT.get(key, "currency"),
        })

    all_vals = [v for s in series for v in s["values"] if v is not None]
    if not all_vals:
        return

    y_min = min(all_vals)
    y_max = max(all_vals)
    if y_min == y_max:
        pad = abs(y_min) * 0.1 or 1
        y_min -= pad
        y_max += pad

    # Margens internas do gráfico
    lm, bm, tm = 30, 14, 4
    gx = cx + lm
    gy = cy + tm
    gw = cw - lm - 2
    gh = ch - bm - tm

    primary_fmt = series[0]["format"]

    # Grade e labels eixo Y
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.15)
    pdf.set_font("Helvetica", "", 5.5)
    pdf.set_text_color(100, 116, 139)
    for ti in range(5):
        frac = ti / 4
        vy = y_max - frac * (y_max - y_min)
        py = gy + frac * gh
        pdf.line(gx, py, gx + gw, py)
        lbl = _fmt_axis(vy, primary_fmt)
        pdf.set_xy(cx, py - 2.5)
        pdf.cell(lm - 1, 5, lbl, align="R")

    # Labels eixo X
    labels = [p["data"] for p in pts]
    step = max(1, n // 10)
    for i, lbl in enumerate(labels):
        if i % step == 0 or i == n - 1:
            if chart_type == "line":
                px = gx + (i / max(n - 1, 1)) * gw
            else:
                px = gx + (i + 0.5) / n * gw
            pdf.set_xy(px - 9, gy + gh + 1)
            pdf.cell(18, 4, lbl[-5:], align="C")

    # Séries
    for s in series:
        cr, cg, cb = s["color"]
        vals = s["values"]
        if chart_type == "bar":
            bar_w = gw / n * 0.5
            for i, v in enumerate(vals):
                if v is None:
                    continue
                frac = (v - y_min) / (y_max - y_min)
                bh = frac * gh
                bxp = gx + (i + 0.25) / n * gw
                pdf.set_fill_color(cr, cg, cb)
                pdf.rect(bxp, gy + gh - bh, bar_w, bh, style="F")
        else:
            pdf.set_draw_color(cr, cg, cb)
            pdf.set_line_width(0.5)
            prev_px = prev_py = None
            for i, v in enumerate(vals):
                if v is None:
                    prev_px = prev_py = None
                    continue
                px = gx + (i / max(n - 1, 1)) * gw
                frac = (v - y_min) / (y_max - y_min)
                py = gy + gh - frac * gh
                if prev_px is not None:
                    pdf.line(prev_px, prev_py, px, py)
                pdf.set_fill_color(cr, cg, cb)
                pdf.ellipse(px - 1, py - 1, 2, 2, style="F")
                prev_px, prev_py = px, py

    # Borda do gráfico
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.25)
    pdf.rect(gx, gy, gw, gh, style="D")

    # Legenda
    leg_x = gx
    leg_y = gy + gh + bm + 1
    for s in series:
        cr, cg, cb = s["color"]
        pdf.set_fill_color(cr, cg, cb)
        pdf.rect(leg_x, leg_y, 4, 3, style="F")
        pdf.set_xy(leg_x + 5, leg_y - 0.5)
        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(71, 85, 105)
        field_label = s["key"].replace("_", " ").title()
        pdf.cell(38, 4, field_label, align="L")
        leg_x += 44


def _add_charts_pages(pdf: FPDF, periodos: list[dict], charts_config: list[dict]) -> None:
    pdf_charts = [c for c in (charts_config or []) if c.get("includePdf")]
    if not pdf_charts:
        return

    pdf.add_page()
    page_w = pdf.w - pdf.l_margin - pdf.r_margin

    # Título da seção
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, pdf.w, 16, style="F")
    pdf.set_xy(pdf.l_margin, 4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(page_w, 8, "Graficos", align="L")
    pdf.ln(20)

    chart_h = 62
    gap = 10

    for cfg in pdf_charts:
        remaining = pdf.h - pdf.b_margin - pdf.get_y()
        if remaining < chart_h + 14:
            pdf.add_page()
            pdf.ln(4)

        # Título do gráfico
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(page_w, 6, cfg.get("name", "Grafico"), align="L")
        pdf.ln(7)

        y_start = pdf.get_y()
        _draw_line_chart(pdf, cfg, periodos, pdf.l_margin, y_start, page_w, chart_h)
        pdf.set_y(y_start + chart_h + gap)

    # Rodapé
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 5, "Service Farma - Grupo A3 - Direitos Reservados", align="C")


# ── Entry point ───────────────────────────────────────────────────────────────

def build_relatorio_pdf(
    tenant_nome: str,
    periodos: list[dict],
    charts_config: list[dict] | None = None,
) -> bytes:
    """
    Gera PDF do relatório QTQD e retorna os bytes do arquivo.

    periodos: lista de {"data": "dd/mm/yyyy", "indicadores": [...], "valores": {...}}
    charts_config: lista de configs salvas pelo chart_builder (tenants.charts_config)
    """
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)

    _add_table_page(pdf, tenant_nome, periodos)
    _add_inspector_page(pdf, periodos)
    _add_charts_pages(pdf, periodos, charts_config or [])

    return bytes(pdf.output())

"""
PDF do relatório QTQD — gerado via xhtml2pdf (HTML -> PDF).
Replica a estrutura e visual do Inspetor IA do Portal do Cliente.
"""
from __future__ import annotations
from datetime import date
from io import BytesIO
import base64
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Lookup de valores ─────────────────────────────────────────────────────────

def _ind(indicadores, key):
    for i in indicadores:
        if i.codigo == key:
            return i.valor
    return None

def _val(p: dict, key: str):
    """Busca valor: pmv/pmp/pme_excel vêm dos valores raw (igual ao portal)."""
    if key == "_pme":
        raw = p.get("valores", {})
        e = float(raw.get("pme_excel") or 0)
        return e if e > 0 else _ind(p["indicadores"], "pme")
    v = _ind(p["indicadores"], key)
    if v is not None:
        return v
    raw = p.get("valores", {})
    r = raw.get(key)
    if r is None:
        return None
    f = float(r)
    return f if f > 0 else None

# ── Formatadores ──────────────────────────────────────────────────────────────

def _brl(v):
    if v is None: return "-"
    a = abs(v); s = "-" if v < 0 else ""
    if a >= 1e6: return f"{s}R${a/1e6:.1f}M".replace(".", ",")
    if a >= 1e3: return f"{s}R${a/1e3:.1f}K".replace(".", ",")
    return f"{s}R${a:.0f}"

def _brl_full(v):
    if v is None: return "-"
    return f"R$ {abs(v):_.2f}".replace("_", ".").replace(",","X").replace(".",",").replace("X",".") if v >= 0 \
        else f"-R$ {abs(v):_.2f}".replace("_", ".").replace(",","X").replace(".",",").replace("X",".")

def _ratio(v): return f"{v:.2f}x".replace(".", ",") if v is not None else "-"
def _days(v):  return f"{int(v)} dias"             if v is not None else "-"

FMT: dict[str, str] = {
    "qt_total":"currency","qd_total":"currency","saldo_qt_qd":"currency",
    "indice_qt_qd":"ratio","saldo_sem_dividas":"currency","ciclo_financiamento":"days",
    "pme":"days","pmp":"days","pmv":"days","pme_excel":"days","_pme":"days",
    "margem_bruta":"percent","excesso_total":"currency",
    "saldo_bancario":"currency","estoque_custo":"currency",
    "contas_receber":"currency","fornecedores":"currency","dividas":"currency",
    "faturamento_previsto_mes":"currency","compras_mes":"currency",
    "venda_cupom_mes":"currency","venda_custo_mes":"currency",
}
LABELS: dict[str, str] = {
    "qt_total":"QT Total","qd_total":"QD Total","saldo_qt_qd":"Saldo QT/QD",
    "indice_qt_qd":"Indice QT/QD","saldo_sem_dividas":"Saldo s/ Dividas",
    "ciclo_financiamento":"Ciclo Financeiro","_pme":"PME","pmp":"PMP","pmv":"PMV",
    "estoque_custo":"Estoque (custo)","saldo_bancario":"Saldo Bancario",
    "contas_receber":"Contas a Receber","fornecedores":"Fornecedores","dividas":"Dividas",
    "margem_bruta":"Margem Bruta","excesso_total":"Excesso Total",
}

PALETTE = ["#2563eb","#16a34a","#dc2626","#d97706","#7c3aed","#0891b2","#be185d","#65a30d"]

def _fmt_by(v, key):
    f = FMT.get(key, "currency")
    if f == "ratio":   return _ratio(v)
    if f == "days":    return _days(v)
    if f == "percent": return f"{v*100:.1f}%" if v is not None else "-"
    return _brl(v)

# ── Cores condicionais (igual ao portal) ──────────────────────────────────────

def _kpi_cls(key, v):
    if key == "indice_qt_qd":
        return "good" if (v and v >= 1.5) else ("warn" if (v and v >= 1.0) else "bad")
    if key in ("saldo_qt_qd","saldo_sem_dividas"):
        return "good" if (v is not None and v >= 0) else "bad"
    if key == "ciclo_financiamento":
        return "good" if (v and v >= 10) else ("warn" if (v and v >= -10) else "bad")
    return "blue"

def _sem_cls(key, v):
    if v is None: return "neutral"
    if key == "indice_qt_qd": return "good" if v >= 1.5 else ("warning" if v >= 1.0 else "bad")
    if key == "saldo_qt_qd":  return "good" if v >= 0 else "bad"
    if key == "pmp":  return "good" if v > 60 else ("warning" if v > 30 else "bad")
    if key == "pmv":  return "good" if v < 60 else ("warning" if v < 90 else "bad")
    if key == "_pme": return "good" if v < 90 else ("warning" if v < 120 else "bad")
    if key == "ciclo_financiamento": return "good" if v >= 10 else ("warning" if v >= -10 else "bad")
    return "neutral"

def _row_cls(ct, v):
    if ct == "saldo":  return "good" if (v is not None and v >= 0) else "bad"
    if ct == "indice":
        if v is None: return ""
        return "good" if v >= 1.5 else ("warn" if v >= 1.0 else "bad")
    if ct == "ciclo":
        if v is None: return ""
        return "good" if v >= 10 else ("warn" if v >= -10 else "bad")
    return ""

# ── Matplotlib ────────────────────────────────────────────────────────────────

def _mpl_tick(v, _, fmt="currency"):
    if fmt == "days":    return f"{v:.0f}d"
    if fmt == "percent": return f"{v*100:.0f}%"
    if fmt == "ratio":   return f"{v:.1f}x"
    a = abs(v); s = "-" if v < 0 else ""
    if a >= 1e6: return f"{s}{a/1e6:.1f}M"
    if a >= 1e3: return f"{s}{a/1e3:.0f}K"
    return f"{s}{a:.0f}"

def _style_ax(ax, title=""):
    ax.set_facecolor("#f8fafc")
    for sp in ["top","right"]: ax.spines[sp].set_visible(False)
    for sp in ["left","bottom"]: ax.spines[sp].set_color("#e2e8f0")
    ax.tick_params(colors="#64748b", labelsize=7)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.5, linestyle="--", zorder=0)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, fontsize=9, color="#0f172a", fontweight="bold", pad=6)

def _fig_to_b64(fig) -> str:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def _chart_qt_qd(periodos, w_in) -> str:
    labels = [p["data"][-5:] for p in periodos]
    qt  = [_val(p,"qt_total")    or 0 for p in periodos]
    qd  = [_val(p,"qd_total")    or 0 for p in periodos]
    sal = [_val(p,"saldo_qt_qd") or 0 for p in periodos]
    idx = [_val(p,"indice_qt_qd") or 0 for p in periodos]
    x = list(range(len(labels)))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(w_in, 3.2))
    fig.patch.set_facecolor("white")

    bw = 0.35
    ax1.bar([i-bw/2 for i in x], qt, width=bw, label="QT", color="#2563eb", alpha=0.85, zorder=3)
    ax1.bar([i+bw/2 for i in x], qd, width=bw, label="QD", color="#dc2626", alpha=0.85, zorder=3)
    ax1.set_xticks(x); ax1.set_xticklabels(labels, rotation=40, ha="right", fontsize=6)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,p: _mpl_tick(v,p,"currency")))
    ax1.legend(fontsize=7, framealpha=0.5, loc="upper left")
    _style_ax(ax1, "QT vs QD por Semana")

    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in sal]
    ax2.bar(x, sal, color=colors, alpha=0.85, zorder=3, label="Saldo")
    ax2r = ax2.twinx()
    ax2r.plot(x, idx, color="#2563eb", lw=2, marker="o", ms=3, label="Indice", zorder=5)
    ax2r.axhline(1.0, color="#d97706", lw=1, ls="--", alpha=0.7)
    ax2r.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,p: f"{v:.1f}x"))
    ax2r.tick_params(colors="#64748b", labelsize=6)
    ax2r.spines["top"].set_visible(False)
    ax2.set_xticks(x); ax2.set_xticklabels(labels, rotation=40, ha="right", fontsize=6)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,p: _mpl_tick(v,p,"currency")))
    h1,l1 = ax2.get_legend_handles_labels(); h2,l2 = ax2r.get_legend_handles_labels()
    ax2.legend(h1+h2, l1+l2, fontsize=7, framealpha=0.5, loc="upper left")
    _style_ax(ax2, "Saldo QT/QD e Indice")

    fig.tight_layout(pad=0.8)
    return _fig_to_b64(fig)

def _chart_prazos(periodos, w_in) -> str:
    labels = [p["data"][-5:] for p in periodos]
    pmp   = [_val(p,"pmp")               or 0           for p in periodos]
    pmv   = [_val(p,"pmv")               or 0           for p in periodos]
    pme   = [_val(p,"_pme")              or 0           for p in periodos]
    ciclo = [(_val(p,"ciclo_financiamento") if _val(p,"ciclo_financiamento") is not None else float("nan")) for p in periodos]
    x = list(range(len(labels)))

    fig, ax = plt.subplots(figsize=(w_in, 2.8))
    fig.patch.set_facecolor("white")
    ax.plot(x, pmp,  color="#2563eb", lw=2, marker="o", ms=3, label="PMP")
    ax.plot(x, pmv,  color="#d97706", lw=2, marker="s", ms=3, label="PMV")
    ax.plot(x, pme,  color="#16a34a", lw=2, marker="^", ms=3, label="PME")
    ax.plot(x, ciclo,color="#dc2626", lw=1.5, marker="D", ms=3, ls="--", label="Ciclo")
    ax.axhline(0, color="#e2e8f0", lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,p: f"{v:.0f}d"))
    ax.legend(fontsize=7, framealpha=0.5, ncol=4, loc="upper left")
    _style_ax(ax, "Prazos Operacionais: PMP | PMV | PME | Ciclo")
    fig.tight_layout(pad=0.8)
    return _fig_to_b64(fig)

def _chart_custom(cfg: dict, periodos, w_in) -> str | None:
    keys: list[str] = cfg.get("fields", [])
    count = max(1, int(cfg.get("count", 12)))
    pts = periodos[-count:] if len(periodos) > count else periodos
    if not pts or not keys: return None
    labels = [p["data"][-5:] for p in pts]
    x = list(range(len(labels)))
    series = []
    for k in keys:
        vals = [_val(p, k) for p in pts]
        if all(v is None for v in vals): continue
        series.append({
            "key": k, "vals": vals,
            "fmt": FMT.get(k, "currency"),
            "color": PALETTE[len(series) % len(PALETTE)],
            "label": LABELS.get(k, k.replace("_"," ").title()),
        })
    if not series: return None

    fig, ax = plt.subplots(figsize=(w_in, 2.8))
    fig.patch.set_facecolor("white")
    pf = series[0]["fmt"]
    ct = cfg.get("type", "line")

    for s in series:
        vals = [v if v is not None else float("nan") for v in s["vals"]]
        if ct == "bar":
            bw = 0.6 / max(len(series), 1)
            off = (series.index(s) - len(series)/2 + 0.5) * bw
            ax.bar([xi+off for xi in x], vals, width=bw, color=s["color"], alpha=0.85, label=s["label"], zorder=3)
        else:
            ax.plot(x, vals, color=s["color"], lw=2, marker="o", ms=3, label=s["label"], zorder=3)

    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,p,f=pf: _mpl_tick(v,p,f)))
    if len(series) > 1:
        ax.legend(fontsize=7, framealpha=0.5, loc="best", ncol=min(len(series), 4))
    _style_ax(ax, cfg.get("name", "Grafico"))
    fig.tight_layout(pad=0.8)
    return _fig_to_b64(fig)

# ── HTML builder ──────────────────────────────────────────────────────────────

_CSS = """
@page { size: A4 landscape; margin: 1.2cm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #0f172a; margin: 0; padding: 0; }

/* HEADER */
.page-header { background-color: #0f172a; padding: 14px 18px; margin-bottom: 14px; }
.page-header-title { color: #ffffff; font-size: 16px; font-weight: bold; margin: 0 0 3px; }
.page-header-sub { color: #bfdbfe; font-size: 10px; margin: 0; }

/* SECTION TITLE */
.section-title { font-size: 8px; font-weight: bold; text-transform: uppercase;
    letter-spacing: 0.06em; color: #2563eb; margin: 14px 0 8px;
    padding-left: 7px; border-left: 3px solid #2563eb; }

/* KPI CARDS TABLE */
.kpi-table { width: 100%; border-spacing: 8px; border-collapse: separate; margin-bottom: 4px; }
.kpi-card { padding: 13px 11px 10px; border: 1px solid #e2e8f0; background-color: #f8fafc;
    vertical-align: top; width: 25%; }
.kpi-card.good { border-left: 4px solid #16a34a; }
.kpi-card.bad  { border-left: 4px solid #dc2626; }
.kpi-card.warn { border-left: 4px solid #d97706; }
.kpi-card.blue { border-left: 4px solid #2563eb; }
.kpi-label { font-size: 8px; font-weight: bold; text-transform: uppercase;
    color: #64748b; letter-spacing: 0.05em; margin-bottom: 6px; }
.kpi-value { font-size: 20px; font-weight: bold; margin: 0 0 4px; }
.kpi-value.good { color: #16a34a; }
.kpi-value.bad  { color: #dc2626; }
.kpi-value.warn { color: #d97706; }
.kpi-value.blue { color: #2563eb; }
.kpi-sub { font-size: 9px; color: #64748b; }

/* SEMAPHORE TABLE */
.sem-table { width: 100%; border-spacing: 6px; border-collapse: separate; margin-bottom: 4px; }
.sem-item { padding: 9px 6px 7px; border: 1px solid #e2e8f0; text-align: center;
    background-color: #f8fafc; vertical-align: top; }
.sem-item.good    { border-color: #16a34a; background-color: #f0fdf4; }
.sem-item.bad     { border-color: #dc2626; background-color: #fef2f2; }
.sem-item.warning { border-color: #d97706; background-color: #fffbeb; }
.sem-label { font-size: 7px; font-weight: bold; text-transform: uppercase;
    color: #64748b; letter-spacing: 0.04em; margin-bottom: 4px; }
.sem-value { font-size: 15px; font-weight: bold; margin: 0 0 2px; color: #0f172a; }
.sem-value.good    { color: #16a34a; }
.sem-value.bad     { color: #dc2626; }
.sem-value.warning { color: #d97706; }
.sem-meta { font-size: 7px; color: #64748b; }

/* DATA TABLES */
.data-table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
.data-table th { background-color: #1e3a8a; color: #ffffff; padding: 6px 8px;
    font-size: 9px; font-weight: 600; text-align: right; }
.data-table th.left { text-align: left; }
.data-table td { padding: 5px 8px; font-size: 9px; border-bottom: 1px solid #f1f5f9;
    text-align: right; }
.data-table td.left { text-align: left; font-weight: 600; color: #475569; }
.data-table tr.even td { background-color: #f8fafc; }
.txt-good { color: #16a34a; font-weight: bold; }
.txt-bad  { color: #dc2626; font-weight: bold; }
.txt-warn { color: #d97706; font-weight: bold; }

/* CHARTS */
.chart-img { width: 100%; }
.chart-title { font-size: 9px; font-weight: bold; color: #0f172a; margin: 10px 0 4px; }

/* FOOTER */
.footer { font-size: 7px; color: #94a3b8; text-align: center; margin-top: 12px;
    border-top: 1px solid #f1f5f9; padding-top: 6px; }
"""

def _h(s: str) -> str:
    """Escapa HTML."""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _build_html(tenant_nome: str, periodos: list[dict], charts_config: list[dict]) -> str:
    hoje = date.today().strftime("%d/%m/%Y")
    latest = periodos[-1]
    chart_w_in = 10.2   # ~260mm

    # ── Gráficos base64 ──────────────────────────────────────────────────────
    b64_qt_qd  = _chart_qt_qd(periodos, chart_w_in)
    b64_prazos = _chart_prazos(periodos, chart_w_in)
    pdf_charts = [c for c in charts_config if c.get("includePdf")]
    custom_b64 = []
    for cfg in pdf_charts:
        b64 = _chart_custom(cfg, periodos, chart_w_in)
        if b64:
            custom_b64.append((cfg.get("name","Grafico"), b64))

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 1 — TABELA DE SEMANAS
    # ══════════════════════════════════════════════════════════════════════════
    _TABELA_ROWS = [
        ("qt_total",            "QT Total",         _brl,   ""),
        ("qd_total",            "QD Total",         _brl,   ""),
        ("saldo_qt_qd",         "Saldo QT/QD",      _brl,   "saldo"),
        ("indice_qt_qd",        "Indice QT/QD",     _ratio, "indice"),
        ("saldo_sem_dividas",   "Saldo s/ Dividas", _brl,   "saldo"),
        ("_pme",                "PME",              _days,  ""),
        ("pmp",                 "PMP",              _days,  ""),
        ("pmv",                 "PMV",              _days,  ""),
        ("ciclo_financiamento", "Ciclo Financeiro", _days,  "ciclo"),
    ]

    thead_cells = '<th class="left">Indicador</th>' + "".join(
        f'<th>{_h(p["data"])}</th>' for p in periodos)

    tbody = ""
    for i, (key, nome, fn, ct) in enumerate(_TABELA_ROWS):
        row_cls = "even" if i % 2 == 0 else ""
        cells = f'<td class="left">{_h(nome)}</td>'
        for p in periodos:
            v = _val(p, key)
            txt_cls = _row_cls(ct, v)
            cells += f'<td class="{txt_cls}">{_h(fn(v))}</td>'
        tbody += f'<tr class="{row_cls}">{cells}</tr>'

    tabela_html = f"""
<div class="page-header">
  <div class="page-header-title">QTQD - Relatorio Semanal | {_h(tenant_nome)}</div>
  <div class="page-header-sub">Tabela de Indicadores | {len(periodos)} retratos | Gerado em {hoje}</div>
</div>
<p class="section-title">Evolucao dos Indicadores por Semana</p>
<table class="data-table">
  <thead><tr>{thead_cells}</tr></thead>
  <tbody>{tbody}</tbody>
</table>
<div class="footer">Service Farma - Grupo A3 - Direitos Reservados | Enviado automaticamente pelo sistema QTQD</div>
"""

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 2 — INSPETOR IA FINANCEIRO
    # ══════════════════════════════════════════════════════════════════════════
    _KPIS = [
        ("indice_qt_qd",        "INDICE QT/QD",     _ratio),
        ("saldo_qt_qd",         "SALDO QT/QD",      _brl),
        ("saldo_sem_dividas",   "SALDO S/ DIVIDAS", _brl),
        ("ciclo_financiamento", "CICLO FINANCEIRO", _days),
    ]

    kpi_cells = ""
    for key, lbl, fn in _KPIS:
        v = _val(latest, key)
        cls = _kpi_cls(key, v)
        delta_html = ""
        if len(periodos) >= 2:
            pv = _val(periodos[-2], key)
            if v is not None and pv and pv != 0:
                d = ((v - pv) / abs(pv)) * 100
                sign = "+" if d >= 0 else ""
                dc = "good" if d >= 0 else "bad"
                delta_html = f'<div class="kpi-sub txt-{dc}">{sign}{d:.1f}% vs semana anterior</div>'
        kpi_cells += f"""
        <td class="kpi-card {cls}">
          <div class="kpi-label">{_h(lbl)}</div>
          <div class="kpi-value {cls}">{_h(fn(v)) if v is not None else "-"}</div>
          {delta_html}
        </td>"""

    _SEM = [
        ("indice_qt_qd", "LIQUIDEZ",  _ratio, "Indice &gt;= 1,5x"),
        ("saldo_qt_qd",  "SALDO",     _brl,   "Positivo"),
        ("pmp",          "PMP",       _days,  "&gt; 60 dias"),
        ("pmv",          "PMV",       _days,  "&lt; 60 dias"),
        ("_pme",         "PME",       _days,  "&lt; 90 dias"),
        ("ciclo_financiamento","CICLO",_days, "&gt;= +10 dias"),
    ]

    sem_cells = ""
    for key, lbl, fn, meta in _SEM:
        v = _val(latest, key)
        cls = _sem_cls(key, v)
        sem_cells += f"""
        <td class="sem-item {cls}">
          <div class="sem-label">{_h(lbl)}</div>
          <div class="sem-value {cls}">{_h(fn(v)) if v is not None else "-"}</div>
          <div class="sem-meta">{meta}</div>
        </td>"""

    # Tabela histórica (últimas 8 semanas, mais recente primeiro)
    _HIST = [
        ("qt_total",           "QT Total",  _brl_full, ""),
        ("qd_total",           "QD Total",  _brl_full, ""),
        ("saldo_qt_qd",        "Saldo",     _brl_full, "saldo"),
        ("indice_qt_qd",       "Indice",    _ratio,    "indice"),
        ("_pme",               "PME",       _days,     ""),
        ("pmp",                "PMP",       _days,     ""),
        ("pmv",                "PMV",       _days,     ""),
        ("ciclo_financiamento","Ciclo",     _days,     "ciclo"),
    ]
    rec8 = list(reversed(periodos[-8:]))

    hist_head = '<th class="left">Indicador</th>' + "".join(
        f'<th>{_h(p["data"])}</th>' for p in rec8)
    hist_body = ""
    for i, (key, nome, fn, ct) in enumerate(_HIST):
        row_cls = "even" if i % 2 == 0 else ""
        cells = f'<td class="left">{_h(nome)}</td>'
        for p in rec8:
            v = _val(p, key)
            tc = _row_cls(ct, v)
            cells += f'<td class="{tc}">{_h(fn(v))}</td>'
        hist_body += f'<tr class="{row_cls}">{cells}</tr>'

    inspetor_html = f"""
<div class="page-header">
  <div class="page-header-title">Inspetor IA Financeiro | {_h(tenant_nome)}</div>
  <div class="page-header-sub">Semana de {_h(latest["data"])} | Gerado em {hoje}</div>
</div>

<p class="section-title">Inspetor IA Financeiro</p>
<table class="kpi-table">
  <tr>{kpi_cells}</tr>
</table>

<p class="section-title">Semaforo IA Financeiro</p>
<table class="sem-table">
  <tr>{sem_cells}</tr>
</table>

<p class="section-title">Evolucao Recente</p>
<table class="data-table">
  <thead><tr>{hist_head}</tr></thead>
  <tbody>{hist_body}</tbody>
</table>
<div class="footer">Service Farma - Grupo A3 - Direitos Reservados</div>
"""

    # ══════════════════════════════════════════════════════════════════════════
    # SEÇÃO 3 — GRÁFICOS
    # ══════════════════════════════════════════════════════════════════════════
    custom_blocks = "".join(
        f'<div class="chart-title">{_h(nome)}</div>'
        f'<img class="chart-img" src="data:image/png;base64,{b64}"/>'
        for nome, b64 in custom_b64
    )

    graficos_html = f"""
<div class="page-header">
  <div class="page-header-title">Graficos | {_h(tenant_nome)}</div>
  <div class="page-header-sub">{_h(periodos[0]["data"])} a {_h(periodos[-1]["data"])} | Gerado em {hoje}</div>
</div>

<p class="section-title">QT vs QD por Semana e Saldo &amp; Indice QT/QD</p>
<img class="chart-img" src="data:image/png;base64,{b64_qt_qd}"/>

<p class="section-title">Prazos Operacionais: PMP | PMV | PME | Ciclo Financeiro</p>
<img class="chart-img" src="data:image/png;base64,{b64_prazos}"/>

{f'<p class="section-title">Graficos Personalizados</p>' + custom_blocks if custom_blocks else ''}

<div class="footer">Service Farma - Grupo A3 - Direitos Reservados</div>
"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{_CSS}</style>
</head><body>
{tabela_html}
<pdf:nextpage/>
{inspetor_html}
<pdf:nextpage/>
{graficos_html}
</body></html>"""


# ── Entry point ───────────────────────────────────────────────────────────────

def build_relatorio_pdf(
    tenant_nome: str,
    periodos: list[dict],
    charts_config: list[dict] | None = None,
) -> bytes:
    from xhtml2pdf import pisa

    html = _build_html(tenant_nome, periodos, charts_config or [])
    buf = BytesIO()
    pisa.CreatePDF(html, dest=buf, encoding="utf-8")
    buf.seek(0)
    return buf.read()

"""
PDF do relatório QTQD.
- Layout: fpdf2
- Gráficos: quickchart.io (Chart.js API — mesma biblioteca do portal)
"""
from __future__ import annotations
from datetime import date
from io import BytesIO
import json
import urllib.request
import urllib.parse

from fpdf import FPDF

# ── Lookup ────────────────────────────────────────────────────────────────────

def _ind(indicadores, key):
    for i in indicadores:
        if i.codigo == key:
            return i.valor
    return None

def _val(p: dict, key: str):
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
    neg = v < 0
    s = f"R$ {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-{s}" if neg else s

def _ratio(v): return f"{v:.2f}x".replace(".", ",") if v is not None else "-"
def _days(v):  return f"{int(round(v))} d"           if v is not None else "-"

FMT: dict[str, str] = {
    "qt_total": "currency", "qd_total": "currency", "saldo_qt_qd": "currency",
    "indice_qt_qd": "ratio", "saldo_sem_dividas": "currency",
    "ciclo_financiamento": "days", "pme": "days", "pmp": "days", "pmv": "days",
    "_pme": "days", "margem_bruta": "percent", "excesso_total": "currency",
}
LABELS: dict[str, str] = {
    "qt_total": "QT Total", "qd_total": "QD Total", "saldo_qt_qd": "Saldo QT/QD",
    "indice_qt_qd": "Indice QT/QD", "saldo_sem_dividas": "Saldo s/ Dividas",
    "ciclo_financiamento": "Ciclo Financeiro", "_pme": "PME", "pmp": "PMP", "pmv": "PMV",
    "estoque_custo": "Estoque (custo)", "saldo_bancario": "Saldo Bancario",
    "contas_receber": "Contas a Receber", "fornecedores": "Fornecedores",
    "dividas": "Dividas", "margem_bruta": "Margem Bruta", "excesso_total": "Excesso Total",
}

def _fmt_by(v, key):
    f = FMT.get(key, "currency")
    if f == "ratio":   return _ratio(v)
    if f == "days":    return _days(v)
    if f == "percent": return f"{v*100:.1f}%" if v is not None else "-"
    return _brl(v)

# ── Cores condicionais ────────────────────────────────────────────────────────

def _kpi_color(key, v):
    if key == "indice_qt_qd":
        return (22,163,74) if (v and v>=1.5) else ((217,119,6) if (v and v>=1.0) else (220,38,38))
    if key in ("saldo_qt_qd", "saldo_sem_dividas"):
        return (22,163,74) if (v is not None and v>=0) else (220,38,38)
    if key == "ciclo_financiamento":
        return (22,163,74) if (v and v>=10) else ((217,119,6) if (v and v>=-10) else (220,38,38))
    return (37,99,235)

def _sem_color(key, v):
    if v is None: return (100,116,139)
    if key == "indice_qt_qd": return (22,163,74) if v>=1.5 else ((217,119,6) if v>=1.0 else (220,38,38))
    if key == "saldo_qt_qd":  return (22,163,74) if v>=0   else (220,38,38)
    if key == "pmp":  return (22,163,74) if v>60  else ((217,119,6) if v>30  else (220,38,38))
    if key == "pmv":  return (22,163,74) if v<60  else ((217,119,6) if v<90  else (220,38,38))
    if key == "_pme": return (22,163,74) if v<90  else ((217,119,6) if v<120 else (220,38,38))
    if key == "ciclo_financiamento": return (22,163,74) if v>=10 else ((217,119,6) if v>=-10 else (220,38,38))
    return (100,116,139)

def _row_color(ct, v):
    if ct == "saldo":  return (22,163,74) if (v is not None and v>=0) else (220,38,38)
    if ct == "indice":
        if v is None: return (71,85,105)
        return (22,163,74) if v>=1.5 else ((217,119,6) if v>=1.0 else (220,38,38))
    if ct == "ciclo":
        if v is None: return (71,85,105)
        return (22,163,74) if v>=10 else ((217,119,6) if v>=-10 else (220,38,38))
    return (71,85,105)

# ── fpdf2 helpers ─────────────────────────────────────────────────────────────

def _rgb(pdf, c, t="text"):
    r,g,b = c
    if t == "text":  pdf.set_text_color(r,g,b)
    elif t == "fill": pdf.set_fill_color(r,g,b)
    elif t == "draw": pdf.set_draw_color(r,g,b)

def _page_header(pdf, tenant, subtitle, pw):
    _rgb(pdf,(15,23,42),"fill"); pdf.rect(0,0,pdf.w,18,style="F")
    pdf.set_xy(pdf.l_margin,3); pdf.set_font("Helvetica","B",12)
    _rgb(pdf,(255,255,255)); pdf.cell(pw*0.65,7,f"QTQD | {tenant}",align="L")
    pdf.set_font("Helvetica","",8); _rgb(pdf,(191,219,254))
    pdf.cell(pw*0.35,7,subtitle,align="R"); pdf.ln(21)

def _section(pdf, title, pw):
    _rgb(pdf,(37,99,235),"fill"); pdf.rect(pdf.l_margin,pdf.get_y(),3,5,style="F")
    pdf.set_xy(pdf.l_margin+5,pdf.get_y()); pdf.set_font("Helvetica","B",8)
    _rgb(pdf,(15,23,42)); pdf.cell(pw-5,5,title.upper(),align="L"); pdf.ln(8)

def _footer(pdf):
    pdf.set_y(-10); pdf.set_font("Helvetica","I",6); _rgb(pdf,(148,163,184))
    pdf.cell(0,4,"Service Farma - Grupo A3 - Direitos Reservados  |  Enviado automaticamente pelo sistema QTQD",align="C")

# ── quickchart.io — Chart.js server-side ─────────────────────────────────────

_QC_BASE = "https://quickchart.io/chart"
_BLUE, _RED, _GREEN, _AMBER = "#2563eb", "#dc2626", "#16a34a", "#d97706"

def _qc_png(config: dict, width=800, height=350) -> bytes | None:
    """Chama quickchart.io e retorna bytes PNG do gráfico."""
    try:
        params = urllib.parse.urlencode({
            "c": json.dumps(config, separators=(",", ":")),
            "w": width, "h": height,
            "bkg": "white", "f": "png",
        })
        url = f"{_QC_BASE}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "QTQD/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read()
    except Exception:
        return None

def _embed_png(pdf, png_bytes: bytes, x, y, w, h):
    buf = BytesIO(png_bytes)
    pdf.image(buf, x=x, y=y, w=w, h=h, type="PNG")

def _tick_callback(fmt):
    if fmt == "days":    return "value + 'd'"
    if fmt == "percent": return "(value*100).toFixed(1)+'%'"
    if fmt == "ratio":   return "value.toFixed(1)+'x'"
    return "(Math.abs(value)>=1e6?(value/1e6).toFixed(1)+'M':Math.abs(value)>=1e3?(value/1e3).toFixed(0)+'K':value.toFixed(0))"

def _axis_opts(fmt):
    return {"ticks": {"callback": f"function(value){{return {_tick_callback(fmt)}}}", "maxTicksLimit": 6}}

def _chart_qt_qd(periodos: list[dict]) -> bytes | None:
    labels = [p["data"] for p in periodos]
    qt  = [(_val(p,"qt_total")    or 0) for p in periodos]
    qd  = [(_val(p,"qd_total")    or 0) for p in periodos]
    cfg = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {"label":"QT Total","data":qt,"backgroundColor":f"{_BLUE}CC","borderColor":_BLUE,"borderWidth":1},
                {"label":"QD Total","data":qd,"backgroundColor":f"{_RED}CC", "borderColor":_RED, "borderWidth":1},
            ],
        },
        "options": {
            "plugins": {"title": {"display":True,"text":"QT vs QD por Semana"}},
            "scales": {"y": _axis_opts("currency")},
        },
    }
    return _qc_png(cfg, width=760, height=320)

def _chart_saldo_indice(periodos: list[dict]) -> bytes | None:
    labels = [p["data"] for p in periodos]
    sal = [(_val(p,"saldo_qt_qd")  or 0) for p in periodos]
    idx = [(_val(p,"indice_qt_qd") or 0) for p in periodos]
    cores_sal = [_GREEN if v >= 0 else _RED for v in sal]
    cfg = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {"label":"Saldo QT/QD","data":sal,"backgroundColor":cores_sal,"borderWidth":0,"yAxisID":"y"},
                {"label":"Indice QT/QD","data":idx,"type":"line","borderColor":_BLUE,"backgroundColor":"transparent",
                 "borderWidth":2,"pointRadius":3,"yAxisID":"y2"},
            ],
        },
        "options": {
            "plugins": {"title":{"display":True,"text":"Saldo QT/QD e Indice QT/QD"}},
            "scales": {
                "y":  dict(position="left", **_axis_opts("currency")),
                "y2": dict(position="right", grid={"drawOnChartArea":False}, **_axis_opts("ratio")),
            },
        },
    }
    return _qc_png(cfg, width=760, height=320)

def _chart_prazos(periodos: list[dict]) -> bytes | None:
    labels = [p["data"] for p in periodos]
    pmp   = [(_val(p,"pmp")  or 0) for p in periodos]
    pmv   = [(_val(p,"pmv")  or 0) for p in periodos]
    pme   = [(_val(p,"_pme") or 0) for p in periodos]
    ciclo = [(_val(p,"ciclo_financiamento") if _val(p,"ciclo_financiamento") is not None else None) for p in periodos]
    cfg = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [
                {"label":"PMP",  "data":pmp,   "borderColor":_BLUE,  "backgroundColor":"transparent","borderWidth":2,"pointRadius":3},
                {"label":"PMV",  "data":pmv,   "borderColor":_AMBER, "backgroundColor":"transparent","borderWidth":2,"pointRadius":3},
                {"label":"PME",  "data":pme,   "borderColor":_GREEN, "backgroundColor":"transparent","borderWidth":2,"pointRadius":3},
                {"label":"Ciclo","data":ciclo, "borderColor":_RED,   "backgroundColor":"transparent","borderWidth":2,"pointRadius":3,"borderDash":[5,3]},
            ],
        },
        "options": {
            "plugins": {"title":{"display":True,"text":"Prazos Operacionais: PMP | PMV | PME | Ciclo"}},
            "scales": {"y": _axis_opts("days")},
        },
    }
    return _qc_png(cfg, width=760, height=300)

def _chart_custom(cfg_chart: dict, periodos: list[dict]) -> bytes | None:
    keys: list[str] = cfg_chart.get("fields", [])
    count = max(1, int(cfg_chart.get("count", 12)))
    chart_type = cfg_chart.get("type", "line")
    pts = periodos[-count:] if len(periodos) > count else periodos
    if not pts or not keys: return None

    labels = [p["data"] for p in pts]
    COLORS = ["#2563eb","#16a34a","#dc2626","#d97706","#7c3aed","#0891b2","#be185d","#65a30d"]
    datasets = []
    prim_fmt = FMT.get(keys[0], "currency")

    for i, key in enumerate(keys):
        vals = [_val(p, key) for p in pts]
        if all(v is None for v in vals): continue
        color = COLORS[i % len(COLORS)]
        lbl = LABELS.get(key, key.replace("_"," ").title())
        if chart_type == "bar":
            datasets.append({"label":lbl,"data":vals,"backgroundColor":f"{color}CC","borderColor":color,"borderWidth":1})
        else:
            datasets.append({"label":lbl,"data":vals,"borderColor":color,"backgroundColor":"transparent","borderWidth":2,"pointRadius":3})

    if not datasets: return None
    cfg = {
        "type": chart_type,
        "data": {"labels": labels, "datasets": datasets},
        "options": {
            "plugins": {"title":{"display":True,"text":cfg_chart.get("name","Grafico")}},
            "scales": {"y": _axis_opts(prim_fmt)},
        },
    }
    return _qc_png(cfg, width=760, height=300)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — TABELA DE SEMANAS
# ═══════════════════════════════════════════════════════════════════════════════

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

def _page_tabela(pdf, tenant, periodos):
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin

    _rgb(pdf,(15,23,42),"fill"); pdf.rect(0,0,pdf.w,26,style="F")
    pdf.set_xy(pdf.l_margin,5); pdf.set_font("Helvetica","B",14)
    _rgb(pdf,(255,255,255))
    pdf.cell(pw*0.75,8,f"Relatorio QTQD - {tenant}",align="L")
    pdf.set_font("Helvetica","",9); _rgb(pdf,(191,219,254))
    pdf.set_xy(pdf.l_margin,14)
    pdf.cell(pw,7,f"Gerado em {date.today().strftime('%d/%m/%Y')} | {len(periodos)} retratos",align="L")
    pdf.ln(18)

    n = len(periodos); lw = 46.0; dw = (pw-lw)/max(n,1); rh = 7.5
    pdf.set_font("Helvetica","B",8); _rgb(pdf,(241,245,249),"fill")
    _rgb(pdf,(71,85,105)); _rgb(pdf,(226,232,240),"draw")
    pdf.set_x(pdf.l_margin)
    pdf.cell(lw,rh,"Indicador",border="B",align="L",fill=True)
    for p in periodos:
        pdf.cell(dw,rh,p["data"],border="B",align="R",fill=True)
    pdf.ln()

    for i,(cod,nome,fn,ct) in enumerate(_TABELA_ROWS):
        _rgb(pdf,(248,250,252) if i%2==0 else (255,255,255),"fill")
        pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","",8); _rgb(pdf,(71,85,105))
        pdf.cell(lw,rh,nome,border="B",align="L",fill=True)
        for p in periodos:
            v = _val(p,cod); c = _row_color(ct,v)
            _rgb(pdf,c)
            pdf.set_font("Helvetica","B" if ct in ("saldo","indice","ciclo") else "",8)
            pdf.cell(dw,rh,fn(v),border="B",align="R",fill=True)
        pdf.ln()
    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — INSPETOR IA FINANCEIRO
# ═══════════════════════════════════════════════════════════════════════════════

_KPIS = [
    ("indice_qt_qd",        "INDICE QT/QD",     _ratio),
    ("saldo_qt_qd",         "SALDO QT/QD",      _brl),
    ("saldo_sem_dividas",   "SALDO S/ DIVIDAS", _brl),
    ("ciclo_financiamento", "CICLO FINANCEIRO", _days),
]
_SEM = [
    ("indice_qt_qd",        "LIQUIDEZ",  _ratio, ">=1,5x"),
    ("saldo_qt_qd",         "SALDO",     _brl,   "Positivo"),
    ("pmp",                 "PMP",       _days,  ">60d"),
    ("pmv",                 "PMV",       _days,  "<60d"),
    ("_pme",                "PME",       _days,  "<90d"),
    ("ciclo_financiamento", "CICLO",     _days,  ">=+10d"),
]

def _page_inspetor(pdf, tenant, periodos):
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin
    latest = periodos[-1]

    _page_header(pdf, tenant, f"Inspetor IA Financeiro | Semana {latest['data']}", pw)
    _section(pdf, "Inspetor IA Financeiro", pw)

    # KPI cards
    bw = (pw-9)/4; bh = 28; by = pdf.get_y()
    for i,(key,lbl,fn) in enumerate(_KPIS):
        v = _val(latest,key); c = _kpi_color(key,v)
        bx = pdf.l_margin + i*(bw+3)
        _rgb(pdf,(248,250,252),"fill"); _rgb(pdf,c,"draw")
        pdf.set_line_width(0.5); pdf.rect(bx,by,bw,bh,style="FD")
        _rgb(pdf,c,"fill"); pdf.rect(bx,by,2.5,bh,style="F")
        pdf.set_xy(bx+5,by+4); pdf.set_font("Helvetica","B",6.5)
        _rgb(pdf,(100,116,139)); pdf.cell(bw-7,4,lbl,align="L")
        pdf.set_xy(bx+5,by+11); pdf.set_font("Helvetica","B",15)
        _rgb(pdf,c); pdf.cell(bw-7,10,fn(v) if v is not None else "-",align="L")
        if len(periodos)>=2:
            pv = _val(periodos[-2],key)
            if v is not None and pv and pv!=0:
                d = ((v-pv)/abs(pv))*100
                dc = (22,163,74) if d>=0 else (220,38,38)
                sign = "+" if d>=0 else ""
                pdf.set_xy(bx+5,by+22); pdf.set_font("Helvetica","",6)
                _rgb(pdf,dc); pdf.cell(bw-7,4,f"{sign}{d:.1f}% vs anterior",align="L")
    pdf.set_y(by+bh+8)

    # Semáforo
    _section(pdf,"Semaforo IA Financeiro",pw)
    cw = pw/6; sh = 22; sy = pdf.get_y()
    for i,(key,lbl,fn,meta) in enumerate(_SEM):
        v = _val(latest,key); c = _sem_color(key,v)
        soft = tuple(min(255,x+205) for x in c)
        bx = pdf.l_margin + i*cw
        _rgb(pdf,soft,"fill"); _rgb(pdf,c,"draw")
        pdf.set_line_width(0.6); pdf.rect(bx,sy,cw-1,sh,style="FD")
        pdf.set_xy(bx,sy+2); pdf.set_font("Helvetica","B",6.5)
        _rgb(pdf,(100,116,139)); pdf.cell(cw-1,4,lbl,align="C")
        pdf.set_xy(bx,sy+8); pdf.set_font("Helvetica","B",12)
        _rgb(pdf,c); pdf.cell(cw-1,7,fn(v) if v is not None else "-",align="C")
        pdf.set_xy(bx,sy+17); pdf.set_font("Helvetica","",6)
        _rgb(pdf,(100,116,139)); pdf.cell(cw-1,4,meta,align="C")
    pdf.set_y(sy+sh+8)

    # Histórico (últimas 8 semanas, mais recente primeiro)
    _section(pdf,"Evolucao Recente",pw)
    hist_keys = [
        ("qt_total","QT Total",_brl,""),("qd_total","QD Total",_brl,""),
        ("saldo_qt_qd","Saldo",_brl,"saldo"),("indice_qt_qd","Indice",_ratio,"indice"),
        ("_pme","PME",_days,""),("pmp","PMP",_days,""),("pmv","PMV",_days,""),
        ("ciclo_financiamento","Ciclo",_days,"ciclo"),
    ]
    rec = list(reversed(periodos[-8:]))
    lw2 = 34; hcw = (pw-lw2)/max(len(rec),1); rh2 = 6.5

    _rgb(pdf,(241,245,249),"fill"); _rgb(pdf,(226,232,240),"draw"); pdf.set_line_width(0.2)
    pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","B",6.5); _rgb(pdf,(71,85,105))
    pdf.cell(lw2,rh2,"Indicador",border="B",align="L",fill=True)
    for p in rec: pdf.cell(hcw,rh2,p["data"][-5:],border="B",align="R",fill=True)
    pdf.ln()

    for i,(cod,nome,fn,ct) in enumerate(hist_keys):
        _rgb(pdf,(248,250,252) if i%2==0 else (255,255,255),"fill")
        pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","B",6.5); _rgb(pdf,(15,23,42))
        pdf.cell(lw2,rh2,nome,border="B",align="L",fill=True)
        for p in rec:
            v = _val(p,cod); c = _row_color(ct,v); _rgb(pdf,c)
            pdf.set_font("Helvetica","B" if ct in ("saldo","indice","ciclo") else "",6.5)
            pdf.cell(hcw,rh2,fn(v),border="B",align="R",fill=True)
        pdf.ln()
    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINAS 3+ — GRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════════

def _pages_graficos(pdf, tenant, periodos, charts_config):
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin
    _page_header(pdf, tenant,
                 f"Graficos | {periodos[0]['data']} a {periodos[-1]['data']}", pw)

    chart_h = 60.0

    def _draw(title, png, with_break=False):
        nonlocal pw
        if png is None: return
        remaining = pdf.h - pdf.b_margin - pdf.get_y()
        if remaining < chart_h + 12:
            pdf.add_page()
            pw = pdf.w - pdf.l_margin - pdf.r_margin
            _page_header(pdf, tenant, "Graficos", pw)
        _section(pdf, title, pw)
        _embed_png(pdf, png, pdf.l_margin, pdf.get_y(), pw, chart_h)
        pdf.set_y(pdf.get_y() + chart_h + 8)

    _draw("QT vs QD por Semana",              _chart_qt_qd(periodos))
    _draw("Saldo QT/QD e Indice QT/QD",       _chart_saldo_indice(periodos))
    _draw("Prazos: PMP | PMV | PME | Ciclo",  _chart_prazos(periodos))

    for cfg in (charts_config or []):
        if not cfg.get("includePdf"): continue
        png = _chart_custom(cfg, periodos)
        _draw(cfg.get("name","Grafico"), png)

    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def build_relatorio_pdf(
    tenant_nome: str,
    periodos: list[dict],
    charts_config: list[dict] | None = None,
) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(12, 12, 12)

    _page_tabela(pdf, tenant_nome, periodos)
    _page_inspetor(pdf, tenant_nome, periodos)
    _pages_graficos(pdf, tenant_nome, periodos, charts_config or [])

    return bytes(pdf.output())

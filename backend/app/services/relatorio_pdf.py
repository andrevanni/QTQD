"""Gera o PDF do relatório QTQD — anexo do e-mail com 3 seções."""
from __future__ import annotations
from datetime import date
from io import BytesIO
import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from fpdf import FPDF

# ── Cores (mesmo tom do portal) ───────────────────────────────────────────────
C_DARK  = (15,  23,  42)
C_BLUE  = (37,  99,  235)
C_GOOD  = (22,  163, 74)
C_WARN  = (217, 119, 6)
C_BAD   = (220, 38,  38)
C_MUTED = (100, 116, 139)
C_SURF  = (248, 250, 252)
C_SURF2 = (241, 245, 249)
C_BDR   = (226, 232, 240)
C_WHITE = (255, 255, 255)
C_INK   = (15,  23,  42)

HEX = dict(
    blue="#2563eb", good="#16a34a", warn="#d97706", bad="#dc2626",
    muted="#64748b", surf="#f8fafc", surf2="#f1f5f9", bdr="#e2e8f0",
)
PALETTE = ["#2563eb","#16a34a","#dc2626","#d97706","#7c3aed","#0891b2","#be185d","#65a30d"]

# ── Catálogo de formatos ──────────────────────────────────────────────────────
FMT: dict[str,str] = {
    "qt_total":"currency","qd_total":"currency","saldo_qt_qd":"currency",
    "indice_qt_qd":"ratio","saldo_sem_dividas":"currency","indice_sem_dividas":"ratio",
    "saldo_sem_dividas_sem_estoque":"currency","pme":"days","prazo_medio_compra":"days",
    "prazo_venda":"days","ciclo_financiamento":"days","indice_compra_venda":"percent",
    "indice_entrada_venda":"percent","margem_bruta":"percent","excesso_total":"currency",
    "saldo_bancario":"currency","contas_receber":"currency","cartoes":"currency",
    "convenios":"currency","cheques":"currency","trade_marketing":"currency",
    "outros_qt":"currency","estoque_custo":"currency","contas_pagar":"currency",
    "fornecedores":"currency","investimentos_assumidos":"currency",
    "outras_despesas_assumidas":"currency","dividas":"currency","financiamentos":"currency",
    "tributos_atrasados":"currency","acoes_processos":"currency",
    "faturamento_previsto_mes":"currency","compras_mes":"currency","entrada_mes":"currency",
    "venda_cupom_mes":"currency","venda_custo_mes":"currency","lucro_liquido_mes":"currency",
    "pmp":"days","pmv":"days","pme_excel":"days","indice_faltas":"percent",
    "pmv_avista":"currency","pmv_30":"currency","pmv_60":"currency",
    "pmv_90":"currency","pmv_120":"currency","pmv_outros":"currency",
    "excesso_curva_a":"currency","excesso_curva_b":"currency",
    "excesso_curva_c":"currency","excesso_curva_d":"currency",
}
LABELS: dict[str,str] = {
    "qt_total":"QT Total","qd_total":"QD Total","saldo_qt_qd":"Saldo QT/QD",
    "indice_qt_qd":"Indice QT/QD","saldo_sem_dividas":"Saldo s/ Dividas",
    "ciclo_financiamento":"Ciclo Financeiro","pme":"PME","pmp":"PMP","pmv":"PMV",
    "estoque_custo":"Estoque (custo)","saldo_bancario":"Saldo Bancario",
    "contas_receber":"Contas a Receber","fornecedores":"Fornecedores","dividas":"Dividas",
    "margem_bruta":"Margem Bruta","excesso_total":"Excesso Total",
}

# ── Formatadores ──────────────────────────────────────────────────────────────
def _brl(v):
    if v is None: return "-"
    a=abs(v); s="-" if v<0 else ""
    if a>=1e6: return f"{s}R${a/1e6:.1f}M".replace(".",",")
    if a>=1e3: return f"{s}R${a/1e3:.1f}K".replace(".",",")
    return f"{s}R${a:.0f}"

def _ratio(v): return f"{v:.2f}x".replace(".",",") if v is not None else "-"
def _days(v):  return f"{v:.0f}d"                  if v is not None else "-"
def _pct(v):   return f"{v*100:.1f}%".replace(".",",") if v is not None else "-"

def _fmt(v, fmt):
    if fmt=="ratio":   return _ratio(v)
    if fmt=="days":    return _days(v)
    if fmt=="percent": return _pct(v)
    return _brl(v)

def _mpl_tick(v, _, fmt="currency"):
    if fmt=="days":    return f"{v:.0f}d"
    if fmt=="percent": return f"{v*100:.0f}%"
    if fmt=="ratio":   return f"{v:.1f}x"
    a=abs(v); s="-" if v<0 else ""
    if a>=1e6: return f"{s}{a/1e6:.1f}M"
    if a>=1e3: return f"{s}{a/1e3:.0f}K"
    return f"{s}{a:.0f}"

# ── Lookup ────────────────────────────────────────────────────────────────────
def _ind(indicadores, key):
    for i in indicadores:
        if i.codigo == key: return i.valor
    return None

def _val(p, key):
    if key == "_pme":
        raw = p.get("valores", {})
        e = float(raw.get("pme_excel") or 0)
        return e if e > 0 else _ind(p["indicadores"], "pme")
    v = _ind(p["indicadores"], key)
    if v is not None: return v
    raw = p.get("valores", {})
    r = raw.get(key)
    if r is None: return None
    f = float(r)
    return f if f > 0 else None

# ── Cores condicionais ────────────────────────────────────────────────────────
def _kpi_color(key, v):
    if key == "indice_qt_qd":
        return C_GOOD if (v and v>=1.5) else (C_WARN if (v and v>=1.0) else C_BAD)
    if key in ("saldo_qt_qd","saldo_sem_dividas"):
        return C_GOOD if (v is not None and v>=0) else C_BAD
    if key == "ciclo_financiamento":
        return C_GOOD if (v and v>=10) else (C_WARN if (v and v>=-10) else C_BAD)
    return C_BLUE

def _sem_color(key, v):
    if v is None: return C_MUTED
    if key=="indice_qt_qd": return C_GOOD if v>=1.5 else (C_WARN if v>=1.0 else C_BAD)
    if key=="saldo_qt_qd":  return C_GOOD if v>=0   else C_BAD
    if key=="pmp":  return C_GOOD if v>60  else (C_WARN if v>30  else C_BAD)
    if key=="pmv":  return C_GOOD if v<60  else (C_WARN if v<90  else C_BAD)
    if key=="_pme": return C_GOOD if v<90  else (C_WARN if v<120 else C_BAD)
    if key=="ciclo_financiamento": return C_GOOD if v>=10 else (C_WARN if v>=-10 else C_BAD)
    return C_MUTED

def _row_color(ctype, v):
    if ctype=="saldo":
        return C_GOOD if (v is not None and v>=0) else C_BAD
    if ctype=="indice":
        if v is None:   return C_MUTED
        if v>=1.5:      return C_GOOD
        if v>=1.0:      return C_WARN
        return C_BAD
    if ctype=="ciclo":
        if v is None:   return C_MUTED
        return C_GOOD if v>=10 else (C_WARN if v>=-10 else C_BAD)
    return C_INK

# ── Helpers fpdf2 ─────────────────────────────────────────────────────────────
def _rgb(pdf, c, t="text"):
    r,g,b=c
    if t=="text": pdf.set_text_color(r,g,b)
    elif t=="fill": pdf.set_fill_color(r,g,b)
    elif t=="draw": pdf.set_draw_color(r,g,b)

def _hdr(pdf, tenant, subtitle, pw):
    _rgb(pdf, C_DARK, "fill")
    pdf.rect(0,0,pdf.w,18,style="F")
    pdf.set_xy(pdf.l_margin,3)
    pdf.set_font("Helvetica","B",12)
    _rgb(pdf, C_WHITE)
    pdf.cell(pw*0.65,7,f"QTQD | {tenant}",align="L")
    pdf.set_font("Helvetica","",8)
    _rgb(pdf,(191,219,254))
    pdf.cell(pw*0.35,7,subtitle,align="R")
    pdf.ln(20)

def _sec(pdf, title, pw):
    _rgb(pdf,C_BLUE,"fill")
    pdf.rect(pdf.l_margin,pdf.get_y(),3,5,style="F")
    pdf.set_xy(pdf.l_margin+5,pdf.get_y())
    pdf.set_font("Helvetica","B",8)
    _rgb(pdf,C_INK)
    pdf.cell(pw-5,5,title.upper(),align="L")
    pdf.ln(8)

def _footer(pdf):
    pdf.set_y(-10)
    pdf.set_font("Helvetica","I",6)
    _rgb(pdf,C_MUTED)
    pdf.cell(0,4,"Service Farma - Grupo A3 - Direitos Reservados  |  Enviado automaticamente pelo QTQD",align="C")

# ── Matplotlib helpers ────────────────────────────────────────────────────────
def _style(ax, title=""):
    ax.set_facecolor("#f8fafc")
    for sp in ["top","right"]: ax.spines[sp].set_visible(False)
    for sp in ["left","bottom"]: ax.spines[sp].set_color("#e2e8f0")
    ax.tick_params(colors="#64748b",labelsize=7)
    ax.grid(axis="y",color="#e2e8f0",linewidth=0.5,linestyle="--",zorder=0)
    ax.set_axisbelow(True)
    if title: ax.set_title(title,fontsize=8,color="#0f172a",fontweight="bold",pad=5)

def _png(fig):
    buf=BytesIO()
    fig.savefig(buf,format="png",dpi=130,bbox_inches="tight",facecolor="white",edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def _embed(pdf, png, x, y, w, h):
    pdf.image(BytesIO(png),x=x,y=y,w=w,h=h,type="PNG")

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — TABELA DE SEMANAS
# ═══════════════════════════════════════════════════════════════════════════════
_TABELA = [
    ("qt_total",            "QT Total",         _brl,   "money"),
    ("qd_total",            "QD Total",         _brl,   "money"),
    ("saldo_qt_qd",         "Saldo QT/QD",      _brl,   "saldo"),
    ("indice_qt_qd",        "Indice QT/QD",     _ratio, "indice"),
    ("saldo_sem_dividas",   "Saldo s/ Dividas", _brl,   "saldo"),
    ("_pme",                "PME",              _days,  None),
    ("pmp",                 "PMP",              _days,  None),
    ("pmv",                 "PMV",              _days,  None),
    ("ciclo_financiamento", "Ciclo Financeiro", _days,  "ciclo"),
]

def _page_tabela(pdf, tenant, periodos):
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin

    _rgb(pdf,C_DARK,"fill"); pdf.rect(0,0,pdf.w,26,style="F")
    pdf.set_xy(pdf.l_margin,5); pdf.set_font("Helvetica","B",15)
    _rgb(pdf,C_WHITE); pdf.cell(pw*0.75,8,f"Relatorio QTQD - {tenant}",align="L")
    pdf.set_font("Helvetica","",9); _rgb(pdf,(191,219,254))
    pdf.set_xy(pdf.l_margin,14)
    pdf.cell(pw,7,f"Gerado em {date.today().strftime('%d/%m/%Y')}",align="L")
    pdf.ln(18)

    n=len(periodos); lw=46.0; dw=(pw-lw)/max(n,1); rh=7.5

    pdf.set_font("Helvetica","B",8); _rgb(pdf,C_SURF2,"fill")
    _rgb(pdf,C_MUTED); _rgb(pdf,C_BDR,"draw")
    pdf.set_x(pdf.l_margin)
    pdf.cell(lw,rh,"Indicador",border="B",align="L",fill=True)
    for p in periodos:
        pdf.cell(dw,rh,p["data"],border="B",align="R",fill=True)
    pdf.ln()

    for i,(cod,nome,fn,ct) in enumerate(_TABELA):
        _rgb(pdf,C_SURF if i%2==0 else C_WHITE,"fill")
        pdf.set_font("Helvetica","",8); _rgb(pdf,C_INK)
        pdf.set_x(pdf.l_margin)
        pdf.cell(lw,rh,nome,border="B",align="L",fill=True)
        for p in periodos:
            v=_val(p,cod)
            c=_row_color(ct,v)
            _rgb(pdf,c)
            pdf.set_font("Helvetica","B" if ct in ("saldo","indice","ciclo") else "",8)
            pdf.cell(dw,rh,fn(v),border="B",align="R",fill=True)
        pdf.ln()

    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — INSPETOR IA FINANCEIRO
# ═══════════════════════════════════════════════════════════════════════════════
_KPIS = [
    ("indice_qt_qd",        "INDICE QT/QD",    _ratio, None),
    ("saldo_qt_qd",         "SALDO QT/QD",     _brl,   None),
    ("saldo_sem_dividas",   "SALDO S/ DIVIDAS",_brl,   None),
    ("ciclo_financiamento", "CICLO FINANCEIRO",_days,  None),
]
_SEM = [
    ("indice_qt_qd","LIQUIDEZ", _ratio,"Indice >= 1,5x"),
    ("saldo_qt_qd", "SALDO",    _brl,  "Positivo"),
    ("pmp",         "PMP",      _days, "> 60 dias"),
    ("pmv",         "PMV",      _days, "< 60 dias"),
    ("_pme",        "PME",      _days, "< 90 dias"),
    ("ciclo_financiamento","CICLO",_days,">= +10 dias"),
]

def _page_inspetor(pdf, tenant, periodos):
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin
    latest = periodos[-1]

    _hdr(pdf, tenant, f"Inspetor IA Financeiro  |  Semana {latest['data']}", pw)
    _sec(pdf, "Inspetor IA Financeiro", pw)

    # KPIs
    bw=(pw-9)/4; bh=26; by=pdf.get_y()
    for i,(k,lbl,fn,_) in enumerate(_KPIS):
        v=_val(latest,k); c=_kpi_color(k,v); bx=pdf.l_margin+i*(bw+3)
        _rgb(pdf,C_SURF,"fill"); _rgb(pdf,c,"draw")
        pdf.set_line_width(0.5); pdf.rect(bx,by,bw,bh,style="FD")
        _rgb(pdf,c,"fill"); pdf.rect(bx,by,2.5,bh,style="F")
        pdf.set_xy(bx+5,by+4); pdf.set_font("Helvetica","B",6)
        _rgb(pdf,C_MUTED); pdf.cell(bw-7,4,lbl,align="L")
        pdf.set_xy(bx+5,by+11); pdf.set_font("Helvetica","B",14)
        _rgb(pdf,c); pdf.cell(bw-7,9,fn(v) if v is not None else "-",align="L")
        if len(periodos)>=2:
            pv=_val(periodos[-2],k)
            if v and pv and pv!=0:
                d=((v-pv)/abs(pv))*100
                dc=C_GOOD if d>=0 else C_BAD
                pdf.set_xy(bx+5,by+21); pdf.set_font("Helvetica","",6)
                _rgb(pdf,dc)
                pdf.cell(bw-7,4,f"{'+'if d>=0 else ''}{d:.1f}% vs anterior",align="L")
    pdf.set_y(by+bh+8)

    # Semáforo
    _sec(pdf,"Semaforo IA Financeiro",pw)
    cw=pw/6; sh=20; sy=pdf.get_y()
    for i,(k,lbl,fn,meta) in enumerate(_SEM):
        v=_val(latest,k); c=_sem_color(k,v)
        soft=tuple(min(255,x+210) for x in c)
        bx=pdf.l_margin+i*cw
        _rgb(pdf,soft,"fill"); _rgb(pdf,c,"draw")
        pdf.set_line_width(0.5); pdf.rect(bx,sy,cw-1,sh,style="FD")
        pdf.set_xy(bx,sy+2); pdf.set_font("Helvetica","B",6)
        _rgb(pdf,C_MUTED); pdf.cell(cw-1,4,lbl,align="C")
        pdf.set_xy(bx,sy+8); pdf.set_font("Helvetica","B",11)
        _rgb(pdf,c); pdf.cell(cw-1,6,fn(v) if v is not None else "-",align="C")
        pdf.set_xy(bx,sy+15); pdf.set_font("Helvetica","",5.5)
        _rgb(pdf,C_MUTED); pdf.cell(cw-1,4,meta,align="C")
    pdf.set_y(sy+sh+8)

    # Tabela histórica (últimas 8 semanas)
    _sec(pdf,"Evolucao Recente (ultimas semanas)",pw)
    hist=[
        ("qt_total",           "QT Total",  _brl,   "money"),
        ("qd_total",           "QD Total",  _brl,   "money"),
        ("saldo_qt_qd",        "Saldo",     _brl,   "saldo"),
        ("indice_qt_qd",       "Indice",    _ratio, "indice"),
        ("_pme",               "PME",       _days,  None),
        ("pmp",                "PMP",       _days,  None),
        ("pmv",                "PMV",       _days,  None),
        ("ciclo_financiamento","Ciclo",     _days,  "ciclo"),
    ]
    rec=periodos[-8:]; lw2=34; hcw=(pw-lw2)/max(len(rec),1); rh2=6

    _rgb(pdf,C_SURF2,"fill"); _rgb(pdf,C_BDR,"draw"); pdf.set_line_width(0.2)
    pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","B",6.5); _rgb(pdf,C_MUTED)
    pdf.cell(lw2,rh2,"Indicador",border="B",align="L",fill=True)
    for p in rec:
        pdf.cell(hcw,rh2,p["data"][-5:],border="B",align="R",fill=True)
    pdf.ln()

    for i,(cod,nome,fn,ct) in enumerate(hist):
        _rgb(pdf,C_SURF if i%2==0 else C_WHITE,"fill")
        pdf.set_x(pdf.l_margin); pdf.set_font("Helvetica","B",6.5); _rgb(pdf,C_INK)
        pdf.cell(lw2,rh2,nome,border="B",align="L",fill=True)
        for p in rec:
            v=_val(p,cod); c=_row_color(ct,v)
            _rgb(pdf,c)
            pdf.set_font("Helvetica","B" if ct in ("saldo","indice","ciclo") else "",6.5)
            pdf.cell(hcw,rh2,fn(v),border="B",align="R",fill=True)
        pdf.ln()

    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — GRÁFICOS DE EVOLUÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
def _chart_evolucao(periodos, pw_mm):
    labels=[p["data"][-5:] for p in periodos]
    qt =[_val(p,"qt_total")       or 0 for p in periodos]
    qd =[_val(p,"qd_total")       or 0 for p in periodos]
    sal=[_val(p,"saldo_qt_qd")    or 0 for p in periodos]
    idx=[_val(p,"indice_qt_qd")   or 0 for p in periodos]
    x=list(range(len(labels))); w=pw_mm/25.4

    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(w,3.0))
    fig.patch.set_facecolor("white")

    bw=0.35
    ax1.bar([i-bw/2 for i in x],qt,width=bw,label="QT",color=HEX["blue"],alpha=0.85,zorder=3)
    ax1.bar([i+bw/2 for i in x],qd,width=bw,label="QD",color=HEX["bad"], alpha=0.85,zorder=3)
    ax1.set_xticks(x); ax1.set_xticklabels(labels,rotation=40,ha="right",fontsize=6)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:_mpl_tick(v,_,"currency")))
    ax1.legend(fontsize=7,framealpha=0.5,loc="upper left"); _style(ax1,"QT vs QD")

    colors=[HEX["good"] if v>=0 else HEX["bad"] for v in sal]
    ax2.bar(x,sal,color=colors,alpha=0.85,zorder=3,label="Saldo")
    ax2r=ax2.twinx()
    ax2r.plot(x,idx,color=HEX["blue"],lw=2,marker="o",ms=4,label="Indice",zorder=5)
    ax2r.axhline(1.0,color=HEX["warn"],lw=0.8,ls="--",alpha=0.7)
    ax2r.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:f"{v:.1f}x"))
    ax2r.tick_params(colors="#64748b",labelsize=6); ax2r.spines["top"].set_visible(False)
    ax2.set_xticks(x); ax2.set_xticklabels(labels,rotation=40,ha="right",fontsize=6)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:_mpl_tick(v,_,"currency")))
    h1,l1=ax2.get_legend_handles_labels(); h2,l2=ax2r.get_legend_handles_labels()
    ax2.legend(h1+h2,l1+l2,fontsize=7,framealpha=0.5,loc="upper left"); _style(ax2,"Saldo & Indice QT/QD")

    fig.tight_layout(pad=0.8); return _png(fig)

def _chart_prazos(periodos, pw_mm):
    labels=[p["data"][-5:] for p in periodos]
    pmp =[_val(p,"pmp")               or 0 for p in periodos]
    pmv =[_val(p,"pmv")               or 0 for p in periodos]
    pme =[_val(p,"_pme")              or 0 for p in periodos]
    ciclo=[(_val(p,"ciclo_financiamento") or float("nan")) for p in periodos]
    x=list(range(len(labels))); w=pw_mm/25.4

    fig,ax=plt.subplots(figsize=(w,2.8))
    fig.patch.set_facecolor("white")
    ax.plot(x,pmp, color=HEX["blue"],lw=2,marker="o",ms=3,label="PMP")
    ax.plot(x,pmv, color=HEX["warn"],lw=2,marker="s",ms=3,label="PMV")
    ax.plot(x,pme, color=HEX["good"],lw=2,marker="^",ms=3,label="PME")
    ax.plot(x,ciclo,color=HEX["bad"], lw=1.5,marker="D",ms=3,ls="--",label="Ciclo")
    ax.axhline(0,color="#e2e8f0",lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels(labels,rotation=40,ha="right",fontsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_:f"{v:.0f}d"))
    ax.legend(fontsize=7,framealpha=0.5,ncol=4,loc="upper left"); _style(ax,"Prazos: PMP | PMV | PME | Ciclo")
    fig.tight_layout(pad=0.8); return _png(fig)

def _page_graficos_evolucao(pdf, tenant, periodos):
    pdf.add_page()
    pw=pdf.w-pdf.l_margin-pdf.r_margin
    _hdr(pdf,tenant,f"Graficos de Evolucao  |  {periodos[0]['data']} a {periodos[-1]['data']}",pw)

    _sec(pdf,"Evolucao QT, QD, Saldo e Indice QT/QD",pw)
    h=58; png=_chart_evolucao(periodos,pw)
    _embed(pdf,png,pdf.l_margin,pdf.get_y(),pw,h)
    pdf.set_y(pdf.get_y()+h+6)

    _sec(pdf,"Prazos Operacionais: PMP | PMV | PME | Ciclo Financeiro",pw)
    h2=52; png2=_chart_prazos(periodos,pw)
    _embed(pdf,png2,pdf.l_margin,pdf.get_y(),pw,h2)

    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# PÁGINAS 4+ — GRÁFICOS PERSONALIZADOS (includePdf=true)
# ═══════════════════════════════════════════════════════════════════════════════
def _chart_custom(cfg, periodos, pw_mm):
    keys=cfg.get("fields",[]); count=max(1,int(cfg.get("count",12)))
    pts=periodos[-count:] if len(periodos)>count else periodos
    if not pts or not keys: return None
    labels=[p["data"][-5:] for p in pts]; x=list(range(len(labels)))
    series=[]
    for k in keys:
        vals=[_val(p,k) for p in pts]
        if all(v is None for v in vals): continue
        series.append({"key":k,"vals":vals,"fmt":FMT.get(k,"currency"),"color":PALETTE[len(series)%len(PALETTE)]})
    if not series: return None
    pf=series[0]["fmt"]; w=pw_mm/25.4; ct=cfg.get("type","line")

    fig,ax=plt.subplots(figsize=(w,2.8)); fig.patch.set_facecolor("white")
    for s in series:
        lbl=LABELS.get(s["key"],s["key"].replace("_"," ").title())
        vals=[v if v is not None else float("nan") for v in s["vals"]]
        if ct=="bar":
            bw=0.6/max(len(series),1); off=(series.index(s)-len(series)/2+0.5)*bw
            ax.bar([xi+off for xi in x],vals,width=bw,color=s["color"],alpha=0.85,label=lbl,zorder=3)
        else:
            ax.plot(x,vals,color=s["color"],lw=2,marker="o",ms=3,label=lbl,zorder=3)
    ax.set_xticks(x); ax.set_xticklabels(labels,rotation=40,ha="right",fontsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_,f=pf:_mpl_tick(v,_,f)))
    if len(series)>1: ax.legend(fontsize=7,framealpha=0.5,loc="best",ncol=min(len(series),4))
    _style(ax,cfg.get("name","Grafico")); fig.tight_layout(pad=0.8); return _png(fig)

def _pages_graficos_custom(pdf, tenant, periodos, charts_config):
    pdf_charts=[c for c in (charts_config or []) if c.get("includePdf")]
    if not pdf_charts: return
    pdf.add_page()
    pw=pdf.w-pdf.l_margin-pdf.r_margin
    _hdr(pdf,tenant,"Graficos Personalizados",pw)
    _sec(pdf,"Graficos configurados para o relatorio PDF",pw)

    h=62; first=True
    for cfg in pdf_charts:
        if not first and (pdf.h-pdf.b_margin-pdf.get_y())<h+12:
            pdf.add_page(); pw=pdf.w-pdf.l_margin-pdf.r_margin
            _hdr(pdf,tenant,"Graficos Personalizados",pw); pdf.ln(2)
        first=False
        png=_chart_custom(cfg,periodos,pw)
        if png is None: continue
        _embed(pdf,png,pdf.l_margin,pdf.get_y(),pw,h)
        pdf.set_y(pdf.get_y()+h+8)

    _footer(pdf)

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def build_relatorio_pdf(
    tenant_nome: str,
    periodos: list[dict],
    charts_config: list[dict] | None = None,
) -> bytes:
    pdf=FPDF(orientation="L",unit="mm",format="A4")
    pdf.set_auto_page_break(auto=True,margin=12)
    pdf.set_margins(12,12,12)

    _page_tabela(pdf, tenant_nome, periodos)
    _page_inspetor(pdf, tenant_nome, periodos)
    _page_graficos_evolucao(pdf, tenant_nome, periodos)
    _pages_graficos_custom(pdf, tenant_nome, periodos, charts_config or [])

    return bytes(pdf.output())

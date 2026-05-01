"""Monta o HTML do e-mail de relatório QTQD — layout compatível com clientes de e-mail."""
from __future__ import annotations
from datetime import datetime


def _fmt_brl(v: float | None) -> str:
    if v is None:
        return "—"
    return f"R$ {v:_.2f}".replace("_", ".").replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_ratio(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:.2f}x"


def _fmt_days(v: float | None) -> str:
    if v is None:
        return "—"
    return f"{v:.0f} dias"


def _color_saldo(v: float | None) -> str:
    if v is None:
        return "#374151"
    return "#16a34a" if v >= 0 else "#dc2626"


def _color_indice(v: float | None) -> str:
    if v is None:
        return "#374151"
    if v >= 1.5:
        return "#16a34a"
    if v >= 1.0:
        return "#d97706"
    return "#dc2626"


SF_LOGO_URL = "https://qtqd-vt2a.vercel.app/cliente/assets/logo_alta.jpg"

# Igual ao portal: usa pmv/pmp raw e pme_excel preferencial
INDICADORES_SHOW = [
    ("qt_total",            "QT Total",          _fmt_brl,   None),
    ("qd_total",            "QD Total",          _fmt_brl,   None),
    ("saldo_qt_qd",         "Saldo QT/QD",       _fmt_brl,   _color_saldo),
    ("indice_qt_qd",        "Índice QT/QD",      _fmt_ratio, _color_indice),
    ("saldo_sem_dividas",   "Saldo s/ dívidas",  _fmt_brl,   _color_saldo),
    ("_pme",                "PME",               _fmt_days,  None),
    ("pmp",                 "PMP",               _fmt_days,  None),
    ("pmv",                 "PMV",               _fmt_days,  None),
    ("ciclo_financiamento", "Ciclo Financeiro",  _fmt_days,  None),
]


def _get_ind(indicadores: list, codigo: str) -> float | None:
    for i in indicadores:
        if i.codigo == codigo:
            return i.valor
    return None


def _get_period_val(p: dict, key: str) -> float | None:
    """Busca valor do período: campos raw (pmv, pmp, pme_excel) têm prioridade."""
    if key == "_pme":
        # Preferência: pme_excel (input do ERP) > pme calculado
        raw = p.get("valores", {})
        pme_excel = float(raw.get("pme_excel") or 0)
        if pme_excel > 0:
            return pme_excel
        return _get_ind(p["indicadores"], "pme")
    # Campos que vêm dos valores raw (inputs do usuário)
    _RAW_FIELDS = {"pmp", "pmv", "pme_excel"}
    if key in _RAW_FIELDS:
        raw = p.get("valores", {})
        val = raw.get(key)
        if val is not None:
            f = float(val)
            return f if f > 0 else None
        return None
    # Campos calculados
    return _get_ind(p["indicadores"], key)


def build_relatorio_html(
    tenant_nome: str,
    portal_url: str,
    periodos: list[dict],
    incluir_inspetor: bool = False,
    incluir_graficos: bool = False,
    logo_cliente_url: str | None = None,
) -> str:
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    n = len(periodos)

    # ── Logo do cliente ───────────────────────────────────────────────────────
    if logo_cliente_url:
        logo_block = (
            f'<img src="{logo_cliente_url}" width="56" height="56" alt="{tenant_nome}" '
            f'style="width:56px;height:56px;border-radius:10px;object-fit:contain;'
            f'background:#ffffff;padding:4px;display:block;margin-bottom:10px;">'
        )
    else:
        initials = "".join(w[0].upper() for w in tenant_nome.split()[:2])
        logo_block = (
            f'<div style="width:56px;height:56px;border-radius:10px;'
            f'background:rgba(255,255,255,.20);display:inline-block;line-height:56px;'
            f'text-align:center;font-size:20px;font-weight:700;color:#fff;'
            f'margin-bottom:10px;">{initials}</div>'
        )

    # ── Colunas de data ───────────────────────────────────────────────────────
    header_cells = "".join(
        f'<td style="padding:8px 10px;text-align:right;font-size:11px;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:0.05em;color:#475569;'
        f'background:#f1f5f9;border-bottom:2px solid #e2e8f0;white-space:nowrap;">'
        f'{p["data"]}</td>'
        for p in periodos
    )

    # ── Linhas de dados ───────────────────────────────────────────────────────
    rows_html = ""
    for i, (cod, nome, fmt_fn, color_fn) in enumerate(INDICADORES_SHOW):
        bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
        cells = ""
        for p in periodos:
            v = _get_period_val(p, cod)
            color = color_fn(v) if color_fn else "#374151"
            weight = "700" if color_fn else "400"
            cells += (
                f'<td style="padding:8px 10px;font-size:12px;color:{color};'
                f'font-weight:{weight};border-bottom:1px solid #f1f5f9;'
                f'text-align:right;white-space:nowrap;">{fmt_fn(v)}</td>'
            )
        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td style="padding:8px 10px;font-size:12px;font-weight:600;color:#475569;'
            f'border-bottom:1px solid #f1f5f9;white-space:nowrap;">{nome}</td>'
            f'{cells}</tr>'
        )

    # ── Blocos opcionais ──────────────────────────────────────────────────────
    graficos_block = ""
    if incluir_graficos:
        graficos_block = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">'
            f'<tr><td style="padding:14px 20px;background:#f0f9ff;border-radius:8px;'
            f'border:1px solid #bae6fd;">'
            f'<p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#0369a1;">📊 Gráficos</p>'
            f'<p style="margin:0;font-size:13px;color:#0c4a6e;">Acesse '
            f'<a href="{portal_url}" style="color:#2563eb;">{portal_url}</a> '
            f'para visualizar os gráficos configurados.</p>'
            f'</td></tr></table>'
        )

    inspetor_block = ""
    if incluir_inspetor:
        inspetor_block = (
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:20px;">'
            f'<tr><td style="padding:14px 20px;background:#fefce8;border-radius:8px;'
            f'border:1px solid #fde68a;">'
            f'<p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#92400e;">🤖 Inspetor IA</p>'
            f'<p style="margin:0;font-size:13px;color:#78350f;">Acesse o portal para a análise completa: '
            f'<a href="{portal_url}" style="color:#2563eb;">{portal_url}</a></p>'
            f'</td></tr></table>'
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relatório QTQD — {tenant_nome}</title>
</head>
<body style="margin:0;padding:20px;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;">

  <!-- Cabeçalho -->
  <tr><td style="background:#0f172a;border-radius:10px 10px 0 0;padding:24px 28px;">
    {logo_block}
    <p style="margin:0 0 2px;font-size:10px;font-weight:600;letter-spacing:0.12em;
       text-transform:uppercase;color:#93c5fd;">QTQD — Saúde Financeira Semanal</p>
    <h1 style="margin:0 0 4px;font-size:20px;font-weight:700;color:#ffffff;">{tenant_nome}</h1>
    <p style="margin:0;font-size:13px;color:#bfdbfe;">
      Relatório de {n} período{"s" if n != 1 else ""} · Gerado em {now_str}
    </p>
  </td></tr>

  <!-- Barra de meta -->
  <tr><td style="background:#1e3a8a;padding:8px 28px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td style="font-size:12px;color:#bfdbfe;">📅 {n} retrato{"s" if n != 1 else ""} incluído{"s" if n != 1 else ""}</td>
      <td align="right"><a href="{portal_url}" style="font-size:12px;color:#93c5fd;text-decoration:none;">Acessar portal →</a></td>
    </tr>
    </table>
  </td></tr>

  <!-- Tabela de indicadores -->
  <tr><td style="background:#ffffff;border-radius:0 0 10px 10px;
      box-shadow:0 4px 6px rgba(0,0,0,0.07);overflow:hidden;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <thead>
        <tr style="background:#f1f5f9;">
          <th style="padding:8px 10px;text-align:left;font-size:11px;font-weight:600;
              text-transform:uppercase;letter-spacing:0.05em;color:#475569;
              background:#f1f5f9;border-bottom:2px solid #e2e8f0;white-space:nowrap;">
            Indicador
          </th>
          {header_cells}
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </td></tr>

  <!-- Blocos opcionais -->
  {f'<tr><td>{graficos_block}</td></tr>' if graficos_block else ''}
  {f'<tr><td>{inspetor_block}</td></tr>' if inspetor_block else ''}

  <!-- Rodapé -->
  <tr><td style="padding:20px 0 0;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td width="52" valign="middle">
        <img src="{SF_LOGO_URL}" width="44" height="44" alt="Service Farma"
          style="width:44px;height:44px;object-fit:contain;border-radius:10px;
          background:#fff;padding:3px;border:1px solid #e2e8f0;display:block;">
      </td>
      <td style="padding-left:12px;" valign="middle">
        <p style="margin:0;font-size:12px;font-weight:700;color:#475569;">
          Service Farma · Grupo A3 · Direitos Reservados
        </p>
        <p style="margin:3px 0 0;font-size:11px;color:#94a3b8;">
          Enviado automaticamente pelo sistema QTQD. Não responda a esta mensagem.
        </p>
      </td>
    </tr>
    </table>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

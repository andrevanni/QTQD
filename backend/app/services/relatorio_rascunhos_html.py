"""
Template HTML do e-mail de Acompanhamento de Rascunhos QTQD.
Mostra o status de cada lançamento dos últimos meses:
  - quais estão fechados/finalizados (confirmados)
  - quais ainda são rascunho (pendentes)
"""
from __future__ import annotations
from datetime import date, datetime


SF_LOGO_URL = "https://qtqd-vt2a.vercel.app/cliente/assets/logo_alta.jpg"

DIAS_SEMANA = {1: "segunda-feira", 2: "terça-feira", 3: "quarta-feira",
               4: "quinta-feira",  5: "sexta-feira",  6: "sábado", 7: "domingo"}


def _fmt_brl_short(v: float | None) -> str:
    if v is None:
        return "—"
    abs_v = abs(v)
    if abs_v >= 1_000_000:
        return f"R$ {v/1_000_000:.1f}M".replace(".", ",")
    if abs_v >= 1_000:
        return f"R$ {v/1_000:.1f}K".replace(".", ",")
    return f"R$ {v:_.0f}".replace("_", ".")


def _status_badge(status: str) -> str:
    if status in ("fechada", "finalizado"):
        return (
            '<span style="display:inline-block;padding:2px 8px;border-radius:12px;'
            'font-size:10px;font-weight:700;background:#dcfce7;color:#166534;'
            'text-transform:uppercase;letter-spacing:0.05em;">✓ Confirmado</span>'
        )
    return (
        '<span style="display:inline-block;padding:2px 8px;border-radius:12px;'
        'font-size:10px;font-weight:700;background:#fef9c3;color:#854d0e;'
        'text-transform:uppercase;letter-spacing:0.05em;">⚠ Rascunho</span>'
    )


def _row_bg(status: str, idx: int) -> str:
    if status == "rascunho":
        return "#fffbeb"
    return "#f8fafc" if idx % 2 == 0 else "#ffffff"


def build_acompanhamento_html(
    tenant_nome: str,
    portal_url: str,
    registros: list[dict],          # {semana_referencia, status, qt_total, qd_total, saldo}
    logo_cliente_url: str | None = None,
    meses: int = 3,
) -> str:
    """
    registros: lista de dicts com chaves:
      - semana_referencia: str (YYYY-MM-DD)
      - status: str ('rascunho' | 'fechada' | 'finalizado')
      - qt_total: float | None
      - qd_total: float | None
      - saldo: float | None
    """
    now_str  = datetime.now().strftime("%d/%m/%Y %H:%M")
    hoje     = date.today()

    # Contadores
    total    = len(registros)
    n_rasc   = sum(1 for r in registros if r["status"] == "rascunho")
    n_conf   = total - n_rasc

    # Alerta no cabeçalho
    if n_rasc == 0:
        alert_color = "#16a34a"
        alert_icon  = "✅"
        alert_msg   = f"Todos os {total} lançamentos dos últimos {meses} meses estão confirmados."
    elif n_rasc == 1:
        alert_color = "#d97706"
        alert_icon  = "⚠️"
        alert_msg   = "1 lançamento ainda está em rascunho — revise e feche para incluir nas análises."
    else:
        alert_color = "#dc2626"
        alert_icon  = "⚠️"
        alert_msg   = f"{n_rasc} lançamentos ainda estão em rascunho — revise e feche para incluir nas análises."

    # Logo
    if logo_cliente_url:
        logo_block = (
            f'<img src="{logo_cliente_url}" width="56" height="56" alt="{tenant_nome}" '
            f'style="width:56px;height:56px;border-radius:10px;object-fit:contain;'
            f'background:#ffffff;padding:4px;display:block;margin-bottom:10px;">'
        )
    else:
        initials = "".join(w[0].upper() for w in tenant_nome.split()[:2])
        logo_block = (
            f'<div style="width:56px;height:56px;border-radius:10px;background:rgba(255,255,255,.20);'
            f'display:inline-block;line-height:56px;text-align:center;font-size:20px;'
            f'font-weight:700;color:#fff;margin-bottom:10px;">{initials}</div>'
        )

    # Tabela de lançamentos
    rows_html = ""
    for idx, r in enumerate(registros):
        try:
            d = date.fromisoformat(r["semana_referencia"])
            data_fmt = d.strftime("%d/%m/%Y")
        except Exception:
            data_fmt = r["semana_referencia"]

        bg = _row_bg(r["status"], idx)
        qt  = _fmt_brl_short(r.get("qt_total"))
        qd  = _fmt_brl_short(r.get("qd_total"))
        saldo = r.get("saldo")
        saldo_color = "#16a34a" if (saldo or 0) >= 0 else "#dc2626"
        saldo_fmt = _fmt_brl_short(saldo)

        # Semanas antigas em rascunho: highlight mais forte
        is_old_draft = r["status"] == "rascunho"
        border_left = "border-left:3px solid #f59e0b;" if is_old_draft else ""

        rows_html += f"""
        <tr style="background:{bg};{border_left}">
          <td style="padding:8px 10px;font-size:12px;color:#374151;white-space:nowrap;">{data_fmt}</td>
          <td style="padding:8px 10px;">{_status_badge(r["status"])}</td>
          <td style="padding:8px 10px;font-size:12px;color:#374151;text-align:right;">{qt}</td>
          <td style="padding:8px 10px;font-size:12px;color:#374151;text-align:right;">{qd}</td>
          <td style="padding:8px 10px;font-size:12px;font-weight:700;color:{saldo_color};text-align:right;">{saldo_fmt}</td>
        </tr>"""

    if not rows_html:
        rows_html = (
            '<tr><td colspan="5" style="padding:20px;text-align:center;'
            'color:#94a3b8;font-size:13px;">Nenhum lançamento nos últimos '
            f'{meses} meses.</td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Acompanhamento de Rascunhos — {tenant_nome}</title>
</head>
<body style="margin:0;padding:20px;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" border="0" style="max-width:640px;">

  <!-- Cabeçalho -->
  <tr><td style="background:#0f172a;border-radius:10px 10px 0 0;padding:24px 28px;">
    {logo_block}
    <p style="margin:0 0 2px;font-size:10px;font-weight:600;letter-spacing:0.12em;
       text-transform:uppercase;color:#93c5fd;">QTQD — Acompanhamento de Lançamentos</p>
    <h1 style="margin:0 0 4px;font-size:20px;font-weight:700;color:#ffffff;">{tenant_nome}</h1>
    <p style="margin:0;font-size:13px;color:#bfdbfe;">
      Últimos {meses} meses · Gerado em {now_str}
    </p>
  </td></tr>

  <!-- Barra de meta -->
  <tr><td style="background:#1e3a8a;padding:8px 28px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td style="font-size:12px;color:#bfdbfe;">
        {n_conf} confirmados · <span style="color:#fde68a;">{n_rasc} rascunhos</span>
      </td>
      <td align="right"><a href="{portal_url}" style="font-size:12px;color:#93c5fd;text-decoration:none;">Acessar portal →</a></td>
    </tr></table>
  </td></tr>

  <!-- Alerta resumo -->
  <tr><td style="background:#ffffff;padding:16px 28px;border-bottom:1px solid #e2e8f0;">
    <p style="margin:0;font-size:13px;color:{alert_color};font-weight:600;">
      {alert_icon} {alert_msg}
    </p>
  </td></tr>

  <!-- Tabela de lançamentos -->
  <tr><td style="background:#ffffff;border-radius:0 0 10px 10px;
      box-shadow:0 4px 6px rgba(0,0,0,0.07);overflow:hidden;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <thead>
        <tr style="background:#f1f5f9;border-bottom:2px solid #e2e8f0;">
          <th style="padding:8px 10px;text-align:left;font-size:11px;font-weight:600;color:#475569;
              text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;">Semana</th>
          <th style="padding:8px 10px;text-align:left;font-size:11px;font-weight:600;color:#475569;
              text-transform:uppercase;letter-spacing:0.05em;">Status</th>
          <th style="padding:8px 10px;text-align:right;font-size:11px;font-weight:600;color:#475569;
              text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;">QT Total</th>
          <th style="padding:8px 10px;text-align:right;font-size:11px;font-weight:600;color:#475569;
              text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;">QD Total</th>
          <th style="padding:8px 10px;text-align:right;font-size:11px;font-weight:600;color:#475569;
              text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;">Saldo</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </td></tr>

  <!-- Nota explicativa -->
  <tr><td style="padding:16px 0 0;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr><td style="padding:12px 16px;background:#fffbeb;border-radius:8px;
        border-left:4px solid #f59e0b;font-size:12px;color:#78350f;">
      <strong>Lançamentos em rascunho</strong> não entram nos gráficos, no Inspetor IA nem nos
      relatórios. Para incluí-los nas análises, acesse o portal e clique em <strong>"Fechar"</strong>
      ao lado de cada lançamento.
    </td></tr>
    </table>
  </td></tr>

  <!-- Rodapé -->
  <tr><td style="padding:20px 0 0;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td width="52" valign="middle">
        <img src="{SF_LOGO_URL}" height="40" alt="Service Farma"
          style="height:40px;width:auto;border-radius:8px;background:#fff;
          padding:3px;border:1px solid #e2e8f0;display:block;">
      </td>
      <td style="padding-left:12px;" valign="middle">
        <p style="margin:0;font-size:12px;font-weight:700;color:#475569;">
          Service Farma · Grupo A3 · Direitos Reservados
        </p>
        <p style="margin:3px 0 0;font-size:11px;color:#94a3b8;">
          Enviado automaticamente pelo QTQD. Não responda a esta mensagem.
        </p>
      </td>
    </tr></table>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

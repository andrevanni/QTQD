"""Monta o HTML do e-mail de relatório QTQD."""
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


def build_relatorio_html(
    tenant_nome: str,
    portal_url: str,
    periodos: list[dict],  # lista de {data, indicadores: list[IndicadorCalculado]}
    incluir_inspetor: bool = False,
    incluir_graficos: bool = False,
) -> str:
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    n = len(periodos)

    # Cabeçalho das colunas (datas)
    header_cells = "".join(
        f'<th style="{_th_style()}">{p["data"]}</th>' for p in periodos
    )

    # Monta as linhas de indicadores que queremos mostrar
    INDICADORES_SHOW = [
        ("qt_total",    "QT Total",           _fmt_brl,   None),
        ("qd_total",    "QD Total",            _fmt_brl,   None),
        ("saldo_qt_qd", "Saldo QT/QD",         _fmt_brl,   _color_saldo),
        ("indice_qt_qd","Índice QT/QD",        _fmt_ratio, _color_indice),
        ("saldo_sem_dividas", "Saldo s/ dívidas", _fmt_brl, _color_saldo),
        ("pme",         "PME",                 _fmt_days,  None),
        ("prazo_venda", "Prazo de Venda",      _fmt_days,  None),
        ("prazo_medio_compra","Prazo Médio Compra",_fmt_days,None),
        ("ciclo_financiamento","Ciclo Financeiro",_fmt_days,None),
    ]

    def get_ind(indicadores: list, codigo: str) -> float | None:
        for i in indicadores:
            if i.codigo == codigo:
                return i.valor
        return None

    rows_html = ""
    for i, (cod, nome, fmt_fn, color_fn) in enumerate(INDICADORES_SHOW):
        bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
        cells = ""
        for p in periodos:
            v = get_ind(p["indicadores"], cod)
            color = color_fn(v) if color_fn else "#374151"
            cells += f'<td style="padding:9px 14px;font-size:13px;color:{color};font-weight:{"700" if color_fn else "400"};border-bottom:1px solid #f1f5f9;text-align:right;white-space:nowrap;">{fmt_fn(v)}</td>'
        rows_html += f'<tr style="background:{bg};"><td style="padding:9px 14px;font-size:12px;font-weight:600;color:#475569;border-bottom:1px solid #f1f5f9;white-space:nowrap;">{nome}</td>{cells}</tr>'

    graficos_block = ""
    if incluir_graficos:
        graficos_block = f"""
        <div style="margin-top:24px;padding:16px 24px;background:#f0f9ff;border-radius:8px;border:1px solid #bae6fd;">
          <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#0369a1;">📊 Gráficos disponíveis no portal</p>
          <p style="margin:0;font-size:13px;color:#0c4a6e;">
            Acesse <a href="{portal_url}" style="color:#2563eb;">{portal_url}</a> para visualizar
            os gráficos configurados para este relatório.
          </p>
        </div>"""

    inspetor_block = ""
    if incluir_inspetor:
        inspetor_block = f"""
        <div style="margin-top:24px;padding:16px 24px;background:#fefce8;border-radius:8px;border:1px solid #fde68a;">
          <p style="margin:0 0 6px;font-size:13px;font-weight:700;color:#92400e;">🤖 Inspetor IA</p>
          <p style="margin:0;font-size:13px;color:#78350f;">
            Acesse o portal para ver a análise completa do Inspetor IA com diagnóstico e plano de ação:
            <a href="{portal_url}" style="color:#2563eb;">{portal_url}</a>
          </p>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relatório QTQD — {tenant_nome}</title></head>
<body style="margin:0;padding:20px;background:#f0f4f8;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:900px;margin:0 auto;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#2563eb 100%);border-radius:12px 12px 0 0;padding:28px 32px;">
    <p style="margin:0 0 4px;font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:#93c5fd;">
      QTQD — Saúde Financeira
    </p>
    <h1 style="margin:0 0 6px;font-size:22px;font-weight:700;color:#ffffff;">{tenant_nome}</h1>
    <p style="margin:0;font-size:14px;color:#bfdbfe;">Relatório de {n} período{"s" if n != 1 else ""} · Gerado em {now_str}</p>
  </div>

  <!-- Meta bar -->
  <div style="background:#1e3a8a;padding:10px 32px;display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:12px;color:#bfdbfe;">📅 {n} retrato{"s" if n != 1 else ""} incluído{"s" if n != 1 else ""}</span>
    <a href="{portal_url}" style="font-size:12px;color:#93c5fd;text-decoration:none;">Acessar portal →</a>
  </div>

  <!-- Tabela de indicadores -->
  <div style="background:#ffffff;overflow-x:auto;border-radius:0 0 12px 12px;box-shadow:0 4px 6px rgba(0,0,0,0.07);">
    <table style="width:100%;border-collapse:collapse;min-width:500px;">
      <thead>
        <tr style="background:#f1f5f9;">
          <th style="{_th_style("left")}">Indicador</th>
          {header_cells}
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>

  {graficos_block}
  {inspetor_block}

  <!-- Rodapé -->
  <div style="margin-top:20px;text-align:center;">
    <p style="margin:0;font-size:11px;color:#94a3b8;">
      Enviado automaticamente pelo <strong>QTQD</strong> · Service Farma.<br>
      Não responda a esta mensagem. Dúvidas: entre em contato com sua consultora.
    </p>
  </div>

</div>
</body>
</html>"""


def _th_style(align: str = "right") -> str:
    return (
        f"padding:10px 14px;text-align:{align};font-size:11px;font-weight:600;"
        "text-transform:uppercase;letter-spacing:0.06em;color:#475569;"
        "background:#f1f5f9;border-bottom:2px solid #e2e8f0;white-space:nowrap;"
    )

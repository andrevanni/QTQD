"""
Importa QTQDSV.xlsx para o tenant Drogaria SV (8044331a-4531-47c9-bbff-6546110d5767).
Insere diretamente no Supabase via SDK (service role).
Executa via: py tools/importar_qtqdsv.py

Planilha preservada sem alterações — leitura apenas.

Campos importados:
  QT:  saldo_bancario, cartoes, convenios, cheques, estoque_custo
  QD:  fornecedores, outras_despesas_assumidas, financiamentos, acoes_processos
  Info: faturamento_previsto_mes, compras_mes, entrada_mes, venda_cupom_mes, venda_custo_mes
  Ind: pmp, pmv, pme_excel, indice_faltas
  Exc: excesso_curva_a/b/c/d  (a partir de ago/2025)

Campos AUSENTES na planilha (não importados):
  trade_marketing, outros_qt, investimentos_assumidos, tributos_atrasados,
  lucro_liquido_mes, pmv_avista/30/60/90/120/outros

Campos CALCULADOS (gerados pelo sistema, não importados):
  qt_total, qd_total, saldo_qt_qd, indice_qt_qd, saldo_sem_dividas,
  indice_sem_dividas, saldo_sem_dividas_sem_estoque, ciclo_financiamento,
  excesso_total, margem_bruta, indice_compra_venda
"""
import sys, openpyxl
from datetime import datetime
from supabase import create_client
sys.stdout.reconfigure(encoding='utf-8')

# ── Config ────────────────────────────────────────────────────────────
EXCEL_PATH = r'c:\Users\andre\OneDrive\Área de Trabalho\Sistemas Python\QTQD\QTQDSV.xlsx'
TENANT_ID  = '8044331a-4531-47c9-bbff-6546110d5767'
SUPA_URL   = 'https://ludbgghdknwfzcrqfdge.supabase.co'
SUPA_KEY   = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx1ZGJnZ2hka253ZnpjcnFmZGdlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjE4NTc4NSwiZXhwIjoyMDkxNzYxNzg1fQ.o3WyT7Ag6ZSnJqEwsa7uAQ-GxMu0Qa2-yjfAalCdLLY'

# ── Mapeamento linha → (campo, usar_abs)
# linha_idx = índice 0-based na lista rows
ROW_MAP = {
    # QT
    3:  ('saldo_bancario',            False),  # pode ser negativo
    5:  ('cartoes',                   True),
    6:  ('convenios',                 True),
    7:  ('cheques',                   True),
    10: ('estoque_custo',             True),
    # QD
    14: ('fornecedores',              True),
    16: ('outras_despesas_assumidas', True),
    18: ('financiamentos',            True),
    20: ('acoes_processos',           True),
    # Informações complementares (a partir de mai/2025)
    31: ('faturamento_previsto_mes',  True),
    32: ('compras_mes',               True),
    33: ('entrada_mes',               True),
    34: ('venda_cupom_mes',           True),
    35: ('venda_custo_mes',           True),
    # Indicadores operacionais (a partir de mai/2025)
    41: ('indice_faltas',             True),   # já em decimal: 0.0882 = 8,82%
    42: ('pmp',                       True),
    43: ('pmv',                       True),
    44: ('pme_excel',                 True),
    # Excesso (a partir de ago/2025)
    47: ('excesso_curva_a',           True),
    48: ('excesso_curva_b',           True),
    49: ('excesso_curva_c',           True),
    50: ('excesso_curva_d',           True),
}


def parse_num(v, use_abs=False):
    if v is None or v == '':
        return 0.0
    try:
        n = float(v)
        return abs(n) if use_abs else n
    except Exception:
        return 0.0


def parse_date(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    try:
        return datetime.strptime(str(v)[:10], '%Y-%m-%d').date().isoformat()
    except Exception:
        return None


# ── Lê o Excel (read-only, sem alterações) ───────────────────────────
print('Lendo QTQDSV.xlsx (somente leitura)...')
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, read_only=True)
ws = wb['QTQD']
rows = list(ws.iter_rows(values_only=True))
wb.close()

date_row = rows[1]
print(f'Total de linhas: {len(rows)} | Total de colunas: {len(date_row)}')

semanas = []
for col_idx in range(1, len(date_row)):
    data = parse_date(date_row[col_idx])
    if not data:
        continue

    valores = {}
    for row_idx, (campo, usar_abs) in ROW_MAP.items():
        if row_idx < len(rows) and col_idx < len(rows[row_idx]):
            raw = rows[row_idx][col_idx]
            valores[campo] = parse_num(raw, usar_abs)

    # Considera semana válida se tiver QT + QD mínimos
    qt = sum(valores.get(f, 0) for f in ['saldo_bancario', 'cartoes', 'convenios', 'cheques', 'estoque_custo'])
    qd = sum(valores.get(f, 0) for f in ['fornecedores', 'outras_despesas_assumidas', 'financiamentos', 'acoes_processos'])
    if (qt + qd) > 100:
        semanas.append({'data': data, 'valores': valores})

print(f'\n{len(semanas)} semanas com dados válidos')
if semanas:
    print(f'  Periodo: {semanas[0]["data"]} a {semanas[-1]["data"]}')

# ── Conecta ao Supabase ───────────────────────────────────────────────
sb = create_client(SUPA_URL, SUPA_KEY)

existentes_res = sb.table('avaliacoes_semanais') \
    .select('semana_referencia') \
    .eq('tenant_id', TENANT_ID) \
    .execute()
datas_existentes = {r['semana_referencia'] for r in existentes_res.data}
print(f'{len(datas_existentes)} semanas já cadastradas no Supabase para SV.')

# ── Importa ───────────────────────────────────────────────────────────
print()
criadas = ignoradas = erros = 0

for i, s in enumerate(semanas):
    if s['data'] in datas_existentes:
        ignoradas += 1
        print(f'  [{i+1:03d}/{len(semanas)}] JÁ EXISTE  {s["data"]}')
        continue

    try:
        sb.table('avaliacoes_semanais').insert({
            'tenant_id':         TENANT_ID,
            'semana_referencia': s['data'],
            'status':            'fechada',
            'observacoes':       None,
            'valores':           s['valores'],
        }).execute()
        criadas += 1

        # Log resumido: mostra QT e QD para conferência
        qt = sum(s['valores'].get(f, 0) for f in ['saldo_bancario', 'cartoes', 'convenios', 'cheques', 'estoque_custo'])
        qd = sum(s['valores'].get(f, 0) for f in ['fornecedores', 'outras_despesas_assumidas', 'financiamentos', 'acoes_processos'])
        print(f'  [{i+1:03d}/{len(semanas)}] OK  {s["data"]}  QT={qt:>12,.0f}  QD={qd:>12,.0f}')

    except Exception as e:
        erros += 1
        print(f'  [{i+1:03d}/{len(semanas)}] ERRO  {s["data"]} — {e}')
        if erros > 5:
            print('  Muitos erros consecutivos, abortando.')
            break

print()
print(f'Resultado: {criadas} criadas, {ignoradas} já existiam, {erros} erros')

"""
Correções nos dados da Drogaria SV:
  1. Zera excesso_curva_a/b/c/d para as semanas com valores errados (cache de fórmula)
  2. Atualiza cobertura_estoque_dia (linha 40 do Excel) em todos os registros que têm o dado

Executa via: py tools/corrigir_sv_excesso_cobertura.py
"""
import sys, openpyxl
from datetime import datetime
from supabase import create_client
sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = r'c:\Users\andre\OneDrive\Área de Trabalho\Sistemas Python\QTQD\QTQDSV.xlsx'
TENANT_ID  = '8044331a-4531-47c9-bbff-6546110d5767'
SUPA_URL   = 'https://ludbgghdknwfzcrqfdge.supabase.co'
SUPA_KEY   = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx1ZGJnZ2hka253ZnpjcnFmZGdlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjE4NTc4NSwiZXhwIjoyMDkxNzYxNzg1fQ.o3WyT7Ag6ZSnJqEwsa7uAQ-GxMu0Qa2-yjfAalCdLLY'

# Semanas com excesso errado (cache de fórmula inválido no Excel)
EXCESSO_ERRADO = {'2026-04-17', '2026-04-27'}

def parse_num(v):
    if v is None or v == '': return None
    try: return float(v)
    except: return None

def parse_date(v):
    if v is None: return None
    if isinstance(v, datetime): return v.date().isoformat()
    try: return datetime.strptime(str(v)[:10], '%Y-%m-%d').date().isoformat()
    except: return None

# ── Lê o Excel ───────────────────────────────────────────────────────
print('Lendo QTQDSV.xlsx (somente leitura)...')
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True, read_only=True)
ws = wb['QTQD']
rows = list(ws.iter_rows(values_only=True))
wb.close()

date_row = rows[1]
datas = [(i, v) for i, v in enumerate(date_row) if v is not None and i > 0]

# Monta mapa data → cobertura_estoque_dia
cobertura_map = {}
for col_i, data_raw in datas:
    data = parse_date(data_raw)
    if not data: continue
    cob = parse_num(rows[40][col_i] if col_i < len(rows[40]) else None)
    if cob is not None and cob > 0:
        cobertura_map[data] = cob

print(f'Cobertura de Estoque (do Dia): {len(cobertura_map)} semanas com dado')

# ── Conecta Supabase ──────────────────────────────────────────────────
sb = create_client(SUPA_URL, SUPA_KEY)

# Busca todos os registros da SV
res = sb.table('avaliacoes_semanais') \
    .select('id, semana_referencia, valores') \
    .eq('tenant_id', TENANT_ID) \
    .execute()

registros = res.data
print(f'{len(registros)} registros encontrados para SV')
print()

# ── Correções ─────────────────────────────────────────────────────────
corrigidos_excesso = 0
corrigidos_cobertura = 0
erros = 0

for r in registros:
    data = r['semana_referencia']
    valores = dict(r['valores'])
    atualizar = False
    mudancas = []

    # 1. Zera excesso errado
    if data in EXCESSO_ERRADO:
        for campo in ['excesso_curva_a', 'excesso_curva_b', 'excesso_curva_c', 'excesso_curva_d']:
            if valores.get(campo, 0) > 0:
                mudancas.append(f'{campo}: {valores[campo]:.0f} → 0')
                valores[campo] = 0.0
        atualizar = True
        corrigidos_excesso += 1

    # 2. Atualiza cobertura_estoque_dia
    if data in cobertura_map:
        novo_valor = cobertura_map[data]
        if valores.get('cobertura_estoque_dia', 0) != novo_valor:
            mudancas.append(f'cobertura_estoque_dia: {valores.get("cobertura_estoque_dia", 0)} → {novo_valor}')
            valores['cobertura_estoque_dia'] = novo_valor
            atualizar = True
            corrigidos_cobertura += 1

    if not atualizar:
        continue

    try:
        sb.table('avaliacoes_semanais') \
            .update({'valores': valores}) \
            .eq('id', r['id']) \
            .execute()
        print(f'  OK  {data}  |  {" | ".join(mudancas)}')
    except Exception as e:
        erros += 1
        print(f'  ERRO  {data}  —  {e}')

print()
print(f'Resultado:')
print(f'  Excesso zerado:          {corrigidos_excesso} semanas (17/04 e 27/04)')
print(f'  Cobertura do dia update: {corrigidos_cobertura} semanas')
print(f'  Erros:                   {erros}')

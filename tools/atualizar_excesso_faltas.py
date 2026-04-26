"""
Atualiza registros existentes do Total Socorro com:
- excesso_curva_a/b/c/d  (linhas Excel 70-73, idx 69-72)
- indice_faltas           (linha Excel 56, idx 55)

Executa via: py tools/atualizar_excesso_faltas.py
"""
import openpyxl
from datetime import datetime, timezone
from supabase import create_client

EXCEL_PATH  = r'c:\Users\andre\OneDrive\Área de Trabalho\Sistemas Python\QTQD\QTQDTS.xlsx'
TENANT_ID   = 'b2ce08a4-b1f9-4465-b162-9f5e9bb70092'
SUPA_URL    = 'https://ludbgghdknwfzcrqfdge.supabase.co'
SUPA_KEY    = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx1ZGJnZ2hka253ZnpjcnFmZGdlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjE4NTc4NSwiZXhwIjoyMDkxNzYxNzg1fQ.o3WyT7Ag6ZSnJqEwsa7uAQ-GxMu0Qa2-yjfAalCdLLY'

# Campos a atualizar: {row_idx: (campo, usar_abs)}
EXTRA_ROWS = {
    55: ('indice_faltas',   False),
    69: ('excesso_curva_a', True),
    70: ('excesso_curva_b', True),
    71: ('excesso_curva_c', True),
    72: ('excesso_curva_d', True),
}

def parse_num(v, use_abs=False):
    if v is None or v == '': return None
    try:
        n = float(v)
        return abs(n) if use_abs else n
    except: return None

def parse_date(v):
    if v is None: return None
    if isinstance(v, datetime): return v.date().isoformat()
    try: return datetime.strptime(str(v)[:10], '%Y-%m-%d').date().isoformat()
    except: return None

print('Lendo QTQDTS.xlsx...')
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
ws = wb['QT-QD']
rows = list(ws.iter_rows(values_only=True))
date_row = rows[1]

# Monta mapa data -> {campo: valor}
dados_por_data = {}
for col_idx in range(1, len(date_row)):
    data = parse_date(date_row[col_idx])
    if not data:
        continue
    campos = {}
    for row_idx, (campo, usar_abs) in EXTRA_ROWS.items():
        if row_idx < len(rows):
            raw = rows[row_idx][col_idx] if col_idx < len(rows[row_idx]) else None
            v = parse_num(raw, usar_abs)
            if v is not None:
                campos[campo] = v
    if campos:
        dados_por_data[data] = campos

print(f'{len(dados_por_data)} semanas com dados para atualizar')

# Conecta ao Supabase
sb = create_client(SUPA_URL, SUPA_KEY)

# Busca todos os registros existentes
existentes = sb.table('avaliacoes_semanais')\
    .select('id,semana_referencia,valores')\
    .eq('tenant_id', TENANT_ID)\
    .execute()

print(f'{len(existentes.data)} registros no Supabase')

atualizados = ignorados = erros = 0
agora = datetime.now(timezone.utc).isoformat()

for rec in existentes.data:
    data = rec['semana_referencia']
    if data not in dados_por_data:
        ignorados += 1
        print(f'  SEM DADO   {data}')
        continue

    novos_campos = dados_por_data[data]
    valores_atuais = rec.get('valores') or {}
    valores_merged = {**valores_atuais, **novos_campos}

    try:
        sb.table('avaliacoes_semanais')\
            .update({'valores': valores_merged, 'updated_at': agora})\
            .eq('id', rec['id'])\
            .execute()
        atualizados += 1
        campos_str = ', '.join(f'{k}={v:.4g}' for k, v in novos_campos.items())
        print(f'  OK         {data} | {campos_str}')
    except Exception as e:
        erros += 1
        print(f'  ERRO       {data} — {e}')

print()
print(f'Resultado: {atualizados} atualizados, {ignorados} sem dado no Excel, {erros} erros')

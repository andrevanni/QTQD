"""
Apaga toda a config de campos do tenant Drogaria SV no Supabase.
Após rodar, o portal SV voltará ao padrão (todos os campos visíveis).
O admin pode reconfigurar via painel → Campos.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.db.client import get_supabase

SV_TENANT_ID = "8044331a-4531-47c9-bbff-6546110d5767"

sb = get_supabase()

result = sb.table("tenant_componentes_config") \
    .delete() \
    .eq("tenant_id", SV_TENANT_ID) \
    .execute()

deleted = len(result.data) if result.data else 0
print(f"Removidas {deleted} linhas de config de campos da Drogaria SV.")
print("Todos os campos agora aparecem com visibilidade padrão (visível).")

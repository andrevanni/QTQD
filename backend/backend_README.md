# Backend - QTQD

## Estrutura

- `backend/app/main.py`: aplicacao FastAPI principal
- `backend/app/api/v1/admin_clientes.py`: endpoints administrativos
- `backend/app/api/v1/avaliacoes.py`: endpoints operacionais das avaliacoes
- `backend/app/services/calculos_qtqd.py`: calculos financeiros centralizados
- `backend/app/db/session.py`: conexao SQLAlchemy

## Executar local

```powershell
cd "C:\Users\andre\OneDrive\Área de Trabalho\Sistemas Python\QTQD"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
uvicorn backend.app.main:app --reload
```

## Endpoints iniciais

- `GET /health`
- `GET /api/v1/admin/clientes`
- `POST /api/v1/admin/clientes`
- `PATCH /api/v1/admin/clientes/{tenant_id}`
- `GET /api/v1/admin/licencas`
- `POST /api/v1/admin/licencas`
- `GET /api/v1/admin/branding/{tenant_id}`
- `PUT /api/v1/admin/branding/{tenant_id}`
- `GET /api/v1/admin/componentes-config/{tenant_id}`
- `PUT /api/v1/admin/componentes-config/{tenant_id}`
- `GET /api/v1/admin/importacoes`
- `POST /api/v1/admin/importacoes`
- `GET /api/v1/avaliacoes`
- `GET /api/v1/avaliacoes/{avaliacao_id}`
- `POST /api/v1/avaliacoes`
- `PATCH /api/v1/avaliacoes/{avaliacao_id}`
- `DELETE /api/v1/avaliacoes/{avaliacao_id}`
- `POST /api/v1/avaliacoes/{avaliacao_id}/fechar`

## Vercel

O deploy serverless usa `api/index.py` na raiz do projeto como entrada da API.

As dependencias de deploy ficam acessiveis pelo `requirements.txt` da raiz, que referencia `backend/requirements.txt`.

## Supabase

- `supabase/schema_v1_qtqd.sql`: schema principal multi-tenant
- `supabase/seed_componentes.sql`: catalogo base de componentes e indicadores
- `supabase/migrations/`: copia organizada dos SQLs para continuidade da implantacao

## Configuracao

Usar estes arquivos como base:

- `backend/.env.example`
- `.env.vercel.example`
- `docs/implantacao_supabase_vercel.md`

# Implantacao Supabase e Vercel - QTQD

Este documento organiza a transicao da simulacao atual para o ambiente real do projeto.

## Estado atual

Ja esta pronto no repositorio:

- schema principal do banco em `supabase/schema_v1_qtqd.sql`
- seed inicial em `supabase/seed_componentes.sql`
- migracoes espelhadas em `supabase/migrations/`
- API FastAPI em `backend/app/`
- entrada serverless em `api/index.py`
- rotas da Vercel em `vercel.json`

Observacao importante:

- o front atual ainda opera em modo simulacao com `localStorage`
- esta rodada deixa a base de infraestrutura pronta para conectar o modo real na proxima versao
- o schema ja contempla tabelas para vigencias, branding, configuracao de campos, importacoes e perfis do tenant

## Ordem recomendada

1. Criar o projeto no Supabase.
2. Executar o schema e o seed.
3. Configurar as variaveis da API.
4. Publicar a Vercel.
5. Validar `GET /health`.
6. Na proxima versao, trocar o front para consumo real da API.

## 1. Criar o projeto no Supabase

No painel do Supabase, criar um novo projeto para `QTQD`.

Depois disso, separar estes dados:

- `Project URL`
- `anon public key`
- `service_role key`
- `database password`
- `connection string` com `pooler`

Para a Vercel, prefira a conexao `psycopg` com pooler, em formato semelhante a:

```text
postgresql+psycopg://postgres.[REF]:[SENHA]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## 2. Executar o schema e o seed

Opcao mais simples:

1. Abrir `SQL Editor` no Supabase.
2. Executar o conteudo de `supabase/schema_v1_qtqd.sql`.
3. Executar o conteudo de `supabase/seed_componentes.sql`.

Opcao organizada para continuidade:

- usar os arquivos em `supabase/migrations/`

Arquivos:

- `supabase/migrations/001_schema_v1_qtqd.sql`
- `supabase/migrations/002_seed_componentes.sql`

## 3. Variaveis de ambiente

### Backend local

Copiar:

```powershell
Copy-Item backend\.env.example backend\.env
```

Preencher:

- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ADMIN_TOKEN`
- `CORS_ORIGINS`
- `FRONTEND_CLIENT_URL`
- `FRONTEND_ADMIN_URL`
- `VERCEL_PROJECT_URL`

### Vercel

Usar como referencia:

- `.env.vercel.example`

Variaveis minimas para o deploy:

- `APP_ENV=production`
- `DATABASE_URL`
- `ADMIN_TOKEN`
- `CORS_ORIGINS`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `FRONTEND_CLIENT_URL`
- `FRONTEND_ADMIN_URL`
- `VERCEL_PROJECT_URL`

## 4. Publicar na Vercel

Arquivos usados no deploy:

- `vercel.json`
- `api/index.py`
- `requirements.txt`

Rotas configuradas:

- `/` -> `validar_fronts.html`
- `/cliente` -> `frontend_cliente/index.html`
- `/admin` -> `frontend_admin/index.html`
- `/api/*` -> `api/index.py`

## 5. Validacao minima apos deploy

Validar nesta ordem:

1. `GET /health`
2. `GET /api/v1/admin/clientes` com header `x-admin-token`
3. criar um tenant de teste
4. `GET /api/v1/avaliacoes?tenant_id=...`
5. `POST /api/v1/avaliacoes`

Exemplo de health:

```text
https://seu-projeto.vercel.app/health
```

Resposta esperada:

```json
{"status":"ok","env":"production"}
```

## 6. Proxima versao recomendada

Na proxima rodada, evoluir estes pontos:

- trocar `localStorage` do Cliente e Admin por chamadas reais na API
- criar autenticacao Supabase para admin e cliente
- persistir configuracoes de campos e branding em tabelas reais
- implementar importacao inicial de Excel via backend
- publicar indicadores calculados tambem em `avaliacao_indicadores`

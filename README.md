# QTQD

Projeto web para avaliacao financeira semanal de clientes, com base na planilha `QTQD.xlsx`.

## Objetivo

Transformar o modelo atual em Excel em uma aplicacao web multi-cliente, onde:

- o cliente preenche os dados financeiros semanais
- o sistema calcula automaticamente os indicadores
- a area cliente mostra os resultados da semana e o historico
- a area admin gerencia clientes, acessos, vigencias e configuracoes
- em uma fase posterior serao adicionados dashboards e analise com IA

## Base de referencia

O QTQD vai reutilizar a mesma linha tecnica ja usada em `Agenda de Compras Web`:

- aplicacao web com area cliente e area admin separadas
- banco Supabase (PostgreSQL + autenticacao)
- modelo multi-tenant com `tenant_id`
- isolamento de dados com RLS
- frontend hospedado na Vercel
- backend/API para regras de negocio e operacoes administrativas

## Estrutura inicial

- `docs/`: especificacao funcional, arquitetura e modelo de dados
- `backend/`: API FastAPI inicial, schemas e regras de negocio
- `frontend_cliente/`: simulacao web da area cliente
- `frontend_admin/`: simulacao web da area admin
- `supabase/`: scripts SQL, politicas e seeds
- `api/index.py`: entrada serverless para Vercel
- `vercel.json`: rotas de deploy do cliente, admin e API

## MVP previsto

Na primeira fase, o sistema deve:

- cadastrar clientes e usuarios
- registrar avaliacoes financeiras semanais
- armazenar os componentes informados pelo cliente
- calcular automaticamente saldos, indices e indicadores
- exibir o resultado da semana e a evolucao historica

## Simulacao web atual

Ja existe uma primeira simulacao navegavel:

- `frontend_cliente/index.html`: cadastro semanal, edicao, exclusao e painel de avaliacao com rotulos congelados
- `frontend_admin/index.html`: cadastro de clientes, vigencias e registro da primeira carga por arquivo Excel

## Base real iniciada

Ja foi estruturada a base tecnica para evoluir da simulacao para o ambiente real:

- backend FastAPI inicial em `backend/app`
- schema SQL Supabase em `supabase/schema_v1_qtqd.sql`
- seed de componentes e indicadores em `supabase/seed_componentes.sql`
- migracoes espelhadas em `supabase/migrations`
- configuracao da Vercel em `vercel.json`
- entrada serverless da API em `api/index.py`
- dependencias de deploy na raiz em `requirements.txt`

## Implantacao

O passo a passo da implantacao real esta em:

- `docs/implantacao_supabase_vercel.md`
- `docs/integracao_front_api.md`
- `docs/publicacao_github.md`
- `.env.vercel.example`
- `backend/.env.example`

## Proximas fases

- dashboards gerenciais
- analise automatica por IA
- alertas de risco e recomendacoes
- exportacao em PDF e compartilhamento

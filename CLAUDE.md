# CLAUDE.md — QTQD

## Sobre o projeto

QTQD é um sistema de avaliação financeira semanal para farmácias independentes.
Compara **QT (Quanto Tenho)** com **QD (Quanto Devo)** e gera indicadores de saúde financeira.

**Design de referência:** Comercial_A3 — mesma linguagem visual (sidebar escura, azul #2563eb, Manrope/Space Grotesk)
**Produção:** https://qtqd-vt2a.vercel.app
**Repositório:** https://github.com/andrevanni/QTQD
**Supabase:** (definir project ref)

---

## Stack

- **Frontend:** HTML + CSS + JavaScript puro (sem framework)
- **Backend:** FastAPI (Python), publicado via `@vercel/python`
- **Banco:** Supabase (PostgreSQL multi-tenant)
- **Deploy:** Vercel — auto-deploy via `git push origin main`

---

## Regras obrigatórias

- **Idioma:** Sempre responder em português brasileiro
- **Deploy:** Após cada conjunto de alterações, rodar `git push origin main`
- **Caminhos HTML:** Usar `<base href="/cliente/">` no `<head>` do cliente e `<base href="/admin/">` no admin — garante que paths relativos resolvam corretamente na Vercel, onde a URL fica `/cliente` sem barra final
- **Coluna fixa do painel:** Usar `<table>` HTML real com `position: sticky; left: 0` nos `<th>`/`<td>` da primeira coluna. Nunca usar CSS Grid para isso.

---

## Roteamento Vercel

| URL | Destino |
|-----|---------|
| `/cliente` | `frontend_cliente/index.html` |
| `/cliente/(.*)` | `frontend_cliente/$1` |
| `/admin` | `frontend_admin/index.html` |
| `/admin/(.*)` | `frontend_admin/$1` |
| `/shared/(.*)` | `shared/$1` |
| `/api/(.*)` | `api/index.py` |
| `/` | `validar_fronts.html` |

---

## Estrutura de pastas

```
QTQD/
  frontend_cliente/       Portal do cliente
    index.html
    styles.css
    script.js
    assets/logo_alta.jpg
    data/qtqd_seed.js
  frontend_admin/         Painel administrativo
    index.html
    styles.css
    script.js
  shared/                 Recursos compartilhados
    app_config.js         Configuração da API (modo: simulation/api)
    api_client.js         Cliente HTTP para o backend
  api/
    index.py              FastAPI app
  docs/                   Documentação
  vercel.json
  requirements.txt
```

---

## Frontend Cliente — IDs que o script.js exige no HTML

**Nunca remover estes IDs — o script.js os referencia diretamente.**

| ID | Uso |
|----|-----|
| `weeklyForm` | Formulário de lançamento semanal |
| `recordId` | Input hidden com UUID do registro |
| `weekDate` | Input de data |
| `recordStatus` | Select de status (rascunho/fechada) |
| `formModeBadge` | Badge "Nova semana" / "Editando..." |
| `formCalculatedKpis` | Container dos KPIs calculados |
| `matrixTableWrap` | Container do painel (tabela gerada por JS) |
| `historyTable` | `<tbody>` da tabela de histórico |
| `feedbackBox` | Mensagens de feedback ao usuário |
| `connectionModeLabel` | Exibe modo de conexão (simulação/API) |
| `chartFieldsGrid` | Grid de checkboxes de campos do gráfico |
| `chartRangeCount` | Input de quantidade de períodos |
| `chartPanelTitle` | Título dinâmico do gráfico |
| `financialTimelineChart` | `<canvas>` do gráfico de evolução |
| `liquidityChart` | `<canvas>` do gráfico de ciclos |
| `efficiencyChart` | `<canvas>` do gráfico QT/QD/Saldo |
| `inspectorHero` | Grid de KPIs do inspetor |
| `inspectorSemaphore` | Grid do semáforo executivo |
| `inspectorBlocks` | Blocos de análise |
| `inspectorPeriods` | Conclusões por período |
| `inspectorNarrative` | Diagnóstico executivo |
| `inspectorTrendTable` | Tabela de tendências |
| `inspectorRisks` | Pontos de atenção |
| `inspectorActions` | Plano recomendado |
| `inspectorDataTable` | Base analítica (tabela completa) |
| `clientSidebarLogo` | Logo do cliente na sidebar |
| `clientTopLogo` | Logo do cliente na topbar |
| `clientSidebarFallback` | Iniciais do cliente na sidebar |
| `clientTopFallback` | Iniciais do cliente na topbar |
| `clientSidebarName` | Nome do cliente na sidebar |
| `clientTopName` | Nome do cliente na topbar |
| `sidebarLogo` | Logo Service Farma na sidebar |
| `footerLogo` | Logo Service Farma no footer |
| `newEntryButton` | Botão "Nova Semana" |
| `seedDemoButton` | Botão "Recarregar Base" |
| `openGraphsButton` | Botão "Gráficos" |
| `openInspectorButton` | Botão "Inspetor IA" |
| `resetFormButton` | Botão "Limpar" formulário |
| `evaluateButton` | Botão "Avaliar dados" |
| `toggleFocusButton` | Botão "Maximizar" painel |
| `backFromPanelButton` | Botão "Voltar" (modo maximizado) |
| `refreshInspectorButton` | Botão "Atualizar análise" |
| `downloadPdfButton` | Botão "Gerar PDF" |
| `sidebarMiniToggle` | Botão recolher/expandir sidebar |
| `sidebarRevealButton` | Botão menu mobile |

**Campos do formulário (IDs dos inputs):**
`saldo_bancario`, `contas_receber`, `cartoes`, `convenios`, `cheques`, `trade_marketing`, `outros_qt`, `estoque_custo`,
`contas_pagar`, `fornecedores`, `investimentos_assumidos`, `outras_despesas_assumidas`, `dividas`, `financiamentos`, `tributos_atrasados`, `acoes_processos`,
`faturamento_previsto_mes`, `compras_mes`, `entrada_mes`, `venda_cupom_mes`, `venda_custo_mes`, `lucro_liquido_mes`

---

## Classes CSS que o script.js usa

| Classe | Contexto |
|--------|----------|
| `nav-link` + `data-section` | Botões de navegação |
| `section-view hidden` | Mostrar/ocultar seções |
| `active` | Nav item ativo / tema ativo |
| `matrix-table` | Tabela do painel |
| `matrix-scroll` | Container com overflow do painel |
| `matrix-cell` | Célula do painel (th ou td) |
| `matrix-sticky` | Primeira coluna congelada |
| `matrix-head` | Cabeçalho do painel |
| `row-header row-section row-empty` | Tipos de linha no painel |
| `kpi-card good bad neutral` | Cards de KPI |
| `inspector-card inspector-metric` | Cards do inspetor |
| `semaphore-item good warning bad` | Semáforo executivo |
| `analysis-list analysis-copy` | Blocos de texto analítico |
| `action-btn action-row` | Botões de ação na tabela histórico |
| `chart-field-option` | Checkboxes de campos do gráfico |
| `latest-row` | Linha mais recente no histórico |
| `muted eyebrow badge` | Tipografia auxiliar |

**Classes de body gerenciadas pelo script:**
| Classe | Efeito |
|--------|--------|
| `sidebar-mini` | Sidebar recolhida (56px) |
| `focus-painel` | Painel maximizado (tela cheia) |
| `sidebar-open` | Sidebar visível no mobile |

---

## Multi-tenant e modos de operação

- **Modo simulação:** `shared/app_config.js` com `mode: "simulation"` — dados no localStorage, seed em `data/qtqd_seed.js`
- **Modo API:** `mode: "api"` + `tenantId` configurado — conecta ao backend FastAPI + Supabase

### Tabelas Supabase já criadas
`tenants`, `tenant_users`, `tenant_profiles`, `tenant_licencas`, `tenant_branding`,
`qtqd_componentes_catalogo`, `qtqd_indicadores_catalogo`, `tenant_componentes_config`,
`avaliacoes_semanais`, `avaliacao_indicadores`, `avaliacao_analises`, `tenant_importacoes`

---

---

## Backend — FastAPI

### Stack
- **FastAPI** + **SQLAlchemy** (raw SQL via `text()`) + **psycopg** (driver PostgreSQL)
- **PyJWT** para validação de tokens do Supabase Auth
- Deploy via `@vercel/python` — entry point: `api/index.py` → importa `backend.app.main:app`

### Variáveis de ambiente obrigatórias (Vercel + .env local)

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | `postgresql+psycopg://...` (connection string do Supabase) |
| `SUPABASE_JWT_SECRET` | Supabase Dashboard → Settings → API → JWT Secret |
| `ADMIN_TOKEN` | Token secreto para endpoints `/admin/*` |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula |
| `VERCEL_PROJECT_URL` | URL do projeto na Vercel (incluída no CORS automaticamente) |

### Autenticação — dois níveis

| Nível | Como funciona | Endpoints |
|-------|---------------|-----------|
| **Cliente** | `Authorization: Bearer <supabase_jwt>` | `/api/v1/avaliacoes/*`, `/api/v1/me/*` |
| **Admin** | `X-Admin-Token: <admin_token>` | `/api/v1/admin/*` |

O JWT do cliente é validado com `SUPABASE_JWT_SECRET` (HS256). O `sub` do JWT é usado para resolver o `tenant_id` na tabela `tenant_users`.

### Endpoints disponíveis

**Cliente (JWT):**
- `GET  /api/v1/avaliacoes` — lista avaliações do tenant
- `POST /api/v1/avaliacoes` — cria avaliação (status 201)
- `GET  /api/v1/avaliacoes/{id}` — obtém avaliação
- `PATCH /api/v1/avaliacoes/{id}` — atualiza avaliação
- `POST /api/v1/avaliacoes/{id}/fechar` — fecha avaliação
- `DELETE /api/v1/avaliacoes/{id}` — exclui avaliação
- `GET /api/v1/me/branding` — branding do tenant do usuário
- `GET /api/v1/me/componentes-config` — config de campos do tenant

**Admin (X-Admin-Token):**
- `GET/POST /api/v1/admin/clientes` — gestão de tenants
- `PATCH /api/v1/admin/clientes/{id}` — atualiza tenant
- `GET/POST /api/v1/admin/licencas` — vigências
- `GET/PUT /api/v1/admin/branding/{tenant_id}` — branding por tenant
- `GET/PUT /api/v1/admin/componentes-config/{tenant_id}` — config de campos
- `GET/POST /api/v1/admin/importacoes` — importações

**Saúde:**
- `GET /health`

### Estrutura do backend

```
backend/app/
  core/
    config.py       Settings via pydantic-settings (.env + variáveis de ambiente)
    auth.py         Validação JWT Supabase + resolução de tenant_id
    admin_auth.py   Validação do X-Admin-Token
  db/
    session.py      SQLAlchemy engine + get_db_session dependency
  api/
    router.py       Agrega todos os routers em /api/v1
    v1/
      avaliacoes.py       CRUD de avaliações semanais (JWT)
      cliente_config.py   /me/branding e /me/componentes-config (JWT)
      admin_clientes.py   CRUD de tenants (admin token)
      admin_config.py     Licenças, branding, componentes, importações (admin token)
  schemas/
    avaliacoes.py   AvaliacaoValores, AvaliacaoCreateRequest, AvaliacaoResponse, IndicadorCalculado
    admin_clientes.py
    admin_config.py
  services/
    calculos_qtqd.py  Cálculos de QT, QD, saldo, índice, PME, ciclo, prazos
api/
  index.py          Entry point Vercel: from backend.app.main import app
```

### Modelo de dados no Supabase

Os valores QT/QD de cada avaliação ficam em uma coluna `valores JSONB` na tabela `avaliacoes_semanais`. Os indicadores são **calculados pelo backend em tempo de leitura** (não são persistidos).

```
tenants              → um por cliente
tenant_users         → vínculo usuário Supabase Auth ↔ tenant
tenant_branding      → logo, cores, nome do portal
tenant_licencas      → vigência e limites
tenant_componentes_config → labels e visibilidade dos campos por tenant
avaliacoes_semanais  → avaliação semanal (valores como JSONB)
avaliacao_analises   → análises manuais ou por IA
tenant_importacoes   → log de importações
```

### Como ativar o modo API no frontend

1. Usuário faz login via Supabase Auth → obtém JWT
2. Chama `QTQD_API_CLIENT.setJwt(token)` para armazenar o JWT
3. `script.js` chama `isApiMode()` — retorna `true` se `mode === "api"` E `tenantId` está configurado E `QTQD_API_CLIENT` existe
4. Todos os endpoints de avaliações passam o JWT automaticamente via `Authorization: Bearer`

---

## Histórico de problemas resolvidos

1. **CSS não carregava na Vercel:** URL `/cliente` (sem trailing slash) fazia `href="styles.css"` resolver para `/styles.css` (404). **Fix:** `<base href="/cliente/">` no `<head>`.

2. **Coluna fixa do painel não funcionava:** CSS Grid com `position: sticky` é instável. **Fix:** Usar `<table>` HTML real — `<th>`/`<td>` com `position: sticky; left: 0` funciona de forma garantida em todos os navegadores modernos.

---

## Segurança (pendente)

- Regenerar `SUPABASE_SERVICE_ROLE_KEY`
- Trocar senha do banco Supabase
- Revogar tokens GitHub usados durante implantação

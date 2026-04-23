# CLAUDE.md — QTQD

## Sobre o projeto

QTQD é um sistema de avaliação financeira semanal para farmácias independentes.
Compara **QT (Quanto Tenho)** com **QD (Quanto Devo)** e gera indicadores de saúde financeira.

**Design de referência:** Comercial_A3 — mesma linguagem visual (sidebar escura, azul #2563eb, Manrope/Space Grotesk)
**Produção:** https://qtqd-vt2a.vercel.app
**Repositório:** https://github.com/andrevanni/QTQD
**Supabase project ref:** `ludbgghdknwfzcrqfdge`
**Supabase URL:** `https://ludbgghdknwfzcrqfdge.supabase.co`

---

## Stack

- **Frontend:** HTML + CSS + JavaScript puro (sem framework)
- **Backend:** FastAPI (Python), publicado via `@vercel/python`
- **Banco:** Supabase (PostgreSQL multi-tenant) — acesso via Supabase Python SDK (HTTPS/REST)
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
| `/health` | `api/index.py` |
| `/` | `validar_fronts.html` |

---

## Estrutura de pastas

```
QTQD/
  frontend_cliente/       Portal do cliente
    index.html
    styles.css
    script.js
    chart_builder.js      Gerador de gráficos customizados
    assets/logo_alta.jpg
    data/qtqd_seed.js
  frontend_admin/         Painel administrativo
    index.html
    styles.css
    script.js
  shared/                 Recursos compartilhados
    app_config.js         Configuração da API (modo: simulation/api)
    api_client.js         Cliente HTTP para o backend
  backend/app/
    core/
      config.py           Settings via pydantic-settings
      auth.py             Validação JWT Supabase (JWKS/ES256) + resolução de tenant_id
      admin_auth.py       Validação do X-Admin-Token
    db/
      client.py           Supabase SDK client (get_supabase())
    api/
      router.py           Agrega todos os routers em /api/v1
      v1/
        avaliacoes.py
        cliente_config.py
        admin_clientes.py
        admin_config.py
    schemas/
    services/
      calculos_qtqd.py
  api/
    index.py              Entry point Vercel
  vercel.json
  requirements.txt
```

---

## Vercel — Configuração de produção

**Projeto de produção:** `qtqd-vt2a` (ID: `prj_59oqSmERo1jp5hn7RwcaVBuRf9Hn`)
> Não confundir com o projeto `qtqd` — esse é outro projeto diferente.

### Variáveis de ambiente no Vercel (já configuradas)

| Variável | Descrição |
|----------|-----------|
| `SUPABASE_URL` | `https://ludbgghdknwfzcrqfdge.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Chave JWT legacy do Supabase (começa com `eyJ...`) |
| `ADMIN_TOKEN` | Token do painel admin |
| `CORS_ORIGINS` | Origens permitidas |
| `DB_PASSWORD` | Senha do banco (mantida por compatibilidade, não usada com SDK) |

### Como atualizar variáveis de ambiente via API (quando necessário)

```powershell
$token = "<vercel_token_em_auth.json>"  # %APPDATA%\com.vercel.cli\Data\auth.json
$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
$envs = Invoke-RestMethod -Uri "https://api.vercel.com/v9/projects/prj_59oqSmERo1jp5hn7RwcaVBuRf9Hn/env" -Headers $headers
```

---

## Backend — FastAPI + Supabase SDK

### Stack atual
- **FastAPI** + **Supabase Python SDK** (`supabase==2.10.0`) — acesso ao banco via HTTPS/REST
- **PyJWT[crypto]** para validação de tokens JWT do Supabase Auth (ES256)
- Deploy via `@vercel/python` — entry point: `api/index.py` → importa `backend.app.main:app`

### Por que Supabase SDK e não SQLAlchemy/psycopg?

A conexão TCP direta ao PostgreSQL do Supabase **não funciona no Vercel Lambda** por dois motivos:
1. A conexão direta (`db.PROJECT.supabase.co:5432`) é **IPv6 only** — Vercel Lambda não suporta IPv6
2. O Transaction Pooler (`aws-0-*.pooler.supabase.com:6543`) retorna "Tenant or user not found" — problema de autenticação não resolvível sem acesso direto à config do PgBouncer

**Solução definitiva:** usar o Supabase Python SDK (`supabase-py`) que conecta via **HTTPS** ao PostgREST — funciona sempre no Vercel, sem problemas de rede.

### Autenticação — dois níveis

| Nível | Como funciona | Endpoints |
|-------|---------------|-----------|
| **Cliente** | `Authorization: Bearer <supabase_jwt>` | `/api/v1/avaliacoes/*`, `/api/v1/me/*` |
| **Admin** | `X-Admin-Token: <admin_token>` | `/api/v1/admin/*` |

O JWT do cliente é validado via **JWKS** (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`), suportando ES256 (ECC P-256) e HS256 (legado). O `sub` do JWT resolve o `tenant_id` via tabela `tenant_users`.

### Endpoints disponíveis

**Cliente (JWT):**
- `GET  /api/v1/avaliacoes` — lista avaliações do tenant
- `POST /api/v1/avaliacoes` — cria avaliação (status 201)
- `GET  /api/v1/avaliacoes/{id}` — obtém avaliação
- `PATCH /api/v1/avaliacoes/{id}` — atualiza avaliação
- `POST /api/v1/avaliacoes/{id}/fechar` — fecha avaliação
- `DELETE /api/v1/avaliacoes/{id}` — exclui avaliação
- `GET /api/v1/me/branding` — branding do tenant
- `GET /api/v1/me/componentes-config` — config de campos do tenant

**Admin (X-Admin-Token):**
- `GET/POST /api/v1/admin/clientes` — gestão de tenants
- `PATCH /api/v1/admin/clientes/{id}` — atualiza tenant
- `GET/POST /api/v1/admin/licencas` — vigências
- `GET/PUT /api/v1/admin/branding/{tenant_id}` — branding por tenant
- `GET/PUT /api/v1/admin/componentes-config/{tenant_id}` — config de campos
- `GET/POST /api/v1/admin/importacoes` — importações

**Saúde:**
- `GET /health` — retorna `supabase_ok: true` se a conexão estiver OK

### Supabase SDK — padrões de uso

```python
from backend.app.db.client import get_supabase

sb = get_supabase()

# SELECT
result = sb.table("tenants").select("*").order("created_at", desc=True).execute()
rows = result.data  # lista de dicts

# INSERT (retorna o registro criado)
result = sb.table("tenants").insert(data_dict).execute()
row = result.data[0]

# UPDATE
result = sb.table("tenants").update(data_dict).eq("id", str(tenant_id)).execute()

# UPSERT (insert ou update por conflict)
result = sb.table("tenant_branding").upsert(data, on_conflict="tenant_id").execute()

# DELETE
result = sb.table("avaliacoes_semanais").delete().eq("id", str(id)).eq("tenant_id", str(tid)).execute()
```

**Regras importantes:**
- UUIDs devem ser passados como `str()` — PostgREST não aceita objetos UUID nativos
- Datas devem ser passadas como `str()` — ex: `str(payload.inicio_vigencia)`
- JSONB (ex: campo `valores`) vem do banco já como `dict` Python — não precisa de `json.loads()`
- Ao escrever JSONB, passe um `dict` — não passe JSON string
- `updated_at` não atualiza automaticamente (sem trigger) — incluir `"updated_at": datetime.now(timezone.utc).isoformat()` em todo UPDATE/UPSERT

### Modelo de dados no Supabase

```
tenants                   → um por cliente (farmácia)
tenant_users              → vínculo usuário Supabase Auth ↔ tenant
tenant_branding           → logo, cores, nome do portal
tenant_licencas           → vigência e limites de uso
tenant_componentes_config → labels e visibilidade dos campos por tenant
avaliacoes_semanais       → avaliação semanal (valores QT/QD como JSONB)
avaliacao_analises        → análises manuais ou por IA
tenant_importacoes        → log de importações de dados
```

Os indicadores financeiros são **calculados em tempo de leitura** pelo backend (`services/calculos_qtqd.py`), não são persistidos.

---

## Supabase — Como obter a chave de serviço correta

O Supabase tem **dois formatos** de chave para a `service_role`. Apenas o formato JWT funciona com o PostgREST:

| Aba no Dashboard | Formato | Funciona? |
|-----------------|---------|-----------|
| "Publishable and secret API keys" | `sb_secret_...` | ❌ NÃO funciona com PostgREST |
| **"Legacy anon, service_role API keys"** | `eyJ...` (JWT) | ✅ Funciona |

**Caminho:** Settings → API Keys → aba "Legacy anon, service_role API keys" → `service_role` → Reveal

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

## Histórico de problemas resolvidos

1. **CSS não carregava na Vercel:** URL `/cliente` (sem trailing slash) fazia `href="styles.css"` resolver para `/styles.css` (404). **Fix:** `<base href="/cliente/">` no `<head>`.

2. **Coluna fixa do painel não funcionava:** CSS Grid com `position: sticky` é instável. **Fix:** Usar `<table>` HTML real — `<th>`/`<td>` com `position: sticky; left: 0` funciona de forma garantida em todos os navegadores modernos.

3. **Segundo gráfico não aparecia após `destroy()`:** Chart.js deixa estado residual no canvas. **Fix:** `outer.innerHTML = '<canvas id="cbCanvas"></canvas>'` + `setTimeout(30)` antes de criar nova instância.

4. **JWT ES256 vs HS256:** Backend foi escrito para HS256, mas Supabase agora usa ECC P-256 (ES256). **Fix:** usar `PyJWKClient` do PyJWT para validação via JWKS automática.

5. **Rota `/health` não encontrada:** Faltava no `vercel.json`. **Fix:** adicionar `{ "src": "/health", "dest": "/api/index.py" }`.

6. **Variáveis de ambiente não chegavam ao Python:** Foram adicionadas ao projeto errado (`qtqd` em vez de `qtqd-vt2a`). **Fix:** usar Vercel REST API diretamente no projeto `prj_59oqSmERo1jp5hn7RwcaVBuRf9Hn`.

7. **Conexão direta ao banco falhou (IPv6 + pooler):**
   - Conexão direta `db.PROJECT.supabase.co:5432` é IPv6 only — Vercel Lambda não alcança
   - Transaction Pooler `aws-0-*.pooler.supabase.com:6543` retorna "Tenant or user not found" (problema de auth no PgBouncer)
   - **Fix definitivo:** substituir SQLAlchemy/psycopg pelo **Supabase Python SDK** — usa HTTPS, sempre funciona no Vercel

8. **Chave de serviço inválida (`sb_secret_...`):** O Supabase tem duas abas de chaves. O PostgREST exige o formato JWT (`eyJ...`). **Fix:** usar a aba "Legacy anon, service_role API keys" no Supabase Dashboard → Settings → API Keys.

9. **Campo email vazio causava erro 422:** O script enviava `""` para o campo `contato_email`, mas `EmailStr` do Pydantic não aceita string vazia. O `detail` do erro 422 é um array, aparecia como `[object Object]`. **Fix:** `$('clientEmail').value.trim() || null` no script.js, e `api_client.js` agora formata arrays de erro corretamente.

---

## Segurança (pendente)

- Regenerar `SUPABASE_SERVICE_ROLE_KEY` após estabilização
- Revogar tokens GitHub usados durante implantação inicial

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
- **Caminhos HTML:** Usar `<base href="/cliente/">` no `<head>` do cliente e `<base href="/admin/">` no admin
- **Coluna fixa do painel:** Usar `<table>` HTML real com `position: sticky; left: 0`. Nunca usar CSS Grid para isso.
- **Cabeçalho do painel também congelado:** `thead th` com `position: sticky; top: 0; z-index: 4`. Corner cell (`.matrix-head.matrix-sticky`) precisa de `z-index: 5`.
- **Campos calculados no painel:** Usar `configurableKeys` (apenas os de `componentLabels`) no filtro `visibleRows` — campos calculados como `excesso_total`, `qt_total` etc. devem ser sempre visíveis.
- **Inputs do formulário:** Todos monetários/numéricos usam `type="text" inputmode="decimal"` — NUNCA `type="number"`. Valores exibidos em formato pt-BR (vírgula decimal, ponto milhares).
- **Service Worker:** versão atual `qtqd-v3` em `frontend_cliente/sw.js`. Ao fazer mudanças que devem invalidar cache, incrementar a versão.

---

## Roteamento Vercel

| URL | Destino |
|-----|---------|
| `/cliente` | `frontend_cliente/index.html` |
| `/cliente/(.*)` | `frontend_cliente/$1` |
| `/admin` | `frontend_admin/index.html` |
| `/admin/(.*)` | `frontend_admin/$1` |
| `/instalar` | `frontend_instalar/index.html` |
| `/instalar/(.*)` | `frontend_instalar/$1` |
| `/shared/(.*)` | `shared/$1` |
| `/api/(.*)` | `api/index.py` |
| `/health` | `api/index.py` |
| `/` | `validar_fronts.html` → redireciona para `/cliente` (ou `/instalar` se hash tiver `access_token`) |

---

## Estrutura de pastas

```
QTQD/
  frontend_cliente/       Portal do cliente
    index.html
    styles.css
    script.js
    chart_builder.js      Gerador de gráficos customizados
    manifest.json         PWA manifest (ícone, start_url, display standalone)
    sw.js                 Service Worker (cache qtqd-v3)
    assets/logo_alta.jpg
    assets/icon-512.png
    data/qtqd_seed.js
  frontend_admin/         Painel administrativo
    index.html
    styles.css
    script.js
  frontend_instalar/      Página de primeiro acesso do cliente (criação de senha + guia PWA)
    index.html            Standalone — sem sidebar, sem nav. Tem <base href="/instalar/">.
                          Após criar senha: redireciona para /cliente em 3s.
    QTQD.url              Atalho Windows (não é mais oferecido para download — bloqueado por browsers)
  shared/                 Recursos compartilhados
    app_config.js         Configuração da API (mode: simulation/api, tenantId)
    api_client.js         Cliente HTTP — inclui setJwt, setTenantId, abrirPortal, uploadLogo, login, getChartsConfig, putChartsConfig
  backend/app/
    core/
      config.py           Settings (inclui portal_admin_email, portal_admin_password)
      auth.py             JWT Supabase + suporte X-Tenant-Id para multi-tenant
      admin_auth.py       Validação do X-Admin-Token
    db/client.py
    api/v1/
      auth.py             POST /auth/login, POST /auth/definir-senha
      avaliacoes.py
      cliente_config.py
      admin_clientes.py
      cliente_config.py   GET/PUT /me/charts-config (gráficos salvos por tenant)
      admin_config.py     POST /admin/abrir-portal/{tenant_id} (auto-registra admin em tenant_usuarios se ausente)
                          POST /admin/branding/{tenant_id}/logo  (upload para Supabase Storage)
                          POST /admin/usuarios/{id}/enviar-convite (gera link Supabase Auth + envia e-mail)
    schemas/avaliacoes.py
    services/
      calculos_qtqd.py    Indicadores calculados
      relatorio_html.py   Template HTML do e-mail de relatório
      excel_import.py
  api/index.py
  tools/
    importar_qtqdts.py        Importação inicial do QTQDTS.xlsx
    atualizar_excesso_faltas.py  Atualiza excesso_curva_a/b/c/d e indice_faltas nos registros existentes
    analisar_excel.py
    analisar_campos.py
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
| `PORTAL_ADMIN_PASSWORD` | Senha do usuário `andre@servicefarma.far.br` para "Acessar Portal" |

---

## Clientes cadastrados no Supabase

| Nome | tenant_id | Status |
|------|-----------|--------|
| **Total Socorro / Drogaria da Letícia** | `b2ce08a4-b1f9-4465-b162-9f5e9bb70092` | implantacao — **103 semanas importadas** (jun/2024 → abr/2026) |
| Drogaria SV | `8044331a-4531-47c9-bbff-6546110d5767` | implantacao — sem dados |

> `nome_portal` no branding: "Drogaria da Letícia". Logo já configurada no bucket `logos` do Supabase Storage.

### Acesso admin ao portal do cliente

O admin (`andre@servicefarma.far.br` / senha: `service`) está cadastrado no Supabase Auth.

No painel admin, cada card de cliente tem o botão **"Acessar Portal"** que:
1. Chama `POST /admin/abrir-portal/{tenant_id}` → faz login como admin, **auto-registra** o admin em `tenant_usuarios` para o tenant se ainda não existir, retorna JWT
2. Abre `https://qtqd-vt2a.vercel.app/cliente?token=JWT&tenant_id=UUID`
3. Portal lê os params, armazena no localStorage, grava `permissao='edita'` e entra em modo API para aquele tenant

O backend aceita `X-Tenant-Id` header para usuários com acesso a múltiplos tenants.

### Branding e logo

O `initializeClient()` chama `getMyBranding()` ao iniciar em modo API e atualiza o localStorage com `clientName` e `clientLogoUrl`. O admin pode fazer upload de logo via **Identidade Visual → Logo do cliente** (endpoint `POST /admin/branding/{tenant_id}/logo`, salva no bucket `logos`).

---

## Modelo de dados — campo `valores` (JSONB)

Todos os campos financeiros ficam no JSONB `avaliacoes_semanais.valores`.

### Campos do AvaliacaoValores (schema atual completo)

**QT (Quanto Tenho):**
`saldo_bancario`, `contas_receber`, `cartoes`, `convenios`, `cheques`, `trade_marketing`, `outros_qt`, `estoque_custo`

**QD (Quanto Devo):**
`contas_pagar`, `fornecedores`, `investimentos_assumidos`, `outras_despesas_assumidas`, `dividas`, `financiamentos`, `tributos_atrasados`, `acoes_processos`

**Informações Complementares:**
`faturamento_previsto_mes`, `compras_mes`, `entrada_mes`, `venda_cupom_mes`, `venda_custo_mes`, `lucro_liquido_mes`

**Indicadores Operacionais (inputs):**
`pmp`, `pmv`, `pmv_avista`, `pmv_30`, `pmv_60`, `pmv_90`, `pmv_120`, `pmv_outros`, `pme_excel`, `indice_faltas`, `excesso_curva_a`, `excesso_curva_b`, `excesso_curva_c`, `excesso_curva_d`

> **`indice_faltas` — ratio decimal (0–1):** 6,82% é armazenado como `0.0682`. O formulário exibe `valor × 100` e salva `input ÷ 100` automaticamente. `fmtPercent()` já multiplica por 100 para exibição.

**Calculados (não persistidos, gerados em `calculos_qtqd.py`):**
`qt_total`, `qd_total`, `saldo_qt_qd`, `indice_qt_qd`, `saldo_sem_dividas`, `indice_sem_dividas`, `saldo_sem_dividas_sem_estoque`, `pme` (calculado), `prazo_medio_compra`, `prazo_venda`, `ciclo_financiamento`, `indice_compra_venda`, `margem_bruta`, `excesso_total`

### Dados do Total Socorro importados

- **103 semanas** de QT/QD (jun/2024 → abr/2026) — `tools/importar_qtqdts.py`
- **PMP, PMV, PME** para todas as 103 semanas (do QTQDTS.xlsx)
- **PMV por prazo** (à vista, 30d, 60d, 90d, 120d, outros) — 46 semanas (jul/2025 → abr/2026)
- **indice_faltas, excesso_curva_a/b/c/d** — importados via `tools/atualizar_excesso_faltas.py` (100 semanas)
- Para novas semanas: preencher manualmente no portal

---

## Fórmulas e cálculos

### Ciclo de Financiamento

**Fórmula correta:** `Ciclo = PMP − PMV − PME`

- **Positivo** = favorável (fornecedores financiam a operação, PMP > PMV + PME)
- **Negativo** = desfavorável (farmácia financia o capital de giro)
- Usa `pme_excel` (do ERP) quando disponível; fallback para PME calculado (`estoque × 30 / CMV`)
- Retorna `None` quando `pmp == 0 AND pmv == 0`

### Contas a Receber (matrixVal)

`contas_receber = cartoes + convenios + cheques + trade_marketing + outros_qt` (quando campo direto é 0)

> Inclui trade_marketing e outros_qt — igual à estrutura da planilha de controle.

### Contas a Pagar / Dívidas (matrixVal)

- `contas_pagar = fornecedores + investimentos_assumidos + outras_despesas_assumidas`
- `dividas = financiamentos + tributos_atrasados + acoes_processos`

---

## Backend — FastAPI + Supabase SDK

### Autenticação — dois níveis

| Nível | Como funciona | Endpoints |
|-------|---------------|-----------|
| **Cliente** | `Authorization: Bearer <supabase_jwt>` + `X-Tenant-Id: UUID` | `/api/v1/avaliacoes/*`, `/api/v1/me/*` |
| **Admin** | `X-Admin-Token: <admin_token>` | `/api/v1/admin/*` |

### Endpoints relevantes

- `POST /api/v1/auth/login` — e-mail + senha → JWT + tenant_id (login independente do cliente)
- `POST /api/v1/auth/definir-senha` — access_token Supabase + nova_senha → atualiza senha + retorna JWT + tenant_id
- `POST /api/v1/admin/abrir-portal/{tenant_id}` — gera JWT para acesso ao portal cliente
- `POST /api/v1/admin/branding/{tenant_id}/logo` — upload de logo (JPG/PNG/WebP ≤2MB) para Supabase Storage bucket `logos`
- `GET/POST /api/v1/admin/usuarios` — gestão de `tenant_usuarios`
- `POST /api/v1/admin/usuarios/{id}/enviar-convite` — gera link Supabase Auth (tenta `recovery` primeiro, depois `invite`) + salva `qtqd_usuario_id`/`qtqd_tenant_id` no `app_metadata` do Auth + envia e-mail
- `POST /api/v1/avaliacoes/{id}/fechar` — muda status para `fechada`
- `POST /api/v1/avaliacoes/{id}/finalizar` — muda para `finalizado` + envia e-mail de relatório
- `POST /api/v1/avaliacoes/{id}/reenviar-relatorio` — reenvia e-mail do relatório sem alterar status

### Supabase SDK — padrões

```python
from backend.app.db.client import get_supabase
sb = get_supabase()
result = sb.table("avaliacoes_semanais").select("*").eq("tenant_id", str(tid)).execute()
rows = result.data
```

**Regras:** UUIDs e datas como `str()`. JSONB vem como `dict`. `updated_at` manual em todo UPDATE.

> **CRÍTICO — sem singleton:** `get_supabase()` cria um cliente **novo a cada chamada** (sem cache). Isso evita que `sb.auth.get_user(jwt)` contamine o cliente com o JWT do usuário, quebrando as queries de banco por RLS nas requisições seguintes. **Nunca reverter para singleton.**

---

## Frontend Cliente — Painel (matrixRows)

O painel usa `matrixRows` (definido em `script.js`) com **3 níveis de hierarquia**:

| Nível | rowClass | Descrição |
|-------|----------|-----------|
| Cabeçalho de grupo | `row-header` | QT, QD, Saldo/Índice — bold, ícone |
| Linha pai | `row-subheader` | contas_receber, contas_pagar, dividas, pmv — semi-bold, indent leve |
| Sub-item | `subItem: true` | cartoes, fornecedores, financiamentos, pmv_avista etc. — indent 32px, fonte 11px |

**CSS:**
- `.row-subheader` — font-weight 700, padding-left 14px, fundo `surface-2`
- `.matrix-subitem` — padding-left 22px, font 12px, cor muted
- `.matrix-subitem-deep` — padding-left 32px, font 11px, cor muted (sub-itens de row-subheader)

### Funções auxiliares no script.js

- `matrixVal(r, key)` — calcula totais de grupos a partir de sub-itens quando campo direto é 0
- `fmtMoneyShort(v)` — formata valores monetários abreviados (R$ 1,9M, R$ 234K)
- `fmtNumInput(v, dec)` — formata número para exibição em input (pt-BR: 1.234,56)
- `parseMoney(v)` — aceita formato pt-BR (`1.234,56`) e EN (`1234.56`), incluindo negativos
- `fmtPercent(v)` — formata como percentual
- `populateYearFilter()` — popula o `<select id="matrixYearFilter">`
- `isoToBr(d)` — converte `YYYY-MM-DD` → `dd/mm/yyyy` (usado em `fillForm` para exibir data no input)
- `brToIso(d)` — converte `dd/mm/yyyy` → `YYYY-MM-DD` (usado em `collectFormData` ao salvar)
- `publishedRecords()` — retorna `records.filter(r => r.status !== 'rascunho')` — usado em TODOS os renders analíticos (painel, inspetor, gráficos). `renderHistory()` usa `records` completo.

---

## Frontend Cliente — Formulário de Lançamentos

Todos os inputs numéricos usam `type="text" inputmode="decimal"`. O `fillForm()` formata os valores em pt-BR ao carregar. O `parseMoney()` aceita ambos os formatos na leitura.

**Sub-grupos visuais** (borda azul à esquerda + label em uppercase):
- `.form-subgroup` + `.form-subgroup-label` (CSS em styles.css)
- QT: **Contas a receber** → [Total, Cartões, Convênios, Cheques, Trade marketing, Outros]
- QD: **Contas a pagar** → [Total, Fornecedores, Investimentos, Outras despesas]
- QD: **Dívidas** → [Total, Financiamentos, Tributos atrasados, Ações e processos]
- Indicadores: **PMV** → [Total, À Vista, 30d, 60d, 90d, 120d, Outros]

---

## Frontend Cliente — Configuração de campos (admin → cliente)

O admin configura visibilidade e labels em **Campos** (painel admin). O cliente carrega via `getMyComponentesConfig()` no startup dentro de `initializeClient()`.

**Ordem crítica (timing):** a config de campos é carregada em `Promise.all([getMyBranding(), getMyComponentesConfig()])` ANTES do primeiro `renderAll()`. Isso garante que campos ocultos não reapareçam ao abrir o portal.

1. Carrega branding + config de campos em paralelo
2. Aplica visibilidade e labels de **todos** os campos (não só `custom_`)
3. Salva em `localStorage` (`qtqd_field_config_v1`)
4. Chama `renderAll()` — propaga para formulário, painel e gerador de gráficos

> **Importante:** campos `custom_` também são adicionados ao `chartFieldCatalog`.

---

## Frontend Cliente — Inspetor IA

Seção inicial do portal (abre por padrão ao entrar).

- **Botão "Analisar"** (`#refreshInspectorButton`) — renderiza conteúdo completo
- **Botão "Gerar PDF"** (`#downloadPdfButton`) — força re-render, aguarda 1s, abre `window.print()`
- **4 KPIs** com borda colorida condicional (`#inspectorHero`)
- **Semáforo 6 indicadores:** Liquidez, Saldo, PMP, PMV, PME, Ciclo (`#inspectorSemaphore`)
  - Ciclo: verde ≥ +10 / amarelo ≥ −10 / vermelho < −10
- **Barras de composição QT e QD** (`#inspectorQtBars`, `#inspectorQdBars`)
- **Gráfico evolução** duplo eixo: QT/QD/Saldo + Índice (`#efficiencyChart`)
- **Diagnóstico IA em streaming** com formatação markdown (`#inspectorNarrative`)
- **Riscos** com ícones (`#inspectorRisks`) e **Ações numeradas** (`#inspectorActions`)
- **Tabela histórica** mais recente primeiro (`#inspectorDataTable`)

---

## Frontend Cliente — PDF (window.print)

O PDF usa CSS `@media print` em `styles.css`. **NÃO usa jsPDF.**

**Estratégia:**
1. `generateInspectorPdf()` chama `renderInspector()` + aguarda 1000ms
2. Completa o streaming do narrativo antes de imprimir
3. Preenche `#printHeader` com logo do cliente + nome + data
4. Chama `window.print()` — browser gera PDF nativo

**CSS `@media print`:**
- Reseta variáveis CSS para tema claro (`body[data-theme="dark"]` tem spec maior que `:root` — precisa incluir `body[data-theme], body[data-theme="dark"]` no seletor)
- Oculta sidebar, topbar, page-hero, botões
- Força `display:grid` em `.inspector-hero-grid` e `.semaphore-grid` (não pode depender só das variáveis)
- `@page` com margens A4 e numeração de páginas

**Cabeçalho/rodapé de impressão:**
- `#printHeader` / `#printFooter` — class `.print-only` (ocultos na tela, visíveis só no print)
- Rodapé: logo Service Farma + "Service Farma · Grupo A3 · Direitos Reservados"

---

## Frontend Cliente — Gerador de Gráficos

`chart_builder.js` substitui completamente `renderChartsPanel()` do `script.js`.

- Campos organizados por grupo (usa `matrixRows` para estrutura)
- Respeita `isFieldVisible()` — campos desativados no admin não aparecem
- Configurador oculto por padrão, abre via botão "Criar novo gráfico" (`#cbToggleNew`)
- Após salvar gráfico, configurador fecha automaticamente
- **Botão Editar** em cada gráfico salvo: abre painel inline com campo de nome e botões ↑/↓ para reordenar
- **Formatação correta por tipo de campo:** `fmtVal` trata `percent` (→ `fmtPercent`), `days` (→ `fmtDays`), `number` (→ `fmtNum`) e `currency` (→ `fmtMoneyShort` abreviado). Eixo Y também respeita o formato do campo.
- **`matrixVal()` nos gráficos:** campos como `dividas`, `contas_receber`, `contas_pagar` usam `matrixVal()` para calcular totais corretos (evita valor zero quando campo direto é 0)

---

## Frontend Cliente — IDs obrigatórios no HTML

**Formulário:**
`weeklyForm`, `recordId`, `weekDate`, `recordStatus`, `formModeBadge`, `formCalculatedKpis`

**Painel:**
`matrixTableWrap`, `matrixYearFilter`

**Gráficos (legado — ocultos):**
`chartFieldsGrid`, `chartRangeCount`, `chartPanelTitle`, `financialTimelineChart`

**Gráficos (chart_builder.js):**
`cbFieldButtons`, `cbSelectedFields`, `cbName`, `cbCountInput`, `cbPreview`, `cbSave`, `cbClear`, `cbPreviewWrap`, `savedChartsContainer`, `cbToggleNew`, `cbNewCard`, `cbCollapseNew`

**Navegação:**
`newEntryButton`, `seedDemoButton`, `openGraphsButton`, `openInspectorButton`, `resetFormButton`, `evaluateButton`, `toggleFocusButton`, `backFromPanelButton`, `refreshInspectorButton`, `downloadPdfButton`, `sidebarMiniToggle`, `sidebarRevealButton`

**Impressão:**
`printHeader`, `printClientLogo`, `printClientName`, `printDate`, `printFooter`

**Campos do formulário (IDs dos inputs — todos `type="text"`):**
`saldo_bancario`¹, `contas_receber`, `cartoes`, `convenios`, `cheques`, `trade_marketing`, `outros_qt`, `estoque_custo`,
`contas_pagar`, `fornecedores`, `investimentos_assumidos`, `outras_despesas_assumidas`, `dividas`, `financiamentos`, `tributos_atrasados`, `acoes_processos`,
`faturamento_previsto_mes`, `compras_mes`, `entrada_mes`, `venda_cupom_mes`, `venda_custo_mes`, `lucro_liquido_mes`¹,
`pmp`, `pmv`, `pme_excel`, `indice_faltas`, `pmv_avista`, `pmv_30`, `pmv_60`, `pmv_90`, `pmv_120`, `pmv_outros`,
`excesso_curva_a`, `excesso_curva_b`, `excesso_curva_c`, `excesso_curva_d`

¹ Podem ser negativos.

---

## Status das avaliações (lançamentos)

| Status | Significado | Efeito técnico |
|--------|-------------|----------------|
| `rascunho` | Lançamento incompleto/em edição | **Excluído** de `publishedRecords()` → não aparece em painel, inspetor IA, gráficos, `getLatestRecord()`. Aparece no histórico com botão **"Fechar"** (azul). |
| `fechada` | Lançamento encerrado normalmente | **Incluído** em todas as análises. Status padrão após clicar "Fechar". |
| `finalizado` | Encerrado com envio de relatório | **Incluído** nas análises. Gerado pelo botão "Finalizar" (envia e-mail automático via `relatorio_service`). |

> Botão **"Fechar"** no histórico: aparece só para linhas com `status === 'rascunho'`. Chama `POST /avaliacoes/{id}/fechar` e re-renderiza tudo via `renderAll()`.
> Botão **"Reenviar PDF"**: aparece em todas as linhas no modo API. Chama `POST /avaliacoes/{id}/reenviar-relatorio`.

## Status dos clientes (tenants no Admin)

| Status | Badge | Significado |
|--------|-------|-------------|
| `implantacao` | laranja | Cliente em processo de implantação |
| `ativo` | verde | Cliente com acesso ativo |
| `inativo` | cinza | Cliente desativado |
| `cancelado` | vermelho | Contrato encerrado |

> **Atenção:** O status do tenant é **apenas informativo** — não bloqueia login, acesso ao portal ou nenhuma funcionalidade técnica. É exibido no card do cliente no admin e usado para filtros visuais. Para bloquear acesso de um usuário específico, use `ativo = false` no registro de `tenant_usuarios`.

---

## Multi-tenant e modos de operação

- **Modo simulação:** `mode: "simulation"` — dados no localStorage
- **Modo API:** JWT no localStorage (`qtqd_jwt_v1`) + tenant_id (`qtqd_tenant_id_v1`)
- **Auto-detecção:** `getRuntimeConfig()` verifica localStorage e ativa modo API automaticamente
- **Ativação por URL:** `?token=JWT&tenant_id=UUID` — portal lê, armazena e limpa a URL
- **X-Tenant-Id:** `api_client.js` envia em todos os requests autenticados

## Permissões de usuário (`permissao` em `tenant_usuarios`)

| Valor | Significado | Efeito no portal |
|-------|-------------|-----------------|
| `edita` | Acesso completo | Pode criar/editar/excluir lançamentos e gráficos |
| `visualiza` | Somente leitura | Vê tudo, mas sem botões de edição nos gráficos nem "Criar novo gráfico" |
| `relatorio` | Somente relatórios | (reservado para uso futuro) |

- `permissao` é retornada no login e gravada em `localStorage['qtqd_permissao_v1']`
- Helper `canEdit()` em `script.js` — retorna `true` se ausente (simulação/admin) ou `=== 'edita'`
- Admin abrindo portal via URL params recebe `'edita'` automaticamente

## Gráficos personalizados — armazenamento por tenant

- Gráficos salvos ficam em `tenants.charts_config` (JSONB) — **compartilhados entre todos os usuários do tenant**
- Em modo API: `chart_builder.js` usa `GET/PUT /me/charts-config` via `QTQD_API_CLIENT`
- Em modo simulação: fallback para `localStorage['qtqd_saved_charts_v2_<tenant_id>']`
- **Migração automática:** na primeira abertura em modo API com banco vazio, migra do localStorage para o banco e limpa a chave local
- Coluna adicionada ao Supabase: `ALTER TABLE tenants ADD COLUMN IF NOT EXISTS charts_config JSONB DEFAULT '[]'::jsonb`

## Autenticação do cliente — fluxo completo

### Primeiro acesso (via convite)
1. Admin cria usuário em **Usuários** no painel admin (nome, e-mail, permissão)
2. Admin clica **"Enviar convite + instalar app"** → backend tenta `recovery` primeiro (preserva UUID existente), depois `invite` (usuário novo) → salva `qtqd_usuario_id` e `qtqd_tenant_id` no `app_metadata` do Supabase Auth → envia e-mail
3. Cliente clica no botão do e-mail → abre `https://qtqd-vt2a.vercel.app/instalar#access_token=...`
4. Página `/instalar` lê o `access_token` do hash, exibe formulário de senha
5. Cliente digita senha → POST `/api/v1/auth/definir-senha` → backend lê `app_metadata.qtqd_usuario_id` (lookup por ID primário, mais confiável) + atualiza senha + faz login + retorna JWT + tenant_id
6. Frontend armazena JWT + tenant_id → redireciona automaticamente para `/cliente` após 3 segundos
7. Modal de instalação PWA aparece 2s após abrir o portal → cliente clica **"Instalar agora"** → ícone na área de trabalho

> **Fluxo do convite — ordem recovery/invite é crítica.** Usar `invite` para e-mail já existente no Supabase Auth recria o UUID do usuário, o que pode acionar CASCADE DELETE na `tenant_usuarios` se houver FK oculta. Sempre tentar `recovery` primeiro.

### Acessos seguintes (login normal)
- Portal detecta `qtqd_tenant_id_v1` sem `qtqd_jwt_v1` → exibe tela de login (`#loginOverlay`)
- Cliente digita e-mail + senha → POST `/api/v1/auth/login` → JWT + tenant_id armazenados → portal carrega
- JWT válido por 1 hora; ao expirar, próximo acesso exibe tela de login novamente

### Detecção de JWT expirado
- `initializeClient()` verifica: se `tenant_id` existe mas `jwt` não → exibe login imediatamente
- Se `loadRecordsFromSource()` lança erro 401 → limpa JWT expirado → exibe login

### Funções de login em `script.js`
- `showLoginScreen()` / `hideLoginScreen()` — controla visibilidade do overlay `#loginOverlay`
- `doLogin(email, password)` — chama `api_client.login()`, armazena credenciais + `permissao`
- `handleLogin()` — handler do botão, chama `doLogin` e depois `initializeClient()`
- `isExpiredOrUnauthorized(msg)` — detecta erros 401/unauthorized/expired
- `canEdit()` — retorna `true` se `qtqd_permissao_v1` é `'edita'` ou ausente

---

## Histórico de problemas resolvidos

1. **CSS não carregava na Vercel:** `<base href="/cliente/">` no `<head>`.
2. **Coluna fixa instável:** usar `<table>` com `position: sticky; left: 0`.
3. **Gráfico não aparecia após `destroy()`:** `outer.innerHTML = '<canvas...>'` + `setTimeout(30)`.
4. **JWT ES256 vs HS256:** `PyJWKClient` com JWKS automático.
5. **Rota `/health` não encontrada:** adicionar ao `vercel.json`.
6. **Variáveis de ambiente no projeto errado:** usar `prj_59oqSmERo1jp5hn7RwcaVBuRf9Hn`.
7. **Conexão direta ao banco falhou:** substituir por Supabase Python SDK (HTTPS).
8. **Chave `sb_secret_...` inválida:** usar aba "Legacy" no Supabase Dashboard.
9. **Email vazio causava erro 422:** `value.trim() || null`.
10. **Sticky column transparente:** `accent-soft` é rgba — usar `var(--surface-2)` sólido em `.matrix-sticky.row-header`.
11. **Campos calculados ocultos no painel:** fix: usar `configurableKeys` baseado em `componentLabels`.
12. **Ciclo com valores absurdos:** só calcular quando `pmp > 0 OR pmv > 0`; fórmula correta `PMP − PMV − PME` (não `PME + PMV − PMP`).
13. **Backend crash com `import openpyxl`:** tornar import lazy.
14. **`python-multipart` faltando:** necessário para `File`/`UploadFile` no FastAPI.
15. **Excesso/faltas não importados:** colunas Excel com fórmulas sem cache — lidas com `data_only=True` só nas últimas colunas. Script `atualizar_excesso_faltas.py` atualiza registros existentes.
16. **Flash de Lançamentos ao abrir portal:** Service Worker servindo script.js antigo. Fix: incrementar versão do SW (`qtqd-v3`) + chamar `openSection("inspetor")` antes do await.
17. **PDF com conteúdo invisível:** CSS variables do tema escuro (`--ink`, `--surface-2`) não eram sobrescritas pelo `@media print`. Fix: incluir `body[data-theme="dark"]` no seletor de reset + `display:grid/flex !important` explícito nos containers.
18. **Config de campos do admin não propagava:** o loader de `getMyComponentesConfig()` só processava campos `custom_`. Fix: aplicar visibilidade/labels de todos os campos e salvar no localStorage.
19. **Inputs com formato inglês:** `type="number"` exibe ponto decimal. Fix: mudar para `type="text" inputmode="decimal"` + `parseMoney()` aceita pt-BR + `fillForm()` formata em pt-BR.
20. **Preview de logo no admin não abria:** `addEventListener('change')` com timing. Fix: usar `onchange="previewLogoFile(this)"` inline no HTML + `URL.createObjectURL()`.
21. **Campos ocultos reapareciam ao abrir portal:** `getMyComponentesConfig()` era chamado após `renderAll()` em IIFE separada. Fix: mover para dentro de `initializeClient()` com `Promise.all([branding, cfg])` antes do `renderAll()`.
22. **Gráfico Dívidas zerado:** `chart_builder.js` usava `p.record[field.key]` diretamente, bypassando `matrixVal()`. Fix: usar `matrixVal(p.record, field.key)` nos gráficos salvos.
23. **Percentual exibido como R$ nos gráficos:** `fmtVal` não tratava `field.format === 'percent'`. Fix: adicionar case e usar `fmtPercent(v)`. Eixo Y também atualizado para respeitar formato do campo.
24. **Rótulos monetários muito longos nos gráficos:** `fmtVal` usava `fmtMoney` completo. Fix: usar `fmtMoneyShort` (abreviado: R$ 1,9M, R$ 234K).
25. **Cliente perdia acesso ao expirar o JWT:** sem tela de login, portal caía em modo simulação silenciosamente. Fix: `#loginOverlay` detecta `tenant_id` sem `jwt` e exibe formulário de e-mail + senha.
26. **Data do lançamento exibida em ISO no formulário:** `fillForm()` usava `record.weekDate` diretamente (YYYY-MM-DD). Fix: `isoToBr()` para exibição + `brToIso()` em `collectFormData` para salvar.
27. **Rascunhos alimentando gráficos/inspetor:** `records` sem filtro incluía rascunhos. Fix: `publishedRecords()` filtra `status !== 'rascunho'` em todos os renders analíticos.
28. **Singleton do Supabase contaminado por auth.get_user():** `sb.auth.get_user(jwt)` atualiza a sessão interna do cliente singleton, fazendo queries seguintes usarem o JWT do usuário em vez da service role key. RLS bloqueava todas as queries. Fix: `get_supabase()` cria cliente fresco a cada chamada (sem singleton).
29. **Convite apagava registro da tenant_usuarios:** `generate_link(type="invite")` para e-mail já existente no Supabase Auth pode recriar o UUID (trigger CASCADE DELETE se houver FK oculta). Fix: tentar `recovery` primeiro, `invite` só para novos.
30. **definir-senha não encontrava usuário:** lookup por email falhava por RLS (causa #28). Fix: após auth.get_user(), usar `app_metadata.qtqd_usuario_id` (gravado no envio do convite) para lookup direto por ID primário.
31. **Botão "Criar senha" na /instalar não respondia:** referência a `#pwaInstallBtn` (removido do HTML) causava TypeError ao registrar event listener, impedindo todos os handlers da página. Fix: remover o código JS do elemento inexistente.
32. **Admin token inválido após request de definir-senha:** causa era o singleton contaminado (#28) que quebrava `listClients`. Fix: singleton removido (ver #28).
33. **Raiz `/` expunha link "Abrir Admin" para clientes:** `validar_fronts.html` era página de desenvolvimento visível em produção. Cliente que caía na raiz (convite antigo sem `redirect_to`) via botão e acessava o painel admin. Fix: `/` agora redireciona direto para `/cliente`; hash com `access_token` ainda vai para `/instalar`.
34. **Gráficos não apareciam para novos usuários:** gráficos salvos em `localStorage` são específicos do dispositivo. Usuário com permissão `visualiza` em outro computador via seção vazia. Fix: gráficos migrados para `tenants.charts_config` (banco), compartilhados entre todos os usuários do tenant. Migração automática do localStorage na primeira abertura.
35. **"Acessar Portal" falhava com HTTP 500 / "Usuario sem acesso":** `abrir-portal` faz login como admin (`portal_admin_email`) mas não garantia que esse usuário existia em `tenant_usuarios` para o tenant solicitado. Fix: endpoint verifica e insere automaticamente o admin em `tenant_usuarios` se ausente.

---

## Relatório por E-mail

### Fluxo
1. Botão **"Fechar"** no histórico (status `rascunho`) → `POST /api/v1/avaliacoes/{id}/fechar`
2. Backend muda status para `fechada` e chama `enviar_relatorio_para_tenant()`
3. `relatorio_service.py` busca as últimas `n_retratos` avaliações **excluindo rascunhos**
4. Gera o HTML do e-mail (`relatorio_html.py`) e envia via SMTP — **sem anexo PDF**
5. Botão **"Reenviar"** no histórico → `POST /api/v1/avaliacoes/{id}/reenviar-relatorio` (não altera status)

> **Não há mais PDF em anexo.** Tentativas de gerar PDF server-side idêntico ao portal falharam por limitações do ambiente Lambda (sem acesso a browser, libs nativas indisponíveis). O e-mail envia apenas o corpo HTML.

### Corpo do e-mail (`relatorio_html.py`)
- Tabela de indicadores: N retratos configurados no admin, **mais recente à esquerda** (`list(reversed(periodos))`)
- Indicadores exibidos: QT Total, QD Total, Saldo QT/QD, Índice QT/QD, Saldo s/ Dívidas, PME, PMP, PMV, Ciclo Financeiro
- **Dados corretos:** PMV, PMP e PME usam os campos **raw** do input do usuário (`pmv`, `pmp`, `pme_excel`) — não os calculados (`prazo_venda`, `prazo_medio_compra`, `pme` calculado). Isso garante os mesmos valores que aparecem no portal.
- Logo Service Farma no rodapé: `height:40px; width:auto` (proporcional)
- Link "Acessar portal →" para o cliente gerar o Inspetor IA completo

### Parâmetro de teste
`POST /api/v1/avaliacoes/{id}/reenviar-relatorio?email_teste=addr@x.com`
→ Restringe o envio apenas a esse e-mail.
No admin: campo "E-mail para teste" na seção Relatório.

### Arquivos envolvidos
| Arquivo | Responsabilidade |
|---|---|
| `services/relatorio_html.py` | Template HTML do e-mail — 100% tabela, compatível com Gmail/Outlook/Apple Mail |
| `services/relatorio_service.py` | Orquestra: busca dados, gera HTML, envia; aceita `email_teste` |
| `services/email_service.py` | `send_html()` — SMTP_SSL (465) ou STARTTLS (587) conforme `SMTP_PORT` |
| `api/v1/avaliacoes.py` | `/fechar` → envia e-mail; `/reenviar-relatorio` aceita `?email_teste=` |

### Configuração (`tenant_pdf_config`)
- Tabela `tenant_pdf_config` por tenant: `n_retratos` (padrão 8), `ativo`, `envio_timing`, `dias_apos`
- Campos `incluir_inspetor` e `incluir_graficos` **ignorados** (removidos da UI)

### SMTP
- Vercel env: `SMTP_PORT=587` → STARTTLS | `SMTP_PORT=465` → SSL direto
- Host: `mail.servicefarma.far.br` | User: `comercial@servicefarma.far.br`

---

## Admin — Seção "Relatório" (ex-"Envio PDF")

| Elemento | Função |
|---|---|
| Select **Cliente** | Carrega config do tenant (reset automático ao trocar) |
| **Nº de retratos** | Quantas semanas aparecem no corpo do e-mail |
| **Envio automático ativo** | Liga/desliga disparo automático ao fechar lançamento |
| **E-mail para teste** | Se preenchido, envia só para esse endereço |
| Botão **"Salvar configuração"** | Persiste em `tenant_pdf_config` |
| Botão **"Enviar relatório"** | Dispara o e-mail imediatamente (com ou sem e-mail teste) |
| Botão **"Baixar PDF"** | Abre o portal do cliente com `?autoprint=1` → browser gera PDF **idêntico ao portal** via `window.print()` |

> **"Baixar PDF" funciona assim:** chama `POST /admin/abrir-portal/{tenant_id}` → obtém JWT → abre `https://qtqd-vt2a.vercel.app/cliente?token=JWT&tenant_id=UUID&autoprint=1` em nova aba → portal detecta `window._qtqdAutoprint=true` → após carregar, chama `generateInspectorPdf()` que executa `window.print()`. O PDF resultante é idêntico ao que o cliente vê no Inspetor IA.

---

## Clientes — Situação atual (2026-05-01)

| Cliente | tenant_id | Lançamentos | Observação |
|---|---|---|---|
| Total Socorro / Drogaria da Letícia | `b2ce08a4-b1f9-4465-b162-9f5e9bb70092` | 103+ semanas | Jun/2024 → atualização contínua |
| Drogaria SV | `8044331a-4531-47c9-bbff-6546110d5767` | 65+ semanas | Jul/2024 → atualização contínua; e-mail configurado |

---

## Histórico de problemas resolvidos (continuação)

36. **E-mail com PMV/PMP/PME errados (0 ou absurdos):** `relatorio_html.py` usava campos calculados (`prazo_venda`, `prazo_medio_compra`, `pme`) que dependem de `venda_cupom_mes`/`compras_mes` (muitas vezes zerados). Fix: usar campos raw `pmv`, `pmp`, e `pme_excel` (com fallback para `pme` calculado), igual ao portal.
37. **`pdfClient` não populava ao entrar na seção:** `populateClientSelects()` tinha lista fixa sem `pdfClient`. Fix: adicionar `'pdfClient'` à lista.
38. **Troca de cliente mostrava config do anterior:** campos do painel PDF não eram limpos antes do load async. Fix: reset para defaults imediatamente ao trocar o select.
39. **PDF server-side não replicável:** todas as libs que convertem HTML→PDF (xhtml2pdf, WeasyPrint) dependem de Cairo/Pango (libs nativas indisponíveis no Vercel Lambda). matplotlib gera charts mas diferentes do Chart.js do portal. Decisão: **sem PDF em anexo**; e-mail envia só HTML; botão "Baixar PDF" no admin abre o portal com `?autoprint=1`.
40. **`xhtml2pdf` quebrava o build:** depende de `pycairo` que requer Cairo em nível de sistema. Fix: remover `xhtml2pdf` do `requirements.txt`.
41. **`indice_faltas` exibindo 682% ao digitar 6,82:** campo é armazenado como ratio (0–1), mas o formulário não fazia a conversão. Fix: `fillForm` multiplica por 100 antes de exibir; `collectFormData` divide por 100 antes de salvar. Único registro incorreto corrigido diretamente no banco (Drogaria SV, semana 2026-05-01: 6.82 → 0.0682).

> **Convenção `indice_faltas`:** armazenado como **ratio decimal** (ex: 0.0682 = 6,82%). No formulário, o usuário digita o valor percentual (6,82) e o sistema converte automaticamente. `fmtPercent()` multiplica por 100 para exibição — não alterar essa lógica.

---

## Segurança (pendente)

- Regenerar `SUPABASE_SERVICE_ROLE_KEY` após estabilização
- Revogar tokens GitHub usados durante implantação inicial

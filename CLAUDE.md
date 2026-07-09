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

## ⚠️ CRÍTICO — Autenticação e Service Worker

> **Esta é a parte mais sensível do sistema. Qualquer alteração nos arquivos abaixo exige análise cuidadosa de impacto antes de qualquer mudança:**
>
> - `frontend_cliente/script.js` — qualquer erro de sintaxe (ex: template literals aninhados mal formados) derruba o script inteiro e o portal para de funcionar completamente, sem mensagem de erro visível ao usuário
> - `shared/api_client.js` — lê JWT e tenant_id do `localStorage`; não alterar sem testar o fluxo completo de login
> - `frontend_cliente/sw.js` — cada bump de versão exige Ctrl+Shift+R nos clientes; usar com parcimônia
> - `frontend_admin/script.js` — o botão "Acessar Portal" usa `window.open(url, '_blank')` com URL contendo `?token=JWT&tenant_id=UUID`; a IIFE em `script.js` do portal processa esses parâmetros; qualquer mudança nesse fluxo precisa ser testada end-to-end

### Fluxo "Acessar Portal" — como funciona (NÃO ALTERAR sem teste completo)

1. Admin clica "Acessar Portal" → `POST /admin/abrir-portal/{tenant_id}` → JWT do admin
2. Admin abre `https://qtqd-vt2a.vercel.app/cliente?token=JWT&tenant_id=UUID` via `window.open(url, '_blank')`
3. Portal carrega; IIFE em `script.js` lê `?token=` e `?tenant_id=`, grava em `localStorage` via `QTQD_API_CLIENT.setJwt/setTenantId`, remove params da URL
4. `initializeClient()` lê `localStorage`, detecta modo API, carrega dados do tenant correto

> **Lição aprendida (2026-05-18):** Um SyntaxError em template literal aninhado no `buildInspectorNarrative` impediu a execução do `script.js` inteiro. O portal entrava em modo simulação silenciosamente — sem nenhuma mensagem de erro visível. Horas foram gastas tentando "corrigir" o fluxo de autenticação quando o real problema era um erro de sintaxe JS. **Sempre verificar o console do browser (F12) antes de tentar qualquer fix de autenticação.**

### Regra de ouro para o `script.js`

- Nunca usar template literals aninhados (backtick dentro de `${}` dentro de outro backtick) — usar concatenação de strings ou variáveis intermediárias
- Após qualquer edição no `script.js`, verificar ausência de erros no console antes de testar funcionalidades

---

## Regras obrigatórias

- **Idioma:** Sempre responder em português brasileiro
- **Deploy:** Após cada conjunto de alterações, rodar `git push origin main`
- **Caminhos HTML:** Usar `<base href="/cliente/">` no `<head>` do cliente e `<base href="/admin/">` no admin
- **Coluna fixa do painel:** Usar `<table>` HTML real com `position: sticky; left: 0`. Nunca usar CSS Grid para isso.
- **Cabeçalho do painel também congelado:** `thead th` com `position: sticky; top: 0; z-index: 4`. Corner cell (`.matrix-head.matrix-sticky`) precisa de `z-index: 5`.
- **Campos calculados no painel:** Usar `configurableKeys` (apenas os de `componentLabels`) no filtro `visibleRows` — campos calculados como `excesso_total`, `qt_total` etc. devem ser sempre visíveis.
- **Inputs do formulário:** Todos monetários/numéricos usam `type="text" inputmode="decimal"` — NUNCA `type="number"`. Valores exibidos em formato pt-BR (vírgula decimal, ponto milhares).
- **Service Worker:** versão atual `qtqd-v15` em `frontend_cliente/sw.js`. Ao fazer mudanças que devem invalidar cache, incrementar a versão.

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
    excesso_critico.js    Assistente de Excesso Crítico (upload Excel → totais por curva → aplica em lançamento)
    multiloja.js          Módulo isolado multi-loja (seletor de nível, troca de série, Comparativo) — ativo só com modo_rede
    manifest.json         PWA manifest (ícone, start_url, display standalone)
    sw.js                 Service Worker (cache qtqd-v15)
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
      excesso_critico.py  GET/PUT /me/excesso-critico/limites + POST /calcular + POST /aplicar/{avaliacao_id}
      estrutura.py        Multi-loja: admin CRUD grupos/lojas + toggle modo_rede + GET /me/lojas
      comparativo.py      Multi-loja: GET /me/comparativo (snapshot + evolução)
      admin_config.py     POST /admin/abrir-portal/{tenant_id} (auto-registra admin em tenant_usuarios se ausente)
                          POST /admin/branding/{tenant_id}/logo  (upload para Supabase Storage)
                          POST /admin/usuarios/{id}/enviar-convite (gera link Supabase Auth + envia e-mail)
                          GET  /admin/email-log (histórico de envios, filtrável por tenant_id)
    services/
      relatorio_service.py  Orquestra envio: busca dados, gera HTML, envia SMTP, grava em email_log
    schemas/avaliacoes.py
    services/
      calculos_qtqd.py    Indicadores calculados
      consolidacao_service.py  Multi-loja: consolidar_valores (soma aditivos + prazos ponderados)
      series_service.py   Multi-loja: build_series por nível (loja/grupo/rede) + comparativo
      relatorio_html.py   Template HTML do e-mail de relatório
      excel_import.py
  api/index.py
  tools/
    importar_qtqdsv.py           Importação de dados históricos via Excel (base para novos clientes)
    atualizar_excesso_faltas.py  Atualiza excesso_curva_a/b/c/d e indice_faltas nos registros existentes
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
| `RESEND_API_KEY` | API key do Resend para envio de e-mail (começa com `re_...`) — **primário** |

---

## Clientes cadastrados no Supabase

| Nome | tenant_id | Status |
|------|-----------|--------|
| **Total Socorro / Drogaria da Letícia** | `b2ce08a4-b1f9-4465-b162-9f5e9bb70092` | implantacao — **103 semanas importadas** (jun/2024 → abr/2026) |
| Drogaria SV | `8044331a-4531-47c9-bbff-6546110d5767` | implantacao — **65+ semanas importadas**; 7 usuários ativos configurados |

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

**Campo apply-only (persistido só pelo `/aplicar` do Excesso Crítico, sem input no formulário):**
`total_estoque_lancamentos` — soma do estoque de itens em lançamento. Preservado no PATCH/import-excel via `_preserve_apply_only()`. Ver seção Excesso Crítico.

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
- `POST /api/v1/avaliacoes/{id}/fechar` — muda status para `fechada` + envia e-mail se `tenant_pdf_config.ativo = true`
- `POST /api/v1/avaliacoes/{id}/finalizar` — muda para `finalizado` + envia e-mail de relatório
- `POST /api/v1/avaliacoes/{id}/reenviar-relatorio` — reenvia e-mail do relatório sem alterar status
- `GET /api/v1/admin/email-log` — histórico de envios de e-mail (admin)

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
36. **Portal em modo simulação após mudança no Inspetor IA (2026-05-18):** template literals aninhados mal formados em `buildInspectorNarrative` causavam `SyntaxError` no `script.js` inteiro — o script parava de executar silenciosamente, o portal caía em modo simulação mostrando "Cliente Demonstração". Horas gastas tentando corrigir autenticação quando o problema era sintaxe JS. Fix: substituir templates aninhados por concatenação de strings. **Lição: sempre verificar console F12 antes de tentar qualquer fix de autenticação.**

---

## Relatório por E-mail

### Fluxo
1. Botão **"Fechar"** no histórico (status `rascunho`) → `POST /api/v1/avaliacoes/{id}/fechar`
2. Backend muda status para `fechada` e chama `enviar_relatorio_para_tenant()`
3. `relatorio_service.py` busca as últimas `n_retratos` avaliações **excluindo rascunhos**
4. Gera o HTML do e-mail (`relatorio_html.py`) e envia via **Resend** (fallback SMTP) — **sem anexo PDF**
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
| `services/email_service.py` | `send_html()` — usa **Resend** quando `RESEND_API_KEY` configurada; fallback SMTP_SSL (465) ou STARTTLS (587) conforme `SMTP_PORT` |
| `api/v1/avaliacoes.py` | `/fechar` → envia e-mail; `/reenviar-relatorio` aceita `?email_teste=` |

### Configuração (`tenant_pdf_config`)
- Tabela `tenant_pdf_config` por tenant: `n_retratos` (padrão 8), `ativo`
- Campos `incluir_inspetor`, `incluir_graficos`, `envio_timing` e `dias_apos` **ignorados** (removidos da UI e do schema Pydantic — envio é sempre imediato ao fechar)

### Log de envios (`email_log`)
Tabela criada em 2026-05-04. Cada tentativa de envio grava um registro:

| Coluna | Descrição |
|---|---|
| `tenant_id` | Tenant destinatário |
| `avaliacao_id` | Avaliação que disparou o envio (NULL para envios manuais) |
| `enviado_em` | Timestamp UTC do envio |
| `destinatarios` | Array de e-mails que receberam |
| `status` | `'success'` ou `'error'` |
| `erro` | Mensagem de erro SMTP (preenchida só em falhas) |
| `n_destinatarios` | Quantidade de destinatários |
| `origem` | `'fechar'`, `'finalizar'`, `'reenviar'` ou `'admin'` |

> O log é visível no painel admin → **Relatório → Log de envios de e-mail**, filtrado por cliente.

### Envio de e-mail — Resend (primário) + SMTP (fallback)
- **Resend:** usado quando `RESEND_API_KEY` está configurada no Vercel. Mais confiável em ambiente serverless (HTTP API, sem problemas de porta/firewall). Pacote `resend==2.10.0` no `requirements.txt`.
- **SMTP (fallback):** `mail.servicefarma.far.br` | User: `comercial@servicefarma.far.br` | `SMTP_PORT=465` → SSL com `ssl.create_default_context()` | `SMTP_PORT=587` → STARTTLS
- **`reenviar-relatorio` retorna 400** quando não há destinatários ativos com e-mail (antes retornava 200 vazio, parecendo sucesso)

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
| **Log de envios** | Tabela com histórico de todos os envios — data, cliente, origem, destinatários, status/erro. Filtra por cliente ao selecionar; botão "↻ Atualizar" recarrega. |

> **"Baixar PDF" funciona assim:** chama `POST /admin/abrir-portal/{tenant_id}` → obtém JWT → abre `https://qtqd-vt2a.vercel.app/cliente?token=JWT&tenant_id=UUID&autoprint=1` em nova aba → portal detecta `window._qtqdAutoprint=true` → após carregar, chama `generateInspectorPdf()` que executa `window.print()`. O PDF resultante é idêntico ao que o cliente vê no Inspetor IA.

---

## Clientes — Situação atual (2026-07-08)

**12 tenants cadastrados** (o projeto cresceu): Total Socorro (113 semanas), Drogaria SV (74), TREVIZAN & FERNANDES (21), TOTAL ILHABELA (29), TOTAL SÃO CARLOS (18), TOTAL COLINA (8), TOTAL SEVERINIA (7), CONVIVA VIANA (3), TOMAL & OLIVEIRA (3), FARMAPLUS (2), HELIRENE (1), CONVIVA BUENO (0). Total: **279 avaliações**.

> **Multi-loja está dormant:** nenhum cliente tem `modo_rede` ligado ainda (todos operam como loja única, `grupo_id`/`loja_id` NULL). Para ativar, ver a seção "Multi-loja / Grupo Econômico".

| Cliente | tenant_id | Lançamentos | Observação |
|---|---|---|---|
| Total Socorro / Drogaria da Letícia | `b2ce08a4-b1f9-4465-b162-9f5e9bb70092` | 113 semanas | Jun/2024 → atualização contínua |
| Drogaria SV | `8044331a-4531-47c9-bbff-6546110d5767` | 74 semanas | Jul/2024 → atualização contínua; 7 usuários ativos (Admin, AVJ, Caio, Cassiano, Elias, Evandro, Raquel). Validou Excesso Crítico em 2026-05-26 (R$ 425K). |

---

## Histórico de problemas resolvidos (continuação)

36. **E-mail com PMV/PMP/PME errados (0 ou absurdos):** `relatorio_html.py` usava campos calculados (`prazo_venda`, `prazo_medio_compra`, `pme`) que dependem de `venda_cupom_mes`/`compras_mes` (muitas vezes zerados). Fix: usar campos raw `pmv`, `pmp`, e `pme_excel` (com fallback para `pme` calculado), igual ao portal.
37. **`pdfClient` não populava ao entrar na seção:** `populateClientSelects()` tinha lista fixa sem `pdfClient`. Fix: adicionar `'pdfClient'` à lista.
38. **Troca de cliente mostrava config do anterior:** campos do painel PDF não eram limpos antes do load async. Fix: reset para defaults imediatamente ao trocar o select.
39. **PDF server-side não replicável:** todas as libs que convertem HTML→PDF (xhtml2pdf, WeasyPrint) dependem de Cairo/Pango (libs nativas indisponíveis no Vercel Lambda). matplotlib gera charts mas diferentes do Chart.js do portal. Decisão: **sem PDF em anexo**; e-mail envia só HTML; botão "Baixar PDF" no admin abre o portal com `?autoprint=1`.
40. **`xhtml2pdf` quebrava o build:** depende de `pycairo` que requer Cairo em nível de sistema. Fix: remover `xhtml2pdf` do `requirements.txt`.
41. **`indice_faltas` exibindo 682% ao digitar 6,82:** campo é armazenado como ratio (0–1), mas o formulário não fazia a conversão. Fix: `fillForm` multiplica por 100 antes de exibir; `collectFormData` divide por 100 antes de salvar. Único registro incorreto corrigido diretamente no banco (Drogaria SV, semana 2026-05-01: 6.82 → 0.0682).

> **Convenção `indice_faltas`:** armazenado como **ratio decimal** (ex: 0.0682 = 6,82%). No formulário, o usuário digita o valor percentual (6,82) e o sistema converte automaticamente. `fmtPercent()` multiplica por 100 para exibição — não alterar essa lógica.

42. **Flag `ativo` do `tenant_pdf_config` ignorada no `/fechar`:** o endpoint enviava e-mail sempre, independente da checkbox "Envio automático ativo". Fix: verificar `cfg.ativo` antes de chamar `enviar_relatorio_para_tenant`. Envios manuais pelo admin não são afetados.
43. **Campos "Timing de envio" e "Enviar após quantos dias" sem implementação:** existiam na UI e no schema Pydantic mas nunca foram lidos no backend — o envio sempre foi imediato. Fix: removidos do HTML, JS e `PdfConfigRequest`. Campos `envio_timing` e `dias_apos` permanecem no banco mas são ignorados.
44. **Log de envios ausente:** falhas de SMTP eram silenciadas por `except: pass` sem rastro. Fix: tabela `email_log` no Supabase + `relatorio_service.py` grava sucesso/erro em bloco `finally` após cada envio. Endpoint `GET /admin/email-log` e seção visual no painel admin.
45. **E-mail não enviado ao fechar lançamento (Drogaria SV, mai/2026):** `email_service.py` usava apenas SMTP direto; servidor `mail.servicefarma.far.br` retornava `535 Incorrect authentication data` para IPs do Vercel (AWS). `RESEND_API_KEY` existia no Vercel mas nunca havia sido integrada ao código. Fix: `email_service.py` agora usa Resend quando `RESEND_API_KEY` configurada, com fallback SMTP. Padrão idêntico ao PEC-SF. Pacote `resend==2.10.0` adicionado ao `requirements.txt`.
46. **`reenviar-relatorio` mostrava sucesso falso com destinatários vazios:** endpoint retornava 200 com lista vazia quando não havia usuários ativos com e-mail; frontend exibia "PDF reenviado para destinatários cadastrados." Fix: endpoint agora retorna 400 com mensagem clara, igual ao endpoint admin.
47. **Data de lançamento fechado não podia ser editada:** `AvaliacaoUpdateRequest` não incluía `semana_referencia`; endpoint PATCH e payload do frontend também não a enviavam — a data ficava inalterada após salvar. Fix: campo `semana_referencia` adicionado ao schema, ao endpoint PATCH e ao payload do frontend.

48. **E-mail não enviado ao fechar pelo formulário (Drogaria SV, 22/05/2026):** Usuário mudou o status para "fechada" usando o select de status no formulário de edição e salvou — isso chama `PATCH`, não `POST /fechar`. O `PATCH` apenas salva dados, nunca dispara e-mail. O `POST /fechar` (que envia e-mail) só é chamado pelo botão "Fechar" no histórico (exclusivo de registros `rascunho`). Fix: o endpoint `PATCH` agora detecta a transição `rascunho → fechada` e dispara `enviar_relatorio_para_tenant` automaticamente. Frontend exibe "Fechando semana e enviando e-mail..." durante o processo e "Semana fechada. E-mail enviado para os destinatários cadastrados." ao concluir. Também corrigido o `config.py`: validator Pydantic para `smtp_port` aceita string vazia (usa default 465), evitando `ValidationError` silencioso caso `SMTP_PORT=""` seja configurado no Vercel.

> **Lição aprendida (2026-05-22):** O `PATCH` e o `POST /fechar` atingem o mesmo campo `status`, mas apenas `/fechar` enviava e-mail. O `except Exception: pass` no `/fechar` silenciava erros — sem log nenhum. Diagnóstico confirmado pelos logs do Vercel, que mostraram somente `PATCH` e nenhum `POST /fechar` para aquela avaliação. Sempre verificar os logs do Vercel (`vercel logs --environment production --since 3h --no-follow`) antes de investigar a API de e-mail.

49. **Upload do Excel de Excesso Crítico falhava com HTTP 413 (Drogaria SV, 26/05/2026):** o cliente tentou importar o arquivo `excesso_tabela_fabricante.xlsx` (1.7 MB) e recebeu "Erro HTTP 413". A primeira versão da feature subia o arquivo via multipart para `/me/excesso-critico/calcular` e processava com openpyxl no backend. Logs do Vercel mostraram `source: "static"` e `responseStatusCode: 413` — o request **não chegava na função Python**, era rejeitado pelo Edge do Vercel. Apesar da doc oficial mencionar 4.5 MB de limite de body, o limite efetivo do runtime Python no Vercel para multipart é menor (~1–2 MB na prática). Fix: refatorar para processar o XLSX **100% no browser** via SheetJS (`xlsx@0.18.5` por CDN). A regra de cálculo foi espelhada em JS com paridade exata validada contra o Python (R$ 425.542,14 idêntico nos dois ambientes). Backend `/calcular` permanece como API mas a UI usa só `/aplicar/{avaliacao_id}` (payload de poucos KB). Resolve uploads de qualquer tamanho.

> **Lição aprendida (2026-05-26):** Para qualquer upload de arquivo "grande" (>1MB) no Vercel Python runtime, NÃO usar multipart. Processar no browser (XLSX/CSV via SheetJS/Papaparse) e mandar só o resultado agregado. O limite documentado de 4.5MB não vale para o Python runtime — confirmado via `vercel logs --status-code 413 --json`.

48. **Cadastro de admins no painel admin:** nova seção "Admins" no menu lateral. Tabela `admin_logins` no Supabase (id, email, nome, ativo, is_master, created_at). Endpoints `GET/POST /admin/admins`, `PATCH /admin/admins/{id}/revogar`, `PATCH /admin/admins/{id}/reativar`, `DELETE /admin/admins/{id}`. Convite envia e-mail via Resend com link do painel + ADMIN_TOKEN. Admin master (`andre@servicefarma.far.br`, `is_master=true`) não pode ser revogado nem excluído.

> **Limitação atual:** todos os admins compartilham o mesmo `ADMIN_TOKEN`. "Revogar" apenas marca o registro como inativo no banco — não impede acesso técnico com o token. Autenticação individual por admin (e-mail + senha + JWT) está pendente (ver **Segurança (pendente)**).

50. **Painel admin não salvava ícone nos favoritos do Safari/iOS (2026-06-30):** o `<head>` do `frontend_admin/index.html` não tinha **nenhuma** tag de ícone (`apple-touch-icon`/`favicon`), então o iOS salvava um screenshot ao "Adicionar à Tela de Início". O favicon `/service_icone.ico` referenciado no `frontend_cliente` nem existe no repo (404). Fix: copiar o `icon-512.png` do QTQD para `frontend_admin/assets/` (forçar `git add -f` porque `*.png` está no `.gitignore`) + adicionar `apple-touch-icon`, `icon` e `apple-mobile-web-app-title` no `<head>` do admin. Validado em produção: HTTP 200 em `/admin/assets/icon-512.png`. Obs.: iOS cacheia ícone de forma agressiva — pode exigir limpar histórico do Safari para ver o novo.

51. **Usuário novo "abria o portal de outro cliente" / caía na demonstração (Elias, Drogaria SV, 2026-07-04):** relato era "o Elias não consegue acessar, abre outro portal pra ele". Diagnóstico (não era bug de autenticação): no Supabase Auth a conta do Elias estava criada mas **nunca ativada** — `identities=[]`, `email_confirmed_at=None`, `last_sign_in_at=None`; o convite de abril expirou em 24h e ele nunca definiu senha. O registro em `tenant_usuarios` estava 100% correto (único, Drogaria SV, ativo, `edita`, `app_metadata` certo). O único caminho que ele tinha era o link **"Acessar portal →"** dos e-mails de relatório, que é **genérico** (`https://qtqd-vt2a.vercel.app/cliente`, sem `?token`/`?tenant_id` — ver `relatorio_service.py:79`). **Causa raiz secundária (o "buraco"):** em `initializeClient()` (`script.js`), quando o navegador não tinha sessão válida, o portal caía silenciosamente em **modo simulação/demonstração** em vez de exibir o `#loginOverlay` — a tela de login só era acionada por `hasTenant && !hasJwt`. Num navegador limpo (sem tenant), mostrava demo; com sessão de outro tenant em cache, mostrava o portal do outro cliente. **Não existe botão "Entrar" manual** — o overlay só aparece por esse gatilho. Fix: (a) definida senha temporária + `email_confirm=True` para o Elias via admin API (destrava o login); (b) `script.js` agora mostra o login quando `QTQD_APP_CONFIG.mode==="api"` (deploy real) e não há sessão válida (`apiDeploy && !(hasTenant&&hasJwt)`), preservando o caso antigo. Fluxos com `?token&tenant_id` (Acessar Portal/autoprint) não são afetados — a IIFE planta a sessão antes do `initializeClient`. Validado em produção com Chromium headless: navegador limpo → login cobre a tela (z-9999); login do Elias → grava tenant Drogaria SV + JWT, aplica **logo e nome "SV"** (branding real da SV existe em `tenant_branding`: `nome_portal="SV"` + `logo_cliente_url`) e carrega os **73 registros reais** da SV (jul/2024 → jun/2026). SW `qtqd-v11 → qtqd-v12`. Nota de timing: o branding é aplicado por `getMyBranding()` **depois** do login dentro de `initializeClient()`; um screenshot tirado cedo demais ainda mostra o default "Cliente Demonstração" por ~1–2s — não é bug, só ordem de render.

> **Lição aprendida (2026-07-04):** "abre outro portal" com conta nova quase nunca é bug de autenticação de código — checar primeiro `last_sign_in_at`/`email_confirmed_at`/`identities` no Supabase Auth (conta ativada?) e lembrar que o link do e-mail de relatório é genérico e herda a sessão que estiver no `localStorage` do navegador.

52. **Multi-loja bloqueado por constraint antiga (2026-07-08):** ao rodar o E2E do multi-loja contra o Supabase real, a criação da 2ª loja na mesma semana falhou com `duplicate key ... avaliacoes_semanais_tenant_id_semana_referencia_key`. Existia uma constraint UNIQUE antiga em `(tenant_id, semana_referencia)` que **impedia 2 lojas na mesma semana** — a migração criou os índices parciais mas não removeu a constraint. Fix: `ALTER TABLE avaliacoes_semanais DROP CONSTRAINT IF EXISTS avaliacoes_semanais_tenant_id_semana_referencia_key;` (adicionado ao `multi-loja.sql` + aplicado). A unicidade dos clientes sem rede segue garantida pelo índice parcial `uq_aval_tenant_semana_sem_unidade`.

> **Lição aprendida (2026-07-08):** testes unitários (dados sintéticos) **não pegam** constraints do banco. Antes de shipar mudança de modelo, rodar um E2E contra o Supabase real. **Como rodar SQL/DDL no Supabase daqui:** conexão direta ao Postgres é bloqueada (problema #7), mas a **Management API** roda DDL — `POST https://api.supabase.com/v1/projects/ludbgghdknwfzcrqfdge/database/query` com `Authorization: Bearer <PAT sbp_...>` + header `User-Agent` de navegador (senão Cloudflare 1010). O PAT é gerado pelo usuário em Account → Access Tokens e deve ser revogado após o uso.

---

## Admin — Seção "Admins"

| Elemento | Função |
|---|---|
| Lista de cards | Exibe todos os admins com nome, e-mail, data de cadastro e badges (master / revogado) |
| **Convidar administrador** | Formulário com e-mail + nome → cria registro em `admin_logins` + envia e-mail com link e token |
| Botão **Revogar** | Marca `ativo = false` no banco (não impede acesso técnico) |
| Botão **Reativar** | Marca `ativo = true` |
| Botão **Excluir** | Remove permanentemente do banco (bloqueado para master) |

### Arquivos envolvidos

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/api/v1/admin_logins.py` | CRUD de admins protegido por `X-Admin-Token` |
| `frontend_admin/index.html` | Nav "Admins" + seção HTML com lista e formulário de convite |
| `frontend_admin/script.js` | `loadAdmins()`, `renderAdmins()`, handlers de revogar/reativar/excluir/convidar |
| `shared/api_client.js` | Métodos `listAdmins`, `convidarAdmin`, `revogarAdmin`, `reativarAdmin`, `excluirAdmin` |

### Tabela `admin_logins` (Supabase)

```sql
CREATE TABLE IF NOT EXISTS admin_logins (
  id         uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  email      text        NOT NULL UNIQUE,
  nome       text,
  ativo      boolean     DEFAULT true,
  is_master  boolean     DEFAULT false,
  created_at timestamptz DEFAULT now()
);
```

---

## Funcionalidades implementadas em 2026-05-18

### Máscaras de input no formulário de lançamentos
- Campos monetários: máscara estilo calculadora (preenche da direita, ex: digitar `5000` → `50,00` → `500,00`)
- Campos negativos (`saldo_bancario`, `lucro_liquido_mes`): tecla `-` alterna sinal
- Data da semana: máscara automática `dd/mm/aaaa` com barras inseridas ao digitar
- Campos de dias/percentual: formatação ao sair do campo (`blur`)
- Foco em campo monetário: seleciona todo o conteúdo para facilitar edição

### Template Excel para lançamento semanal
- Botões "⬇ Excel" e "⬆ Importar" no cabeçalho do card de Lançamentos
- **Download:** `GET /api/v1/avaliacoes/template-excel?semana=YYYY-MM-DD` — em branco para nova semana, pré-preenchido ao editar
- **Import:** `POST /api/v1/avaliacoes/import-excel` — lê coluna A (chave) e coluna C (valor), cria/atualiza como `rascunho`
- Campos de total (`contas_receber`, `contas_pagar`, `dividas`) não incluídos no template — apenas sub-itens
- Parser suporta números Excel nativos, strings pt-BR (`1.234,56`) e en-US (`1234.56`)
- `indice_faltas`: template mostra percentual (`6,82`), import divide por 100 automaticamente

### Fix de dupla contagem no cálculo QT/QD
- **Bug:** `qt_total` e `qd_total` somavam tanto o campo direto (`contas_receber`) quanto os sub-itens (`cartoes + convenios + ...`), gerando dupla contagem quando ambos estavam preenchidos
- **Fix:** sub-itens têm prioridade — se qualquer sub-item > 0, usa a soma dos sub-itens; campo direto só vale quando sub-itens são todos zero
- Aplicado em: `backend/app/services/calculos_qtqd.py` e `frontend_cliente/script.js` (`createRecordFromValues`)
- Mesmo padrão em `prazo_medio_compra` e `prazo_venda`
- Dado do Total Socorro 15/05 corrigido diretamente no banco

### Inspetor IA — narrativa analítica
- Reescrita completa do `buildInspectorNarrative` com análise real de tendências
- Calcula slope (regressão linear) nas últimas 8 semanas para QT, QD, Índice e Ciclo
- Seção "Movimentações da Semana": top 3 componentes que mais se moveram (R$ e %)
- Tendência e projeção: velocidade do índice em pontos/semana, projeção para 4 semanas
- Comparação com médias de 4 e 8 semanas
- Riscos baseados em tendência (não apenas snapshot)
- Recomendações específicas aos dados reais

---

## Funcionalidades corrigidas em 2026-05-22

### E-mail automático ao fechar pelo formulário
- **Problema:** fechar pelo select de status no formulário chamava `PATCH` (sem e-mail) em vez de `POST /fechar` (com e-mail)
- **Fix backend (`avaliacoes.py`):** `PATCH` agora detecta transição `rascunho → fechada` e dispara `enviar_relatorio_para_tenant` com `origem="fechar"`, igualando o comportamento ao `POST /fechar`
- **Fix frontend (`script.js`):** exibe "Fechando semana e enviando e-mail..." durante a operação e "Semana fechada. E-mail enviado para os destinatários cadastrados." ao concluir
- **Fix config (`config.py`):** validator Pydantic em `smtp_port` aceita `""` (usa default 465) — evita `ValidationError` silencioso se `SMTP_PORT=""` no Vercel

---

## Funcionalidades implementadas em 2026-05-26

### Excesso Crítico — assistente de cálculo a partir do Excel de estoque ✅ EM PRODUÇÃO

Nova seção no menu lateral do portal cliente (**"Excesso Crítico"**) que processa o arquivo `excesso_tabela_fabricante_*.xlsx` (saída do ERP do cliente) e calcula o excesso de estoque por curva (A/B/C/D). O resultado pode ser aplicado a qualquer lançamento existente (rascunho ou fechada), preenchendo automaticamente os campos `excesso_curva_a/b/c/d`.

#### Formato esperado do Excel
Colunas (qualquer ordem, header na linha 1): `Nome Completo`, `Linha`, `Curva` (A/B/C/D), `Filial` (1-6), `MediaF Un` (média mensal de venda em unidades), `Qtd Estoque`, `Estoque Valor`. **Coluna opcional `lancamento`** (aceita `lancamento`/`Lançamento`/`Lançamentos`) — valores tipo `"Sim - 90D"` marcam produtos em lançamento.

#### Regra de cálculo
**Itens de lançamento** (coluna `lancamento` cujo valor, sem espaços e minúsculo, **começa com "sim"**) são **retirados do cálculo de excesso** e somados à parte no campo `total_estoque_lancamentos` (soma pura do `Estoque Valor`, **sem regra e sem quebra por curva**). Se a coluna não existir, `total_estoque_lancamentos = 0` e nada é excluído (retrocompatível).

Os demais produtos são agregados por `(nome, linha, curva)` somando todas as filiais. Para cada produto agregado:
- Se `MediaF Un > 0`: cobertura em dias = `(Qtd Estoque / MediaF Un) × 30`
  - Se cobertura > limite da curva → excesso_un = `Qtd Estoque − (MediaF Un × limite / 30)`
- Se `MediaF Un == 0` e `Qtd Estoque > 1`: produto sem venda → excesso_un = `Qtd Estoque` (todo o estoque)
- Custo unitário = `Estoque Valor / Qtd Estoque`
- Excesso R$ = `excesso_un × custo_un`

Limites padrão (configuráveis por tenant): **A=120, B=150, C=150, D=180** dias.

> **`total_estoque_lancamentos` — campo apply-only.** É persistido no JSONB `valores` só pelo `/aplicar`; **não existe input no formulário semanal**. Por isso o backend o **preserva** nas escritas que substituem `valores` inteiro (PATCH do formulário e import-excel) via `_preserve_apply_only()`/`APPLY_ONLY_VALORES_FIELDS` em `avaliacoes.py` — senão o save do formulário zeraria o valor. No painel e no gerador de gráficos a linha/campo "Total de Estoque em Lançamentos" só aparece quando o tenant tem ao menos uma semana com valor > 0 (`hasLancamentosData()` em `script.js`; `chart_builder.js` usa o mesmo gate).

#### Endpoints (`backend/app/api/v1/excesso_critico.py`)
| Método | Path | Função |
|---|---|---|
| GET | `/me/excesso-critico/limites` | Retorna limites do tenant (ou defaults) |
| PUT | `/me/excesso-critico/limites` | Salva limites por curva (upsert em `tenant_excesso_config`) |
| POST | `/me/excesso-critico/calcular` | Multipart (`file` + `limite_a/b/c/d`) → totais, resumo e top 100 produtos críticos |
| POST | `/me/excesso-critico/aplicar/{avaliacao_id}` | Body JSON com `excesso_curva_a/b/c/d` → atualiza JSONB `valores` (preserva os outros campos) |

#### Frontend
- `frontend_cliente/excesso_critico.js` — módulo isolado, expõe `window.QTQD_EXCESSO.init()`. **Processa o XLSX 100% no browser via SheetJS** (`xlsx@0.18.5` carregado por CDN no `index.html`). O backend `/calcular` permanece como API mas não é mais chamado pela UI — só os 4 totais finais sobem para `/aplicar/{avaliacao_id}`.
- `frontend_cliente/index.html` — nav-link `data-section="excesso"` + seção com inputs de limites, botão de upload, KPIs por curva, tabela de produtos críticos (filtro curva + busca) e seletor de semana
- `shared/api_client.js` — métodos `getExcessoLimites`, `putExcessoLimites`, `calcularExcesso` (legacy, não usado), `aplicarExcesso`
- Permissão `visualiza`: inputs e botões ficam desabilitados; tabela continua visível

> **Por que processar no browser:** o Edge do Vercel rejeita uploads multipart acima de ~1–2 MB com HTTP 413 antes mesmo de invocar a função Python (logs mostram `source: "static"`). O limite documentado de 4.5 MB não vale para o runtime Python do Vercel. Processar o XLSX no browser elimina o upload e funciona para arquivos de qualquer tamanho. Paridade do cálculo JS↔Python validada (Drogaria SV: R$ 425.542,14 idêntico nas duas implementações).

#### Tabela `tenant_excesso_config` (Supabase)

> **⚠ Precisa ser criada no Supabase antes do deploy.** Rodar no SQL Editor:

```sql
CREATE TABLE IF NOT EXISTS tenant_excesso_config (
  tenant_id  uuid        PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  limite_a   integer     DEFAULT 120,
  limite_b   integer     DEFAULT 150,
  limite_c   integer     DEFAULT 150,
  limite_d   integer     DEFAULT 180,
  updated_at timestamptz DEFAULT now()
);
```

Se a tabela não existir, o endpoint `GET /limites` retorna os defaults; `PUT` falha com erro do Supabase até a tabela ser criada.

#### Resultado validado (arquivo de teste 2026-05-26, Drogaria SV)
- 33.640 linhas no Excel → 17.213 produtos únicos após agregação por filial
- Excesso total: **R$ 425.542,14** (17,98% do estoque de R$ 2,37M)
- Distribuição: A R$ 11K (21 prod) · B R$ 29K (71) · C R$ 38K (516) · D R$ 347K (3.748)

#### Atualização 2026-07-04 — Exclusão de Lançamentos + `total_estoque_lancamentos`
Ver spec/plano em `docs/superpowers/`. Coluna `lancamento` no Excel; itens "Sim*" saem do excesso e viram o campo `total_estoque_lancamentos` (soma pura). Persistido no `valores` via `/aplicar`, preservado no PATCH/import-excel (`_preserve_apply_only`), exibido no painel e nos gráficos só quando há dado (`hasLancamentosData()`). SW `qtqd-v12 → qtqd-v13`.
- Validado em produção (arquivo 2026-07-04, limites reais da SV A=90/B=120/C=150/D=180): **Lançamentos R$ 66.232,77** (1.133 itens) · **Excesso retirando lançamentos R$ 422.764,06** (4.368 prod: A 8.762,67 · B 37.438,50 · C 29.209,99 · D 347.352,90). Sem excluir seria R$ 456.019,34 (redução de R$ 33.255,28).
- Aplicado à semana 2026-06-30 da SV durante a verificação E2E (valor gravado e preservado após save do formulário).

> **Pendências menores (deferidas na revisão final, não bloqueiam):** (a) o docstring de `aplicar()` em `excesso_critico.py` ainda cita só `excesso_curva_a/b/c/d` — atualizar para mencionar `total_estoque_lancamentos`; (b) no cálculo do browser, `resumo.total_linhas_excel` e `total_produtos_unicos` passaram a excluir as linhas de lançamento — o resumo mostra "N itens de lançamento excluídos" à parte, então os números reconciliam, mas o rótulo "linhas no Excel" ficou um pouco menor que a contagem bruta.

### Menu "Ajuda" no portal cliente ✅ EM PRODUÇÃO

Nav-link **"Ajuda"** no menu lateral (grupo SUPORTE) abrindo seção `#ajuda` com guia completo das 6 funcionalidades: Visão geral, Inspetor IA, Painel, Gráficos, Histórico, Lançamentos, Excesso Crítico, Boas práticas, Suporte.

- Conteúdo 100% estático em HTML — sem JS, sem dependências
- Cada bloco usa `.card-inner` com `.eyebrow` + título + parágrafo/lista
- Suporte: e-mail `comercial@servicefarma.far.br`
- Para atualizar: editar diretamente o `<section id="ajuda">` no [frontend_cliente/index.html](frontend_cliente/index.html) e bumpar SW
- **Atualização 2026-07-08:** ganhou o bloco **"🏬 Multi-loja / Rede"**. O **painel admin também ganhou uma seção "Ajuda"** (`#ajuda`, `admin-section`) com a parametrização multi-loja — ver seção abaixo.

---

## Multi-loja / Grupo Econômico ✅ EM PRODUÇÃO (2026-07-08)

Permite que um cliente (rede) com várias lojas/CNPJs lance dados **por loja** e veja a **visão consolidada** (loja → grupo econômico → rede). **Opt-in por cliente** via `tenants.modo_rede` — cliente com a flag desligada (todos os atuais) funciona **idêntico a hoje**. Deployado; migração já aplicada no Supabase; **nenhum cliente usa ainda** (dormant).

### Hierarquia e preenchimento
- **Rede** (o cliente) → **Grupos econômicos** (1+) → **Lojas** (1+ por grupo).
- Cada grupo tem `nivel_preenchimento`: `'loja'` (lança cada loja; grupo = soma) ou `'grupo'` (lança direto no grupo, sem lojas). Um cliente pode misturar os dois.
- Quando há um só grupo, a UX omite o nível "grupo" (rede ≡ grupo).

### Modelo de dados (Supabase — DDL em `tools/sql/2026-07-08-multi-loja.sql` e `...-nivel-relatorio.sql`)
- `tenants.modo_rede boolean DEFAULT false` (opt-in).
- `grupos_economicos(id, tenant_id, nome, nivel_preenchimento, ordem, ativo, created_at)`.
- `lojas(id, tenant_id, grupo_id, nome, cnpj, filial_excel, ordem, ativo, created_at)` — `filial_excel` liga a loja à coluna `Filial` do Excel de Excesso.
- `avaliacoes_semanais` ganhou `grupo_id`/`loja_id` (NULL = comportamento atual).
- `tenant_pdf_config.nivel_relatorio text DEFAULT 'loja'` (nível do e-mail: loja/grupo/rede).
- **Unicidade:** a constraint antiga `avaliacoes_semanais_tenant_id_semana_referencia_key` foi **removida** (bloqueava 2 lojas na mesma semana). Agora é via índices únicos parciais: `uq_aval_tenant_semana_sem_unidade` (WHERE grupo/loja NULL — mantém a garantia dos clientes atuais) + `uq_aval_rede` (por unidade, com COALESCE do loja_id).

### Consolidação — `series_service.py` + `consolidacao_service.py` (fonte única, backend)
- **Aditivos** (QT/QD em R$, excesso, estoque, compras, vendas): **somam**.
- **Ponderados:** PMP por `compras_mes`, PMV (e faixas) por `venda_custo_mes`, PME por `estoque_custo`, indice_faltas por `venda_custo_mes`. Peso 0 → média simples.
- **Calculados** (índice, ciclo): recalculados sobre o consolidado (índice da rede = QT_rede ÷ QD_rede, nunca média de índices).
- **Encadeamento:** grupo = soma das lojas (ou lançamento direto); rede = soma dos grupos.
- **`consolidar_valores(itens) -> AvaliacaoValores`** é puro/testável. `build_series(avaliacoes, grupos, nivel, ref_id)` monta a série por nível. `build_comparativo_snapshot/evolucao` para o Comparativo.
- **Detalhe heterogêneo:** `_preparar_para_consolidar` colapsa total↔sub-itens ao nível efetivo **só quando a lista mistura** detalhado com só-total (senão preserva os sub-itens) — evita descartar silenciosamente o total de uma loja.

### Endpoints
| Método | Path | Função |
|---|---|---|
| GET/POST/PATCH/DELETE | `/admin/tenants/{tid}/grupos` e `/lojas` | CRUD estrutura (admin) |
| PATCH | `/admin/tenants/{tid}/modo-rede` | liga/desliga `modo_rede` (body `{ativo}`) |
| GET | `/me/lojas` | árvore grupos→lojas + modo_rede (alimenta o seletor) |
| GET | `/avaliacoes?nivel=loja&loja_id=…` \| `nivel=grupo&grupo_id=…` \| `nivel=rede` | série por nível (sem `nivel` = comportamento atual) |
| GET | `/me/comparativo?nivel=…&grupo_id=…&modo=snapshot\|evolucao&semana=…` | comparativo |

`avaliacoes.py`: `criar`/`atualizar` persistem `grupo_id`/`loja_id`; `_validar_unidade()` valida a unidade conforme o modo. Séries consolidadas são sintéticas/read-only (id `uuid5` por semana, status "fechada" placeholder) e **excluem rascunho** (`.neq("status","rascunho")`).

### Frontend
- **Admin:** seção **"Estrutura"** (`#estrutura`, `admin-section`) — seleciona cliente, cria grupos/lojas, liga modo_rede. Seção **"Relatório"** ganhou o select **Nível do relatório**.
- **Portal:** módulo **isolado `multiloja.js`** (padrão de `excesso_critico.js`/`chart_builder.js`) — `init()` só ativa com `modo_rede`; injeta o seletor no `.topbar-right`, troca a série via `window.QTQD_PORTAL.applyApiRecords`, revela o menu Comparativo (escondido por padrão via `style="display:none"`), desabilita o novo-lançamento em nível consolidado. O `script.js` tem só **3 hooks cirúrgicos** (`window.QTQD_PORTAL`, fundir unidade ativa no create, chamar `QTQD_MULTILOJA.init()`).
- **Comparativo:** seção `#comparativo` (`section-view`) — snapshot (tabela indicador×unidade+Total) e evolução (semanas×unidade), renderizadas por `multiloja.js`.
- **Excesso por loja:** `excesso_critico.js` filtra as linhas do Excel pela filial da loja ativa (`calcularExcessoDeRows(rows, limites, filial)` + `multiloja.activeFilial()`).

### Como ativar num cliente
Admin → **Estrutura** → selecionar cliente → criar grupo(s) + lojas (com nº da Filial) → ligar **Modo rede** → Admin → **Relatório** → escolher Nível. Cliente recarrega o portal.

### E2E / verificação (2026-07-08, contra Supabase real via Management API)
- Regressão SV + Total Socorro OK (produção ao vivo + backend da branch, grupo/loja NULL).
- Backend 17/17: rede→2 lojas mesma semana→consolidado (QT 9K/QD 1K/índice 9)→comparativo→validações.
- Frontend (Playwright local): seletor, troca de série, trava de nível, comparativo, **zero erros de console**.
- **Bug real achado no E2E** (não pego pelos unit tests): a constraint antiga de unicidade bloqueava multi-loja → removida (ver Modelo de dados).

### Pendências multi-loja (fora de escopo da fase 1)
- **Permissão por loja/grupo** (hoje todos os usuários do cliente veem todas as unidades).
- **Metas/orçamento por loja** (realizado × meta).
- **Excesso "todas as lojas de uma vez"** (hoje é por loja ativa; ideal: um upload aplica em todas via `filial_excel`).
- Aviso quando o Excesso é aberto em nível consolidado (evitar aplicar em id sintético).

---

## Segurança (pendente)

- Regenerar `SUPABASE_SERVICE_ROLE_KEY` após estabilização
- Revogar tokens GitHub usados durante implantação inicial
- **⚠ PENDÊNCIA PRIORITÁRIA — Login individual de admin (e-mail + senha):** Hoje **o painel admin NÃO tem login de usuário/senha** — o acesso é por um único `ADMIN_TOKEN` compartilhado por todos os admins (valor atual em produção: `qtqd-admin-a3-2026`, na env var `ADMIN_TOKEN` do Vercel). Isso confunde quem espera logar com e-mail/senha (o e-mail/senha `andre@servicefarma.far.br` serve só para o **portal cliente**, não para o admin). Consequências do modelo atual:
  - O botão "Revogar" na seção Admins apenas marca `ativo = false` em `admin_logins` — **não impede** acesso técnico, pois o token continua válido.
  - Não há rastreabilidade de qual admin fez cada ação (todos usam o mesmo token).
  - **Solução pretendida:** substituir o `ADMIN_TOKEN` compartilhado por login e-mail + senha com JWT por admin. Cada admin teria credenciais próprias no Supabase Auth (`app_metadata.qtqd_admin = true`). Revogação passaria a funcionar de verdade e cada ação seria atribuível. Padrão: igual ao PEC-SF e Agenda de Compras Web.
- **⚠ PENDÊNCIA — "Esqueci minha senha" / troca de senha self-service no portal cliente:** hoje **não existe** troca de senha pelo cliente. Se o usuário esquece a senha (ou tem só uma senha provisória), a única saída é o admin regerar via convite (`/admin/usuarios/{id}/enviar-convite`, que gera link `recovery`) ou definir a senha direto via admin API (`sb.auth.admin.update_user_by_id(uid, {"password":..., "email_confirm":True})`). Falta: (a) botão "Esqueci minha senha" na tela de login (`#loginOverlay`) que dispara um `recovery` do Supabase Auth para o e-mail do usuário → link cai em `/instalar` (fluxo `definir-senha` já existe e funciona); (b) opcionalmente, um "Trocar senha" dentro do portal para quem já está logado. Contexto: originou-se do caso Elias/Drogaria SV (2026-07-04, problema #51), onde uma senha provisória (`EliasSV@2026`) foi definida manualmente e não há como o próprio Elias trocá-la.
- **⚠ PENDÊNCIA (menor) — link "Acessar portal →" dos e-mails de relatório é genérico:** aponta para `https://qtqd-vt2a.vercel.app/cliente` sem `?token`/`?tenant_id` (ver `relatorio_service.py`), então herda a sessão do navegador. Com o fix do #51 isso deixou de cair na demonstração (agora mostra login), mas o link ainda não leva o usuário direto ao portal dele. Melhoria futura: incluir no link algo que force a identificação (ex.: `?tenant_id=` para pré-selecionar o tenant e exibir o login já contextualizado, sem embutir JWT no e-mail).

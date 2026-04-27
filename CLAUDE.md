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
    sw.js                 Service Worker (cache qtqd-v3)
    assets/logo_alta.jpg
    data/qtqd_seed.js
  frontend_admin/         Painel administrativo
    index.html
    styles.css
    script.js
  shared/                 Recursos compartilhados
    app_config.js         Configuração da API (mode: simulation/api, tenantId)
    api_client.js         Cliente HTTP — inclui setJwt, setTenantId, abrirPortal, uploadLogo
  backend/app/
    core/
      config.py           Settings (inclui portal_admin_email, portal_admin_password)
      auth.py             JWT Supabase + suporte X-Tenant-Id para multi-tenant
      admin_auth.py       Validação do X-Admin-Token
    db/client.py
    api/v1/
      avaliacoes.py
      cliente_config.py
      admin_clientes.py
      admin_config.py     POST /admin/abrir-portal/{tenant_id}
                          POST /admin/branding/{tenant_id}/logo  (upload para Supabase Storage)
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

O admin (`andre@servicefarma.far.br` / senha: `service`) está cadastrado no Supabase Auth e vinculado a **todos** os tenants via `tenant_users` com `role: admin`.

No painel admin, cada card de cliente tem o botão **"Acessar Portal"** que:
1. Chama `POST /admin/abrir-portal/{tenant_id}` → retorna JWT
2. Abre `https://qtqd-vt2a.vercel.app/cliente?token=JWT&tenant_id=UUID`
3. Portal lê os params, armazena no localStorage e entra em modo API para aquele tenant

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

- `POST /api/v1/admin/abrir-portal/{tenant_id}` — gera JWT para acesso ao portal cliente
- `POST /api/v1/admin/branding/{tenant_id}/logo` — upload de logo (JPG/PNG/WebP ≤2MB) para Supabase Storage bucket `logos`
- `GET/POST /api/v1/admin/usuarios` — gestão de `tenant_usuarios`

### Supabase SDK — padrões

```python
from backend.app.db.client import get_supabase
sb = get_supabase()
result = sb.table("avaliacoes_semanais").select("*").eq("tenant_id", str(tid)).execute()
rows = result.data
```

**Regras:** UUIDs e datas como `str()`. JSONB vem como `dict`. `updated_at` manual em todo UPDATE.

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

O admin configura visibilidade e labels em **Campos** (painel admin). O cliente carrega via `getMyComponentesConfig()` no startup. A lógica em `script.js` (bloco async ao final):
1. Chama `getMyComponentesConfig()` da API
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

## Multi-tenant e modos de operação

- **Modo simulação:** `mode: "simulation"` — dados no localStorage
- **Modo API:** JWT no localStorage (`qtqd_jwt_v1`) + tenant_id (`qtqd_tenant_id_v1`)
- **Auto-detecção:** `getRuntimeConfig()` verifica localStorage e ativa modo API automaticamente
- **Ativação por URL:** `?token=JWT&tenant_id=UUID` — portal lê, armazena e limpa a URL
- **X-Tenant-Id:** `api_client.js` envia em todos os requests autenticados

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

---

## Segurança (pendente)

- Regenerar `SUPABASE_SERVICE_ROLE_KEY` após estabilização
- Revogar tokens GitHub usados durante implantação inicial

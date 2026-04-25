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
    chart_builder.js      Gerador de gráficos customizados (chart_builder.js substitui renderChartsPanel do script.js)
    assets/logo_alta.jpg
    data/qtqd_seed.js
  frontend_admin/         Painel administrativo
    index.html
    styles.css
    script.js
  shared/                 Recursos compartilhados
    app_config.js         Configuração da API (mode: simulation/api, tenantId)
    api_client.js         Cliente HTTP — inclui setJwt, setTenantId, abrirPortal
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
      admin_config.py     Inclui endpoint POST /admin/abrir-portal/{tenant_id}
    schemas/avaliacoes.py
    services/
      calculos_qtqd.py    Indicadores calculados (inclui indice_compra_venda, margem_bruta, excesso_total, ciclo)
      excel_import.py
  api/index.py
  tools/
    importar_qtqdts.py    Script de importação do QTQDTS.xlsx via Supabase SDK direto
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
| **Total Socorro** | `b2ce08a4-b1f9-4465-b162-9f5e9bb70092` | implantacao — **103 semanas importadas** (jun/2024 → abr/2026) |
| Drogaria SV | `8044331a-4531-47c9-bbff-6546110d5767` | implantacao — sem dados |

### Acesso admin ao portal do cliente

O admin (`andre@servicefarma.far.br` / senha: `service`) está cadastrado no Supabase Auth e vinculado a **todos** os tenants via `tenant_users` com `role: admin`.

No painel admin, cada card de cliente tem o botão **"Acessar Portal"** que:
1. Chama `POST /admin/abrir-portal/{tenant_id}` → retorna JWT
2. Abre `https://qtqd-vt2a.vercel.app/cliente?token=JWT&tenant_id=UUID`
3. Portal lê os params, armazena no localStorage e entra em modo API para aquele tenant

O backend aceita `X-Tenant-Id` header para usuários com acesso a múltiplos tenants.

---

## Modelo de dados — campo `valores` (JSONB)

Todos os campos financeiros ficam no JSONB `avaliacoes_semanais.valores`. Não há colunas separadas — novos campos são adicionados ao schema Pydantic e salvos automaticamente.

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

> **Ciclo de financiamento:** usa `pmp` e `pmv` como inputs do ERP quando `pmp > 0 OR pmv > 0`. Se ambos zero, retorna `None` (não exibe).

### Dados do Total Socorro importados

- **103 semanas** de QT/QD (jun/2024 → abr/2026) — `tools/importar_qtqdts.py`
- **PMP, PMV, PME** para todas as 103 semanas (do QTQDTS.xlsx)
- **PMV por prazo** (à vista, 30d, 60d, 90d, 120d, outros) — 46 semanas (jul/2025 → abr/2026)
- Para novas semanas: preencher manualmente no portal

---

## Backend — FastAPI + Supabase SDK

### Autenticação — dois níveis

| Nível | Como funciona | Endpoints |
|-------|---------------|-----------|
| **Cliente** | `Authorization: Bearer <supabase_jwt>` + `X-Tenant-Id: UUID` | `/api/v1/avaliacoes/*`, `/api/v1/me/*` |
| **Admin** | `X-Admin-Token: <admin_token>` | `/api/v1/admin/*` |

### Endpoints relevantes (além dos padrão)

- `POST /api/v1/admin/abrir-portal/{tenant_id}` — gera JWT para acesso ao portal cliente
- `GET/POST /api/v1/admin/usuarios` — gestão de `tenant_usuarios` (para notificações PDF)

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

O painel usa `matrixRows` (definido em `script.js`) com grupos e ícones:

| Grupo | Ícone | Cor | rowClass |
|-------|-------|-----|----------|
| QT (Quanto Tenho) | 💰 | `#2563eb` | `row-header` |
| QD (Quanto Devo) | 📋 | `#ef4444` | `row-header` |
| Saldo/Índice QT/QD | ⚖️ | `#16a34a` | `row-header` |
| INFORMAÇÕES COMPLEMENTARES | 📈 | `#7c3aed` | section |
| INDICADORES OPERACIONAIS | ⚙️ | `#0891b2` | section |

Sub-itens: indent de 22px, fonte 12px, cor muted.

**Filtro de visibilidade:** só campos em `componentLabels` passam por `isFieldVisible()`. Campos calculados (não em componentLabels) são sempre exibidos.

### Funções auxiliares no script.js

- `matrixVal(r, key)` — calcula `contas_receber`, `contas_pagar`, `dividas` a partir de sub-itens quando o campo direto é 0
- `fmtMoneyShort(v)` — formata valores monetários abreviados (R$ 1,9M, R$ 234K)
- `fmtPercent(v)` — formata como percentual (multiplica por 100)
- `populateYearFilter()` — popula o `<select id="matrixYearFilter">` com os anos disponíveis

---

## Frontend Cliente — Inspetor IA

Redesenhado com conceito do SFI (Comercial_A3):

- **Estado inicial** com 4 cards de feature (antes de analisar)
- **Botão "Analisar"** (`#refreshInspectorButton`) — aciona análise completa
- **4 KPIs** com borda colorida condicional (`#inspectorHero`)
- **Semáforo 6 indicadores:** Liquidez, Saldo, PMP, PMV, PME, Ciclo (`#inspectorSemaphore`)
- **Barras de composição QT e QD** (`#inspectorQtBars`, `#inspectorQdBars`)
- **Gráfico evolução** duplo eixo: QT/QD/Saldo + Índice (`#efficiencyChart`)
- **Diagnóstico IA em streaming** com formatação markdown (`#inspectorNarrative`)
- **Riscos** com ícones (`#inspectorRisks`) e **Ações numeradas** (`#inspectorActions`)
- **Tabela histórica** mais recente primeiro (`#inspectorDataTable`)

IDs do inspetor que DEVEM existir no HTML:
`inspectorInitial`, `inspectorContent`, `inspectorHero`, `inspectorSemaphore`, `inspectorQtBars`, `inspectorQdBars`, `efficiencyChart`, `inspectorNarrative`, `inspectorAnalysisStatus`, `inspectorTrendTable`, `inspectorRisks`, `inspectorActions`, `inspectorDataTable`

IDs legado (ocultos, mantidos para compatibilidade):
`inspectorBlocks`, `inspectorPeriods`, `liquidityChart`

---

## Frontend Cliente — Gerador de Gráficos

`chart_builder.js` substitui completamente `renderChartsPanel()` do `script.js`.

- Campos organizados por grupo (usa `matrixRows` para estrutura)
- Grupos: QT, QD, Indicadores QT/QD, Informações Complementares, Indicadores Operacionais
- CSS: `.cb-field-group` (grid label-esquerda + pills-direita), `.cb-field-group-label`, `.cb-field-pills`
- Salvar requer nome no campo `#cbName` — ao falhar, faz scroll até o campo e destaca em vermelho

---

## Frontend Cliente — IDs obrigatórios no HTML

**Formulário:**
`weeklyForm`, `recordId`, `weekDate`, `recordStatus`, `formModeBadge`, `formCalculatedKpis`

**Painel:**
`matrixTableWrap`, `matrixYearFilter`

**Gráficos (legado — ocultos):**
`chartFieldsGrid`, `chartRangeCount`, `chartPanelTitle`, `financialTimelineChart`

**Gráficos (chart_builder.js):**
`cbFieldButtons`, `cbSelectedFields`, `cbName`, `cbCountInput`, `cbPreview`, `cbSave`, `cbClear`, `cbPreviewWrap`, `savedChartsContainer`

**Navegação:**
`newEntryButton`, `seedDemoButton`, `openGraphsButton`, `openInspectorButton`, `resetFormButton`, `evaluateButton`, `toggleFocusButton`, `backFromPanelButton`, `refreshInspectorButton`, `downloadPdfButton`, `sidebarMiniToggle`, `sidebarRevealButton`

**Campos do formulário (IDs dos inputs):**
`saldo_bancario`¹, `contas_receber`, `cartoes`, `convenios`, `cheques`, `trade_marketing`, `outros_qt`, `estoque_custo`,
`contas_pagar`, `fornecedores`, `investimentos_assumidos`, `outras_despesas_assumidas`, `dividas`, `financiamentos`, `tributos_atrasados`, `acoes_processos`,
`faturamento_previsto_mes`, `compras_mes`, `entrada_mes`, `venda_cupom_mes`, `venda_custo_mes`, `lucro_liquido_mes`¹,
`pmp`, `pmv`, `pme_excel`, `indice_faltas`, `pmv_avista`, `pmv_30`, `pmv_60`, `pmv_90`, `pmv_120`, `pmv_outros`,
`excesso_curva_a`, `excesso_curva_b`, `excesso_curva_c`, `excesso_curva_d`

¹ Não tem `min="0"` — podem ser negativos.

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
11. **Campos calculados ocultos no painel:** `excesso_total` e outros não estavam em `componentLabels`, o filtro `isFieldVisible` os ocultava. Fix: usar `configurableKeys` baseado em `componentLabels`.
12. **Ciclo mostrando valores absurdos:** Ciclo só é calculado quando `pmp > 0 OR pmv > 0`, senão retorna `null`.
13. **Backend crash com `import openpyxl`:** tornar import lazy (dentro da função).
14. **`python-multipart` faltando:** necessário para `File`/`UploadFile` no FastAPI.

---

## Segurança (pendente)

- Regenerar `SUPABASE_SERVICE_ROLE_KEY` após estabilização
- Revogar tokens GitHub usados durante implantação inicial

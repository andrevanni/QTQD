# Multi-loja / Grupo Econômico — visão por unidade e consolidada

**Data:** 2026-07-08
**Origem:** sugestão de sócio para atender clientes (redes) que operam com múltiplas lojas / CNPJs separados
**Status:** design aprovado no brainstorming — pendente revisão do spec antes do plano de implementação

## Contexto

Hoje o QTQD modela um cliente (`tenant`) com **um lançamento semanal único** por semana (`avaliacoes_semanais` chaveado por `tenant_id` + `semana_referencia`). Redes com várias lojas / grupos econômicos não conseguem lançar dados separados por unidade nem ver uma visão consolidada.

O sistema **já possui infraestrutura multi-tenant** (um usuário pode acessar vários tenants via header `X-Tenant-Id`), mas isso não resolve o caso: o requisito é **acesso único**, com preenchimento por unidade e **consolidação** dentro do mesmo cliente, herdando toda a configuração.

### Decisões do brainstorming (2026-07-08)

1. **Consolidação:** mostrar **totais em R$ + índices/prazos ponderados** (não só totais).
2. **Independência das unidades:** unidades **compartilham toda a configuração do cliente** (usuários, branding, campos visíveis, limites de excesso, e-mail). A unidade é apenas uma dimensão de preenchimento dos dados.
3. **Hierarquia de 3 níveis:** **Cliente (rede) → Grupos econômicos → Lojas**. Um cliente pode ter vários grupos econômicos; cada grupo, uma ou mais lojas.
4. **Consolidado por grupo:** o nível "grupo econômico" **tem visão consolidada própria** (não é só rótulo). Três níveis de análise: loja, grupo, rede.
5. **Nível de preenchimento configurável por grupo:** alguns grupos são lançados **loja a loja**; outros já vêm **consolidados por grupo** (o cliente lança direto no grupo). Um mesmo cliente pode misturar os dois tipos.
6. **Escopo da 1ª entrega:** completo ("tudo redondo") — preenchimento por unidade, seletor de 3 níveis no portal, consolidado ponderado em Inspetor + Painel + Gráficos, Excesso Crítico por loja e relatório por e-mail por nível.
7. **Ciclo de financiamento opcional (2ª sugestão):** basta o admin ocultar PMP/PMV/PME pela config de Campos (já existe); único ajuste é garantir que, ocultos, não gerem alerta "vermelho" no semáforo.
8. **Comparativo lado a lado (incluído na fase 1):** nova seção comparando unidades — **snapshot** (uma semana) **+ evolução** (linha por unidade ao longo das semanas). Render isolado, sem tocar os renders existentes.

### Enquadramento: todo cliente é uma "rede"

Conceitualmente **todo cliente é uma rede**. A quebra em **grupos econômicos** e **lojas** é opcional e, **hoje, nenhum cliente a utiliza** — todos operam como uma rede sem grupo econômico (uma unidade só). O modelo suporta os 3 níveis, mas eles só entram em cena quando o cliente cadastra grupos/lojas.

### Princípio de risco (NÃO comprometer clientes atuais)

**Requisito duro:** nenhum cliente já cadastrado pode ser afetado. Garantias:

- **Ativação por dados, não por código:** um cliente sem grupos/lojas cadastrados (todos os atuais) tem `grupo_id`/`loja_id` NULL em todos os lançamentos e comporta-se **exatamente como hoje** — sem seletor, série única, mesmos números.
- **Flag explícita `tenants.modo_rede`** como trava adicional (cinto e suspensório): mesmo que grupos existam, nada muda na UI até a flag ser ligada. Default `false`.
- **Retrocompatibilidade testada:** todos os endpoints devolvem resposta **idêntica à atual** para cliente sem modo_rede (ver seção Testes).
- Protege os arquivos sensíveis (`script.js`, auth, SW) — ver seção CRÍTICO do CLAUDE.md.

### Grupo único implícito (para "rede sem grupo econômico")

Quando uma rede tem lojas mas o cliente **não** raciocina em termos de grupo econômico, o sistema usa **um grupo único implícito** ("Geral"). O modelo continua 3-níveis internamente, mas a UX esconde o nível grupo quando há apenas um grupo (rede ≡ grupo). Assim "rede direto com lojas" e "rede com vários grupos" usam a mesma estrutura, sem forçar o cliente a criar grupos que não existem para ele.

### Casos de exemplo

- **Rede com 3 lojas, lançando loja a loja (caso comum):** 1 grupo "Geral" (`nivel='loja'`) + 3 lojas. Seletor mostra **Loja 1 / Loja 2 / Loja 3 / REDE (consolidado)** — nível grupo omitido por ser único. Vê cada loja independente e o consolidado das três.
- **Rede que já recebe consolidado por grupo:** 1+ grupos com `nivel='grupo'`, lançamento direto no grupo, sem lojas. Seletor mostra os grupos + REDE.
- **Rede mista:** grupo A por loja (várias lojas) + grupo B consolidado (direto). Seletor mostra lojas do A, grupo A (soma), grupo B (direto) e REDE (soma de A+B).
- **Cliente comum de hoje (sem modo_rede):** nenhum grupo/loja, série única, sem seletor — idêntico ao atual.

## Modelo de dados

### `tenants` (alteração)

```sql
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS modo_rede boolean DEFAULT false;
```

### `grupos_economicos` (nova)

```sql
CREATE TABLE IF NOT EXISTS grupos_economicos (
  id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tenant_id           uuid        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome                text        NOT NULL,
  nivel_preenchimento text        NOT NULL DEFAULT 'loja',  -- 'loja' | 'grupo'
  ordem               integer     DEFAULT 0,
  ativo               boolean     DEFAULT true,
  created_at          timestamptz DEFAULT now()
);
```

### `lojas` (nova)

```sql
CREATE TABLE IF NOT EXISTS lojas (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tenant_id    uuid        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  grupo_id     uuid        NOT NULL REFERENCES grupos_economicos(id) ON DELETE CASCADE,
  nome         text        NOT NULL,
  cnpj         text,                       -- opcional
  filial_excel integer,                    -- opcional: mapeia a coluna Filial do Excel de Excesso
  ordem        integer     DEFAULT 0,
  ativo        boolean     DEFAULT true,
  created_at   timestamptz DEFAULT now()
);
```

### `avaliacoes_semanais` (alteração)

```sql
ALTER TABLE avaliacoes_semanais ADD COLUMN IF NOT EXISTS grupo_id uuid REFERENCES grupos_economicos(id) ON DELETE CASCADE;
ALTER TABLE avaliacoes_semanais ADD COLUMN IF NOT EXISTS loja_id  uuid REFERENCES lojas(id) ON DELETE CASCADE;
```

- **Cliente sem `modo_rede`:** `grupo_id = NULL`, `loja_id = NULL`. Comportamento atual preservado.
- **Grupo `nivel_preenchimento='loja'`:** cada lançamento tem `grupo_id` + `loja_id` setados. O consolidado do grupo é a soma das lojas.
- **Grupo `nivel_preenchimento='grupo'`:** o lançamento tem `grupo_id` setado e `loja_id = NULL` (lançamento direto no grupo; não exige cadastrar lojas).

**Unicidade — atenção (risco de regressão):** hoje vale "1 lançamento por (tenant, semana)"; passa a "1 por (tenant, semana, grupo_id, loja_id)". **Cuidado:** um índice único ingênuo sobre `(tenant_id, semana_referencia, grupo_id, loja_id)` trata múltiplos NULL como distintos no Postgres — o que **permitiria duplicatas** `(tenant, semana, NULL, NULL)` para clientes sem modo_rede, quebrando a garantia atual. O plano deve preservar a unicidade dos registros antigos via **índice único parcial** (`WHERE grupo_id IS NULL AND loja_id IS NULL` sobre `(tenant_id, semana_referencia)`) + índice separado para os registros de rede, ou `COALESCE`/`NULLS NOT DISTINCT`. Verificar antes se já existe constraint de unicidade em produção para não introduzir/duplicar.

## Consolidação (regra central)

Função isolada e testável no backend: `consolidar_valores(lista_de_valores) -> valores`. Fonte **única** (evita drift JS↔Python, lição do Excesso Crítico).

**Estratégia:** consolidar os **inputs crus** e depois rodar o **mesmo `calculos_qtqd`** sobre o resultado. Assim os calculados (qt_total, qd_total, saldo, índices, ciclo) saem coerentes — ex.: índice da rede = QT_rede ÷ QD_rede, nunca média de índices.

### Campos que somam direto

Todos os QT/QD em R$ e derivados aditivos:
`saldo_bancario`, `contas_receber` e sub-itens (`cartoes`, `convenios`, `cheques`, `trade_marketing`, `outros_qt`), `estoque_custo`, `contas_pagar` e sub-itens (`fornecedores`, `investimentos_assumidos`, `outras_despesas_assumidas`), `dividas` e sub-itens (`financiamentos`, `tributos_atrasados`, `acoes_processos`), `faturamento_previsto_mes`, `compras_mes`, `entrada_mes`, `venda_cupom_mes`, `venda_custo_mes`, `lucro_liquido_mes`, `excesso_curva_a/b/c/d`, `total_estoque_lancamentos`.

### Campos ponderados (inputs de prazo — não somam)

| Campo | Base de ponderação |
|---|---|
| `pmp` | `compras_mes` |
| `pmv`, `pmv_avista`, `pmv_30`, `pmv_60`, `pmv_90`, `pmv_120`, `pmv_outros` | `venda_custo_mes` |
| `pme_excel` | `estoque_custo` |
| `indice_faltas` | `venda_custo_mes` |
| `cobertura_estoque_dia` | `estoque_custo` |

- Média ponderada: `Σ(valor_i × peso_i) / Σ(peso_i)`.
- **Peso total = 0:** cai para média aritmética simples dos valores > 0; se todos forem 0, resultado 0. Nunca lança exceção nem divide por zero.

### Encadeamento hierárquico

- **Consolidado do grupo:**
  - `nivel_preenchimento='grupo'` → é o próprio lançamento direto do grupo (sem consolidar).
  - `nivel_preenchimento='loja'` → `consolidar_valores(lançamentos das lojas do grupo naquela semana)`.
- **Consolidado da rede:** `consolidar_valores(consolidados de cada grupo)`.

Cada grupo "entrega" seu consolidado de forma uniforme; a rede não precisa saber como cada grupo foi preenchido.

### ⚠ Atenção para o Plano 2 — detalhamento heterogêneo entre lojas

`calcular_indicadores` usa prioridade "ou-ou": se qualquer sub-item de um grupo (ex.: `cartoes`) > 0, usa a soma dos sub-itens e **ignora** o campo total (`contas_receber`). A consolidação, porém, soma total **e** sub-itens de forma independente e aditiva (correto isoladamente). Combinação problemática: se a **Loja A detalha sub-itens** (`cartoes>0`) e a **Loja B preenche só o total** (`contas_receber>0`, sub-itens 0), o consolidado terá ambos > 0 → `calcular_indicadores` escolhe a soma dos sub-itens e **descarta silenciosamente o total da Loja B**, subestimando o QT/QD da rede. Aplica-se igualmente a `contas_pagar`/`fornecedores…` e `dividas`/`financiamentos…`.

Hoje **não é regressão** (nenhum dado passa por esse caminho ainda, e lojas de uma mesma rede tendem a usar o mesmo modo de preenchimento). Mas o Plano 2 deve tratar: (a) **normalizar total→sub-itens** (ou vice-versa) antes de consolidar, ou (b) **exigir modo de detalhamento uniforme por rede**. Decidir e travar com teste no Plano 2.

## Backend

### Estrutura (setup) — admin

Gerenciada no painel admin (como Usuários), protegida por `X-Admin-Token`:

- `GET/POST/PATCH/DELETE /admin/tenants/{tenant_id}/grupos`
- `GET/POST/PATCH/DELETE /admin/tenants/{tenant_id}/lojas`
- Ligar/desligar `modo_rede` do tenant (campo em `PATCH` do tenant ou endpoint dedicado).

### Portal (cliente)

- `GET /me/lojas` — devolve a árvore grupos → lojas + `nivel_preenchimento` + `modo_rede`, para montar o seletor.
- `GET /me/avaliacoes?nivel=loja&loja_id=…` | `nivel=grupo&grupo_id=…` | `nivel=rede`
  - `nivel=loja` → série crua da loja.
  - `nivel=grupo` → série consolidada do grupo (por semana).
  - `nivel=rede` → série consolidada da rede (por semana).
  - Sem `modo_rede`: endpoint atual inalterado (série do tenant).
- **Lançamentos** (`POST`/`PATCH`): aceitam `grupo_id` e `loja_id`.
  - `modo_rede` on + grupo `nivel='loja'` → `loja_id` obrigatório.
  - `modo_rede` on + grupo `nivel='grupo'` → `grupo_id` obrigatório, `loja_id` NULL.
  - `modo_rede` off → ambos NULL (comportamento atual).
- **Preservação de campos apply-only:** manter `_preserve_apply_only()` (`total_estoque_lancamentos`) funcionando por (tenant, semana, grupo, loja).

### Novo serviço

`backend/app/services/consolidacao_service.py` — `consolidar_valores()` + helpers de ponderação. Coberto por testes unitários (ver seção Testes).

## Frontend — Portal cliente

**Princípio:** o portal já carrega tudo em `records[]` e todos os renders (Inspetor, Painel, Gráficos, Histórico) operam sobre essa série genérica. A mudança é cirúrgica: **um seletor de nível troca qual série está em `records[]` e chama `renderAll()`**. O código de render praticamente não muda — respeita a regra de ouro do `script.js`.

### Seletor de nível (topbar)

- Aparece **somente** quando `modo_rede` on.
- Estrutura em 3 níveis, agrupada visualmente:
  - `REDE (consolidado)`
  - por grupo: `Grupo X (consolidado)`
  - loja (aninhada sob o grupo): só para grupos `nivel='loja'`.
- Ao trocar: busca a série do nível → substitui `records[]` → `renderAll()`.

### Lançamentos

- Exige uma **unidade de preenchimento** selecionada:
  - grupo `nivel='grupo'` → lança no grupo.
  - grupo `nivel='loja'` → escolhe a loja.
- Níveis consolidados (rede / grupo somado) são **somente leitura** — sem botão de novo lançamento.
- `collectFormData()` inclui `grupo_id`/`loja_id` conforme a unidade ativa.

### Regras de sintaxe

Sem template literals aninhados (lição 2026-05-18). Concatenação/variáveis intermediárias. Verificar console F12 sem erros após cada edição.

## Excesso Crítico por loja

O Excel de Excesso já traz a coluna `Filial` (1–6). Com `lojas.filial_excel` mapeando Filial → loja:

- Assistente agrupa produtos por `Filial` → aplica o excesso de cada filial no lançamento **da loja correspondente** (via `/aplicar/{avaliacao_id}` da respectiva loja).
- `filial_excel` é único por tenant (uma filial do Excel = uma unidade). Para **grupo `nivel='grupo'`** (sem lojas), a(s) filial(is) daquele grupo somam e aplicam **no lançamento do grupo**.
- Excesso consolidado (grupo/rede) = **soma** dos `excesso_curva_*` (já aditivo — cai na consolidação padrão).
- `modo_rede` off → comportamento atual (aplica no único lançamento do tenant).

## Relatório por e-mail por nível

`relatorio_service` reusa `consolidar_valores`:

- Envio no nível **rede** (padrão), **grupo** e/ou **loja**, configurável no admin (`tenant_pdf_config`).
- `relatorio_html` renderiza a série do nível escolhido (mesmo template).

## Comparativo lado a lado

Nova **seção isolada** no portal ("Comparativo"), com render próprio (`renderComparativo()`) que **não toca** Inspetor/Painel/Gráficos/Histórico existentes — isolamento protege o `script.js` sensível. Visível somente com `modo_rede` on e mais de uma unidade comparável.

**Unidades comparadas** dependem do nível ativo:
- Nível **rede** → compara os **grupos** (cada grupo pelo seu consolidado).
- Nível **grupo** (`nivel='loja'`) → compara as **lojas** daquele grupo.

### Modo snapshot (uma semana)

- Seletor de semana (padrão = mais recente).
- **Tabela comparativa:** indicadores nas linhas × uma coluna por unidade + coluna **Total (consolidado)**. Reusa `matrixVal`/`fmtMoneyShort`/`fmtPercent`.
- **Gráfico de barras agrupadas** dos indicadores-chave (QT, QD, Saldo, Índice QT/QD, Excesso) por unidade.

### Modo evolução (várias semanas)

- **Gráfico de linhas:** uma linha por unidade ao longo das semanas, para um indicador selecionável (ex.: Índice QT/QD, Saldo, QT). Seletor de indicador.

### Backend

- `GET /me/comparativo?nivel=rede|grupo&grupo_id=…&modo=snapshot&semana=…`
  → array `[{ unidade:{id,nome,tipo}, valores, indicadores }]` por unidade filha + o consolidado (Total). Reusa `consolidar_valores`.
- `GET /me/comparativo?nivel=rede|grupo&grupo_id=…&modo=evolucao`
  → por unidade, série `[{ semana, indicadores }]` (frontend escolhe o campo a plotar). Um único request (evita N chamadas).
- Sem `modo_rede`: seção não aparece; endpoint retorna vazio/404.

## Ciclo de financiamento opcional (2ª sugestão)

- Preenchimento opcional de PMP/PMV/PME já é possível: admin oculta os campos pela config de Campos.
- **Único ajuste:** garantir que, quando ocultos/ausentes, PMP/PMV/PME/Ciclo **não** sejam pintados de vermelho nem cobrados como risco no semáforo/diagnóstico do Inspetor — exibir como "não acompanhado" ou omitir.

## Ativação / migração

**Estado atual (todos os clientes):** rede sem grupo econômico, `modo_rede = false`, histórico com `grupo_id`/`loja_id` NULL → **intocado**.

Para ligar o recurso num cliente específico (opt-in deliberado):

1. Admin cria a estrutura: grupos econômicos e, para grupos `nivel='loja'`, as lojas. Rede sem noção de grupo → cria um **grupo único "Geral"**.
2. Script de migração **por cliente**: atribui o histórico existente à unidade adequada (ex.: uma loja "Matriz" no grupo Geral, ou o próprio grupo se `nivel='grupo'`). Executado sob demanda, nunca em massa.
3. Liga `modo_rede = true` só para aquele cliente.
4. Bump do Service Worker `qtqd-v13 → qtqd-v14`.

> Nenhuma etapa acima toca clientes que permanecem `modo_rede=false`. A migração é individual e reversível (basta desligar a flag).

## Testes

- **Unitários (`consolidar_valores`):** somatório de aditivos; ponderação de prazos; peso zero → média simples / zero; encadeamento loja→grupo→rede; grupo direto (`nivel='grupo'`) sem consolidar; índices/ciclo recalculados coerentes.
- **Paridade:** conferir que o consolidado da rede de um cliente = os números que o cliente somaria manualmente (validar com dados reais de um cliente piloto).
- **Retrocompatibilidade:** cliente `modo_rede=false` produz exatamente a mesma resposta de hoje em todos os endpoints (grupo_id/loja_id NULL).
- **E2E no portal:** seletor troca a série corretamente; lançamento grava no grupo/loja certo; consolidado bate; sem erros no console F12.
- **Comparativo:** snapshot com N unidades + Total soma corretamente; evolução plota uma linha por unidade; seção some para `modo_rede=false`; render isolado não altera Inspetor/Painel/Gráficos.

## Fora de escopo (fase 1)

- **Permissão de usuário por loja/grupo** (todos os usuários do cliente veem todas as unidades — coerente com "config compartilhada"). Deixado para depois deliberadamente, para não mexer em login/`tenant_usuarios` nesta fase.
- **Metas/orçamento por loja** (realizado × meta).

## Arquivos afetados (previsão)

| Arquivo | Mudança |
|---|---|
| Supabase (SQL) | +`modo_rede`, +`grupos_economicos`, +`lojas`, +`grupo_id`/`loja_id` |
| `backend/app/schemas/avaliacoes.py` | `grupo_id`/`loja_id` nos requests; schemas de grupo/loja |
| `backend/app/services/consolidacao_service.py` | **novo** — `consolidar_valores()` |
| `backend/app/api/v1/avaliacoes.py` | filtro por nível; consolidação; `_preserve_apply_only` por unidade |
| `backend/app/api/v1/comparativo.py` (ou em avaliacoes) | **novo** — `GET /me/comparativo` snapshot + evolução |
| `backend/app/api/v1/admin_clientes.py` (ou novo `admin_estrutura.py`) | CRUD grupos/lojas + toggle `modo_rede` |
| `backend/app/api/v1/excesso_critico.py` | aplicar por loja via `filial_excel` |
| `backend/app/services/relatorio_service.py` / `relatorio_html.py` | envio por nível |
| `shared/api_client.js` | métodos `getLojas`, CRUD grupos/lojas, série por nível |
| `frontend_cliente/script.js` | seletor de nível; troca de série; `loja_id`/`grupo_id` em lançamentos; semáforo tolerante a ciclo ausente; **`renderComparativo()` isolado** |
| `frontend_cliente/excesso_critico.js` | aplicar por loja |
| `frontend_cliente/index.html` | seletor no topbar; SW bump |
| `frontend_cliente/sw.js` | `qtqd-v13 → v14` |
| `frontend_admin/*` | seção de estrutura (grupos/lojas) + toggle `modo_rede` |

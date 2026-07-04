# Excesso Crítico — Exclusão de Lançamentos + Total de Estoque em Lançamentos

**Data:** 2026-07-04
**Cliente motivador:** Drogaria SV (`8044331a-4531-47c9-bbff-6546110d5767`)
**Arquivo de referência:** `~/Downloads/excesso_tabela_fabricante_2026-07-04.xlsx`

## Contexto

A fonte de dados do assistente de Excesso Crítico (Excel do ERP do cliente) ganhou uma nova coluna **`lancamento`**. Produtos em fase de lançamento não devem ser tratados como excesso de estoque (o giro ainda está se formando), então precisam ser **retirados do cálculo de excesso** e contabilizados separadamente.

### Estrutura do Excel novo (aba `Dados`, 8 colunas)

| Índice | Coluna | Observação |
|---|---|---|
| 0 | `Nome Completo` | |
| 1 | `Linha` | |
| 2 | `Curva` | A/B/C/D |
| 3 | `Filial` | 1–6 |
| 4 | **`lancamento`** | **NOVA** — valores observados: `"Sim - 90D"` (1.133 linhas), `"Não"` (32.758), 1 vazia |
| 5 | `MediaF Un` | média mensal de venda em unidades |
| 6 | `Qtd Estoque` | |
| 7 | `Estoque Valor` | |

### Fatos validados nos dados (2026-07-04)

- 33.892 linhas (produto × filial); 17.207 produtos agregados por (nome, linha, curva).
- **1.133 linhas de lançamento** ("Sim - 90D"), somando **R$ 66.232,77** de `Estoque Valor`.
- **Nenhum produto tem filiais mistas** (0 casos de Sim e Não no mesmo produto agregado) → excluir por linha ou por produto dá o mesmo resultado. A implementação exclui **por linha** (mais simples).

## Requisitos

1. **Retirar lançamentos do Excesso Crítico:** itens cujo `lancamento` começa com "Sim" não entram na agregação nem no cálculo de excesso. Os demais itens continuam passando pelas regras atuais de cobertura/curva **sem alteração**.
2. **Novo campo `total_estoque_lancamentos`:** soma pura do `Estoque Valor` de todos os itens de lançamento — **sem aplicar regra alguma** e **sem quebra por curva** (apenas o total).
3. **Exibir** o total no assistente de Excesso Crítico.
4. **Persistir** o total na avaliação semanal ao clicar em "Aplicar".
5. **Mostrar no painel semanal** o valor persistido, **somente leitura** (sem campo editável no formulário).
6. **Disponibilizar no gerador de gráficos** o campo "Total de Estoque em Lançamentos" como opção selecionável (consequência automática de incluí-lo em `matrixRows`, do qual `chartFieldCatalog` é derivado).

## Regra de detecção do lançamento

```
is_lancamento(cell) = String(cell).trim().toLowerCase().startsWith('sim')
```

- Captura "Sim - 90D", "Sim - 60D", "Sim", etc.
- "Não", vazio e `null` → não é lançamento.
- **Compatibilidade retroativa:** se a coluna `lancamento` não existir no arquivo (planilhas antigas), `total_estoque_lancamentos = 0` e o comportamento é idêntico ao atual (nenhum item excluído).

## Componentes e mudanças

### 1. Frontend — `frontend_cliente/excesso_critico.js` (cálculo no browser)

- `findColIndex(header, ['lancamento','Lançamento','Lançamentos','Lancamentos'])` → `iLanc` (pode ser `-1`).
- Helper `isLancamento(v)` conforme regra acima.
- No loop de linhas (`processarExcelArrayBuffer`): se `iLanc >= 0 && isLancamento(row[iLanc])` → `totalEstoqueLancamentos += toFloat(row[iValor])`, `qtdLancamentos++`, e `continue` (não agrega, não calcula excesso). Caso contrário, fluxo atual inalterado.
- Retorno passa a incluir, em `totais`: `total_estoque_lancamentos` (arredondado 2 casas); e em `resumo`: `qtd_lancamentos`.
- `renderResultado`: novo card KPI **"Estoque em Lançamentos"** com `fmtBRL(total_estoque_lancamentos)` + `qtd_lancamentos` produtos. Sem quebra por curva. Linha de resumo (`excResumo`) acrescenta "· X itens de lançamento excluídos".
- `aplicar` (payload de `aplicarExcesso`): inclui `total_estoque_lancamentos` junto de `excesso_curva_a/b/c/d`.

### 2. Backend — `backend/app/`

- `schemas/avaliacoes.py` → `AvaliacaoValores`: novo campo `total_estoque_lancamentos: float | None = 0` (segue o padrão dos demais campos monetários do JSONB).
- `api/v1/excesso_critico.py` → endpoint `POST /me/excesso-critico/aplicar/{avaliacao_id}`: o body passa a aceitar `total_estoque_lancamentos` e gravá-lo no JSONB `valores` (preservando os demais campos), junto com os `excesso_curva_*`.
- `services/calculos_qtqd.py`: **sem mudança** — não é campo calculado; é input armazenado, lido diretamente do `valores`.

### 3. Frontend — Painel semanal (`frontend_cliente/script.js` + `index.html`)

- Nova linha em `matrixRows` para `total_estoque_lancamentos`, rótulo "Total de Estoque em Lançamentos", formato moeda (`fmtMoneyShort`/`fmtMoney`).
- Tratado como **campo de indicador sempre visível** (fora de `componentLabels`/`configurableKeys`, como `excesso_total`), para não depender de config do admin e não sumir do painel.
- **Somente leitura** — nenhum input novo no formulário de lançamentos.
- Ler o valor direto de `record.total_estoque_lancamentos` (via `matrixVal`/acesso direto), com fallback `0`/`—` quando ausente.
- Bump do Service Worker: `qtqd-v12 → qtqd-v13` em `frontend_cliente/sw.js`.

## Fluxo de dados

```
Excel (browser) ──► excesso_critico.js
   ├─ itens "Sim*"  ─► soma em total_estoque_lancamentos (sem regra)
   └─ demais itens  ─► agregação + regras de cobertura/curva ─► excesso por curva
                                     │
                        "Aplicar" (payload: excesso_curva_a/b/c/d + total_estoque_lancamentos)
                                     ▼
        POST /me/excesso-critico/aplicar/{avaliacao_id}
                                     ▼
             avaliacoes_semanais.valores (JSONB) ← grava campos, preserva o resto
                                     ▼
        Painel semanal lê valores.total_estoque_lancamentos (somente leitura)
```

## Tratamento de erros / bordas

- Coluna `lancamento` ausente → sem exclusão, total = 0 (retrocompatível).
- Célula de lançamento vazia/`null` → item normal.
- `Estoque Valor` não numérico → `toFloat` já trata (0).
- Avaliação sem o campo no `valores` (registros antigos) → painel exibe `—`/`R$ 0`.

## Verificação (paridade de dados)

- Rodar o cálculo no browser com o arquivo de 2026-07-04 e confirmar:
  - `total_estoque_lancamentos = R$ 66.232,77`
  - `qtd_lancamentos = 1.133`
  - excesso por curva calculado apenas sobre os 32.758 itens não-lançamento.
- Testar "Aplicar" numa avaliação da Drogaria SV e conferir o valor gravado no `valores` (via API/DB) e exibido no painel.

## Fora de escopo (YAGNI)

- Quebra do total de lançamentos por curva.
- Campo editável de lançamentos no formulário semanal.
- Migração retroativa de avaliações antigas (o campo aparece só a partir do próximo "Aplicar").
- Configuração de visibilidade do campo no admin.

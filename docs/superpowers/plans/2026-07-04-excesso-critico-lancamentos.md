# Excesso Crítico — Lançamentos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Excluir os itens de lançamento ("Sim*") do cálculo de Excesso Crítico e expor/persistir um novo campo `total_estoque_lancamentos` (soma pura, sem curva).

**Architecture:** Cálculo do Excel roda 100% no browser (`excesso_critico.js`). Extrai-se uma função pura testável do cálculo. O total de lançamentos é persistido no JSONB `valores` da avaliação via `/aplicar`, e exibido no assistente e no painel semanal (leitura).

**Tech Stack:** JavaScript puro (browser + Node para teste), SheetJS (`xlsx`), FastAPI + Pydantic, Supabase SDK, pytest.

## Global Constraints

- **`script.js` é sensível:** nunca usar template literals aninhados; após qualquer edição, rodar `node --check frontend_cliente/script.js`.
- **Regra de detecção de lançamento:** `String(cell).trim().toLowerCase().startsWith('sim')`.
- **Nome do campo persistido (exato):** `total_estoque_lancamentos` no JSONB `valores`.
- **Sem quebra por curva** para o total de lançamentos — apenas o total.
- **Retrocompatível:** arquivo sem coluna `lancamento` → `total_estoque_lancamentos = 0`, comportamento atual inalterado.
- **Valores de referência (Excel Drogaria SV 2026-07-04):** `total_estoque_lancamentos = 66232.77`, `qtd_lancamentos = 1133`.
- **Idioma:** respostas e labels em pt-BR.
- **Deploy:** ao final, `git push origin main`.

---

### Task 1: Backend — schema + `/aplicar` aceita `total_estoque_lancamentos`

**Files:**
- Modify: `backend/app/schemas/avaliacoes.py:44` (adicionar campo após `excesso_curva_d`)
- Modify: `backend/app/api/v1/excesso_critico.py:222-260` (função `aplicar`)
- Create: `tests/backend/__init__.py`
- Test: `tests/backend/test_aplicar_lancamentos.py`

**Interfaces:**
- Produces: `AvaliacaoValores` com campo `total_estoque_lancamentos: float = 0`.
- Produces: helper puro `_merge_aplicar_valores(valores: dict, payload: dict) -> dict` em `excesso_critico.py` que grava `excesso_curva_a/b/c/d` e `total_estoque_lancamentos` (quando presentes e numéricos), preservando os demais campos; lança `ValueError` se algum for não-numérico.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/backend/__init__.py` (vazio) e `tests/backend/test_aplicar_lancamentos.py`:

```python
import pytest
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.api.v1.excesso_critico import _merge_aplicar_valores


def test_schema_tem_campo_com_default_zero():
    v = AvaliacaoValores()
    assert v.total_estoque_lancamentos == 0


def test_schema_aceita_valor():
    v = AvaliacaoValores(total_estoque_lancamentos=66232.77)
    assert v.total_estoque_lancamentos == 66232.77


def test_merge_grava_total_lancamentos_e_preserva_outros():
    valores = {"saldo_bancario": 100.0, "excesso_curva_a": 5.0}
    payload = {
        "excesso_curva_a": 11.0,
        "excesso_curva_b": 22.0,
        "excesso_curva_c": 33.0,
        "excesso_curva_d": 44.0,
        "total_estoque_lancamentos": 66232.77,
    }
    out = _merge_aplicar_valores(valores, payload)
    assert out["total_estoque_lancamentos"] == 66232.77
    assert out["excesso_curva_a"] == 11.0
    assert out["saldo_bancario"] == 100.0  # preservado


def test_merge_ignora_campo_ausente():
    valores = {"total_estoque_lancamentos": 10.0}
    out = _merge_aplicar_valores(valores, {"excesso_curva_a": 1.0})
    assert out["total_estoque_lancamentos"] == 10.0  # não sobrescrito


def test_merge_rejeita_nao_numerico():
    with pytest.raises(ValueError):
        _merge_aplicar_valores({}, {"total_estoque_lancamentos": "abc"})
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && python -m pytest tests/backend/test_aplicar_lancamentos.py -v`
Expected: FAIL — `ImportError: cannot import name '_merge_aplicar_valores'` e/ou `total_estoque_lancamentos` não existe no schema.

- [ ] **Step 3: Adicionar o campo ao schema**

Em `backend/app/schemas/avaliacoes.py`, após a linha `excesso_curva_d: float = 0` (linha 44), adicionar:

```python
    total_estoque_lancamentos: float = 0
```

- [ ] **Step 4: Extrair o helper e usá-lo no endpoint**

Em `backend/app/api/v1/excesso_critico.py`, adicionar o helper puro (antes da função `aplicar`, após a definição de `CURVA_KEYS`):

```python
APLICAR_FIELDS = list(CURVA_KEYS.values()) + ["total_estoque_lancamentos"]


def _merge_aplicar_valores(valores: dict, payload: dict) -> dict:
    """Grava os campos aplicáveis (excesso por curva + total de lançamentos) em `valores`,
    preservando os demais. Lança ValueError se algum campo presente for não-numérico."""
    out = dict(valores)
    for field in APLICAR_FIELDS:
        v = payload.get(field)
        if v is not None:
            try:
                out[field] = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"{field} deve ser numérico")
    return out
```

Substituir o bloco atual dentro de `aplicar` (linhas ~242-249) que faz o loop `for curva, field in CURVA_KEYS.items()` por:

```python
    valores = dict(res.data[0].get("valores") or {})
    try:
        valores = _merge_aplicar_valores(valores, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

E atualizar o retorno `valores_aplicados` para incluir o novo campo:

```python
        "valores_aplicados": {f: valores.get(f, 0) for f in APLICAR_FIELDS},
```

- [ ] **Step 5: Rodar o teste para confirmar que passa**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && python -m pytest tests/backend/test_aplicar_lancamentos.py -v`
Expected: PASS (5 passed).

- [ ] **Step 6: Commit**

```bash
cd "/Users/avj/Developer/Sistemas Python/QTQD"
git add backend/app/schemas/avaliacoes.py backend/app/api/v1/excesso_critico.py tests/backend/
git commit -m "feat(excesso): persistir total_estoque_lancamentos no /aplicar"
```

---

### Task 2: Frontend — cálculo puro exclui lançamentos + soma total (Node test)

**Files:**
- Modify: `frontend_cliente/excesso_critico.js` (extrair função pura + detecção de lançamento)
- Create: `tests/frontend/test_excesso_lancamentos.js`

**Interfaces:**
- Produces: função pura `calcularExcessoDeRows(rows, limites)` onde `rows` é `Array<Array>` (linha 0 = header) e `limites` é `{limite_a,limite_b,limite_c,limite_d}`. Retorna objeto com `totais` (incluindo `total_estoque_lancamentos`), `resumo` (incluindo `qtd_lancamentos`) e `produtos`.
- Produces: export CommonJS `module.exports = { calcularExcessoDeRows }` sob guarda `typeof module`.
- Consumes (Task 3): `processarExcelArrayBuffer` passa a delegar para `calcularExcessoDeRows` após ler o XLSX.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/frontend/test_excesso_lancamentos.js`:

```javascript
const assert = require('assert');
const { calcularExcessoDeRows } = require('../../frontend_cliente/excesso_critico.js');

const LIM = { limite_a: 120, limite_b: 150, limite_c: 150, limite_d: 180 };
const HEADER = ['Nome Completo','Linha','Curva','Filial','lancamento','MediaF Un','Qtd Estoque','Estoque Valor'];

// Produto de lançamento (deve ser excluído do excesso e somado no total)
// Produto normal sem venda com estoque > 1 (vira excesso total)
const rows = [
  HEADER,
  ['PROD LANC A','PERF','C','1','Sim - 90D', 0, 10, 500],   // lançamento → excluído
  ['PROD LANC B','PERF','D','2','Sim - 60D', 5, 3,  120],   // lançamento → excluído
  ['PROD NORMAL','PERF','D','1','Não',        0, 4,  200],   // sem venda, qtd>1 → excesso = todo o estoque (200)
];

const r = calcularExcessoDeRows(rows, LIM);

// total de lançamentos = 500 + 120 = 620, sem regra
assert.strictEqual(r.totais.total_estoque_lancamentos, 620);
assert.strictEqual(r.resumo.qtd_lancamentos, 2);
// excesso calculado só sobre o produto normal (curva D): 200
assert.strictEqual(r.totais.excesso_curva_d, 200);
assert.strictEqual(r.totais.total, 200);
// os produtos de lançamento não aparecem na lista de críticos
assert.ok(!r.produtos.some(p => p.nome.startsWith('PROD LANC')));

// Retrocompat: sem coluna lancamento → total 0, produto normal continua excesso
const HEADER2 = ['Nome Completo','Linha','Curva','Filial','MediaF Un','Qtd Estoque','Estoque Valor'];
const rows2 = [ HEADER2, ['PROD NORMAL','PERF','D','1', 0, 4, 200] ];
const r2 = calcularExcessoDeRows(rows2, LIM);
assert.strictEqual(r2.totais.total_estoque_lancamentos, 0);
assert.strictEqual(r2.totais.excesso_curva_d, 200);

console.log('OK — todos os asserts passaram');
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && node tests/frontend/test_excesso_lancamentos.js`
Expected: FAIL — `TypeError: calcularExcessoDeRows is not a function` (ainda não exportado).

- [ ] **Step 3: Extrair a função pura e adicionar a detecção de lançamento**

Em `frontend_cliente/excesso_critico.js`:

(a) Adicionar helper de detecção perto de `normCurva` (linha ~49):

```javascript
  const isLancamento = (v) => v != null && String(v).trim().toLowerCase().startsWith('sim');
```

(b) Extrair o corpo de cálculo de `processarExcelArrayBuffer` para uma função pura. Localizar o bloco que hoje monta `header`, `iNome..iValor`, agrega e calcula (linhas ~163-277) e movê-lo para uma nova função no mesmo escopo do IIFE:

```javascript
  function calcularExcessoDeRows(rows, limites) {
    if (!rows || !rows.length) throw new Error('Planilha sem dados.');
    const header = rows[0].map(c => String(c || '').trim());

    const iNome  = findColIndex(header, ['Nome Completo', 'Nome']);
    const iLinha = findColIndex(header, ['Linha']);
    const iCurva = findColIndex(header, ['Curva']);
    const iMedia = findColIndex(header, ['MediaF Un', 'Media', 'Media Un', 'MediaF']);
    const iQtd   = findColIndex(header, ['Qtd Estoque', 'Qtd', 'Estoque Qtd']);
    const iValor = findColIndex(header, ['Estoque Valor', 'Valor', 'Estoque R$']);
    const iLanc  = findColIndex(header, ['lancamento', 'Lançamento', 'Lançamentos', 'Lancamentos', 'Lancamento']);

    if (iNome < 0 || iCurva < 0 || iMedia < 0 || iQtd < 0 || iValor < 0) {
      throw new Error('Cabeçalho inválido. Esperado: Nome Completo, Linha, Curva, Filial, MediaF Un, Qtd Estoque, Estoque Valor.');
    }

    const limMap = { A: limites.limite_a, B: limites.limite_b, C: limites.limite_c, D: limites.limite_d };

    const agg = new Map();
    let totalLinhas = 0;
    let totalEstoqueLancamentos = 0;
    let qtdLancamentos = 0;

    for (let r = 1; r < rows.length; r++) {
      const row = rows[r];
      if (!row || row.every(v => v === null || v === undefined || v === '')) continue;
      const nome = row[iNome];
      if (!nome) continue;

      // Lançamento: soma pura no total e sai (não entra no excesso)
      if (iLanc >= 0 && isLancamento(row[iLanc])) {
        totalEstoqueLancamentos += toFloat(row[iValor]);
        qtdLancamentos++;
        continue;
      }

      const curva = normCurva(row[iCurva]);
      if (!limMap[curva]) continue;

      const linha = iLinha >= 0 ? String(row[iLinha] || '').trim() : '';
      const media = toFloat(row[iMedia]);
      const qtd   = toFloat(row[iQtd]);
      const valor = toFloat(row[iValor]);

      const key = String(nome).trim() + '||' + linha + '||' + curva;
      const existing = agg.get(key);
      if (existing) {
        existing.qtd   += qtd;
        existing.media += media;
        existing.valor += valor;
      } else {
        agg.set(key, { nome: String(nome).trim(), linha, curva, qtd, media, valor });
      }
      totalLinhas++;
    }

    const totaisCurva = { A: 0, B: 0, C: 0, D: 0 };
    const qtdCriticos = { A: 0, B: 0, C: 0, D: 0 };
    const produtosCriticos = [];
    let valorTotalEstoque = 0;

    agg.forEach(item => {
      valorTotalEstoque += item.valor;
      const { qtd, media, valor, curva } = item;
      if (qtd <= 0) return;

      const custoUn = qtd > 0 ? valor / qtd : 0;
      let excessoUn = 0;
      let coberturaDias = null;

      if (media === 0) {
        if (qtd > 1) { excessoUn = qtd; coberturaDias = null; }
      } else {
        coberturaDias = (qtd / media) * 30;
        const lim = limMap[curva];
        if (coberturaDias > lim) {
          const ideal = (media * lim) / 30;
          excessoUn = qtd - ideal;
        }
      }

      if (excessoUn > 0) {
        const excessoValor = excessoUn * custoUn;
        totaisCurva[curva] += excessoValor;
        qtdCriticos[curva]++;
        produtosCriticos.push({
          nome: item.nome, linha: item.linha, curva,
          qtd_estoque: Math.round(qtd * 100) / 100,
          media_un: Math.round(media * 10000) / 10000,
          cobertura_dias: coberturaDias !== null ? Math.round(coberturaDias * 10) / 10 : null,
          excesso_un: Math.round(excessoUn * 100) / 100,
          custo_un: Math.round(custoUn * 10000) / 10000,
          excesso_valor: Math.round(excessoValor * 100) / 100,
        });
      }
    });

    produtosCriticos.sort((a, b) => b.excesso_valor - a.excesso_valor);

    const round2 = v => Math.round(v * 100) / 100;
    const totalExcesso = totaisCurva.A + totaisCurva.B + totaisCurva.C + totaisCurva.D;

    return {
      limites: limMap,
      totais: {
        excesso_curva_a: round2(totaisCurva.A),
        excesso_curva_b: round2(totaisCurva.B),
        excesso_curva_c: round2(totaisCurva.C),
        excesso_curva_d: round2(totaisCurva.D),
        total: round2(totalExcesso),
        total_estoque_lancamentos: round2(totalEstoqueLancamentos),
      },
      resumo: {
        total_linhas_excel: totalLinhas,
        total_produtos_unicos: agg.size,
        total_produtos_criticos: produtosCriticos.length,
        qtd_criticos_por_curva: qtdCriticos,
        valor_total_estoque: round2(valorTotalEstoque),
        pct_excesso: valorTotalEstoque > 0 ? round2(totalExcesso / valorTotalEstoque * 100) : 0,
        qtd_lancamentos: qtdLancamentos,
      },
      produtos: produtosCriticos.slice(0, 100),
    };
  }
```

(c) Reescrever `processarExcelArrayBuffer` para apenas ler o XLSX e delegar:

```javascript
  function processarExcelArrayBuffer(buf, limites) {
    const wb = window.XLSX.read(buf, { type: 'array' });
    const ws = wb.Sheets[wb.SheetNames[0]];
    if (!ws) throw new Error('Planilha vazia.');
    const rows = window.XLSX.utils.sheet_to_json(ws, { header: 1, defval: null });
    return calcularExcessoDeRows(rows, limites);
  }
```

(d) Tornar o módulo carregável em Node SEM mover funções para fora do IIFE. Duas mudanças cirúrgicas:

1. Guardar o acesso a `window` na última linha do IIFE (linha 477). Trocar:

```javascript
  window.QTQD_EXCESSO = { init };
```

por:

```javascript
  if (typeof window !== 'undefined') window.QTQD_EXCESSO = { init };
  if (typeof module !== 'undefined' && module.exports) module.exports = { calcularExcessoDeRows };
```

> Como essa linha está DENTRO do IIFE, `calcularExcessoDeRows` (também definida dentro do IIFE) está no escopo — não é preciso mover nada. No load em Node, o único código executado no IIFE é a atribuição de variáveis e essas duas linhas guardadas; nenhuma função toca DOM em tempo de definição, então `require()` não lança.

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && node tests/frontend/test_excesso_lancamentos.js`
Expected: `OK — todos os asserts passaram`

- [ ] **Step 5: Verificar sintaxe do módulo**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && node --check frontend_cliente/excesso_critico.js && echo "SINTAXE OK"`
Expected: `SINTAXE OK`

- [ ] **Step 6: Verificação de paridade contra o Excel real (não commitada)**

Rodar um script ad-hoc que lê `~/Downloads/excesso_tabela_fabricante_2026-07-04.xlsx` com o pacote `xlsx` e chama `calcularExcessoDeRows`. Confirmar:
`total_estoque_lancamentos = 66232.77` e `qtd_lancamentos = 1133`.
(Instalar `xlsx` num prefixo temporário se necessário: `npm install xlsx --no-save --prefix /tmp/xlsx-verify`.)

- [ ] **Step 7: Commit**

```bash
cd "/Users/avj/Developer/Sistemas Python/QTQD"
git add frontend_cliente/excesso_critico.js tests/frontend/
git commit -m "feat(excesso): excluir lançamentos do cálculo e somar total_estoque_lancamentos (browser)"
```

---

### Task 3: Frontend — KPI no assistente + payload do "Aplicar"

**Files:**
- Modify: `frontend_cliente/excesso_critico.js` (`renderResultado` ~326-358 e `aplicar` ~414-420)

**Interfaces:**
- Consumes: `resp.totais.total_estoque_lancamentos` e `resp.resumo.qtd_lancamentos` (Task 2).
- Produces: payload de `aplicarExcesso` com `total_estoque_lancamentos` (consumido pelo backend da Task 1).

- [ ] **Step 1: Adicionar o KPI de lançamentos no `renderResultado`**

Em `renderResultado`, após montar `cardsHtml` e antes de `$('excKpis').innerHTML = cardsHtml;`, acrescentar um card extra ao final:

```javascript
    const lancCard = '<article class="kpi-card neutral" style="border-left:4px solid #7c3aed">'
      + '<span>Estoque em Lançamentos</span>'
      + '<strong>' + fmtBRL(t.total_estoque_lancamentos || 0) + '</strong>'
      + '<span class="txt-muted txt-xs">' + fmtInt(r.qtd_lancamentos || 0) + ' itens excluídos</span>'
      + '</article>';
    $('excKpis').innerHTML = cardsHtml + lancCard;
```

(Remover a linha antiga `$('excKpis').innerHTML = cardsHtml;`.)

- [ ] **Step 2: Incluir lançamentos na linha de resumo**

Substituir a montagem de `resumoTxt` para acrescentar os lançamentos excluídos:

```javascript
    const resumoTxt = fmtInt(r.total_linhas_excel) + ' linhas no Excel · '
      + fmtInt(r.total_produtos_unicos) + ' produtos únicos (após somar filiais) · '
      + fmtInt(r.qtd_lancamentos || 0) + ' itens de lançamento excluídos (' + fmtBRL(t.total_estoque_lancamentos || 0) + ') · '
      + 'Estoque total: ' + fmtBRL(r.valor_total_estoque) + ' · '
      + 'Excesso representa ' + fmtNum(r.pct_excesso) + '% do estoque';
```

- [ ] **Step 3: Enviar `total_estoque_lancamentos` no payload do "Aplicar"**

Na função `aplicar`, no objeto `payload` (linhas ~414-420), adicionar a chave:

```javascript
    const payload = {
      excesso_curva_a: t.excesso_curva_a,
      excesso_curva_b: t.excesso_curva_b,
      excesso_curva_c: t.excesso_curva_c,
      excesso_curva_d: t.excesso_curva_d,
      total_estoque_lancamentos: t.total_estoque_lancamentos || 0,
    };
```

- [ ] **Step 4: Verificar sintaxe**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && node --check frontend_cliente/excesso_critico.js && echo "SINTAXE OK"`
Expected: `SINTAXE OK`

- [ ] **Step 5: Commit**

```bash
cd "/Users/avj/Developer/Sistemas Python/QTQD"
git add frontend_cliente/excesso_critico.js
git commit -m "feat(excesso): KPI de lançamentos + envia total_estoque_lancamentos no aplicar"
```

---

### Task 4: Painel semanal (leitura) + bump do Service Worker

**Files:**
- Modify: `frontend_cliente/script.js:9` (array `matrixRows` — adicionar linha após `excesso_total`)
- Modify: `frontend_cliente/sw.js:1` (`qtqd-v12` → `qtqd-v13`)

**Interfaces:**
- Consumes: `record.total_estoque_lancamentos` (gravado no `valores` pela Task 1). `createRecordFromValues` faz `{...v, ...}`, então o campo passa direto para o record.

- [ ] **Step 1: Adicionar a linha no `matrixRows`**

Em `frontend_cliente/script.js`, no array `matrixRows` (linha 9), localizar o último item:

```javascript
{key:"excesso_total",label:"EXCESSO CRÍTICO TOTAL",format:"currency",rowClass:"row-header"}
```

e acrescentar, logo após ele (antes do `]` que fecha o array):

```javascript
,{key:"total_estoque_lancamentos",label:"TOTAL DE ESTOQUE EM LANÇAMENTOS",format:"currency"}
```

> Como `total_estoque_lancamentos` NÃO está em `componentLabels`, o filtro `visibleRows` o mantém sempre visível (igual a `excesso_total`). Não adicionar a `componentLabels`.

> **Gráficos (requisito adicional):** adicionar a linha ao `matrixRows` também faz o campo aparecer no gerador de gráficos automaticamente — `chartFieldCatalog` é derivado de `matrixRows` ([script.js:10](../../frontend_cliente/script.js)) e `isFieldVisible` retorna `true` para chaves fora da config. Nenhuma mudança em `chart_builder.js` é necessária. A verificação de que o campo aparece e pode ser plotado sem erro está na Task 5.

- [ ] **Step 2: Verificar sintaxe do script.js (CRÍTICO)**

Run: `cd "/Users/avj/Developer/Sistemas Python/QTQD" && node --check frontend_cliente/script.js && echo "SINTAXE OK"`
Expected: `SINTAXE OK`

- [ ] **Step 3: Bump do Service Worker**

Em `frontend_cliente/sw.js`, linha 1, trocar:

```javascript
const CACHE = 'qtqd-v12';
```

por:

```javascript
const CACHE = 'qtqd-v13';
```

- [ ] **Step 4: Commit**

```bash
cd "/Users/avj/Developer/Sistemas Python/QTQD"
git add frontend_cliente/script.js frontend_cliente/sw.js
git commit -m "feat(painel): linha somente-leitura Total de Estoque em Lançamentos + SW qtqd-v13"
```

---

### Task 5: Deploy + verificação end-to-end em produção

**Files:** nenhum (deploy + verificação)

- [ ] **Step 1: Push (auto-deploy Vercel)**

```bash
cd "/Users/avj/Developer/Sistemas Python/QTQD" && git push origin main
```

- [ ] **Step 2: Confirmar que o novo código está no ar**

Run (aguardar deploy): `curl -s "https://qtqd-vt2a.vercel.app/cliente/excesso_critico.js?n=$RANDOM" | grep -c "total_estoque_lancamentos"`
Expected: valor ≥ 1.

- [ ] **Step 3: Verificação E2E (headless) — assistente + aplicar + painel**

Com Chromium headless (padrão do projeto), logar como usuário da Drogaria SV, ir em Excesso Crítico, subir o Excel de 2026-07-04, confirmar o KPI "Estoque em Lançamentos = R$ 66.232,77 (1.133 itens)", clicar "Aplicar" numa semana de teste, e confirmar no painel a linha "TOTAL DE ESTOQUE EM LANÇAMENTOS" com o valor. Alternativamente, confirmar via API que `valores.total_estoque_lancamentos` foi gravado.

Confirmar também o requisito de **gráficos**: na seção Gráficos, o campo "Total de Estoque em Lançamentos" aparece como opção selecionável e pode ser plotado sem erro de console (o desenho usa `chartFieldCatalog.find`, que agora inclui a chave).

- [ ] **Step 4: Atualizar documentação**

Atualizar `CLAUDE.md`: seção Excesso Crítico (regra de exclusão de lançamentos + novo campo `total_estoque_lancamentos`), referência do SW para `qtqd-v13`, e um item no histórico de problemas/funcionalidades. Commit + push.

---

## Notas de verificação da regra

- Excesso continua idêntico ao atual para itens não-lançamento (mesmas fórmulas de cobertura/curva).
- `total_estoque_lancamentos` é soma pura de `Estoque Valor` dos itens "Sim*", sem curva e sem regra.
- Retrocompatibilidade validada pelo Step 3 da Task 2 (arquivo sem coluna `lancamento`).

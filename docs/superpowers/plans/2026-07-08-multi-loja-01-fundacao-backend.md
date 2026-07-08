# Multi-loja — Plano 1: Fundação backend (schema + consolidação)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a lógica de consolidação de valores (soma de aditivos + média ponderada de prazos/índices) como função pura testável, e adicionar os campos `grupo_id`/`loja_id` aos schemas — sem tocar em nenhum endpoint, DB ou frontend.

**Architecture:** Uma função pura `consolidar_valores(itens) -> AvaliacaoValores` no novo `consolidacao_service.py`, reaproveitada depois por todos os níveis (loja→grupo→rede) e pelo comparativo/e-mail. Estratégia: consolidar os inputs crus e deixar o `calcular_indicadores` existente derivar os calculados — garante coerência (índice da rede = QT_rede ÷ QD_rede). Campos `grupo_id`/`loja_id` entram nos schemas Pydantic como opcionais (default None) para retrocompatibilidade total.

**Tech Stack:** Python 3.14, Pydantic, pytest. Testes em `tests/backend/`, rodados com `python3 -m pytest`.

## Global Constraints (valem para TODOS os planos multi-loja)

- **Idioma:** português brasileiro em toda mensagem/UI/commit.
- **Não-regressão (requisito duro):** cliente sem `modo_rede` (todos os atuais) deve manter comportamento idêntico. Novos campos `grupo_id`/`loja_id` default NULL; nenhum caminho novo acionado sem grupos/lojas cadastrados.
- **Fonte única da consolidação:** a regra vive só no backend (`consolidacao_service.py`). Não duplicar em JS (lição do drift do Excesso Crítico).
- **Roteiro de planos (referência):** este é o Plano 1 de 4.
  - **Plano 1 (este):** schema + `consolidar_valores` (puro, TDD, sem DB).
  - **Plano 2:** DDL Supabase (tabelas/colunas/índice único parcial) + endpoints admin (CRUD grupos/lojas, toggle `modo_rede`) + `/me/lojas` + avaliações com unidade + série por nível + `/me/comparativo`.
  - **Plano 3:** UI admin (estrutura grupos/lojas + toggle).
  - **Plano 4:** UI portal (seletor de nível, troca de série, lançamentos por unidade, Comparativo isolado, Excesso por loja, e-mail por nível, semáforo tolerante a ciclo ausente) + bump SW `qtqd-v13 → v14`.
- **Spec de referência:** `docs/superpowers/specs/2026-07-08-multi-loja-grupo-economico-design.md`.

---

## File Structure (Plano 1)

- **Create:** `backend/app/services/consolidacao_service.py` — `consolidar_valores()`, `media_ponderada()`, constantes `ADITIVOS`/`PONDERADOS`. Responsabilidade única: consolidar uma lista de `AvaliacaoValores` numa só.
- **Modify:** `backend/app/schemas/avaliacoes.py` — campos `grupo_id`/`loja_id` opcionais em `AvaliacaoCreateRequest`, `AvaliacaoUpdateRequest` e `AvaliacaoResponse`.
- **Create:** `tests/backend/test_consolidacao.py` — testes unitários da consolidação.
- **Create:** `tests/backend/test_schema_unidade.py` — testes dos campos novos do schema.

---

### Task 1: Campos `grupo_id`/`loja_id` nos schemas (retrocompat)

**Files:**
- Modify: `backend/app/schemas/avaliacoes.py`
- Test: `tests/backend/test_schema_unidade.py`

**Interfaces:**
- Consumes: nada.
- Produces: `AvaliacaoCreateRequest`, `AvaliacaoUpdateRequest`, `AvaliacaoResponse` passam a ter `grupo_id: UUID | None = None` e `loja_id: UUID | None = None`.

- [ ] **Step 1: Write the failing test**

Create `tests/backend/test_schema_unidade.py`:

```python
from uuid import UUID
from datetime import date
from backend.app.schemas.avaliacoes import (
    AvaliacaoCreateRequest,
    AvaliacaoUpdateRequest,
)

TID = UUID("b2ce08a4-b1f9-4465-b162-9f5e9bb70092")
GID = UUID("11111111-1111-1111-1111-111111111111")
LID = UUID("22222222-2222-2222-2222-222222222222")


def test_create_default_unidade_none():
    req = AvaliacaoCreateRequest(tenant_id=TID, semana_referencia=date(2026, 7, 6))
    assert req.grupo_id is None
    assert req.loja_id is None


def test_create_aceita_unidade():
    req = AvaliacaoCreateRequest(
        tenant_id=TID, semana_referencia=date(2026, 7, 6), grupo_id=GID, loja_id=LID
    )
    assert req.grupo_id == GID
    assert req.loja_id == LID


def test_update_aceita_unidade():
    req = AvaliacaoUpdateRequest(grupo_id=GID, loja_id=LID)
    assert req.grupo_id == GID
    assert req.loja_id == LID
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_schema_unidade.py -q`
Expected: FAIL — `AvaliacaoCreateRequest` não aceita `grupo_id`/`loja_id` (ou atributo inexistente).

- [ ] **Step 3: Add the fields**

In `backend/app/schemas/avaliacoes.py`, add `grupo_id`/`loja_id` to the three models:

```python
class AvaliacaoCreateRequest(AvaliacaoValores):
    tenant_id: UUID
    semana_referencia: date
    status: str = "rascunho"
    observacoes: str | None = None
    grupo_id: UUID | None = None
    loja_id: UUID | None = None


class AvaliacaoUpdateRequest(BaseModel):
    semana_referencia: date | None = None
    status: str | None = None
    observacoes: str | None = None
    valores: AvaliacaoValores | None = None
    grupo_id: UUID | None = None
    loja_id: UUID | None = None
```

And in `AvaliacaoResponse`, add after `tenant_id`:

```python
    grupo_id: UUID | None = None
    loja_id: UUID | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_schema_unidade.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Verify no regression on existing tests**

Run: `python3 -m pytest tests/backend/ -q`
Expected: all previous tests still PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/avaliacoes.py tests/backend/test_schema_unidade.py
git commit -m "feat(schema): campos opcionais grupo_id/loja_id nas avaliacoes (retrocompat)"
```

---

### Task 2: `media_ponderada` — helper com fallback

**Files:**
- Create: `backend/app/services/consolidacao_service.py`
- Test: `tests/backend/test_consolidacao.py`

**Interfaces:**
- Consumes: nada.
- Produces: `media_ponderada(valores: list[float], pesos: list[float]) -> float`. Retorna média ponderada; se `sum(pesos) == 0`, média simples dos valores > 0; se não houver valor > 0, `0.0`.

- [ ] **Step 1: Write the failing test**

Create `tests/backend/test_consolidacao.py`:

```python
import pytest
from backend.app.services.consolidacao_service import media_ponderada


def test_media_ponderada_basica():
    # (30*100 + 60*300) / (100+300) = 21000/400 = 52.5
    assert media_ponderada([30.0, 60.0], [100.0, 300.0]) == pytest.approx(52.5)


def test_peso_zero_cai_para_media_simples_dos_positivos():
    # pesos zerados -> média simples de [30, 50] (ignora o 0)
    assert media_ponderada([30.0, 0.0, 50.0], [0.0, 0.0, 0.0]) == pytest.approx(40.0)


def test_tudo_zero_retorna_zero():
    assert media_ponderada([0.0, 0.0], [0.0, 0.0]) == 0.0


def test_nao_divide_por_zero():
    # não lança exceção mesmo com pesos zerados
    assert media_ponderada([10.0], [0.0]) == pytest.approx(10.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_consolidacao.py -q`
Expected: FAIL — módulo `consolidacao_service` não existe.

- [ ] **Step 3: Create the module with `media_ponderada`**

Create `backend/app/services/consolidacao_service.py`:

```python
from backend.app.schemas.avaliacoes import AvaliacaoValores


def media_ponderada(valores: list[float], pesos: list[float]) -> float:
    """Média ponderada com fallback seguro.

    Se a soma dos pesos for > 0, retorna Σ(v·p)/Σ(p).
    Se todos os pesos forem 0, retorna a média simples dos valores > 0.
    Se não houver valor > 0, retorna 0.0. Nunca divide por zero.
    """
    soma_pesos = sum(pesos)
    if soma_pesos > 0:
        return sum(v * p for v, p in zip(valores, pesos)) / soma_pesos
    positivos = [v for v in valores if v > 0]
    if positivos:
        return sum(positivos) / len(positivos)
    return 0.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_consolidacao.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/consolidacao_service.py tests/backend/test_consolidacao.py
git commit -m "feat(consolidacao): helper media_ponderada com fallback seguro"
```

---

### Task 3: `consolidar_valores` — soma de aditivos + ponderação

**Files:**
- Modify: `backend/app/services/consolidacao_service.py`
- Test: `tests/backend/test_consolidacao.py`

**Interfaces:**
- Consumes: `media_ponderada` (Task 2); `AvaliacaoValores` (schema).
- Produces: `consolidar_valores(itens: list[AvaliacaoValores | dict]) -> AvaliacaoValores`. Soma os campos de `ADITIVOS`; pondera os de `PONDERADOS` pela sua base. Lista vazia → `AvaliacaoValores()` (tudo zero).

- [ ] **Step 1: Write the failing test**

Append to `tests/backend/test_consolidacao.py`:

```python
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.consolidacao_service import consolidar_valores


def test_consolidar_soma_aditivos():
    l1 = AvaliacaoValores(saldo_bancario=100.0, estoque_custo=1000.0, excesso_curva_d=50.0)
    l2 = AvaliacaoValores(saldo_bancario=200.0, estoque_custo=3000.0, excesso_curva_d=70.0)
    out = consolidar_valores([l1, l2])
    assert out.saldo_bancario == 300.0
    assert out.estoque_custo == 4000.0
    assert out.excesso_curva_d == 120.0


def test_consolidar_pondera_pmp_por_compras():
    # PMP ponderado por compras_mes: (30*100 + 60*300)/(400) = 52.5
    l1 = AvaliacaoValores(pmp=30.0, compras_mes=100.0)
    l2 = AvaliacaoValores(pmp=60.0, compras_mes=300.0)
    out = consolidar_valores([l1, l2])
    assert out.pmp == pytest.approx(52.5)
    assert out.compras_mes == 400.0  # aditivo


def test_consolidar_pondera_pmv_e_pme():
    l1 = AvaliacaoValores(pmv=40.0, venda_custo_mes=1000.0, pme_excel=25.0, estoque_custo=500.0)
    l2 = AvaliacaoValores(pmv=20.0, venda_custo_mes=1000.0, pme_excel=35.0, estoque_custo=1500.0)
    out = consolidar_valores([l1, l2])
    assert out.pmv == pytest.approx(30.0)                       # (40+20)/2 pesos iguais
    assert out.pme_excel == pytest.approx((25*500 + 35*1500)/2000)  # 32.5


def test_consolidar_lista_vazia_zero():
    out = consolidar_valores([])
    assert out.saldo_bancario == 0.0
    assert out.pmp == 0.0


def test_consolidar_aceita_dict():
    out = consolidar_valores([{"saldo_bancario": 10.0}, {"saldo_bancario": 5.0}])
    assert out.saldo_bancario == 15.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_consolidacao.py -q`
Expected: FAIL — `consolidar_valores` não existe.

- [ ] **Step 3: Implement `consolidar_valores` + constantes**

Append to `backend/app/services/consolidacao_service.py` (acima de `media_ponderada`, adicionar as constantes; abaixo, a função):

```python
# Campos que somam diretamente na consolidação
ADITIVOS = [
    "saldo_bancario", "contas_receber", "cartoes", "convenios", "cheques",
    "trade_marketing", "outros_qt", "estoque_custo", "contas_pagar",
    "fornecedores", "investimentos_assumidos", "outras_despesas_assumidas",
    "dividas", "financiamentos", "tributos_atrasados", "acoes_processos",
    "faturamento_previsto_mes", "compras_mes", "entrada_mes",
    "venda_cupom_mes", "venda_custo_mes", "lucro_liquido_mes",
    "excesso_curva_a", "excesso_curva_b", "excesso_curva_c", "excesso_curva_d",
    "total_estoque_lancamentos",
]

# Campos ponderados: campo -> campo base do peso
PONDERADOS = {
    "pmp": "compras_mes",
    "pmv": "venda_custo_mes",
    "pmv_avista": "venda_custo_mes",
    "pmv_30": "venda_custo_mes",
    "pmv_60": "venda_custo_mes",
    "pmv_90": "venda_custo_mes",
    "pmv_120": "venda_custo_mes",
    "pmv_outros": "venda_custo_mes",
    "pme_excel": "estoque_custo",
    "cobertura_estoque_dia": "estoque_custo",
    "indice_faltas": "venda_custo_mes",
}


def _as_valores(item) -> AvaliacaoValores:
    if isinstance(item, AvaliacaoValores):
        return item
    return AvaliacaoValores(**item)


def consolidar_valores(itens) -> AvaliacaoValores:
    """Consolida uma lista de AvaliacaoValores numa só.

    Aditivos somam; prazos/índices são média ponderada pela sua base
    (ver PONDERADOS). Lista vazia -> AvaliacaoValores() (tudo zero).
    Os campos calculados NÃO são tratados aqui: quem precisar deles roda
    calcular_indicadores() sobre o resultado desta função.
    """
    registros = [_as_valores(i) for i in itens]
    if not registros:
        return AvaliacaoValores()
    out: dict = {}
    for campo in ADITIVOS:
        out[campo] = sum(getattr(r, campo) for r in registros)
    for campo, base in PONDERADOS.items():
        valores = [getattr(r, campo) for r in registros]
        pesos = [getattr(r, base) for r in registros]
        out[campo] = media_ponderada(valores, pesos)
    return AvaliacaoValores(**out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_consolidacao.py -q`
Expected: PASS (todos).

- [ ] **Step 5: Verify all fields covered (guard test)**

Append test that garante que todo campo do schema é aditivo OU ponderado (evita esquecer um campo no futuro):

```python
def test_todos_os_campos_do_schema_tem_regra():
    from backend.app.services.consolidacao_service import ADITIVOS, PONDERADOS
    campos = set(AvaliacaoValores().model_dump().keys())
    cobertos = set(ADITIVOS) | set(PONDERADOS.keys())
    assert campos == cobertos, f"Sem regra: {campos - cobertos}; sobrando: {cobertos - campos}"
```

Run: `python3 -m pytest tests/backend/test_consolidacao.py::test_todos_os_campos_do_schema_tem_regra -q`
Expected: PASS. Se falhar, ajustar `ADITIVOS`/`PONDERADOS` até cobrir exatamente os campos do schema.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/consolidacao_service.py tests/backend/test_consolidacao.py
git commit -m "feat(consolidacao): consolidar_valores (soma aditivos + prazos ponderados)"
```

---

### Task 4: Propriedades hierárquicas (item único + associatividade loja→grupo→rede)

**Files:**
- Test: `tests/backend/test_consolidacao.py`

**Interfaces:**
- Consumes: `consolidar_valores` (Task 3).
- Produces: nada (só garante propriedades que o encadeamento loja→grupo→rede depende).

Estas propriedades justificam consolidar em cascata (loja→grupo, depois grupo→rede) obtendo o mesmo resultado de consolidar todas as lojas de uma vez — desde que os pesos sejam > 0. Nenhum código novo; apenas travar o comportamento com testes.

- [ ] **Step 1: Write the tests**

Append to `tests/backend/test_consolidacao.py`:

```python
def test_item_unico_reproduz_valores():
    x = AvaliacaoValores(saldo_bancario=123.0, pmp=45.0, compras_mes=900.0)
    out = consolidar_valores([x])
    assert out.saldo_bancario == 123.0
    assert out.pmp == pytest.approx(45.0)
    assert out.compras_mes == 900.0


def test_associatividade_loja_grupo_rede():
    # 3 lojas com pesos > 0: consolidar em cascata == consolidar tudo de uma vez
    l1 = AvaliacaoValores(saldo_bancario=100.0, pmp=30.0, compras_mes=100.0,
                          pmv=40.0, venda_custo_mes=200.0)
    l2 = AvaliacaoValores(saldo_bancario=200.0, pmp=60.0, compras_mes=300.0,
                          pmv=20.0, venda_custo_mes=600.0)
    l3 = AvaliacaoValores(saldo_bancario=50.0, pmp=10.0, compras_mes=50.0,
                          pmv=90.0, venda_custo_mes=100.0)

    plano = consolidar_valores([l1, l2, l3])
    cascata = consolidar_valores([consolidar_valores([l1, l2]), consolidar_valores([l3])])

    assert cascata.saldo_bancario == pytest.approx(plano.saldo_bancario)
    assert cascata.pmp == pytest.approx(plano.pmp)
    assert cascata.pmv == pytest.approx(plano.pmv)
    assert cascata.compras_mes == pytest.approx(plano.compras_mes)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `python3 -m pytest tests/backend/test_consolidacao.py -q`
Expected: PASS (as duas novas passam sem alterar o código — as propriedades já valem).

Se `test_associatividade_loja_grupo_rede` falhar, é sinal de bug na ponderação — revisar `media_ponderada`/`consolidar_valores`, NÃO relaxar o teste.

- [ ] **Step 3: Commit**

```bash
git add tests/backend/test_consolidacao.py
git commit -m "test(consolidacao): trava item único e associatividade loja->grupo->rede"
```

---

### Task 5: Coerência com `calcular_indicadores` (consolidar cru → derivar)

**Files:**
- Test: `tests/backend/test_consolidacao.py`

**Interfaces:**
- Consumes: `consolidar_valores` (Task 3); `calcular_indicadores` (`backend/app/services/calculos_qtqd.py`).
- Produces: nada (garante que rodar `calcular_indicadores` sobre o consolidado dá índice/ciclo coerentes com os agregados).

- [ ] **Step 1: Write the test**

Append to `tests/backend/test_consolidacao.py`:

```python
from backend.app.services.calculos_qtqd import calcular_indicadores


def _ind(indicadores, codigo):
    return next(i.valor for i in indicadores if i.codigo == codigo)


def test_indice_consolidado_eh_qt_sobre_qd_nao_media_de_indices():
    # Loja A: QT alto, QD baixo; Loja B: QT baixo, QD alto.
    a = AvaliacaoValores(saldo_bancario=1000.0, estoque_custo=0.0, contas_pagar=500.0)
    b = AvaliacaoValores(saldo_bancario=100.0, estoque_custo=0.0, contas_pagar=1000.0)
    cons = consolidar_valores([a, b])
    ind = calcular_indicadores(cons)
    # QT_rede = 1100, QD_rede = 1500 -> índice = 1100/1500 ≈ 0.7333
    assert _ind(ind, "qt_total") == pytest.approx(1100.0)
    assert _ind(ind, "qd_total") == pytest.approx(1500.0)
    assert _ind(ind, "indice_qt_qd") == pytest.approx(1100.0 / 1500.0)


def test_ciclo_consolidado_usa_prazos_ponderados():
    # PMP ponderado por compras, PMV por venda_custo, PME_excel por estoque
    a = AvaliacaoValores(pmp=40.0, compras_mes=1000.0, pmv=30.0, venda_custo_mes=1000.0,
                         pme_excel=20.0, estoque_custo=1000.0)
    b = AvaliacaoValores(pmp=20.0, compras_mes=1000.0, pmv=10.0, venda_custo_mes=1000.0,
                         pme_excel=40.0, estoque_custo=1000.0)
    cons = consolidar_valores([a, b])
    ind = calcular_indicadores(cons)
    # pmp=30, pmv=20, pme=30 -> ciclo = 30 - 20 - 30 = -20
    assert cons.pmp == pytest.approx(30.0)
    assert cons.pmv == pytest.approx(20.0)
    assert cons.pme_excel == pytest.approx(30.0)
    assert _ind(ind, "ciclo_financiamento") == pytest.approx(-20.0)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_consolidacao.py -q`
Expected: PASS.

- [ ] **Step 3: Run the full backend suite**

Run: `python3 -m pytest tests/backend/ -q`
Expected: todos PASS (incluindo os testes antigos, intocados).

- [ ] **Step 4: Commit**

```bash
git add tests/backend/test_consolidacao.py
git commit -m "test(consolidacao): índice e ciclo coerentes ao derivar do consolidado"
```

---

## Self-Review (Plano 1)

- **Cobertura do spec (parte "Consolidação"):** aditivos somam (Task 3) ✓; prazos ponderados pelas bases corretas (Task 3, PONDERADOS) ✓; peso zero → média simples (Task 2) ✓; encadeamento loja→grupo→rede (Task 4) ✓; grupo direto = item único reproduz (Task 4) ✓; índices/ciclo recalculados coerentes (Task 5) ✓; `total_estoque_lancamentos` aditivo (Task 3, em ADITIVOS) ✓.
- **Retrocompat:** Task 1 adiciona campos opcionais default None; Step 5 roda a suíte antiga inteira. `consolidar_valores` é código novo não referenciado por nenhum caminho existente → zero efeito nos clientes atuais. ✓
- **Sem placeholders:** todo passo tem código/comando/expected concretos. ✓
- **Consistência de tipos:** `media_ponderada(valores, pesos) -> float`, `consolidar_valores(itens) -> AvaliacaoValores`, `_as_valores` usados de forma consistente entre tasks. `calcular_indicadores(valores) -> list[IndicadorCalculado]` conforme assinatura real do arquivo. ✓
- **Fora deste plano (vai para o Plano 2):** DDL Supabase, índice único parcial (risco de regressão de unicidade documentado no spec), endpoints. Nenhuma dependência de DB neste plano.

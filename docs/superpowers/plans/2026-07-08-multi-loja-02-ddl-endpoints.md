# Multi-loja — Plano 2: DDL Supabase + endpoints

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persistir a estrutura rede→grupo→loja e servir as séries por nível (loja/grupo/rede) e o comparativo, reusando `consolidar_valores` do Plano 1. Toda a lógica de agregação por nível vive em funções puras testáveis; os endpoints são wrappers finos sobre o Supabase.

**Architecture:** DDL entregue como arquivo SQL (rodado manualmente no Supabase, padrão do projeto). Um `series_service.py` puro transforma linhas de avaliações + estrutura em séries por nível e no comparativo — testado sem DB. Endpoints admin (CRUD grupos/lojas + toggle `modo_rede`), `/me/lojas`, série por nível em `/avaliacoes`, e `/me/comparativo` chamam o `series_service`.

**Tech Stack:** Python 3.14, FastAPI, Supabase SDK, Pydantic, pytest (`python3 -m pytest`).

## Global Constraints

- **Idioma:** português brasileiro (mensagens/commits/docstrings).
- **Não-regressão (requisito duro):** cliente com `modo_rede=false` (todos os atuais) — `grupo_id`/`loja_id` NULL — recebe respostas idênticas às de hoje em TODOS os endpoints existentes. O endpoint `GET /avaliacoes` sem parâmetros de nível continua devolvendo a série do tenant como hoje.
- **Fonte única da consolidação:** usar `consolidar_valores` do Plano 1 (`backend/app/services/consolidacao_service.py`); não reimplementar.
- **Padrões do repo:** endpoints de cliente sob `prefix="/me"` com `Depends(get_current_tenant)`; endpoints admin com `dependencies=[Depends(require_admin_token)]`; UUIDs/datas como `str()` nas queries; `updated_at` manual em UPDATE; `get_supabase()` cria cliente novo a cada chamada (nunca singleton).
- **Detalhamento heterogêneo (ver spec):** ao consolidar, para evitar o descarte silencioso de total vs sub-itens, `series_service` normaliza cada `valores` antes de consolidar (ver Task 3, `_normalizar_detalhe`). Regra: se qualquer sub-item de um grupo (contas_receber / contas_pagar / dividas) > 0, zera o campo-total correspondente; senão mantém. Isso torna a soma coerente com a prioridade "ou-ou" do `calcular_indicadores`.
- **Handoff humano:** a Task 1 (DDL) é aplicada pelo usuário no Supabase SQL Editor. Endpoints que tocam o banco não têm teste automatizado (o repo não tem testes de endpoint) — a verificação deles é a revisão + E2E manual do usuário.
- **Spec de referência:** `docs/superpowers/specs/2026-07-08-multi-loja-grupo-economico-design.md`. **Plano 1 (dependência):** já concluído na branch `feature/multi-loja`.

---

## File Structure (Plano 2)

- **Create:** `tools/sql/2026-07-08-multi-loja.sql` — DDL idempotente (colunas + tabelas + índice único parcial). Artefato para o usuário rodar.
- **Create:** `backend/app/schemas/estrutura.py` — schemas `GrupoEconomico*`, `Loja*`, `LojasArvoreResponse`.
- **Create:** `backend/app/services/series_service.py` — funções puras: `build_series`, `build_comparativo_snapshot`, `build_comparativo_evolucao`, helpers `_normalizar_detalhe`, `_consolidar_grupo`.
- **Create:** `backend/app/api/v1/estrutura.py` — admin CRUD grupos/lojas + toggle `modo_rede`; `GET /me/lojas`.
- **Create:** `backend/app/api/v1/comparativo.py` — `GET /me/comparativo`.
- **Modify:** `backend/app/api/v1/avaliacoes.py` — persistir `grupo_id`/`loja_id`; `_COLS`/`_serialize`; validação de unidade; `GET /avaliacoes` aceita `nivel`/`loja_id`/`grupo_id`.
- **Modify:** `backend/app/api/router.py` — registrar `estrutura_router`, `comparativo_router`.
- **Create tests:** `tests/backend/test_series_service.py`, `tests/backend/test_estrutura_schema.py`, `tests/backend/test_avaliacao_unidade_validacao.py`.

---

### Task 1: DDL Supabase (artefato SQL)

**Files:**
- Create: `tools/sql/2026-07-08-multi-loja.sql`

**Interfaces:**
- Produces: as colunas/tabelas que os endpoints e o `series_service` assumem — `tenants.modo_rede`, `grupos_economicos(id,tenant_id,nome,nivel_preenchimento,ordem,ativo,created_at)`, `lojas(id,tenant_id,grupo_id,nome,cnpj,filial_excel,ordem,ativo,created_at)`, `avaliacoes_semanais.grupo_id`, `avaliacoes_semanais.loja_id`.

Não há teste automatizado (DDL roda no Supabase). O deliverable é o arquivo SQL revisado. O usuário roda no SQL Editor.

- [ ] **Step 1: Criar o arquivo SQL**

Create `tools/sql/2026-07-08-multi-loja.sql`:

```sql
-- Multi-loja / Grupo Econômico — DDL idempotente
-- Rodar no Supabase SQL Editor. Seguro: só adiciona; não altera dados existentes.

-- 1) Flag opt-in por cliente
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS modo_rede boolean DEFAULT false;

-- 2) Grupos econômicos
CREATE TABLE IF NOT EXISTS grupos_economicos (
  id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tenant_id           uuid        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome                text        NOT NULL,
  nivel_preenchimento text        NOT NULL DEFAULT 'loja',  -- 'loja' | 'grupo'
  ordem               integer     DEFAULT 0,
  ativo               boolean     DEFAULT true,
  created_at          timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_grupos_tenant ON grupos_economicos(tenant_id);

-- 3) Lojas
CREATE TABLE IF NOT EXISTS lojas (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tenant_id    uuid        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  grupo_id     uuid        NOT NULL REFERENCES grupos_economicos(id) ON DELETE CASCADE,
  nome         text        NOT NULL,
  cnpj         text,
  filial_excel integer,
  ordem        integer     DEFAULT 0,
  ativo        boolean     DEFAULT true,
  created_at   timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lojas_tenant ON lojas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lojas_grupo ON lojas(grupo_id);

-- 4) Dimensão nas avaliações
ALTER TABLE avaliacoes_semanais ADD COLUMN IF NOT EXISTS grupo_id uuid REFERENCES grupos_economicos(id) ON DELETE CASCADE;
ALTER TABLE avaliacoes_semanais ADD COLUMN IF NOT EXISTS loja_id  uuid REFERENCES lojas(id) ON DELETE CASCADE;

-- 5) Unicidade sem regressão:
--    a) registros SEM unidade (clientes atuais) permanecem únicos por (tenant, semana)
CREATE UNIQUE INDEX IF NOT EXISTS uq_aval_tenant_semana_sem_unidade
  ON avaliacoes_semanais(tenant_id, semana_referencia)
  WHERE grupo_id IS NULL AND loja_id IS NULL;
--    b) registros de rede: únicos por (tenant, semana, grupo, loja) usando COALESCE
--       para tratar loja_id NULL (grupo nivel='grupo') como chave estável
CREATE UNIQUE INDEX IF NOT EXISTS uq_aval_rede
  ON avaliacoes_semanais(
    tenant_id, semana_referencia, grupo_id,
    COALESCE(loja_id, '00000000-0000-0000-0000-000000000000'::uuid)
  )
  WHERE grupo_id IS NOT NULL;
```

- [ ] **Step 2: Revisar o SQL**

Confirme: (a) todo comando é idempotente (`IF NOT EXISTS`); (b) o índice parcial `uq_aval_tenant_semana_sem_unidade` preserva a garantia atual; (c) `uq_aval_rede` impede duplicar a mesma unidade na mesma semana. Nenhum comando altera linhas existentes.

- [ ] **Step 3: Commit**

```bash
git add tools/sql/2026-07-08-multi-loja.sql
git commit -m "feat(sql): DDL multi-loja (grupos, lojas, colunas, índices únicos parciais)"
```

- [ ] **Step 4: HANDOFF — usuário roda no Supabase**

O controlador deve avisar o usuário: "Rode `tools/sql/2026-07-08-multi-loja.sql` no Supabase SQL Editor antes do E2E." Não bloqueia os próximos tasks (que são código puro).

---

### Task 2: Schemas da estrutura (grupos/lojas)

**Files:**
- Create: `backend/app/schemas/estrutura.py`
- Test: `tests/backend/test_estrutura_schema.py`

**Interfaces:**
- Produces:
  - `GrupoCreate(nome: str, nivel_preenchimento: str = "loja", ordem: int = 0)`
  - `GrupoUpdate(nome: str | None, nivel_preenchimento: str | None, ordem: int | None, ativo: bool | None)`
  - `GrupoResponse(id: UUID, tenant_id: UUID, nome: str, nivel_preenchimento: str, ordem: int, ativo: bool)`
  - `LojaCreate(grupo_id: UUID, nome: str, cnpj: str | None = None, filial_excel: int | None = None, ordem: int = 0)`
  - `LojaUpdate(grupo_id: UUID | None, nome: str | None, cnpj: str | None, filial_excel: int | None, ordem: int | None, ativo: bool | None)`
  - `LojaResponse(id, tenant_id, grupo_id, nome, cnpj, filial_excel, ordem, ativo)`
  - `GrupoComLojas(GrupoResponse + lojas: list[LojaResponse])`
  - `LojasArvoreResponse(modo_rede: bool, grupos: list[GrupoComLojas])`

- [ ] **Step 1: Write the failing test**

Create `tests/backend/test_estrutura_schema.py`:

```python
from uuid import UUID
from backend.app.schemas.estrutura import (
    GrupoCreate, GrupoResponse, LojaCreate, LojaResponse,
    GrupoComLojas, LojasArvoreResponse,
)

TID = UUID("b2ce08a4-b1f9-4465-b162-9f5e9bb70092")
GID = UUID("11111111-1111-1111-1111-111111111111")
LID = UUID("22222222-2222-2222-2222-222222222222")


def test_grupo_create_default_nivel_loja():
    g = GrupoCreate(nome="Geral")
    assert g.nivel_preenchimento == "loja"
    assert g.ordem == 0


def test_grupo_create_nivel_grupo():
    g = GrupoCreate(nome="Consolidado", nivel_preenchimento="grupo")
    assert g.nivel_preenchimento == "grupo"


def test_loja_create_opcionais():
    l = LojaCreate(grupo_id=GID, nome="Loja 1")
    assert l.cnpj is None
    assert l.filial_excel is None


def test_arvore_response():
    grupo = GrupoComLojas(
        id=GID, tenant_id=TID, nome="Geral", nivel_preenchimento="loja",
        ordem=0, ativo=True,
        lojas=[LojaResponse(id=LID, tenant_id=TID, grupo_id=GID, nome="Loja 1",
                            cnpj=None, filial_excel=1, ordem=0, ativo=True)],
    )
    arvore = LojasArvoreResponse(modo_rede=True, grupos=[grupo])
    assert arvore.modo_rede is True
    assert arvore.grupos[0].lojas[0].nome == "Loja 1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_estrutura_schema.py -q`
Expected: FAIL — módulo `estrutura` não existe.

- [ ] **Step 3: Create the schemas**

Create `backend/app/schemas/estrutura.py`:

```python
from uuid import UUID

from pydantic import BaseModel


class GrupoCreate(BaseModel):
    nome: str
    nivel_preenchimento: str = "loja"  # 'loja' | 'grupo'
    ordem: int = 0


class GrupoUpdate(BaseModel):
    nome: str | None = None
    nivel_preenchimento: str | None = None
    ordem: int | None = None
    ativo: bool | None = None


class GrupoResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nome: str
    nivel_preenchimento: str
    ordem: int
    ativo: bool


class LojaCreate(BaseModel):
    grupo_id: UUID
    nome: str
    cnpj: str | None = None
    filial_excel: int | None = None
    ordem: int = 0


class LojaUpdate(BaseModel):
    grupo_id: UUID | None = None
    nome: str | None = None
    cnpj: str | None = None
    filial_excel: int | None = None
    ordem: int | None = None
    ativo: bool | None = None


class LojaResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    grupo_id: UUID
    nome: str
    cnpj: str | None = None
    filial_excel: int | None = None
    ordem: int
    ativo: bool


class GrupoComLojas(GrupoResponse):
    lojas: list[LojaResponse] = []


class LojasArvoreResponse(BaseModel):
    modo_rede: bool
    grupos: list[GrupoComLojas]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_estrutura_schema.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/estrutura.py tests/backend/test_estrutura_schema.py
git commit -m "feat(schema): estrutura grupos/lojas (multi-loja)"
```

---

### Task 3: `series_service.build_series` — série por nível (o cérebro)

**Files:**
- Create: `backend/app/services/series_service.py`
- Test: `tests/backend/test_series_service.py`

**Interfaces:**
- Consumes: `consolidar_valores` (Plano 1); `AvaliacaoValores`.
- Produces:
  - `_normalizar_detalhe(valores: dict) -> dict` — zera o campo-total quando há sub-itens > 0 (contas_receber/contas_pagar/dividas), para consolidação coerente.
  - `_consolidar_grupo(grupo: dict, avals_por_loja: dict[str, list[dict]], avals_grupo_direto: list[dict]) -> AvaliacaoValores | None`
  - `build_series(avaliacoes: list[dict], grupos: list[dict], nivel: str, ref_id: str | None) -> list[dict]`
    - `avaliacoes`: cada item tem `semana_referencia` (str), `grupo_id` (str|None), `loja_id` (str|None), `valores` (dict).
    - `nivel`: `"loja"` (ref_id=loja_id) | `"grupo"` (ref_id=grupo_id) | `"rede"` (ref_id=None).
    - `grupos`: lista de `{id, nivel_preenchimento}` do tenant.
    - Retorna lista de `{semana_referencia, valores}` (valores = dict consolidado), ordenada por semana desc.

- [ ] **Step 1: Write the failing tests**

Create `tests/backend/test_series_service.py`:

```python
import pytest
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.series_service import (
    _normalizar_detalhe, build_series,
)


def _av(semana, valores, grupo_id=None, loja_id=None):
    return {"semana_referencia": semana, "grupo_id": grupo_id,
            "loja_id": loja_id, "valores": valores}


def test_normalizar_zera_total_quando_ha_subitens():
    v = {"contas_receber": 500.0, "cartoes": 300.0, "convenios": 100.0}
    out = _normalizar_detalhe(v)
    assert out["contas_receber"] == 0.0   # zerado: sub-itens presentes
    assert out["cartoes"] == 300.0


def test_normalizar_mantem_total_sem_subitens():
    v = {"contas_receber": 500.0}
    out = _normalizar_detalhe(v)
    assert out["contas_receber"] == 500.0


def test_series_nivel_loja_retorna_serie_crua():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-06-29", {"saldo_bancario": 90.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 999.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="loja", ref_id="l1")
    assert [s["semana_referencia"] for s in serie] == ["2026-07-06", "2026-06-29"]
    assert serie[0]["valores"]["saldo_bancario"] == 100.0


def test_series_nivel_grupo_soma_lojas():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    serie = build_series(avals, grupos, nivel="grupo", ref_id="g1")
    assert len(serie) == 1
    assert serie[0]["valores"]["saldo_bancario"] == 300.0


def test_series_nivel_grupo_direto_usa_lancamento_do_grupo():
    avals = [_av("2026-07-06", {"saldo_bancario": 500.0}, grupo_id="g2", loja_id=None)]
    grupos = [{"id": "g2", "nivel_preenchimento": "grupo"}]
    serie = build_series(avals, grupos, nivel="grupo", ref_id="g2")
    assert serie[0]["valores"]["saldo_bancario"] == 500.0


def test_series_nivel_rede_soma_todos_os_grupos():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
        _av("2026-07-06", {"saldo_bancario": 500.0}, grupo_id="g2", loja_id=None),
    ]
    grupos = [
        {"id": "g1", "nivel_preenchimento": "loja"},
        {"id": "g2", "nivel_preenchimento": "grupo"},
    ]
    serie = build_series(avals, grupos, nivel="rede", ref_id=None)
    assert serie[0]["valores"]["saldo_bancario"] == 800.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_series_service.py -q`
Expected: FAIL — módulo não existe.

- [ ] **Step 3: Implement `series_service.py`**

Create `backend/app/services/series_service.py`:

```python
from backend.app.schemas.avaliacoes import AvaliacaoValores
from backend.app.services.consolidacao_service import consolidar_valores

# Total -> sub-itens que, se presentes (>0), tornam o total redundante
_GRUPOS_DETALHE = {
    "contas_receber": ("cartoes", "convenios", "cheques", "trade_marketing", "outros_qt"),
    "contas_pagar": ("fornecedores", "investimentos_assumidos", "outras_despesas_assumidas"),
    "dividas": ("financiamentos", "tributos_atrasados", "acoes_processos"),
}


def _normalizar_detalhe(valores: dict) -> dict:
    """Zera o campo-total quando há sub-itens > 0, para que a soma na consolidação
    não conflite com a prioridade 'ou-ou' de calcular_indicadores (evita descarte
    silencioso do total de uma loja quando outra detalha sub-itens)."""
    v = dict(valores)
    for total, subitens in _GRUPOS_DETALHE.items():
        if any(float(v.get(s) or 0) > 0 for s in subitens):
            v[total] = 0.0
    return v


def _valores_norm(av: dict) -> AvaliacaoValores:
    return AvaliacaoValores(**_normalizar_detalhe(av.get("valores") or {}))


def _semanas_desc(avals: list[dict]) -> list[str]:
    return sorted({a["semana_referencia"] for a in avals}, reverse=True)


def _consolidar_grupo(grupo: dict, avals_grupo: list[dict], semana: str) -> AvaliacaoValores | None:
    """Consolidado de um grupo numa semana. Grupo nivel='grupo': lançamento direto
    (loja_id None). Grupo nivel='loja': soma das lojas."""
    da_semana = [a for a in avals_grupo if a["semana_referencia"] == semana]
    if grupo["nivel_preenchimento"] == "grupo":
        diretos = [a for a in da_semana if a.get("loja_id") is None]
        if not diretos:
            return None
        return _valores_norm(diretos[0])
    lojas = [a for a in da_semana if a.get("loja_id") is not None]
    if not lojas:
        return None
    return consolidar_valores([_valores_norm(a) for a in lojas])


def build_series(avaliacoes: list[dict], grupos: list[dict], nivel: str, ref_id: str | None) -> list[dict]:
    """Série por nível: loja (crua), grupo (consolidado), rede (consolidado dos grupos)."""
    grupos_por_id = {g["id"]: g for g in grupos}

    if nivel == "loja":
        da_loja = [a for a in avaliacoes if a.get("loja_id") == ref_id]
        semanas = _semanas_desc(da_loja)
        out = []
        for s in semanas:
            regs = [a for a in da_loja if a["semana_referencia"] == s]
            valores = _valores_norm(regs[0])  # 1 registro por (loja, semana)
            out.append({"semana_referencia": s, "valores": valores.model_dump()})
        return out

    if nivel == "grupo":
        grupo = grupos_por_id.get(ref_id)
        if not grupo:
            return []
        da_grupo = [a for a in avaliacoes if a.get("grupo_id") == ref_id]
        out = []
        for s in _semanas_desc(da_grupo):
            cons = _consolidar_grupo(grupo, da_grupo, s)
            if cons is not None:
                out.append({"semana_referencia": s, "valores": cons.model_dump()})
        return out

    # nivel == "rede": soma dos consolidados de cada grupo, por semana
    out = []
    for s in _semanas_desc(avaliacoes):
        consolidados_grupo = []
        for gid, grupo in grupos_por_id.items():
            da_grupo = [a for a in avaliacoes if a.get("grupo_id") == gid]
            cons = _consolidar_grupo(grupo, da_grupo, s)
            if cons is not None:
                consolidados_grupo.append(cons)
        if consolidados_grupo:
            rede = consolidar_valores(consolidados_grupo)
            out.append({"semana_referencia": s, "valores": rede.model_dump()})
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_series_service.py -q`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/series_service.py tests/backend/test_series_service.py
git commit -m "feat(series): build_series por nível (loja/grupo/rede) + normalização de detalhe"
```

---

### Task 4: `series_service` — comparativo (snapshot + evolução)

**Files:**
- Modify: `backend/app/services/series_service.py`
- Test: `tests/backend/test_series_service.py`

**Interfaces:**
- Consumes: `_consolidar_grupo`, `_valores_norm`, `consolidar_valores`, `calcular_indicadores`.
- Produces:
  - `build_comparativo_snapshot(avaliacoes, grupos, lojas, nivel, ref_id, semana) -> dict`
    - Para `nivel="rede"`: unidades = grupos (consolidado de cada) + Total (rede).
    - Para `nivel="grupo"` (grupo nivel='loja'): unidades = lojas do grupo (cruas) + Total (grupo).
    - Retorna `{"semana": semana, "unidades": [{"id","nome","tipo","valores","indicadores"}], "total": {"valores","indicadores"}}`.
    - `nome` das unidades vem de `grupos`/`lojas` (dicts com `id`,`nome`).
  - `build_comparativo_evolucao(avaliacoes, grupos, lojas, nivel, ref_id) -> dict`
    - Retorna `{"unidades": [{"id","nome","serie":[{"semana","indicadores"}]}]}` — uma série por unidade filha.

- [ ] **Step 1: Write the failing tests**

Append to `tests/backend/test_series_service.py`:

```python
from backend.app.services.series_service import (
    build_comparativo_snapshot, build_comparativo_evolucao,
)


def _ind(indicadores, codigo):
    return next(i["valor"] for i in indicadores if i["codigo"] == codigo)


def test_comparativo_snapshot_rede_compara_grupos_e_total():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0, "contas_pagar": 50.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0, "contas_pagar": 50.0}, grupo_id="g2", loja_id=None),
    ]
    grupos = [
        {"id": "g1", "nivel_preenchimento": "loja", "nome": "Grupo 1"},
        {"id": "g2", "nivel_preenchimento": "grupo", "nome": "Grupo 2"},
    ]
    lojas = [{"id": "l1", "grupo_id": "g1", "nome": "Loja 1"}]
    snap = build_comparativo_snapshot(avals, grupos, lojas, nivel="rede", ref_id=None, semana="2026-07-06")
    nomes = {u["nome"] for u in snap["unidades"]}
    assert nomes == {"Grupo 1", "Grupo 2"}
    assert _ind(snap["total"]["indicadores"], "qt_total") == 300.0  # 100 + 200


def test_comparativo_snapshot_grupo_compara_lojas():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja", "nome": "Grupo 1"}]
    lojas = [{"id": "l1", "grupo_id": "g1", "nome": "Loja 1"},
             {"id": "l2", "grupo_id": "g1", "nome": "Loja 2"}]
    snap = build_comparativo_snapshot(avals, grupos, lojas, nivel="grupo", ref_id="g1", semana="2026-07-06")
    assert {u["nome"] for u in snap["unidades"]} == {"Loja 1", "Loja 2"}
    assert _ind(snap["total"]["indicadores"], "qt_total") == 300.0


def test_comparativo_evolucao_uma_serie_por_unidade():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-06-29", {"saldo_bancario": 90.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja", "nome": "Grupo 1"}]
    lojas = [{"id": "l1", "grupo_id": "g1", "nome": "Loja 1"},
             {"id": "l2", "grupo_id": "g1", "nome": "Loja 2"}]
    evo = build_comparativo_evolucao(avals, grupos, lojas, nivel="grupo", ref_id="g1")
    l1 = next(u for u in evo["unidades"] if u["nome"] == "Loja 1")
    assert [p["semana"] for p in l1["serie"]] == ["2026-07-06", "2026-06-29"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_series_service.py -q`
Expected: FAIL — funções de comparativo não existem.

- [ ] **Step 3: Implement the comparativo functions**

Append to `backend/app/services/series_service.py`:

```python
from backend.app.services.calculos_qtqd import calcular_indicadores


def _pacote(valores: AvaliacaoValores) -> dict:
    return {
        "valores": valores.model_dump(),
        "indicadores": [i.model_dump() for i in calcular_indicadores(valores)],
    }


def _unidades_filhas(grupos: list[dict], lojas: list[dict], nivel: str, ref_id: str | None):
    """Lista de (id, nome, tipo) das unidades comparáveis no nível pedido."""
    if nivel == "rede":
        return [(g["id"], g.get("nome", ""), "grupo") for g in grupos]
    # nivel == "grupo": compara as lojas daquele grupo
    return [(l["id"], l.get("nome", ""), "loja") for l in lojas if l.get("grupo_id") == ref_id]


def build_comparativo_snapshot(avaliacoes, grupos, lojas, nivel, ref_id, semana) -> dict:
    grupos_por_id = {g["id"]: g for g in grupos}
    unidades_out = []
    for uid, nome, tipo in _unidades_filhas(grupos, lojas, nivel, ref_id):
        if tipo == "grupo":
            da_grupo = [a for a in avaliacoes if a.get("grupo_id") == uid]
            cons = _consolidar_grupo(grupos_por_id[uid], da_grupo, semana)
        else:  # loja
            regs = [a for a in avaliacoes if a.get("loja_id") == uid and a["semana_referencia"] == semana]
            cons = _valores_norm(regs[0]) if regs else None
        if cons is not None:
            unidades_out.append({"id": uid, "nome": nome, "tipo": tipo, **_pacote(cons)})
    total_serie = build_series(avaliacoes, grupos, nivel, ref_id)
    total_v = next((s["valores"] for s in total_serie if s["semana_referencia"] == semana), None)
    total = _pacote(AvaliacaoValores(**total_v)) if total_v else _pacote(AvaliacaoValores())
    return {"semana": semana, "unidades": unidades_out, "total": total}


def build_comparativo_evolucao(avaliacoes, grupos, lojas, nivel, ref_id) -> dict:
    unidades_out = []
    for uid, nome, tipo in _unidades_filhas(grupos, lojas, nivel, ref_id):
        sub_nivel = "grupo" if tipo == "grupo" else "loja"
        serie = build_series(avaliacoes, grupos, sub_nivel, uid)
        pontos = [{"semana": s["semana_referencia"],
                   "indicadores": [i.model_dump() for i in calcular_indicadores(AvaliacaoValores(**s["valores"]))]}
                  for s in serie]
        unidades_out.append({"id": uid, "nome": nome, "serie": pontos})
    return {"unidades": unidades_out}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/backend/test_series_service.py -q`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/series_service.py tests/backend/test_series_service.py
git commit -m "feat(series): comparativo snapshot + evolução por unidade"
```

---

### Task 5: Validação de unidade + persistência em `avaliacoes.py`

**Files:**
- Modify: `backend/app/api/v1/avaliacoes.py`
- Test: `tests/backend/test_avaliacao_unidade_validacao.py`

**Interfaces:**
- Produces:
  - `_validar_unidade(modo_rede: bool, nivel_grupo: str | None, grupo_id, loja_id) -> None` — pura; levanta `ValueError` com mensagem clara quando a unidade é inválida para o modo.
  - `criar`/`atualizar` persistem `grupo_id`/`loja_id`; `_COLS` inclui as colunas; `_serialize` popula os campos.

Regras de `_validar_unidade`:
- `modo_rede=False` → `grupo_id` e `loja_id` devem ser None (senão ValueError).
- `modo_rede=True` + grupo `nivel='loja'` → `loja_id` obrigatório (e `grupo_id` presente).
- `modo_rede=True` + grupo `nivel='grupo'` → `grupo_id` obrigatório, `loja_id` deve ser None.

- [ ] **Step 1: Write the failing test**

Create `tests/backend/test_avaliacao_unidade_validacao.py`:

```python
import pytest
from backend.app.api.v1.avaliacoes import _validar_unidade


def test_sem_modo_rede_exige_unidade_nula():
    _validar_unidade(False, None, None, None)  # ok
    with pytest.raises(ValueError):
        _validar_unidade(False, None, "g1", None)
    with pytest.raises(ValueError):
        _validar_unidade(False, None, None, "l1")


def test_modo_rede_grupo_nivel_loja_exige_loja():
    _validar_unidade(True, "loja", "g1", "l1")  # ok
    with pytest.raises(ValueError):
        _validar_unidade(True, "loja", "g1", None)


def test_modo_rede_grupo_nivel_grupo_exige_grupo_sem_loja():
    _validar_unidade(True, "grupo", "g1", None)  # ok
    with pytest.raises(ValueError):
        _validar_unidade(True, "grupo", "g1", "l1")
    with pytest.raises(ValueError):
        _validar_unidade(True, "grupo", None, None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/backend/test_avaliacao_unidade_validacao.py -q`
Expected: FAIL — `_validar_unidade` não existe.

- [ ] **Step 3: Add `_validar_unidade` and wire persistence**

In `backend/app/api/v1/avaliacoes.py`:

(a) Update `_COLS`:
```python
_COLS = "id, tenant_id, grupo_id, loja_id, semana_referencia, status, observacoes, valores, created_at, updated_at"
```

(b) Add the pure validator near `_preserve_apply_only`:
```python
def _validar_unidade(modo_rede: bool, nivel_grupo: str | None, grupo_id, loja_id) -> None:
    """Valida a unidade (grupo/loja) conforme o modo do tenant. Levanta ValueError."""
    if not modo_rede:
        if grupo_id is not None or loja_id is not None:
            raise ValueError("Cliente sem modo_rede não aceita grupo_id/loja_id.")
        return
    if grupo_id is None:
        raise ValueError("modo_rede exige grupo_id.")
    if nivel_grupo == "loja" and loja_id is None:
        raise ValueError("Grupo com preenchimento por loja exige loja_id.")
    if nivel_grupo == "grupo" and loja_id is not None:
        raise ValueError("Grupo com preenchimento direto não aceita loja_id.")
```

(c) In `_serialize`, add `grupo_id=row.get("grupo_id")`, `loja_id=row.get("loja_id")` to the `AvaliacaoResponse(...)` call.

(d) In `criar`, after computing `valores`, look up modo_rede + grupo nivel and validate, then persist:
```python
    sb = get_supabase()
    tenant_row = sb.table("tenants").select("modo_rede").eq("id", str(tenant_id)).limit(1).execute()
    modo_rede = bool(tenant_row.data[0].get("modo_rede")) if tenant_row.data else False
    nivel_grupo = None
    if payload.grupo_id is not None:
        g = sb.table("grupos_economicos").select("nivel_preenchimento").eq("id", str(payload.grupo_id)).eq("tenant_id", str(tenant_id)).limit(1).execute()
        nivel_grupo = g.data[0]["nivel_preenchimento"] if g.data else None
    try:
        _validar_unidade(modo_rede, nivel_grupo, payload.grupo_id, payload.loja_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    data = {
        "tenant_id": str(tenant_id),
        "grupo_id": str(payload.grupo_id) if payload.grupo_id else None,
        "loja_id": str(payload.loja_id) if payload.loja_id else None,
        "semana_referencia": str(payload.semana_referencia),
        "status": payload.status,
        "observacoes": payload.observacoes,
        "valores": valores.model_dump(),
    }
    result = sb.table("avaliacoes_semanais").insert(data).execute()
```
(Replace the existing `get_supabase().table(...).insert(data)` block accordingly; keep the `_serialize(result.data[0])` return.)

(e) In `atualizar`, allow updating `grupo_id`/`loja_id` when provided (fallback to existing row values), add them to `update_data`:
```python
        "grupo_id": str(payload.grupo_id) if payload.grupo_id is not None else row.get("grupo_id"),
        "loja_id": str(payload.loja_id) if payload.loja_id is not None else row.get("loja_id"),
```

- [ ] **Step 4: Run tests + full suite**

Run: `python3 -m pytest tests/backend/test_avaliacao_unidade_validacao.py -q`
Expected: PASS.
Run: `python3 -m pytest tests/backend/ -q`
Expected: all PASS (existing tests intact).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/avaliacoes.py tests/backend/test_avaliacao_unidade_validacao.py
git commit -m "feat(avaliacoes): validação e persistência de grupo_id/loja_id"
```

---

### Task 6: Endpoints de estrutura (admin CRUD + `/me/lojas`)

**Files:**
- Create: `backend/app/api/v1/estrutura.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Consumes: `estrutura` schemas (Task 2); `require_admin_token` (`backend/app/core/admin_auth.py`); `get_current_tenant`.
- Produces: router `estrutura_router` com:
  - Admin (prefix `/admin/tenants/{tenant_id}`, dep `require_admin_token`): `GET/POST /grupos`, `PATCH/DELETE /grupos/{gid}`, `GET/POST /lojas`, `PATCH/DELETE /lojas/{lid}`, `PATCH /modo-rede` (body `{ativo: bool}`).
  - Cliente (prefix `/me`, dep `get_current_tenant`): `GET /lojas` → `LojasArvoreResponse`.

This task is DB-wiring; no unit test (repo has no endpoint tests). Deliverable reviewed against the patterns in `cliente_config.py`/`admin_clientes.py`.

- [ ] **Step 1: Create `estrutura.py`**

Create `backend/app/api/v1/estrutura.py`:

```python
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.app.core.admin_auth import require_admin_token
from backend.app.core.auth import get_current_tenant
from backend.app.db.client import get_supabase
from backend.app.schemas.estrutura import (
    GrupoCreate, GrupoUpdate, GrupoResponse,
    LojaCreate, LojaUpdate, LojaResponse,
    GrupoComLojas, LojasArvoreResponse,
)

router = APIRouter(tags=["estrutura"])

# ---- Cliente: árvore para o seletor ----

@router.get("/me/lojas", response_model=LojasArvoreResponse)
def me_lojas(tenant_id: UUID = Depends(get_current_tenant)) -> LojasArvoreResponse:
    sb = get_supabase()
    t = sb.table("tenants").select("modo_rede").eq("id", str(tenant_id)).limit(1).execute()
    modo_rede = bool(t.data[0].get("modo_rede")) if t.data else False
    grupos = sb.table("grupos_economicos").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    lojas = sb.table("lojas").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    lojas_por_grupo: dict = {}
    for l in lojas:
        lojas_por_grupo.setdefault(l["grupo_id"], []).append(LojaResponse(**l))
    grupos_out = [GrupoComLojas(**g, lojas=lojas_por_grupo.get(g["id"], [])) for g in grupos]
    return LojasArvoreResponse(modo_rede=modo_rede, grupos=grupos_out)


# ---- Admin: CRUD estrutura ----
admin = APIRouter(prefix="/admin/tenants/{tenant_id}", dependencies=[Depends(require_admin_token)])


@admin.get("/grupos", response_model=list[GrupoResponse])
def listar_grupos(tenant_id: UUID) -> list[GrupoResponse]:
    rows = get_supabase().table("grupos_economicos").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    return [GrupoResponse(**r) for r in rows]


@admin.post("/grupos", response_model=GrupoResponse, status_code=201)
def criar_grupo(tenant_id: UUID, payload: GrupoCreate) -> GrupoResponse:
    data = {"tenant_id": str(tenant_id), "nome": payload.nome,
            "nivel_preenchimento": payload.nivel_preenchimento, "ordem": payload.ordem, "ativo": True}
    res = get_supabase().table("grupos_economicos").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Falha ao criar grupo.")
    return GrupoResponse(**res.data[0])


@admin.patch("/grupos/{gid}", response_model=GrupoResponse)
def atualizar_grupo(tenant_id: UUID, gid: UUID, payload: GrupoUpdate) -> GrupoResponse:
    upd = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not upd:
        raise HTTPException(status_code=400, detail="Nada para atualizar.")
    res = get_supabase().table("grupos_economicos").update(upd).eq("id", str(gid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")
    return GrupoResponse(**res.data[0])


@admin.delete("/grupos/{gid}", status_code=204)
def excluir_grupo(tenant_id: UUID, gid: UUID) -> None:
    res = get_supabase().table("grupos_economicos").delete().eq("id", str(gid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Grupo não encontrado.")


@admin.get("/lojas", response_model=list[LojaResponse])
def listar_lojas(tenant_id: UUID) -> list[LojaResponse]:
    rows = get_supabase().table("lojas").select("*").eq("tenant_id", str(tenant_id)).order("ordem").execute().data
    return [LojaResponse(**r) for r in rows]


@admin.post("/lojas", response_model=LojaResponse, status_code=201)
def criar_loja(tenant_id: UUID, payload: LojaCreate) -> LojaResponse:
    data = {"tenant_id": str(tenant_id), "grupo_id": str(payload.grupo_id), "nome": payload.nome,
            "cnpj": payload.cnpj, "filial_excel": payload.filial_excel, "ordem": payload.ordem, "ativo": True}
    res = get_supabase().table("lojas").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Falha ao criar loja.")
    return LojaResponse(**res.data[0])


@admin.patch("/lojas/{lid}", response_model=LojaResponse)
def atualizar_loja(tenant_id: UUID, lid: UUID, payload: LojaUpdate) -> LojaResponse:
    upd = {k: (str(v) if k == "grupo_id" else v) for k, v in payload.model_dump().items() if v is not None}
    if not upd:
        raise HTTPException(status_code=400, detail="Nada para atualizar.")
    res = get_supabase().table("lojas").update(upd).eq("id", str(lid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")
    return LojaResponse(**res.data[0])


@admin.delete("/lojas/{lid}", status_code=204)
def excluir_loja(tenant_id: UUID, lid: UUID) -> None:
    res = get_supabase().table("lojas").delete().eq("id", str(lid)).eq("tenant_id", str(tenant_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")


@admin.patch("/modo-rede")
def toggle_modo_rede(tenant_id: UUID, ativo: bool = Body(embed=True)) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    get_supabase().table("tenants").update({"modo_rede": ativo, "updated_at": now}).eq("id", str(tenant_id)).execute()
    return {"modo_rede": ativo}


router.include_router(admin)
```

- [ ] **Step 2: Register the router**

In `backend/app/api/router.py`, import and include (near the other includes):
```python
from backend.app.api.v1.estrutura import router as estrutura_router
...
api_router.include_router(estrutura_router)
```

- [ ] **Step 3: Import-smoke test**

Run: `python3 -c "from backend.app.api.router import api_router; print('ok')"`
Expected: prints `ok` (no import errors).

- [ ] **Step 4: Full suite (no regression)**

Run: `python3 -m pytest tests/backend/ -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/estrutura.py backend/app/api/router.py
git commit -m "feat(estrutura): endpoints admin CRUD grupos/lojas + toggle modo_rede + GET /me/lojas"
```

---

### Task 7: Endpoints de série por nível + comparativo

**Files:**
- Modify: `backend/app/api/v1/avaliacoes.py` (série por nível no `GET /avaliacoes`)
- Create: `backend/app/api/v1/comparativo.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Consumes: `series_service.build_series`, `build_comparativo_snapshot`, `build_comparativo_evolucao`; `calcular_indicadores`.
- Produces:
  - `GET /avaliacoes?nivel=loja&loja_id=…` | `nivel=grupo&grupo_id=…` | `nivel=rede` → `list[AvaliacaoResponse]` (série do nível; sem params = comportamento atual).
  - `GET /me/comparativo?nivel=…&grupo_id=…&modo=snapshot&semana=…` e `?modo=evolucao` → dicts do `series_service`.

- [ ] **Step 1: Série por nível no `GET /avaliacoes`**

Replace the `listar` function in `backend/app/api/v1/avaliacoes.py` with a version that accepts optional level params. When no `nivel` is given, behavior is identical to today. When given, fetch the tenant's avaliacoes + grupos and delegate to `build_series`, wrapping each `{semana, valores}` into an `AvaliacaoResponse` (synthetic id from a fixed namespace is unnecessary — reuse the semana as a surrogate and set indicadores from valores):

```python
from backend.app.services.series_service import build_series

@router.get("", response_model=list[AvaliacaoResponse])
def listar(
    tenant_id: UUID = Depends(get_current_tenant),
    nivel: str | None = None,
    loja_id: UUID | None = None,
    grupo_id: UUID | None = None,
) -> list[AvaliacaoResponse]:
    sb = get_supabase()
    if not nivel:
        result = (
            sb.table("avaliacoes_semanais").select(_COLS)
            .eq("tenant_id", str(tenant_id))
            .order("semana_referencia", desc=True).execute()
        )
        return [_serialize(row) for row in result.data]
    # série consolidada por nível
    avals = (
        sb.table("avaliacoes_semanais").select(_COLS)
        .eq("tenant_id", str(tenant_id)).execute().data
    )
    grupos = sb.table("grupos_economicos").select("id,nivel_preenchimento").eq("tenant_id", str(tenant_id)).execute().data
    ref = str(loja_id) if nivel == "loja" else (str(grupo_id) if nivel == "grupo" else None)
    serie = build_series(avals, grupos, nivel, ref)
    out = []
    for s in serie:
        v = AvaliacaoValores(**s["valores"])
        out.append(AvaliacaoResponse(
            id=UUID(int=0), tenant_id=tenant_id, grupo_id=grupo_id, loja_id=loja_id,
            semana_referencia=s["semana_referencia"], status="fechada", observacoes=None,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            valores=v, indicadores=calcular_indicadores(v),
        ))
    return out
```

(Note: consolidated series are synthetic/read-only — `id=UUID(int=0)`, status "fechada" is a display placeholder. Frontend uses these only for analytics, never to edit.)

- [ ] **Step 2: Create `comparativo.py`**

Create `backend/app/api/v1/comparativo.py`:

```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.auth import get_current_tenant
from backend.app.db.client import get_supabase
from backend.app.services.series_service import (
    build_comparativo_snapshot, build_comparativo_evolucao,
)

router = APIRouter(prefix="/me", tags=["comparativo"])


def _carregar(tenant_id: UUID):
    sb = get_supabase()
    avals = sb.table("avaliacoes_semanais").select(
        "semana_referencia, grupo_id, loja_id, valores"
    ).eq("tenant_id", str(tenant_id)).execute().data
    grupos = sb.table("grupos_economicos").select("id,nome,nivel_preenchimento").eq("tenant_id", str(tenant_id)).execute().data
    lojas = sb.table("lojas").select("id,grupo_id,nome").eq("tenant_id", str(tenant_id)).execute().data
    return avals, grupos, lojas


@router.get("/comparativo")
def comparativo(
    tenant_id: UUID = Depends(get_current_tenant),
    nivel: str = "rede",
    grupo_id: UUID | None = None,
    modo: str = "snapshot",
    semana: str | None = None,
) -> dict:
    avals, grupos, lojas = _carregar(tenant_id)
    ref = str(grupo_id) if grupo_id else None
    if modo == "evolucao":
        return build_comparativo_evolucao(avals, grupos, lojas, nivel, ref)
    if not semana:
        semanas = sorted({a["semana_referencia"] for a in avals}, reverse=True)
        if not semanas:
            return {"semana": None, "unidades": [], "total": None}
        semana = semanas[0]
    return build_comparativo_snapshot(avals, grupos, lojas, nivel, ref, semana)
```

- [ ] **Step 3: Register the comparativo router**

In `backend/app/api/router.py`:
```python
from backend.app.api.v1.comparativo import router as comparativo_router
...
api_router.include_router(comparativo_router)
```

- [ ] **Step 4: Import-smoke + full suite**

Run: `python3 -c "from backend.app.api.router import api_router; print('ok')"`
Expected: `ok`.
Run: `python3 -m pytest tests/backend/ -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/avaliacoes.py backend/app/api/v1/comparativo.py backend/app/api/router.py
git commit -m "feat(api): série por nível em GET /avaliacoes + GET /me/comparativo"
```

---

## Self-Review (Plano 2)

- **Cobertura do spec:** DDL com índice único parcial anti-regressão (Task 1) ✓; schemas estrutura (Task 2) ✓; série loja/grupo/rede + normalização de detalhe heterogêneo (Task 3) ✓; comparativo snapshot+evolução (Task 4) ✓; validação/persistência de unidade (Task 5) ✓; admin CRUD + `/me/lojas` (Task 6) ✓; endpoints série+comparativo (Task 7) ✓.
- **Não-regressão:** `GET /avaliacoes` sem `nivel` inalterado; `_validar_unidade(False,...)` exige unidade nula; colunas novas default NULL. Full suite roda em Tasks 5-7.
- **Sem placeholders:** todo passo com código/comando/expected. Tasks 1, 6, 7 (DB-wiring) sem teste unitário por não haver testes de endpoint no repo — deliverable revisado + smoke import; verificação E2E é handoff do usuário (documentado nas Global Constraints).
- **Consistência de tipos:** `build_series(avaliacoes, grupos, nivel, ref_id) -> list[dict]`; comparativo retorna dicts com `indicadores` já `model_dump()`; `_validar_unidade(bool, str|None, grupo_id, loja_id)`; schemas de estrutura idênticos entre Tasks 2/6. `_ind` no teste lê `i["valor"]`/`i["codigo"]` (dicts) — coerente com `_pacote` que faz `model_dump()`.
- **Handoffs humanos:** rodar `tools/sql/2026-07-08-multi-loja.sql` no Supabase; E2E dos endpoints. Sinalizados.

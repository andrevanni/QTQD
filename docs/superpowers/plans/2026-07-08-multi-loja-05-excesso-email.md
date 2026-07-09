# Multi-loja — Plano 5: Excesso Crítico por loja + E-mail por nível

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Fechar as pendências do multi-loja: (A) o assistente de Excesso Crítico filtra o Excel pela filial da loja ativa e aplica na avaliação dessa loja; (B) o e-mail de relatório é enviado no nível configurável por tenant (loja/grupo/rede, padrão loja).

**Architecture:** (A) `calcularExcessoDeRows` (função pura já existente) ganha um parâmetro `filial`; `multiloja.js` expõe `activeFilial()`; `excesso_critico.js` passa a filial ativa. (B) `tenant_pdf_config` ganha `nivel_relatorio`; `relatorio_service` monta os `periodos` via `series_service.build_series` no nível configurado quando `modo_rede`; admin ganha um select.

**Tech Stack:** Python (pytest) + JS puro (`node --check`).

## Global Constraints

- **Idioma:** português brasileiro.
- **Verificação:** backend com `python3 -m pytest tests/backend/ -q`; cada `.js` com `node --check`. Sem browser/e-mail real aqui → E2E é handoff do usuário.
- **Não-regressão (duro):** `modo_rede` off → comportamento atual idêntico. Excesso sem filial ativa = sem filtro (como hoje). E-mail sem `modo_rede` (ou `nivel_relatorio` ausente) = série do tenant (como hoje).
- **Ponto 3 (semáforo de ciclo):** JÁ resolvido pela lógica existente (`renderInspector`: ciclo `null` → azul; PMP/PMV/PME 0 → neutral; riscos só com `ciclo!=null`). Nenhuma tarefa — só confirmar no E2E.
- **Regra de ouro:** sem template literals aninhados nas edições de `.js`.
- **Depende de:** Planos 1-4 (branch `feature/multi-loja`) e do DDL do Plano 2 aplicado.
- **Spec:** `docs/superpowers/specs/2026-07-08-multi-loja-grupo-economico-design.md`.

---

## File Structure (Plano 5)

- **Modify:** `frontend_cliente/multiloja.js` — `activeFilial()`, `isRede()`.
- **Modify:** `frontend_cliente/excesso_critico.js` — filtro por filial em `calcularExcessoDeRows` + passar filial ativa.
- **Create:** `tools/sql/2026-07-08-nivel-relatorio.sql` — coluna `nivel_relatorio`.
- **Modify:** `backend/app/services/relatorio_service.py` — série por nível.
- **Modify:** `backend/app/schemas/` (schema do PdfConfig) — campo `nivel_relatorio`.
- **Modify:** `frontend_admin/index.html` + `frontend_admin/script.js` — select de nível na seção Relatório.
- **Create test:** `tests/backend/test_relatorio_nivel.py`.

---

### Task 1: `multiloja.js` expõe `activeFilial()` e `isRede()`

**Files:**
- Modify: `frontend_cliente/multiloja.js`

**Interfaces:**
- Produces: `window.QTQD_MULTILOJA.activeFilial()` → número da filial (Excel) da loja ativa, ou `null`; `window.QTQD_MULTILOJA.isRede()` → `true` quando `modo_rede` ativo.

- [ ] **Step 1: Add the methods**

No objeto `window.QTQD_MULTILOJA = { ... }` em `multiloja.js`, adicionar (sem template literals aninhados):

```javascript
    isRede: function () { return !!(arvore && arvore.modo_rede); },
    activeFilial: function () {
      if (!current || !current.loja_id || !arvore) return null;
      let fil = null;
      arvore.grupos.forEach(function (g) {
        (g.lojas || []).forEach(function (l) {
          if (String(l.id) === String(current.loja_id)) { fil = l.filial_excel; }
        });
      });
      return (fil === undefined || fil === null) ? null : fil;
    },
```

- [ ] **Step 2: Syntax check**

Run: `node --check frontend_cliente/multiloja.js`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add frontend_cliente/multiloja.js
git commit -m "feat(portal): multiloja expõe activeFilial/isRede para o Excesso por loja"
```

---

### Task 2: Filtro por filial no Excesso Crítico

**Files:**
- Modify: `frontend_cliente/excesso_critico.js`

**Interfaces:**
- Consumes: `window.QTQD_MULTILOJA.activeFilial()` (Task 1).
- Produces: `calcularExcessoDeRows(rows, limites, filial)` — quando `filial` não é null e existe coluna `Filial`, considera SÓ as linhas dessa filial (excesso e lançamentos).

- [ ] **Step 1: Add the `filial` param and filter**

Em `frontend_cliente/excesso_critico.js`, na função `calcularExcessoDeRows(rows, limites)`:
1. Trocar a assinatura para `calcularExcessoDeRows(rows, limites, filial)`.
2. Após a linha `const iLanc = findColIndex(...)`, adicionar a busca da coluna Filial:
```javascript
    const iFilial = findColIndex(header, ['Filial']);
```
3. No topo do laço `for (let r = 1; r < rows.length; r++) { ... }`, logo após obter `row` e antes do teste de linha vazia (ou logo após ele), adicionar o filtro de filial:
```javascript
      if (filial != null && iFilial >= 0 && Number(row[iFilial]) !== Number(filial)) continue;
```
(Assim, quando uma loja está ativa, só as linhas da filial dela contam — no excesso E no total de lançamentos.)

- [ ] **Step 2: Pass the active filial at the call site**

Localizar onde `calcularExcessoDeRows(...)` é chamado (grep: `grep -n "calcularExcessoDeRows(" frontend_cliente/excesso_critico.js`). Na chamada do handler de upload, passar a filial ativa como 3º argumento:
```javascript
      const filialAtiva = (window.QTQD_MULTILOJA && window.QTQD_MULTILOJA.activeFilial) ? window.QTQD_MULTILOJA.activeFilial() : null;
      const resultado = calcularExcessoDeRows(rows, limites, filialAtiva);
```
(Mantenha o nome da variável de resultado igual ao que o código já usa; só acrescente o 3º argumento e a linha `filialAtiva`.)

- [ ] **Step 3: (opcional) aviso quando em nível consolidado**

Se `window.QTQD_MULTILOJA && window.QTQD_MULTILOJA.isRede && window.QTQD_MULTILOJA.isRede() && filialAtiva == null`, exibir uma mensagem no lugar do resultado avisando "Selecione uma loja no seletor do topo para aplicar o excesso por unidade." (usar o mesmo elemento de feedback/resultado que o módulo já usa). Não bloquear o cálculo geral se preferir — mas avisar evita aplicar o total da rede numa avaliação consolidada (id sintético).

- [ ] **Step 4: Syntax check**

Run: `node --check frontend_cliente/excesso_critico.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend_cliente/excesso_critico.js
git commit -m "feat(excesso): filtrar Excel pela filial da loja ativa (Excesso por loja)"
```

---

### Task 3: DDL — `nivel_relatorio` no tenant_pdf_config

**Files:**
- Create: `tools/sql/2026-07-08-nivel-relatorio.sql`

- [ ] **Step 1: Criar o SQL**

Create `tools/sql/2026-07-08-nivel-relatorio.sql`:
```sql
-- Nível do relatório por e-mail (multi-loja). Rodar no Supabase SQL Editor.
ALTER TABLE tenant_pdf_config ADD COLUMN IF NOT EXISTS nivel_relatorio text DEFAULT 'loja';
-- valores esperados: 'loja' | 'grupo' | 'rede'
```

- [ ] **Step 2: Commit**

```bash
git add tools/sql/2026-07-08-nivel-relatorio.sql
git commit -m "feat(sql): coluna nivel_relatorio no tenant_pdf_config"
```

- [ ] **Step 3: HANDOFF** — o controlador avisa o usuário para rodar este SQL no Supabase.

---

### Task 4: `relatorio_service` monta período pelo nível configurado

**Files:**
- Modify: `backend/app/services/relatorio_service.py`
- Modify: schema do PdfConfig (localizar; provavelmente `backend/app/schemas/admin_config.py` — `PdfConfigRequest`)
- Test: `tests/backend/test_relatorio_nivel.py`

**Interfaces:**
- Consumes: `series_service.build_series` (Plano 2).
- Produces: helper puro `montar_avals_por_nivel(all_avals, grupos, modo_rede, nivel, ref) -> list[dict]` (retorna `[{semana_referencia, valores}]` ordenado desc) usado por `enviar_relatorio_para_tenant`. Schema `PdfConfigRequest` ganha `nivel_relatorio: str = "loja"`.

- [ ] **Step 1: Write the failing test (helper puro)**

Create `tests/backend/test_relatorio_nivel.py`:
```python
from backend.app.services.relatorio_service import montar_avals_por_nivel


def _av(semana, valores, grupo_id=None, loja_id=None):
    return {"semana_referencia": semana, "grupo_id": grupo_id, "loja_id": loja_id, "valores": valores}


def test_sem_modo_rede_usa_todas_as_avals():
    avals = [_av("2026-07-06", {"saldo_bancario": 100.0}), _av("2026-06-29", {"saldo_bancario": 90.0})]
    out = montar_avals_por_nivel(avals, [], modo_rede=False, nivel="loja", ref=None)
    assert len(out) == 2
    assert out[0]["semana_referencia"] == "2026-07-06"  # desc


def test_modo_rede_nivel_loja_filtra_a_loja():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 999.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    out = montar_avals_por_nivel(avals, grupos, modo_rede=True, nivel="loja", ref="l1")
    assert len(out) == 1
    assert out[0]["valores"]["saldo_bancario"] == 100.0


def test_modo_rede_nivel_rede_soma():
    avals = [
        _av("2026-07-06", {"saldo_bancario": 100.0}, grupo_id="g1", loja_id="l1"),
        _av("2026-07-06", {"saldo_bancario": 200.0}, grupo_id="g1", loja_id="l2"),
    ]
    grupos = [{"id": "g1", "nivel_preenchimento": "loja"}]
    out = montar_avals_por_nivel(avals, grupos, modo_rede=True, nivel="rede", ref=None)
    assert out[0]["valores"]["saldo_bancario"] == 300.0
```

- [ ] **Step 2: Run — fails**

Run: `python3 -m pytest tests/backend/test_relatorio_nivel.py -q`
Expected: FAIL (função não existe).

- [ ] **Step 3: Implement the helper + wire it**

Em `backend/app/services/relatorio_service.py`, adicionar o helper puro (topo do arquivo, após imports):
```python
def montar_avals_por_nivel(all_avals: list[dict], grupos: list[dict], modo_rede: bool, nivel: str, ref: str | None) -> list[dict]:
    """Devolve [{semana_referencia, valores}] no nível pedido, ordenado desc.
    Sem modo_rede: usa as avals como estão (comportamento atual)."""
    if not modo_rede or nivel not in ("loja", "grupo", "rede"):
        return sorted(all_avals, key=lambda x: x["semana_referencia"], reverse=True)
    from backend.app.services.series_service import build_series
    serie = build_series(all_avals, grupos, nivel, ref)  # já desc
    return serie
```

Em `enviar_relatorio_para_tenant`, substituir o bloco que busca `avals` e monta `periodos`:
- Ler `modo_rede` do tenant e `nivel_relatorio` do cfg (default "loja").
- Buscar TODAS as avals publicadas do tenant com `grupo_id,loja_id` (não `.limit(n_retratos)` ainda, pois a consolidação precisa de todas as lojas): `select("semana_referencia,grupo_id,loja_id,valores")`, `.neq("status","rascunho")`.
- Buscar `grupos` do tenant.
- Determinar `ref`: se `avaliacao_id` informado, buscar seu `grupo_id`/`loja_id`; `nivel=loja`→`ref=loja_id`; `nivel=grupo`→`ref=grupo_id`; `nivel=rede`→`ref=None`.
- `serie = montar_avals_por_nivel(all_avals, grupos, modo_rede, nivel_relatorio, ref)[:n_retratos]`.
- Montar `periodos` a partir de `serie` (mesma lógica: `AvaliacaoValores(**v["valores"])` → `calcular_indicadores`).

Código concreto para o trecho (substitui as linhas que hoje fazem o `select(...).limit(n_retratos)` e o loop de `periodos`):
```python
    modo_rede_res = sb.table("tenants").select("modo_rede").eq("id", tenant_id).limit(1).execute()
    modo_rede = bool(modo_rede_res.data[0].get("modo_rede")) if modo_rede_res.data else False
    nivel_relatorio = cfg.get("nivel_relatorio") or "loja"

    all_avals = (
        sb.table("avaliacoes_semanais")
        .select("semana_referencia,grupo_id,loja_id,valores")
        .eq("tenant_id", tenant_id)
        .neq("status", "rascunho")
        .execute()
        .data
    ) or []
    if not all_avals:
        return []
    grupos = sb.table("grupos_economicos").select("id,nivel_preenchimento").eq("tenant_id", tenant_id).execute().data or []

    ref = None
    if modo_rede and avaliacao_id:
        av_ref = sb.table("avaliacoes_semanais").select("grupo_id,loja_id").eq("id", avaliacao_id).limit(1).execute()
        if av_ref.data:
            if nivel_relatorio == "loja":
                ref = av_ref.data[0].get("loja_id")
            elif nivel_relatorio == "grupo":
                ref = av_ref.data[0].get("grupo_id")

    serie = montar_avals_por_nivel(all_avals, grupos, modo_rede, nivel_relatorio, ref)[:n_retratos]

    avals_sorted = sorted(serie, key=lambda x: x["semana_referencia"])
    periodos = []
    for av in avals_sorted:
        try:
            d = date.fromisoformat(av["semana_referencia"])
            data_fmt = d.strftime("%d/%m/%Y")
        except Exception:
            data_fmt = av["semana_referencia"]
        raw_valores = av.get("valores") or {}
        valores = AvaliacaoValores(**raw_valores)
        periodos.append({"data": data_fmt, "indicadores": calcular_indicadores(valores), "valores": raw_valores})
```
(Remover o bloco antigo `avals = sb.table(...).select("semana_referencia,valores")...limit(n_retratos)...` e o `if not avals: return []` e o loop antigo — substituídos pelo acima. Manter todo o resto da função — branding, destinatários, envio, log — inalterado.)

- [ ] **Step 4: Add `nivel_relatorio` to the PdfConfig schema**

Localizar o schema (`grep -rn "class PdfConfigRequest" backend/app/schemas/`). Adicionar:
```python
    nivel_relatorio: str = "loja"
```
E no endpoint que grava o pdf-config (admin), garantir que `nivel_relatorio` é persistido (seguir o padrão dos outros campos do upsert).

- [ ] **Step 5: Run tests + full suite**

Run: `python3 -m pytest tests/backend/test_relatorio_nivel.py -q` → PASS.
Run: `python3 -m pytest tests/backend/ -q` → all PASS.
Run: `python3 -c "from backend.app.api.router import api_router; print('ok')"` → ok.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/relatorio_service.py backend/app/schemas/ tests/backend/test_relatorio_nivel.py
git commit -m "feat(relatorio): montar período pelo nível configurado (loja/grupo/rede)"
```

---

### Task 5: Admin — select de nível na seção Relatório

**Files:**
- Modify: `frontend_admin/index.html`
- Modify: `frontend_admin/script.js`

**Interfaces:**
- Produces: `<select id="pdfNivelRelatorio">` com opções loja/grupo/rede; carregado/salvo junto com o resto do pdf-config.

- [ ] **Step 1: Add the select in the HTML**

Na seção Relatório (`id="enviopdf"`) do `frontend_admin/index.html`, adicionar (replicando as classes reais dos campos vizinhos):
```html
          <label class="field-label" for="pdfNivelRelatorio">Nível do relatório (multi-loja)</label>
          <select id="pdfNivelRelatorio">
            <option value="loja">Loja</option>
            <option value="grupo">Grupo econômico</option>
            <option value="rede">Rede (consolidado)</option>
          </select>
```
(Inspecione a seção `enviopdf` e use as MESMAS classes que os outros campos usam — não invente CSS, lição do Plano 3.)

- [ ] **Step 2: Load/save the value**

Em `frontend_admin/script.js`, na função que CARREGA o pdf-config (grep `loadPdfSection` ou similar), popular `$('pdfNivelRelatorio').value = cfg.nivel_relatorio || 'loja'`. Na função que SALVA (o handler do botão salvar), incluir `nivel_relatorio: $('pdfNivelRelatorio').value` no payload enviado ao `putPdfConfig`/`savePdfConfig`. Ao trocar de cliente (reset), voltar para `'loja'`.

- [ ] **Step 3: Syntax check**

Run: `node --check frontend_admin/script.js`
Expected: exit 0.

- [ ] **Step 4: Commit**

```bash
git add frontend_admin/index.html frontend_admin/script.js
git commit -m "feat(admin): select de nível do relatório na seção Relatório"
```

---

## Self-Review (Plano 5)

- **Cobertura:** Excesso por loja (filtro por filial: Task 1 activeFilial + Task 2 filtro) ✓; e-mail por nível (Task 3 DDL + Task 4 série por nível + Task 5 UI) ✓; ciclo (ponto 3) já resolvido — sem tarefa ✓.
- **Não-regressão:** `modo_rede` off → `montar_avals_por_nivel` retorna todas as avals (comportamento atual); Excesso sem filial → sem filtro. Teste `test_sem_modo_rede_usa_todas_as_avals` trava isso. Full suite roda na Task 4.
- **Testável:** `montar_avals_por_nivel` e o filtro por filial (via `calcularExcessoDeRows` puro) são unitariamente verificáveis; `node --check` nos `.js`.
- **Handoffs:** rodar `tools/sql/2026-07-08-nivel-relatorio.sql`; E2E (excesso aplica na loja certa; e-mail sai no nível configurado; semáforo de ciclo sem vermelho quando oculto).

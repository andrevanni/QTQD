# Multi-loja — Plano 4: UI Portal (núcleo — seletor, série, lançamento por unidade, Comparativo)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Tornar o multi-loja visível no portal do cliente: seletor de nível (loja/grupo/rede), troca da série exibida, lançamento gravando na unidade certa, e uma seção Comparativo (snapshot + evolução em tabela). Isolado num módulo `multiloja.js` para proteger o `script.js` sensível.

**Architecture:** Segue o padrão dos módulos isolados (`chart_builder.js`, `excesso_critico.js`): novo `frontend_cliente/multiloja.js` (`window.QTQD_MULTILOJA`), incluído após `script.js`. Edições no `script.js` são MÍNIMAS e cirúrgicas: (a) expor um hook `window.QTQD_PORTAL`; (b) fundir a unidade ativa no payload de criação; (c) chamar `QTQD_MULTILOJA.init()`. O módulo injeta o seletor no topbar e renderiza o Comparativo por conta própria.

**Tech Stack:** HTML + JS puro. Verificação: `node --check` (sem browser E2E neste ambiente).

## Global Constraints

- **Idioma:** português brasileiro.
- **Verificação obrigatória:** após CADA edição em `.js`, `node --check <arquivo>` sem erro. Sem browser aqui — E2E visual é handoff do usuário.
- **REGRA DE OURO — `script.js`:** sem template literals aninhados; edições mínimas; qualquer erro de sintaxe derruba o portal inteiro silenciosamente (lições #16/#36/#51 do CLAUDE.md). As mudanças no `script.js` estão restritas a 3 pontos cirúrgicos (Task 2).
- **Isolamento:** toda a lógica nova vive em `multiloja.js`. Se `modo_rede` estiver off (todos os clientes atuais), `multiloja.js` **retorna cedo** e o portal se comporta EXATAMENTE como hoje.
- **SW:** bump `qtqd-v13 → qtqd-v14` (mudança de assets exige invalidar cache).
- **Endpoints (Plano 2):** `GET /me/lojas`, `GET /avaliacoes?nivel=…&loja_id=…|grupo_id=…`, `GET /me/comparativo?...`. api_client usa `authHeaders()` (tenant vem do localStorage).
- **Fora deste plano (→ Plano 5):** Excesso Crítico por loja, e-mail de relatório por nível, e o ajuste fino do semáforo de ciclo. Documentado no fim.
- **Spec:** `docs/superpowers/specs/2026-07-08-multi-loja-grupo-economico-design.md`.

---

## File Structure (Plano 4)

- **Modify:** `shared/api_client.js` — `getMeLojas`, `listAvaliacoesNivel`, `getComparativo`.
- **Modify:** `frontend_cliente/script.js` — 3 hooks cirúrgicos (QTQD_PORTAL, unidade no create, init do módulo).
- **Create:** `frontend_cliente/multiloja.js` — módulo isolado (seletor + troca de série + Comparativo).
- **Modify:** `frontend_cliente/index.html` — nav-link + seção Comparativo + `<script src="multiloja.js">`.
- **Modify:** `frontend_cliente/sw.js` — `qtqd-v13 → qtqd-v14`.

---

### Task 1: Métodos cliente no api_client

**Files:**
- Modify: `shared/api_client.js`

**Interfaces:**
- Produces (em `window.QTQD_API_CLIENT`): `getMeLojas()`, `listAvaliacoesNivel(nivel, refId)`, `getComparativo(params)`.

- [ ] **Step 1: Add the methods**

Inside `window.QTQD_API_CLIENT = { ... }`, near the other client (`authHeaders()`) methods, add:

```javascript
    /* ── Multi-loja (exige JWT) ──────────────────────── */
    getMeLojas() {
      return request(base('/me/lojas'), { method: 'GET', headers: authHeaders() });
    },
    listAvaliacoesNivel(nivel, refId) {
      let qs = '?nivel=' + encodeURIComponent(nivel);
      if (nivel === 'loja' && refId) qs += '&loja_id=' + encodeURIComponent(refId);
      if (nivel === 'grupo' && refId) qs += '&grupo_id=' + encodeURIComponent(refId);
      return request(base('/avaliacoes' + qs), { method: 'GET', headers: authHeaders() });
    },
    getComparativo(params) {
      const p = params || {};
      let qs = '?nivel=' + encodeURIComponent(p.nivel || 'rede') + '&modo=' + encodeURIComponent(p.modo || 'snapshot');
      if (p.grupo_id) qs += '&grupo_id=' + encodeURIComponent(p.grupo_id);
      if (p.semana) qs += '&semana=' + encodeURIComponent(p.semana);
      return request(base('/me/comparativo' + qs), { method: 'GET', headers: authHeaders() });
    },
```

- [ ] **Step 2: Syntax check**

Run: `node --check shared/api_client.js`
Expected: exit 0, no output.

- [ ] **Step 3: Commit**

```bash
git add shared/api_client.js
git commit -m "feat(api-client): métodos cliente multi-loja (lojas, série por nível, comparativo)"
```

---

### Task 2: Hooks cirúrgicos no script.js do portal

**Files:**
- Modify: `frontend_cliente/script.js`

**Interfaces:**
- Produces: `window.QTQD_PORTAL = { applyApiRecords(apiRecords), isApiMode() }` — usado por `multiloja.js` para trocar a série exibida. E o create do formulário passa a fundir a unidade ativa (`window.QTQD_MULTILOJA.activeUnit()`).
- Consumes: `apiRecordToLocal`, `records`, `saveRecords`, `renderAll`, `isApiMode`, `localRecordToApi` (todos já existem em `script.js`).

- [ ] **Step 1: Expor o hook QTQD_PORTAL**

Perto do topo de `script.js` (após a declaração de `records`, ou em qualquer ponto de escopo de módulo após `apiRecordToLocal`/`renderAll` existirem — como são function declarations, são hoisted, então pode ser logo após a linha de `let records=...`), adicionar:

```javascript
window.QTQD_PORTAL = {
  applyApiRecords: function (apiRecords) {
    records = (apiRecords || []).map(apiRecordToLocal);
    saveRecords();
    renderAll();
  },
  isApiMode: function () { return isApiMode(); },
};
```

- [ ] **Step 2: Fundir a unidade ativa no CREATE**

No handler do `form.addEventListener("submit", ...)`, no ramo de criação (o `else` onde chama `createAvaliacao(localRecordToApi(record))`), trocar essa chamada por (mantendo tudo o mais igual):

```javascript
          const createPayload = localRecordToApi(record);
          const u = (window.QTQD_MULTILOJA && window.QTQD_MULTILOJA.activeUnit) ? window.QTQD_MULTILOJA.activeUnit() : null;
          if (u && (u.grupo_id || u.loja_id)) { createPayload.grupo_id = u.grupo_id || null; createPayload.loja_id = u.loja_id || null; }
          const api = await window.QTQD_API_CLIENT.createAvaliacao(createPayload);
```

(Apenas o CREATE recebe a unidade; o UPDATE mantém a unidade já gravada na linha. Não alterar o ramo de update.)

- [ ] **Step 3: Chamar o init do módulo**

No fim de `initializeClient()` (após `renderAll()`/carregamento inicial), adicionar:

```javascript
  if (window.QTQD_MULTILOJA && window.QTQD_MULTILOJA.init) { try { await window.QTQD_MULTILOJA.init(); } catch (e) { /* multi-loja é opcional; não bloqueia o portal */ } }
```

- [ ] **Step 4: Syntax check**

Run: `node --check frontend_cliente/script.js`
Expected: exit 0. Se falhar, corrigir o SyntaxError ANTES de commitar (regra de ouro).

- [ ] **Step 5: Commit**

```bash
git add frontend_cliente/script.js
git commit -m "feat(portal): hooks multi-loja (QTQD_PORTAL, unidade no create, init do módulo)"
```

---

### Task 3: Módulo isolado multiloja.js

**Files:**
- Create: `frontend_cliente/multiloja.js`

**Interfaces:**
- Consumes: `window.QTQD_API_CLIENT` (Task 1), `window.QTQD_PORTAL` (Task 2).
- Produces: `window.QTQD_MULTILOJA = { init, activeUnit }`.

Comportamento: em `init()`, busca `getMeLojas()`; se `modo_rede` off ou sem grupos → retorna (portal normal). Senão injeta um `<select>` no topbar, injeta o conteúdo do seletor, e ao trocar carrega a série do nível via `listAvaliacoesNivel` → `QTQD_PORTAL.applyApiRecords`. Também controla a seção Comparativo (renderiza tabelas snapshot/evolução) e desabilita o botão de novo lançamento em níveis consolidados.

- [ ] **Step 1: Create the module**

Create `frontend_cliente/multiloja.js`. Sem template literals aninhados; concatenação de strings.

```javascript
/* Multi-loja — módulo isolado. Ativo só quando o tenant tem modo_rede.
   Protege o script.js: toda a lógica de seletor/série/comparativo vive aqui. */
(function () {
  const API = window.QTQD_API_CLIENT;
  let arvore = null;      // { modo_rede, grupos: [{id,nome,nivel_preenchimento,lojas:[{id,nome}]}] }
  let current = { nivel: 'rede', grupo_id: null, loja_id: null, entrada: false };

  window.QTQD_MULTILOJA = {
    init: init,
    activeUnit: function () {
      if (current && current.entrada) {
        return { grupo_id: current.grupo_id || null, loja_id: current.loja_id || null };
      }
      return null; // rede / grupo consolidado -> não é unidade de entrada
    },
  };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  async function init() {
    if (!API || !window.QTQD_PORTAL || !window.QTQD_PORTAL.isApiMode()) return;
    try { arvore = await API.getMeLojas(); } catch (e) { return; }
    if (!arvore || !arvore.modo_rede || !arvore.grupos || !arvore.grupos.length) return;
    injectSelector();
    wireComparativoNav();
    await selectFromValue('rede::');
  }

  // ---- Seletor no topbar ----
  function injectSelector() {
    const topRight = document.querySelector('.topbar-right') || document.querySelector('.topbar');
    if (!topRight || document.getElementById('mlLevelSelect')) return;
    const wrap = document.createElement('div');
    wrap.className = 'ml-level-wrap';
    wrap.style.marginRight = '12px';
    let html = '<select id="mlLevelSelect" style="padding:6px 10px;border-radius:8px">';
    html += '<option value="rede::">REDE (consolidado)</option>';
    arvore.grupos.forEach(function (g) {
      const single = arvore.grupos.length === 1;
      // nível grupo: só mostra rótulo de grupo quando há mais de um grupo
      if (!single) {
        html += '<option value="grupo:' + esc(g.id) + ':">' + esc(g.nome) + ' (consolidado)</option>';
      }
      if (g.nivel_preenchimento === 'loja' && g.lojas) {
        g.lojas.forEach(function (l) {
          const prefixo = single ? '' : '— ';
          html += '<option value="loja:' + esc(g.id) + ':' + esc(l.id) + '">' + prefixo + esc(l.nome) + '</option>';
        });
      } else if (g.nivel_preenchimento === 'grupo' && single) {
        // grupo único direto: já coberto por REDE; nada a adicionar
      }
    });
    html += '</select>';
    wrap.innerHTML = html;
    topRight.insertBefore(wrap, topRight.firstChild);
    document.getElementById('mlLevelSelect').addEventListener('change', function (e) {
      selectFromValue(e.target.value);
    });
  }

  // value = "nivel:grupoId:lojaId"
  async function selectFromValue(value) {
    const parts = String(value).split(':');
    const nivel = parts[0];
    const grupoId = parts[1] || null;
    const lojaId = parts[2] || null;
    const grupo = grupoId ? findGrupo(grupoId) : null;
    const entrada = nivel === 'loja' || (nivel === 'grupo' && grupo && grupo.nivel_preenchimento === 'grupo');
    current = { nivel: nivel, grupo_id: grupoId, loja_id: lojaId, entrada: entrada };
    // desabilita novo lançamento em nível consolidado (não-entrada)
    const nb = document.getElementById('newEntryButton');
    if (nb) nb.disabled = !entrada;
    try {
      const ref = nivel === 'loja' ? lojaId : (nivel === 'grupo' ? grupoId : null);
      const apiRecords = await API.listAvaliacoesNivel(nivel, ref);
      window.QTQD_PORTAL.applyApiRecords(apiRecords);
    } catch (e) { /* silencioso; mantém a série anterior */ }
  }

  function findGrupo(gid) {
    let found = null;
    arvore.grupos.forEach(function (g) { if (String(g.id) === String(gid)) found = g; });
    return found;
  }

  // ---- Comparativo (seção própria) ----
  function wireComparativoNav() {
    const link = document.querySelector('.nav-link[data-section="comparativo"]');
    if (link) link.addEventListener('click', function () { renderComparativo(); });
    const modoSel = document.getElementById('cmpModo');
    if (modoSel) modoSel.addEventListener('change', renderComparativo);
  }

  async function renderComparativo() {
    const host = document.getElementById('cmpContent');
    if (!host) return;
    const modo = (document.getElementById('cmpModo') || {}).value || 'snapshot';
    // nível do comparativo: rede compara grupos; grupo (nivel=loja) compara lojas
    const nivel = current.nivel === 'grupo' ? 'grupo' : 'rede';
    const grupoId = nivel === 'grupo' ? current.grupo_id : null;
    host.innerHTML = '<p style="color:var(--muted)">Carregando…</p>';
    try {
      const data = await API.getComparativo({ nivel: nivel, grupo_id: grupoId, modo: modo });
      host.innerHTML = modo === 'evolucao' ? renderEvolucao(data) : renderSnapshot(data);
    } catch (e) {
      host.innerHTML = '<p style="color:#dc2626">Não foi possível carregar o comparativo.</p>';
    }
  }

  function fmtMoney(v) {
    const n = Number(v || 0);
    return 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function indVal(indicadores, codigo) {
    let v = null;
    (indicadores || []).forEach(function (i) { if (i.codigo === codigo) v = i.valor; });
    return v;
  }

  const CMP_INDICADORES = [
    ['qt_total', 'QT Total', 'money'],
    ['qd_total', 'QD Total', 'money'],
    ['saldo_qt_qd', 'Saldo QT/QD', 'money'],
    ['indice_qt_qd', 'Índice QT/QD', 'num'],
    ['excesso_total', 'Excesso crítico', 'money'],
  ];

  function fmtByType(v, tipo) {
    if (v == null) return '—';
    if (tipo === 'money') return fmtMoney(v);
    return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 2 });
  }

  function renderSnapshot(data) {
    if (!data || !data.unidades || !data.unidades.length) {
      return '<p style="color:var(--muted)">Sem dados para comparar nesta semana.</p>';
    }
    let h = '<p style="color:var(--muted);font-size:13px">Semana ' + esc(data.semana || '') + '</p>';
    h += '<div style="overflow-x:auto"><table class="ml-table" style="width:100%;border-collapse:collapse;font-size:13px">';
    h += '<thead><tr><th style="text-align:left;padding:6px">Indicador</th>';
    data.unidades.forEach(function (u) { h += '<th style="text-align:right;padding:6px">' + esc(u.nome) + '</th>'; });
    h += '<th style="text-align:right;padding:6px;font-weight:700">Total</th></tr></thead><tbody>';
    CMP_INDICADORES.forEach(function (row) {
      h += '<tr><td style="padding:6px;text-align:left">' + esc(row[1]) + '</td>';
      data.unidades.forEach(function (u) {
        h += '<td style="padding:6px;text-align:right">' + fmtByType(indVal(u.indicadores, row[0]), row[2]) + '</td>';
      });
      const totalVal = data.total ? indVal(data.total.indicadores, row[0]) : null;
      h += '<td style="padding:6px;text-align:right;font-weight:700">' + fmtByType(totalVal, row[2]) + '</td></tr>';
    });
    h += '</tbody></table></div>';
    return h;
  }

  function renderEvolucao(data) {
    if (!data || !data.unidades || !data.unidades.length) {
      return '<p style="color:var(--muted)">Sem dados de evolução.</p>';
    }
    // tabela: semanas nas linhas, unidades nas colunas, indicador = Índice QT/QD
    const semanasSet = {};
    data.unidades.forEach(function (u) {
      (u.serie || []).forEach(function (p) { semanasSet[p.semana] = true; });
    });
    const semanas = Object.keys(semanasSet).sort().reverse();
    let h = '<p style="color:var(--muted);font-size:13px">Evolução do Índice QT/QD por unidade</p>';
    h += '<div style="overflow-x:auto"><table class="ml-table" style="width:100%;border-collapse:collapse;font-size:13px">';
    h += '<thead><tr><th style="text-align:left;padding:6px">Semana</th>';
    data.unidades.forEach(function (u) { h += '<th style="text-align:right;padding:6px">' + esc(u.nome) + '</th>'; });
    h += '</tr></thead><tbody>';
    semanas.forEach(function (s) {
      h += '<tr><td style="padding:6px;text-align:left">' + esc(s) + '</td>';
      data.unidades.forEach(function (u) {
        let val = null;
        (u.serie || []).forEach(function (p) { if (p.semana === s) val = indVal(p.indicadores, 'indice_qt_qd'); });
        h += '<td style="padding:6px;text-align:right">' + (val == null ? '—' : Number(val).toLocaleString('pt-BR', { maximumFractionDigits: 2 })) + '</td>';
      });
      h += '</tr>';
    });
    h += '</tbody></table></div>';
    return h;
  }
})();
```

- [ ] **Step 2: Syntax check**

Run: `node --check frontend_cliente/multiloja.js`
Expected: exit 0, no output.

- [ ] **Step 3: Commit**

```bash
git add frontend_cliente/multiloja.js
git commit -m "feat(portal): módulo isolado multiloja.js (seletor + série por nível + comparativo)"
```

---

### Task 4: HTML do portal (nav + seção Comparativo) + include + SW

**Files:**
- Modify: `frontend_cliente/index.html`
- Modify: `frontend_cliente/sw.js`

**Interfaces:**
- Produces IDs: `cmpModo`, `cmpContent`; nav-link `data-section="comparativo"`; seção `id="comparativo" class="section-view hidden"`.

- [ ] **Step 1: Nav-link**

No `frontend_cliente/index.html`, adicionar um nav-link junto aos outros (ex.: após `data-section="graficos"`):
```html
      <button class="nav-link" data-section="comparativo" type="button">Comparativo</button>
```
(Confirme a estrutura/classe do botão olhando os nav-links vizinhos e replique.)

- [ ] **Step 2: Seção**

Adicionar uma seção no mesmo nível das outras `.section-view` (ex.: após a seção de gráficos):
```html
    <section id="comparativo" class="section-view hidden">
      <div class="page-hero">
        <div>
          <p class="eyebrow">Multi-loja</p>
          <h1>Comparativo</h1>
          <p>Compare as unidades da rede lado a lado.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-inner">
          <label for="cmpModo">Modo</label>
          <select id="cmpModo">
            <option value="snapshot">Snapshot (uma semana)</option>
            <option value="evolucao">Evolução (semanas)</option>
          </select>
          <div id="cmpContent" style="margin-top:16px"></div>
        </div>
      </div>
    </section>
```
(Ajuste as classes `.page-hero`/`.card`/`.card-inner`/`.eyebrow` para as que as seções vizinhas realmente usam — replique uma seção existente para o wrapper ficar nativo.)

- [ ] **Step 3: Incluir o script**

Adicionar, junto aos outros includes de módulo (após `<script src="excesso_critico.js"></script>`):
```html
<script src="multiloja.js"></script>
```

- [ ] **Step 4: Bump do Service Worker**

Em `frontend_cliente/sw.js`, trocar `const CACHE = 'qtqd-v13';` por `const CACHE = 'qtqd-v14';`. Se houver uma lista de assets a cachear e ela incluir os módulos JS, adicionar `'multiloja.js'` a essa lista (seguir o padrão dos outros módulos como `excesso_critico.js`).

- [ ] **Step 5: Verificação**

Run: `node --check frontend_cliente/multiloja.js && node --check frontend_cliente/script.js && node --check shared/api_client.js && echo "js ok"`
Expected: `js ok`.
Confirme (grep) que `index.html` inclui `multiloja.js` e tem a seção `id="comparativo"`, e que `sw.js` está em `qtqd-v14`.

- [ ] **Step 6: Commit**

```bash
git add frontend_cliente/index.html frontend_cliente/sw.js
git commit -m "feat(portal): nav+seção Comparativo, include multiloja.js, SW qtqd-v14"
```

---

## Self-Review (Plano 4)

- **Cobertura (núcleo):** api_client (Task 1) ✓; hooks mínimos no script.js (Task 2) ✓; módulo isolado com seletor+série+comparativo (Task 3) ✓; nav+seção+include+SW (Task 4) ✓.
- **Isolamento/risco:** lógica nova em `multiloja.js`; `script.js` toca 3 pontos cirúrgicos; `modo_rede` off → módulo retorna cedo (portal idêntico a hoje). `node --check` obrigatório em cada `.js`.
- **Regra de ouro:** sem template literals aninhados no módulo (concatenação) e nos hooks.
- **Dependência de classes CSS:** a seção Comparativo deve replicar as classes reais das seções vizinhas (o implementador deve inspecionar `index.html`/`styles.css`, como no aprendizado do Plano 3, onde classes inventadas quebraram o layout). Verificar no E2E.
- **Handoffs (usuário):** rodar o SQL do Plano 2; E2E no navegador (F12 sem erros; seletor troca série; lançamento grava na loja; comparativo exibe). Plano 5: Excesso por loja, e-mail por nível, semáforo de ciclo.

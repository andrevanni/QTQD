# Multi-loja — Plano 3: UI Admin (estrutura grupos/lojas + toggle modo_rede)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Uma seção "Estrutura" no painel admin para, por cliente: ligar/desligar `modo_rede`, cadastrar grupos econômicos (com nível de preenchimento) e lojas, consumindo os endpoints do Plano 2.

**Architecture:** Segue os padrões existentes do admin: nav-link `data-section` → `openSection(id)` → `loadEstrutura()`; métodos no `window.QTQD_API_CLIENT` (admin usa `adminHeaders(getToken())`); render em cards com `el()`/innerHTML; feedback via `fb()`; seletor de cliente via `populateClientSelects()`.

**Tech Stack:** HTML + JS puro (sem framework). Verificação de sintaxe com `node --check` (não há teste automatizado de frontend no repo).

## Global Constraints

- **Idioma:** português brasileiro (UI/commits).
- **Verificação obrigatória:** após CADA edição em `.js`, rodar `node --check <arquivo>` e confirmar sem erro (pega o SyntaxError que já derrubou o portal — lição #36 do CLAUDE.md). Não há browser E2E neste ambiente — a verificação visual final é handoff do usuário.
- **Sem template literals aninhados** (backtick dentro de `${}` dentro de backtick) — usar concatenação/variáveis intermediárias (regra de ouro do projeto).
- **Não quebrar o admin atual:** só ADICIONAR (nav-link, seção, métodos, `loadEstrutura`). Não alterar seções existentes além de: (a) adicionar `'estruturaClient'` à lista de `populateClientSelects`; (b) adicionar o dispatch em `openSection`.
- **Endpoints (Plano 2):** admin `GET/POST /admin/tenants/{tid}/grupos`, `PATCH/DELETE /admin/tenants/{tid}/grupos/{gid}`, idem `/lojas`, `PATCH /admin/tenants/{tid}/modo-rede` (body `{ativo}`).
- **Spec:** `docs/superpowers/specs/2026-07-08-multi-loja-grupo-economico-design.md`.

---

## File Structure (Plano 3)

- **Modify:** `shared/api_client.js` — 9 métodos admin de estrutura.
- **Modify:** `frontend_admin/index.html` — nav-link + `<section id="estrutura">`.
- **Modify:** `frontend_admin/script.js` — `loadEstrutura()`, `renderEstrutura()`, handlers; dispatch em `openSection`; `'estruturaClient'` em `populateClientSelects`.

---

### Task 1: Métodos admin de estrutura no api_client

**Files:**
- Modify: `shared/api_client.js`

**Interfaces:**
- Produces (no objeto `window.QTQD_API_CLIENT`): `listGrupos(adminToken, tenantId)`, `criarGrupo(adminToken, tenantId, payload)`, `atualizarGrupo(adminToken, tenantId, gid, payload)`, `excluirGrupo(adminToken, tenantId, gid)`, `listLojas(adminToken, tenantId)`, `criarLoja(adminToken, tenantId, payload)`, `atualizarLoja(adminToken, tenantId, lid, payload)`, `excluirLoja(adminToken, tenantId, lid)`, `toggleModoRede(adminToken, tenantId, ativo)`.

- [ ] **Step 1: Add the methods**

In `shared/api_client.js`, inside the `window.QTQD_API_CLIENT = { ... }` object, add a new block (e.g. right after the admin usuarios methods). Use the same `request(base(...), {method, headers: adminHeaders(adminToken), body})` pattern already used by the admin methods:

```javascript
    /* ── Estrutura multi-loja (exige X-Admin-Token) ──── */
    listGrupos(adminToken, tenantId) {
      return request(base(`/admin/tenants/${tenantId}/grupos`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    criarGrupo(adminToken, tenantId, payload) {
      return request(base(`/admin/tenants/${tenantId}/grupos`), { method: 'POST', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    atualizarGrupo(adminToken, tenantId, gid, payload) {
      return request(base(`/admin/tenants/${tenantId}/grupos/${gid}`), { method: 'PATCH', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    excluirGrupo(adminToken, tenantId, gid) {
      return request(base(`/admin/tenants/${tenantId}/grupos/${gid}`), { method: 'DELETE', headers: adminHeaders(adminToken) });
    },
    listLojas(adminToken, tenantId) {
      return request(base(`/admin/tenants/${tenantId}/lojas`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    criarLoja(adminToken, tenantId, payload) {
      return request(base(`/admin/tenants/${tenantId}/lojas`), { method: 'POST', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    atualizarLoja(adminToken, tenantId, lid, payload) {
      return request(base(`/admin/tenants/${tenantId}/lojas/${lid}`), { method: 'PATCH', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    excluirLoja(adminToken, tenantId, lid) {
      return request(base(`/admin/tenants/${tenantId}/lojas/${lid}`), { method: 'DELETE', headers: adminHeaders(adminToken) });
    },
    toggleModoRede(adminToken, tenantId, ativo) {
      return request(base(`/admin/tenants/${tenantId}/modo-rede`), { method: 'PATCH', headers: adminHeaders(adminToken), body: JSON.stringify({ ativo: ativo }) });
    },
```

- [ ] **Step 2: Syntax check**

Run: `node --check shared/api_client.js`
Expected: no output (exit 0). If it errors, fix before committing.

- [ ] **Step 3: Commit**

```bash
git add shared/api_client.js
git commit -m "feat(api-client): métodos admin de estrutura (grupos/lojas/modo_rede)"
```

---

### Task 2: Seção "Estrutura" no HTML do admin

**Files:**
- Modify: `frontend_admin/index.html`

**Interfaces:**
- Produces (IDs consumidos pela Task 3): `estruturaClient`, `estruturaModoRede`, `estruturaModoRedeWrap`, `grupoNome`, `grupoNivel`, `addGrupoButton`, `gruposList`, `lojaGrupoSelect`, `lojaNome`, `lojaFilialExcel`, `addLojaButton`, `estruturaEmpty`.

- [ ] **Step 1: Add the nav-link**

In `frontend_admin/index.html`, add a nav-link near the others (e.g., after `data-section="usuarios"`):
```html
          <button class="nav-link" data-section="estrutura" type="button">Estrutura</button>
```

- [ ] **Step 2: Add the section**

Add a `<section id="estrutura" class="section" hidden>` following the structure of the other sections (a `.card` with `.card-inner`). Use plain inputs matching the admin's existing styles:

```html
      <section id="estrutura" class="section" hidden>
        <div class="card">
          <div class="card-inner">
            <p class="eyebrow">Multi-loja</p>
            <h2>Estrutura de rede</h2>
            <p class="section-desc">Configure grupos econômicos e lojas do cliente. O portal só mostra o seletor de rede quando "Modo rede" está ativo.</p>

            <label class="field-label" for="estruturaClient">Cliente</label>
            <select id="estruturaClient"></select>

            <div id="estruturaModoRedeWrap" style="margin-top:16px" hidden>
              <label style="display:flex;align-items:center;gap:8px;cursor:pointer">
                <input type="checkbox" id="estruturaModoRede"> Modo rede ativo (mostra o seletor de loja/grupo no portal)
              </label>
            </div>

            <div id="estruturaEmpty" class="section-desc" style="margin-top:16px">Selecione um cliente para configurar a estrutura.</div>

            <div id="estruturaBody" hidden>
              <h3 style="margin-top:20px">Grupos econômicos</h3>
              <div class="form-row" style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end">
                <div>
                  <label class="field-label" for="grupoNome">Nome do grupo</label>
                  <input type="text" id="grupoNome" placeholder="Ex.: Geral">
                </div>
                <div>
                  <label class="field-label" for="grupoNivel">Preenchimento</label>
                  <select id="grupoNivel">
                    <option value="loja">Por loja</option>
                    <option value="grupo">Direto no grupo</option>
                  </select>
                </div>
                <button id="addGrupoButton" class="btn btn-primary" type="button">Adicionar grupo</button>
              </div>
              <div id="gruposList" style="margin-top:12px"></div>

              <h3 style="margin-top:24px">Nova loja</h3>
              <div class="form-row" style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end">
                <div>
                  <label class="field-label" for="lojaGrupoSelect">Grupo</label>
                  <select id="lojaGrupoSelect"></select>
                </div>
                <div>
                  <label class="field-label" for="lojaNome">Nome da loja</label>
                  <input type="text" id="lojaNome" placeholder="Ex.: Loja Centro">
                </div>
                <div>
                  <label class="field-label" for="lojaFilialExcel">Filial (Excel)</label>
                  <input type="text" inputmode="numeric" id="lojaFilialExcel" placeholder="1" style="width:90px">
                </div>
                <button id="addLojaButton" class="btn btn-primary" type="button">Adicionar loja</button>
              </div>
            </div>
          </div>
        </div>
      </section>
```

(If the admin CSS lacks `.section-desc`/`.field-label`/`.btn`, reuse whatever equivalent classes the neighboring sections use — match the existing markup so the new section looks native. Do not invent new CSS.)

- [ ] **Step 3: Commit**

```bash
git add frontend_admin/index.html
git commit -m "feat(admin): seção Estrutura (grupos/lojas/modo_rede) no HTML"
```

---

### Task 3: Lógica da seção Estrutura no script.js

**Files:**
- Modify: `frontend_admin/script.js`

**Interfaces:**
- Consumes: api_client methods (Task 1); IDs (Task 2); helpers `$`, `el`, `fb`, `getToken`, `clients`, `populateClientSelects`, `openSection`.
- Produces: `loadEstrutura()`, `renderEstrutura()`, module state `estruturaGrupos`, `estruturaLojas`.

- [ ] **Step 1: Add `'estruturaClient'` to populateClientSelects**

In `populateClientSelects()`, add `'estruturaClient'` to the array of select ids.

- [ ] **Step 2: Add the dispatch in openSection**

In `openSection(id)`, add near the other `if (id === '...')` lines:
```javascript
  if (id === 'estrutura')  loadEstrutura();
```

- [ ] **Step 3: Add the module logic**

Add near the other section blocks (e.g., after the USUÁRIOS block). Note: **no nested template literals** — build strings with concatenation.

```javascript
/* ═══════════════════════════════════════════════════════
   ESTRUTURA (multi-loja: grupos/lojas + modo_rede)
   ═══════════════════════════════════════════════════════ */
let estruturaGrupos = [];
let estruturaLojas = [];

async function loadEstrutura() {
  const tid = $('estruturaClient')?.value || '';
  const wrap = $('estruturaModoRedeWrap');
  const body = $('estruturaBody');
  const empty = $('estruturaEmpty');
  if (!tid) {
    if (wrap) wrap.hidden = true;
    if (body) body.hidden = true;
    if (empty) empty.hidden = false;
    return;
  }
  try {
    const arvore = await window.QTQD_API_CLIENT.listGrupos(getToken(), tid);
    // listGrupos devolve só grupos; buscar lojas em paralelo
    const [grupos, lojas] = await Promise.all([
      window.QTQD_API_CLIENT.listGrupos(getToken(), tid),
      window.QTQD_API_CLIENT.listLojas(getToken(), tid),
    ]);
    estruturaGrupos = grupos || [];
    estruturaLojas = lojas || [];
    // modo_rede: ler via /me/lojas não dá (admin); usar o registro do cliente já carregado
    const cli = clients.find(c => String(c.id) === String(tid));
    if ($('estruturaModoRede')) $('estruturaModoRede').checked = !!(cli && cli.modo_rede);
    if (wrap) wrap.hidden = false;
    if (body) body.hidden = false;
    if (empty) empty.hidden = true;
    renderEstrutura();
  } catch (e) {
    fb('Erro ao carregar estrutura: ' + e.message, 'error');
  }
}

function renderEstrutura() {
  // popular select de grupo do formulário de loja
  const sel = $('lojaGrupoSelect');
  if (sel) {
    sel.innerHTML = '<option value="">Selecione o grupo</option>' +
      estruturaGrupos.map(function (g) { return '<option value="' + g.id + '">' + g.nome + '</option>'; }).join('');
  }
  // lista de grupos com suas lojas
  const list = $('gruposList');
  if (!list) return;
  if (!estruturaGrupos.length) {
    list.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhum grupo cadastrado.</p>';
    return;
  }
  list.innerHTML = '';
  estruturaGrupos.forEach(function (g) {
    const lojasDoGrupo = estruturaLojas.filter(function (l) { return String(l.grupo_id) === String(g.id); });
    const card = el('article', 'entity-card');
    const nivelLabel = g.nivel_preenchimento === 'grupo' ? 'Direto no grupo' : 'Por loja';
    let html = '<div style="display:flex;justify-content:space-between;align-items:center;gap:8px">';
    html += '<strong>' + g.nome + '</strong>';
    html += '<span style="font-size:12px;color:var(--muted)">' + nivelLabel + '</span>';
    html += '<button class="btn btn-danger btn-sm" data-del-grupo="' + g.id + '" type="button">Excluir</button>';
    html += '</div>';
    if (g.nivel_preenchimento === 'loja') {
      if (lojasDoGrupo.length) {
        html += '<ul style="margin:8px 0 0;padding-left:18px;font-size:13px">';
        lojasDoGrupo.forEach(function (l) {
          const fil = (l.filial_excel !== null && l.filial_excel !== undefined) ? ' · Filial ' + l.filial_excel : '';
          html += '<li>' + l.nome + fil + ' <button class="btn-link" data-del-loja="' + l.id + '" type="button" style="color:#dc2626">remover</button></li>';
        });
        html += '</ul>';
      } else {
        html += '<p style="font-size:12px;color:var(--muted);margin:8px 0 0">Sem lojas cadastradas.</p>';
      }
    }
    card.innerHTML = html;
    list.appendChild(card);
  });
  // handlers de exclusão (delegação simples)
  list.querySelectorAll('[data-del-grupo]').forEach(function (b) {
    b.addEventListener('click', function () { excluirGrupoEstrutura(b.getAttribute('data-del-grupo')); });
  });
  list.querySelectorAll('[data-del-loja]').forEach(function (b) {
    b.addEventListener('click', function () { excluirLojaEstrutura(b.getAttribute('data-del-loja')); });
  });
}

async function excluirGrupoEstrutura(gid) {
  const tid = $('estruturaClient').value;
  if (!confirm('Excluir este grupo e suas lojas? Esta ação não pode ser desfeita.')) return;
  try {
    await window.QTQD_API_CLIENT.excluirGrupo(getToken(), tid, gid);
    fb('Grupo excluído.', 'success');
    await loadEstrutura();
  } catch (e) { fb('Erro ao excluir grupo: ' + e.message, 'error'); }
}

async function excluirLojaEstrutura(lid) {
  const tid = $('estruturaClient').value;
  if (!confirm('Excluir esta loja?')) return;
  try {
    await window.QTQD_API_CLIENT.excluirLoja(getToken(), tid, lid);
    fb('Loja excluída.', 'success');
    await loadEstrutura();
  } catch (e) { fb('Erro ao excluir loja: ' + e.message, 'error'); }
}

// Listeners (registrados uma vez no load do script)
$('estruturaClient')?.addEventListener('change', loadEstrutura);

$('estruturaModoRede')?.addEventListener('change', async function () {
  const tid = $('estruturaClient').value;
  if (!tid) return;
  try {
    await window.QTQD_API_CLIENT.toggleModoRede(getToken(), tid, $('estruturaModoRede').checked);
    const cli = clients.find(function (c) { return String(c.id) === String(tid); });
    if (cli) cli.modo_rede = $('estruturaModoRede').checked;
    fb('Modo rede ' + ($('estruturaModoRede').checked ? 'ativado' : 'desativado') + '.', 'success');
  } catch (e) { fb('Erro ao alterar modo rede: ' + e.message, 'error'); }
});

$('addGrupoButton')?.addEventListener('click', async function () {
  const tid = $('estruturaClient').value;
  const nome = $('grupoNome').value.trim();
  if (!tid) { fb('Selecione um cliente.', 'error'); return; }
  if (!nome) { fb('Informe o nome do grupo.', 'error'); return; }
  try {
    await window.QTQD_API_CLIENT.criarGrupo(getToken(), tid, { nome: nome, nivel_preenchimento: $('grupoNivel').value });
    $('grupoNome').value = '';
    fb('Grupo adicionado.', 'success');
    await loadEstrutura();
  } catch (e) { fb('Erro ao adicionar grupo: ' + e.message, 'error'); }
});

$('addLojaButton')?.addEventListener('click', async function () {
  const tid = $('estruturaClient').value;
  const grupoId = $('lojaGrupoSelect').value;
  const nome = $('lojaNome').value.trim();
  const filStr = $('lojaFilialExcel').value.trim();
  if (!tid) { fb('Selecione um cliente.', 'error'); return; }
  if (!grupoId) { fb('Selecione o grupo.', 'error'); return; }
  if (!nome) { fb('Informe o nome da loja.', 'error'); return; }
  const payload = { grupo_id: grupoId, nome: nome };
  if (filStr) payload.filial_excel = parseInt(filStr, 10);
  try {
    await window.QTQD_API_CLIENT.criarLoja(getToken(), tid, payload);
    $('lojaNome').value = '';
    $('lojaFilialExcel').value = '';
    fb('Loja adicionada.', 'success');
    await loadEstrutura();
  } catch (e) { fb('Erro ao adicionar loja: ' + e.message, 'error'); }
});
```

> Nota: `loadEstrutura` faz duas chamadas `listGrupos` (a primeira, `arvore`, é redundante). O implementador deve REMOVER a linha redundante `const arvore = await ... listGrupos(...)` e manter só o `Promise.all([listGrupos, listLojas])`.

- [ ] **Step 4: Syntax check**

Run: `node --check frontend_admin/script.js`
Expected: no output (exit 0). Fix any SyntaxError before committing.

- [ ] **Step 5: Grep — sem template literals aninhados**

Run: `node --check frontend_admin/script.js && echo "sintaxe ok"`
Confirme visualmente que o bloco novo usa concatenação (aspas simples + `+`), sem backtick dentro de `${}`.

- [ ] **Step 6: Commit**

```bash
git add frontend_admin/script.js
git commit -m "feat(admin): lógica da seção Estrutura (CRUD grupos/lojas + toggle modo_rede)"
```

---

## Self-Review (Plano 3)

- **Cobertura:** métodos api_client (Task 1) ✓; nav-link + seção + IDs (Task 2) ✓; loadEstrutura/render/handlers + dispatch + client select (Task 3) ✓; toggle modo_rede ✓; CRUD grupos/lojas ✓.
- **Não-regressão:** só adiciona nav/seção/métodos + 2 linhas em funções existentes (`populateClientSelects`, `openSection`). `node --check` em cada `.js`.
- **Regra de ouro:** sem template literals aninhados (concatenação no render). Verificação de sintaxe obrigatória.
- **Dependência:** `clients` precisa conter `modo_rede` — o endpoint admin de clientes deve retornar essa coluna. Se não retornar, o checkbox inicia desmarcado e o toggle ainda funciona (grava no banco). Aceitável; anotar para verificar no E2E.
- **Handoff:** verificação visual/E2E no navegador é do usuário (após rodar o SQL).

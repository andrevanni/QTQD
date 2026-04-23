/* ═══════════════════════════════════════════════════════
   QTQD — Admin Frontend Script
   Conectado ao backend via QTQD_API_CLIENT (shared/api_client.js)
   ═══════════════════════════════════════════════════════ */
'use strict';

const ADMIN_TOKEN_KEY = window.QTQD_APP_CONFIG?.adminTokenStorageKey || 'qtqd_admin_token_v1';
const THEME_KEY       = 'qtqd_admin_theme';
const FIELD_KEY       = 'qtqd_field_config_v1';

const defaultFields = {
  saldo_bancario:           { label: 'Saldo bancário',              visible: true },
  contas_receber:           { label: 'Contas a receber',            visible: true },
  cartoes:                  { label: 'Cartões',                     visible: true },
  convenios:                { label: 'Convênios',                   visible: true },
  cheques:                  { label: 'Cheques',                     visible: true },
  trade_marketing:          { label: 'Trade marketing',             visible: true },
  outros_qt:                { label: 'Outros QT',                   visible: true },
  estoque_custo:            { label: 'Estoque (preço custo)',        visible: true },
  contas_pagar:             { label: 'Contas a pagar',              visible: true },
  fornecedores:             { label: 'Fornecedores',                visible: true },
  investimentos_assumidos:  { label: 'Investimentos assumidos',     visible: true },
  outras_despesas_assumidas:{ label: 'Outras despesas assumidas',   visible: true },
  dividas:                  { label: 'Dívidas',                     visible: true },
  financiamentos:           { label: 'Financiamentos',              visible: true },
  tributos_atrasados:       { label: 'Tributos atrasados',          visible: true },
  acoes_processos:          { label: 'Ações e processos',           visible: true },
  faturamento_previsto_mes: { label: 'Faturamento previsto no mês', visible: true },
  compras_mes:              { label: 'Compras no mês',              visible: true },
  entrada_mes:              { label: 'Entrada no mês',              visible: true },
  venda_cupom_mes:          { label: 'Venda cupom no mês',          visible: true },
  venda_custo_mes:          { label: 'Venda custo no mês - CMV',    visible: true },
  lucro_liquido_mes:        { label: 'Lucro líquido - mês',         visible: true },
};

/* ── Estado ──────────────────────────────────────────── */
let clients     = [];
let licenses    = [];
let imports     = [];
let selectedClient = null;

/* ── Helpers DOM ─────────────────────────────────────── */
const $  = id => document.getElementById(id);
const el = (tag, cls, html = '') => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
};

/* ── Datas BR (flatpickr) ────────────────────────────── */
function brToISO(br) {
  const p = (br || '').split('/');
  if (p.length !== 3 || p[2].length !== 4) return '';
  return `${p[2]}-${p[1].padStart(2,'0')}-${p[0].padStart(2,'0')}`;
}
if (typeof flatpickr !== 'undefined') {
  flatpickr.localize(flatpickr.l10ns.pt);
  document.querySelectorAll('input[data-date-br]').forEach(el => {
    flatpickr(el, { dateFormat: 'd/m/Y', allowInput: true, locale: 'pt' });
  });
}

/* ── Token ───────────────────────────────────────────── */
function getToken()       { return localStorage.getItem(ADMIN_TOKEN_KEY) || ''; }
function saveToken(t)     { localStorage.setItem(ADMIN_TOKEN_KEY, t); }
function clearToken()     { localStorage.removeItem(ADMIN_TOKEN_KEY); }

/* ── Tema ────────────────────────────────────────────── */
function applyTheme(t = localStorage.getItem(THEME_KEY) || 'dark') {
  document.body.dataset.theme = t;
  document.querySelectorAll('[data-theme-choice]').forEach(b =>
    b.classList.toggle('active', b.dataset.themeChoice === t));
  localStorage.setItem(THEME_KEY, t);
}

/* ── Feedback ────────────────────────────────────────── */
function fb(msg, type = 'info') {
  const box = $('feedbackBox');
  if (!box) return;
  box.textContent = msg;
  box.className   = 'feedback-box' + (type === 'error' ? ' error' : type === 'success' ? ' success' : '');
}
function fbClear() { const b=$('feedbackBox'); if(b){b.textContent='';b.className='feedback-box hidden';} }

/* ── Navegação ───────────────────────────────────────── */
const SECTION_META = {
  clientes:   { eyebrow: 'Cadastro Comercial',  title: 'Clientes da plataforma' },
  vigencias:  { eyebrow: 'Licenciamento',        title: 'Vigências e controle de acesso' },
  importacao: { eyebrow: 'Primeira Carga',       title: 'Importação de dados' },
  campos:     { eyebrow: 'Configuração',         title: 'Campos do formulário' },
  identidade: { eyebrow: 'Identidade Visual',    title: 'Branding por cliente' },
  ambiente:   { eyebrow: 'Conexão',              title: 'Ambiente e configurações' },
};

function openSection(id) {
  document.querySelectorAll('.admin-section').forEach(s => s.classList.toggle('hidden', s.id !== id));
  document.querySelectorAll('.nav-link[data-section]').forEach(b =>
    b.classList.toggle('active', b.dataset.section === id));
  fbClear();
  const meta = SECTION_META[id];
  if (meta) {
    const ey = document.getElementById('heroEyebrow');
    const ti = document.getElementById('heroTitle');
    if (ey) ey.textContent = meta.eyebrow;
    if (ti) ti.textContent = meta.title;
  }
  if (id === 'clientes')   loadClients();
  if (id === 'vigencias')  loadLicenses();
  if (id === 'importacao') loadImports();
  if (id === 'campos')     renderFieldConfig();
  if (id === 'identidade') loadBranding();
  if (id === 'ambiente')   renderAmbiente();
}

/* ── Login screen ────────────────────────────────────── */
function showLogin() {
  document.querySelector('.page-shell').style.display = 'none';
  let screen = document.getElementById('loginScreen');
  if (!screen) {
    screen = document.createElement('div');
    screen.id        = 'loginScreen';
    screen.className = 'login-screen';
    screen.innerHTML = `
      <div class="login-card">
        <img src="logo_alta.jpg" alt="Service Farma">
        <h2>QTQD — Painel Admin</h2>
        <p>Informe o token administrativo para continuar</p>
        <div class="field">
          <label for="loginTokenInput">Token administrativo</label>
          <input id="loginTokenInput" type="password" placeholder="Cole o token aqui" autocomplete="off">
        </div>
        <button class="primary-button" id="loginBtn" type="button">Entrar</button>
        <div id="loginError" style="color:#ef4444;font-size:12px;text-align:center;display:none"></div>
      </div>`;
    document.body.appendChild(screen);
    document.getElementById('loginBtn').addEventListener('click', tryLogin);
    document.getElementById('loginTokenInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') tryLogin();
    });
  }
  screen.style.display = 'flex';
}

async function tryLogin() {
  const token = ($('loginTokenInput').value || '').trim();
  if (!token) return;
  $('loginError').style.display = 'none';
  try {
    await window.QTQD_API_CLIENT.listClients(token);
    saveToken(token);
    document.getElementById('loginScreen').style.display = 'none';
    document.querySelector('.page-shell').style.display = '';
    init();
  } catch {
    $('loginError').textContent = 'Token inválido. Verifique e tente novamente.';
    $('loginError').style.display = 'block';
  }
}

/* ═══════════════════════════════════════════════════════
   CLIENTES
   ═══════════════════════════════════════════════════════ */
async function loadClients() {
  try {
    clients = await window.QTQD_API_CLIENT.listClients(getToken());
    renderClients();
    populateClientSelects();
  } catch (e) { fb('Erro ao carregar clientes: ' + e.message, 'error'); }
}

function renderClients() {
  const list = $('clientList');
  if (!list) return;
  if (!clients.length) { list.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhum cliente cadastrado.</p>'; return; }
  list.innerHTML = '';
  clients.forEach(c => {
    const card = el('article', 'entity-card' + (selectedClient?.id === c.id ? ' selected' : ''));
    card.innerHTML = `
      <div class="entity-card-row">
        <strong>${c.nome}</strong>
        <span class="badge ${c.status}">${c.status}</span>
      </div>
      <span>${c.slug} · ${c.plano || '-'}</span>
      <span style="font-size:11px;color:var(--muted)">${c.contato_email || ''}</span>`;
    card.addEventListener('click', () => selectClient(c));
    list.appendChild(card);
  });
}

function selectClient(c) {
  selectedClient = c;
  $('clientId').value      = c.id;
  $('clientName').value    = c.nome;
  $('clientSlug').value    = c.slug;
  $('clientStatus').value  = c.status;
  $('clientPlan').value    = c.plano || '';
  $('clientContact').value = c.contato_nome || '';
  $('clientEmail').value   = c.contato_email || '';
  $('clientModeBadge').textContent = 'Editando';
  renderClients();
}

function resetClientForm() {
  $('clientForm').reset();
  $('clientId').value = '';
  $('clientModeBadge').textContent = 'Novo';
  $('clientPlan').value = 'premium';
  selectedClient = null;
  renderClients();
}

$('clientForm').addEventListener('submit', async e => {
  e.preventDefault(); fbClear();
  const id      = $('clientId').value;
  const payload = {
    nome:           $('clientName').value.trim(),
    slug:           $('clientSlug').value.trim(),
    status:         $('clientStatus').value,
    plano:          $('clientPlan').value.trim(),
    contato_nome:   $('clientContact').value.trim() || null,
    contato_email:  $('clientEmail').value.trim() || null,
  };
  try {
    if (id) {
      await window.QTQD_API_CLIENT.updateClient(getToken(), id, payload);
      fb('Cliente atualizado com sucesso.', 'success');
    } else {
      await window.QTQD_API_CLIENT.createClient(getToken(), payload);
      fb('Cliente cadastrado com sucesso.', 'success');
    }
    resetClientForm();
    await loadClients();
  } catch (err) { fb('Erro ao salvar cliente: ' + err.message, 'error'); }
});

$('clearClientFormButton').addEventListener('click', resetClientForm);

/* ═══════════════════════════════════════════════════════
   VIGÊNCIAS
   ═══════════════════════════════════════════════════════ */
async function loadLicenses() {
  try {
    licenses = await window.QTQD_API_CLIENT.listLicencas(getToken());
    renderLicenses();
  } catch (e) { fb('Erro ao carregar vigências: ' + e.message, 'error'); }
}

function isoToBr(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function setDeleteLicenseVisible(show) {
  const btn = $('deleteLicenseButton');
  if (btn) btn.classList.toggle('hidden', !show);
}

function selectLicense(l) {
  $('licenseId').value      = l.id;
  setDeleteLicenseVisible(true);
  $('licenseClient').value  = String(l.tenant_id);
  $('licensePlan').value    = l.plano || 'premium';
  $('licenseStatus').value  = l.status;
  // Preenche as datas no formato BR
  const startFp = $('licenseStart')._flatpickr;
  const endFp   = $('licenseEnd')._flatpickr;
  if (startFp) startFp.setDate(l.inicio_vigencia, false, 'Y-m-d');
  else $('licenseStart').value = isoToBr(l.inicio_vigencia);
  if (endFp) endFp.setDate(l.fim_vigencia || '', false, 'Y-m-d');
  else $('licenseEnd').value = isoToBr(l.fim_vigencia || '');
  renderLicenses();
}

function resetLicenseForm() {
  $('licenseId').value = '';
  setDeleteLicenseVisible(false);
  $('licenseForm').reset();
  const startFp = $('licenseStart')._flatpickr;
  const endFp   = $('licenseEnd')._flatpickr;
  if (startFp) startFp.clear();
  if (endFp)   endFp.clear();
  renderLicenses();
}

function renderLicenses() {
  const list = $('licenseList');
  if (!list) return;
  if (!licenses.length) { list.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhuma vigência cadastrada.</p>'; return; }
  list.innerHTML = '';
  const selectedId = $('licenseId').value;
  licenses.forEach(l => {
    const client = clients.find(c => c.id === String(l.tenant_id));
    const card = el('article', 'entity-card' + (l.id === selectedId ? ' selected' : ''));
    card.innerHTML = `
      <div class="entity-card-row">
        <strong>${client?.nome || l.tenant_id}</strong>
        <span class="badge ${l.status}">${l.status}</span>
      </div>
      <span>${l.plano} · ${isoToBr(l.inicio_vigencia)} → ${isoToBr(l.fim_vigencia) || 'sem fim'}</span>`;
    card.addEventListener('click', () => selectLicense(l));
    list.appendChild(card);
  });
}

function populateClientSelects() {
  ['licenseClient', 'importClient', 'brandingClient', 'camposClient', 'templateClient'].forEach(id => {
    const sel = $(id);
    if (!sel) return;
    const cur = sel.value;
    sel.innerHTML = '<option value="">Selecione um cliente</option>' +
      clients.map(c => `<option value="${c.id}">${c.nome}</option>`).join('');
    if (cur) sel.value = cur;
  });
}

$('licenseForm').addEventListener('submit', async e => {
  e.preventDefault(); fbClear();
  const id             = $('licenseId').value;
  const inicio_vigencia = brToISO($('licenseStart').value);
  const fim_str         = $('licenseEnd').value;
  const fim_vigencia    = fim_str ? brToISO(fim_str) : null;
  const status          = $('licenseStatus').value;
  const tenant_id       = $('licenseClient').value;

  if (!inicio_vigencia) { fb('Data de início inválida. Use DD/MM/AAAA.', 'error'); return; }

  try {
    if (id) {
      // Edição
      const payload = { plano: $('licensePlan').value.trim(), inicio_vigencia, fim_vigencia, status };
      await window.QTQD_API_CLIENT.updateLicenca(getToken(), id, payload);
      fb('Vigência atualizada com sucesso.', 'success');
    } else {
      // Nova
      if (!tenant_id) { fb('Selecione um cliente.', 'error'); return; }
      // Avisa se já existe vigência ativa para o cliente
      if (status === 'ativo') {
        const ativas = licenses.filter(l => String(l.tenant_id) === tenant_id && l.status === 'ativo');
        if (ativas.length > 0) {
          const nome = clients.find(c => c.id === tenant_id)?.nome || tenant_id;
          const ok = confirm(`"${nome}" já possui vigência ativa.\n\nDeseja criar mesmo assim?\nRecomendado: edite a vigência anterior e mude para "Bloqueado".`);
          if (!ok) return;
        }
      }
      const payload = { tenant_id, plano: $('licensePlan').value.trim(), inicio_vigencia, fim_vigencia, status };
      await window.QTQD_API_CLIENT.createLicenca(getToken(), payload);
      fb('Vigência cadastrada com sucesso.', 'success');
    }
    resetLicenseForm();
    await loadLicenses();
  } catch (err) { fb('Erro ao salvar vigência: ' + err.message, 'error'); }
});

$('clearLicenseFormButton')?.addEventListener('click', resetLicenseForm);

$('deleteLicenseButton')?.addEventListener('click', async () => {
  const id = $('licenseId').value;
  if (!id) return;
  const client = clients.find(c => c.id === $('licenseClient').value);
  if (!confirm(`Excluir esta vigência de "${client?.nome || 'cliente'}"? Esta ação não pode ser desfeita.`)) return;
  try {
    await window.QTQD_API_CLIENT.deleteLicenca(getToken(), id);
    fb('Vigência excluída.', 'success');
    resetLicenseForm();
    await loadLicenses();
  } catch (err) { fb('Erro ao excluir: ' + err.message, 'error'); }
});

/* ═══════════════════════════════════════════════════════
   TEMPLATE EXCEL
   ═══════════════════════════════════════════════════════ */
document.getElementById('downloadTemplateBtn')?.addEventListener('click', async () => {
  const tenantId = $('templateClient')?.value;
  const weeks    = parseInt($('templateWeeks')?.value || '8', 10);

  // Carrega config do cliente se selecionado
  let fieldLabels = Object.entries(defaultFields).map(([k, v]) => ({ key: k, label: v.label }));
  if (tenantId) {
    try {
      const cfg = await window.QTQD_API_CLIENT.getComponentesConfig(getToken(), tenantId);
      if (cfg && cfg.length) {
        fieldLabels = cfg
          .filter(c => c.visivel !== false)
          .sort((a, b) => (a.ordem_exibicao || 999) - (b.ordem_exibicao || 999))
          .map(c => ({ key: c.codigo_componente, label: c.label_customizado || defaultFields[c.codigo_componente]?.label || c.codigo_componente }));
      }
    } catch {}
  }

  // Monta cabeçalho: coluna A = "Campo" + semanas
  const weekHeaders = Array.from({ length: weeks }, (_, i) => `Semana ${i + 1}`);
  const header = ['Campo', ...weekHeaders];

  // Primeira linha: Data (DD/MM/AAAA)
  const rows = [
    header,
    ['Data (DD/MM/AAAA)', ...Array(weeks).fill('')],
    ['Status (rascunho/fechada)', ...Array(weeks).fill('rascunho')],
    ...fieldLabels.map(f => [f.label, ...Array(weeks).fill('')]),
  ];

  // Gera xlsx
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.aoa_to_sheet(rows);

  // Largura das colunas
  ws['!cols'] = [{ wch: 36 }, ...Array(weeks).fill({ wch: 18 })];

  // Estilo do cabeçalho (negrito) — SheetJS CE não faz styles, mas a estrutura fica ok
  XLSX.utils.book_append_sheet(wb, ws, 'QTQD Carga');

  const clientNome = clients.find(c => c.id === tenantId)?.nome || 'padrao';
  const fileName = `QTQD_template_${clientNome.replace(/\s+/g, '_')}.xlsx`;
  XLSX.writeFile(wb, fileName);
  fb(`Template "${fileName}" baixado com ${fieldLabels.length} campos e ${weeks} semanas.`, 'success');
});

/* ═══════════════════════════════════════════════════════
   IMPORTAÇÕES
   ═══════════════════════════════════════════════════════ */
async function loadImports() {
  try {
    imports = await window.QTQD_API_CLIENT.listImportacoes(getToken());
    renderImports();
  } catch (e) { fb('Erro ao carregar importações: ' + e.message, 'error'); }
}

function renderImports() {
  const list = $('importList');
  if (!list) return;
  if (!imports.length) { list.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhuma importação registrada.</p>'; return; }
  list.innerHTML = '';
  imports.forEach(i => {
    const client = clients.find(c => c.id === String(i.tenant_id));
    const card = el('article', 'entity-card');
    card.innerHTML = `
      <div class="entity-card-row">
        <strong>${client?.nome || i.tenant_id}</strong>
        <span class="badge ${i.status}">${i.status}</span>
      </div>
      <span>${i.origem_arquivo_nome || '-'}</span>
      <span style="font-size:11px;color:var(--muted)">${new Date(i.created_at).toLocaleString('pt-BR')}</span>`;
    list.appendChild(card);
  });
}

$('importForm').addEventListener('submit', async e => {
  e.preventDefault(); fbClear();
  const tenantId = $('importClient').value;
  if (!tenantId) { fb('Selecione um cliente destino.', 'error'); return; }
  const fileInput = $('importFile');
  const fileName  = fileInput.files[0]?.name || 'sem-arquivo';
  const payload = {
    tenant_id:           tenantId,
    tipo:                'primeira_carga',
    origem_arquivo_nome: fileName,
    status:              'recebido',
    observacoes:         $('importNotes').value.trim() || null,
    registros_processados: 0,
    registros_com_erro:    0,
    payload_resumo:        {},
  };
  try {
    await window.QTQD_API_CLIENT.createImportacao(getToken(), payload);
    fb('Importação registrada. Processamento acontece no backend.', 'success');
    $('importForm').reset();
    await loadImports();
  } catch (err) { fb('Erro ao registrar importação: ' + err.message, 'error'); }
});

/* ═══════════════════════════════════════════════════════
   CAMPOS
   ═══════════════════════════════════════════════════════ */
function getLocalFieldConfig() {
  try { return { ...defaultFields, ...JSON.parse(localStorage.getItem(FIELD_KEY) || '{}') }; }
  catch { return { ...defaultFields }; }
}

function renderFieldConfig(apiConfig = null) {
  const list = $('fieldConfigList');
  if (!list) return;
  // Mescla defaults com config da API (se houver)
  const cfg = { ...defaultFields };
  if (apiConfig && Array.isArray(apiConfig)) {
    apiConfig.forEach(item => {
      if (cfg[item.codigo_componente]) {
        cfg[item.codigo_componente] = {
          label: item.label_customizado || cfg[item.codigo_componente].label,
          visible: item.visivel,
        };
      }
    });
  } else {
    // Fallback: localStorage
    const local = getLocalFieldConfig();
    Object.assign(cfg, local);
  }
  list.innerHTML = '';
  Object.entries(cfg).forEach(([key, item]) => {
    const row = el('div', 'field-config-item');
    row.innerHTML = `
      <label>
        <input type="checkbox" data-key="${key}" ${item.visible ? 'checked' : ''}>
        <span>${key}</span>
      </label>
      <input type="text" data-label="${key}" value="${item.label}" placeholder="Label do campo">`;
    list.appendChild(row);
  });
}

async function loadCamposConfig() {
  const tenantId = $('camposClient')?.value;
  if (!tenantId) {
    renderFieldConfig(null);
    return;
  }
  try {
    const data = await window.QTQD_API_CLIENT.getComponentesConfig(getToken(), tenantId);
    renderFieldConfig(data);
    fb('Configuração carregada do banco para este cliente.', 'success');
  } catch (e) {
    renderFieldConfig(null);
    fb('Erro ao carregar campos: ' + e.message, 'error');
  }
}

$('saveFieldConfigButton').addEventListener('click', async () => {
  const tenantId = $('camposClient')?.value;
  // Coleta valores do formulário
  const itens = [];
  document.querySelectorAll('#fieldConfigList .field-config-item').forEach((row, idx) => {
    const cb  = row.querySelector('input[type="checkbox"]');
    const inp = row.querySelector('input[type="text"]');
    if (!cb || !inp) return;
    const key = cb.dataset.key;
    itens.push({
      codigo_componente: key,
      label_customizado: inp.value.trim() || defaultFields[key]?.label || key,
      visivel: cb.checked,
      obrigatorio: false,
      ordem_exibicao: idx + 1,
    });
  });

  if (tenantId) {
    // Salva na API
    try {
      await window.QTQD_API_CLIENT.saveComponentesConfig(getToken(), tenantId, itens);
      fb('Configuração de campos salva no banco para este cliente.', 'success');
    } catch (e) { fb('Erro ao salvar: ' + e.message, 'error'); }
  } else {
    // Sem cliente selecionado → salva localmente como padrão
    const cfg = {};
    itens.forEach(i => { cfg[i.codigo_componente] = { label: i.label_customizado, visible: i.visivel }; });
    localStorage.setItem(FIELD_KEY, JSON.stringify(cfg));
    fb('Configuração padrão salva localmente (sem cliente selecionado).', 'success');
  }
});

$('resetFieldConfigButton').addEventListener('click', () => {
  localStorage.removeItem(FIELD_KEY);
  renderFieldConfig(null);
  fb('Configuração restaurada ao padrão.', 'success');
});

/* ═══════════════════════════════════════════════════════
   IDENTIDADE VISUAL (BRANDING)
   ═══════════════════════════════════════════════════════ */
async function loadBranding() {
  const tenantId = $('brandingClient')?.value;
  if (!tenantId) return;
  try {
    const data = await window.QTQD_API_CLIENT.getBranding(getToken(), tenantId);
    if (data) {
      $('brandingClientName').value = data.nome_portal || '';
      updateBrandingPreview(data.nome_portal || '', data.logo_cliente_url || '');
    }
  } catch (e) { fb('Erro ao carregar branding: ' + e.message, 'error'); }
}

function updateBrandingPreview(name, logoUrl) {
  const previewName = $('brandingPreviewName');
  const previewLogo = $('brandingPreviewLogo');
  const previewFb   = $('brandingPreviewFallback');
  if (previewName) previewName.textContent = name || 'Cliente';
  if (previewLogo && previewFb) {
    if (logoUrl) {
      previewLogo.src = logoUrl;
      previewLogo.classList.add('visible');
      previewFb.style.display = 'none';
    } else {
      previewLogo.classList.remove('visible');
      previewFb.style.display = '';
      previewFb.textContent = (name || 'CL').split(' ').filter(Boolean).slice(0, 2).map(p => p[0].toUpperCase()).join('') || 'CL';
    }
  }
}

$('brandingForm').addEventListener('submit', async e => {
  e.preventDefault(); fbClear();
  const tenantId = $('brandingClient')?.value;
  if (!tenantId) { fb('Selecione um cliente.', 'error'); return; }
  const payload = {
    nome_portal:      $('brandingClientName').value.trim() || null,
    logo_cliente_url: null,
    powered_by_label: 'Powered by Service Farma',
  };
  try {
    await window.QTQD_API_CLIENT.saveBranding(getToken(), tenantId, payload);
    fb('Identidade visual salva com sucesso.', 'success');
    updateBrandingPreview(payload.nome_portal || '', '');
  } catch (err) { fb('Erro ao salvar branding: ' + err.message, 'error'); }
});

$('resetBrandingButton')?.addEventListener('click', () => {
  $('brandingForm').reset();
  updateBrandingPreview('Cliente', '');
});

/* ═══════════════════════════════════════════════════════
   AMBIENTE
   ═══════════════════════════════════════════════════════ */
function renderAmbiente() {
  const cfg = window.QTQD_APP_CONFIG || {};
  const el = id => document.getElementById(id);
  if (el('runtimeMode'))       el('runtimeMode').value       = cfg.mode || 'api';
  if (el('runtimeApiBaseUrl')) el('runtimeApiBaseUrl').value = cfg.apiBaseUrl || '';
  if (el('runtimeHealthUrl'))  el('runtimeHealthUrl').value  = cfg.healthUrl || '';
  if (el('runtimeTenantId'))   el('runtimeTenantId').value   = cfg.tenantId || '';
  if (el('runtimeAdminToken')) el('runtimeAdminToken').value = getToken();
  updateAmbienteStatus();
}

function updateAmbienteStatus() {
  const cfg = window.QTQD_APP_CONFIG || {};
  const s = id => { const e = document.getElementById(id); return e; };
  if (s('runtimeModeLabel'))      s('runtimeModeLabel').textContent      = cfg.mode === 'api' ? 'API real' : 'Simulação';
  if (s('runtimeApiBaseLabel'))   s('runtimeApiBaseLabel').textContent   = cfg.apiBaseUrl || '-';
  if (s('runtimeTenantLabel'))    s('runtimeTenantLabel').textContent    = cfg.tenantId || 'Não definido';
}

$('runtimeConfigForm')?.addEventListener('submit', e => {
  e.preventDefault(); fbClear();
  const token = $('runtimeAdminToken').value.trim();
  if (token) saveToken(token);
  window.QTQD_APP_CONFIG = {
    ...(window.QTQD_APP_CONFIG || {}),
    mode:       $('runtimeMode').value,
    apiBaseUrl: $('runtimeApiBaseUrl').value.trim(),
    healthUrl:  $('runtimeHealthUrl').value.trim(),
    tenantId:   $('runtimeTenantId').value.trim(),
  };
  updateAmbienteStatus();
  fb('Ambiente salvo. Recarregue a página do cliente para aplicar.', 'success');
});

$('testApiConnectionButton')?.addEventListener('click', async () => {
  fbClear();
  try {
    const result = await window.QTQD_API_CLIENT.health();
    const label  = document.getElementById('runtimeHealthStatusLabel');
    if (label) label.textContent = `✓ OK — ${result?.env || 'production'}`;
    fb('API respondendo corretamente.', 'success');
  } catch (err) {
    const label = document.getElementById('runtimeHealthStatusLabel');
    if (label) label.textContent = '✗ Falhou';
    fb('Falha na conexão: ' + err.message, 'error');
  }
});

/* ═══════════════════════════════════════════════════════
   EVENTOS GLOBAIS
   ═══════════════════════════════════════════════════════ */
document.querySelectorAll('.nav-link[data-section]').forEach(b =>
  b.addEventListener('click', () => openSection(b.dataset.section)));

document.querySelectorAll('[data-theme-choice]').forEach(b =>
  b.addEventListener('click', () => applyTheme(b.dataset.themeChoice)));

document.getElementById('resetAdminButton')?.addEventListener('click', () => {
  clearToken();
  location.reload();
});

/* Selects de cliente para identidade/campos */
['brandingClient', 'camposClient'].forEach(id => {
  document.getElementById(id)?.addEventListener('change', () => {
    if (id === 'brandingClient') loadBranding();
    if (id === 'camposClient')   loadCamposConfig();
  });
});

/* Sidebar mini */
;(function() {
  const K = 'qtqd_admin_mini';
  const btn = $('sidebarMiniToggle');
  if (!btn) return;
  function apply(v) { document.body.classList.toggle('sidebar-mini', v); localStorage.setItem(K, v ? '1' : '0'); }
  apply(localStorage.getItem(K) === '1');
  btn.addEventListener('click', () => apply(!document.body.classList.contains('sidebar-mini')));
})();

/* ═══════════════════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════════════════ */
async function init() {
  applyTheme();
  const token = getToken();
  if (!token || !window.QTQD_API_CLIENT) { showLogin(); return; }
  try {
    await window.QTQD_API_CLIENT.listClients(token);
  } catch {
    showLogin(); return;
  }
  openSection('clientes');
}

init();

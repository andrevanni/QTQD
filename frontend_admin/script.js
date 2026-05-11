/* ═══════════════════════════════════════════════════════
   QTQD — Admin Frontend Script
   Conectado ao backend via QTQD_API_CLIENT (shared/api_client.js)
   ═══════════════════════════════════════════════════════ */
'use strict';

const ADMIN_TOKEN_KEY = window.QTQD_APP_CONFIG?.adminTokenStorageKey || 'qtqd_admin_token_v1';
const THEME_KEY       = 'qtqd_admin_theme';
const FIELD_KEY       = 'qtqd_field_config_v1';

/* ── Catálogo de campos por grupo (Padrão SF) ────────── */
const FIELD_CATALOG = {
  qt: {
    label: 'QT — Quanto Tenho',
    fields: {
      saldo_bancario:           'Saldo bancário',
      contas_receber:           'Contas a receber',
      cartoes:                  'Cartões',
      convenios:                'Convênios',
      cheques:                  'Cheques',
      trade_marketing:          'Trade marketing',
      outros_qt:                'Outros QT',
      estoque_custo:            'Estoque (preço custo)',
    },
  },
  qd: {
    label: 'QD — Quanto Devo',
    fields: {
      contas_pagar:             'Contas a pagar',
      fornecedores:             'Fornecedores',
      investimentos_assumidos:  'Investimentos assumidos',
      outras_despesas_assumidas:'Outras despesas assumidas',
      dividas:                  'Dívidas',
      financiamentos:           'Financiamentos',
      tributos_atrasados:       'Tributos atrasados',
      acoes_processos:          'Ações e processos',
    },
  },
  operacional: {
    label: 'Informações Complementares',
    fields: {
      faturamento_previsto_mes: 'Faturamento previsto no mês',
      compras_mes:              'Compras no mês',
      entrada_mes:              'Entrada no mês',
      venda_cupom_mes:          'Venda cupom no mês',
      venda_custo_mes:          'Venda custo no mês (CMV)',
      lucro_liquido_mes:        'Lucro líquido no mês',
    },
  },
  indicadores: {
    label: 'Indicadores Operacionais',
    fields: {
      pmp:                      'PMP — Prazo Médio de Pagamento',
      pmv:                      'PMV — Prazo Médio de Venda',
      pmv_avista:               'PMV À Vista',
      pmv_30:                   'PMV 30 dias',
      pmv_60:                   'PMV 60 dias',
      pmv_90:                   'PMV 90 dias',
      pmv_120:                  'PMV 120 dias',
      pmv_outros:               'PMV Outros',
      pme_excel:                'PME — Cobertura Média (ERP)',
      cobertura_estoque_dia:    'Cobertura de Estoque (do Dia)',
      indice_faltas:            'Índice de Faltas %',
      excesso_curva_a:          'Excesso Curva A >90 dias',
      excesso_curva_b:          'Excesso Curva B >120 dias',
      excesso_curva_c:          'Excesso Curva C >150 dias',
      excesso_curva_d:          'Excesso Curva D >180 dias',
    },
  },
};

/* Campos calculados — exibição + fórmula editável (descrição) */
const CALCULATED_CATALOG_DEFAULT = [
  { key: 'qt_total',                     label: 'QT Total',                           formula: 'Saldo bancário + Contas a receber + Estoque' },
  { key: 'qd_total',                     label: 'QD Total',                           formula: 'Contas a pagar + Dívidas' },
  { key: 'saldo_qt_qd',                  label: 'Saldo QT/QD',                        formula: 'QT Total − QD Total' },
  { key: 'indice_qt_qd',                 label: 'Índice QT/QD',                       formula: 'QT Total ÷ QD Total' },
  { key: 'saldo_sem_dividas',            label: 'Saldo sem Dívidas',                  formula: 'Saldo QT/QD + Financiamentos + Tributos + Ações' },
  { key: 'indice_sem_dividas',           label: 'Índice sem Dívidas',                 formula: 'QT Total ÷ (QD Total − Dívidas)' },
  { key: 'saldo_sem_dividas_sem_estoque',label: 'Saldo sem Dívidas e sem Estoque',    formula: 'Saldo sem Dívidas − Estoque' },
  { key: 'pme',                          label: 'PME Calculado',                      formula: 'Estoque × 30 ÷ CMV (mensal)' },
  { key: 'ciclo_financiamento',          label: 'Ciclo de Financiamento (dias)',       formula: 'PMP − PMV − PME  (positivo = fornecedores financiam; negativo = farmácia financia)' },
  { key: 'indice_compra_venda',          label: 'Índice de Compra/Venda % (custo)',   formula: 'Compras no mês ÷ CMV no mês  (resultado em %)  — ex: 80% = comprou 80% do que vendeu a custo' },
  { key: 'indice_entrada_venda',         label: 'Índice de Entrada/Venda % (custo)',  formula: 'Entrada no mês ÷ CMV no mês  (resultado em %)  — ex: 90% = recebeu mercadoria equivalente a 90% do CMV' },
  { key: 'margem_bruta',                 label: 'Margem Bruta no mês %',              formula: '(Venda cupom − CMV) ÷ Venda cupom' },
  { key: 'excesso_total',                label: 'Excesso Crítico Total',              formula: 'Excesso A + Excesso B + Excesso C + Excesso D' },
];

const SF_CALC_KEY = 'qtqd_sf_calc_desc_v1';
function getCalculatedCatalog() {
  try {
    const saved = JSON.parse(localStorage.getItem(SF_CALC_KEY) || '{}');
    return CALCULATED_CATALOG_DEFAULT.map(c => ({ ...c, formula: saved[c.key] || c.formula }));
  } catch { return CALCULATED_CATALOG_DEFAULT; }
}
function saveCalcFormula(key, formula) {
  try {
    const saved = JSON.parse(localStorage.getItem(SF_CALC_KEY) || '{}');
    saved[key] = formula;
    localStorage.setItem(SF_CALC_KEY, JSON.stringify(saved));
  } catch {}
}
const CALCULATED_CATALOG = getCalculatedCatalog();

/* Compat: defaultFields mantido para template download */
const defaultFields = Object.fromEntries(
  Object.values(FIELD_CATALOG).flatMap(g => Object.entries(g.fields).map(([k, v]) => [k, { label: v, visible: true }]))
);

/* ── Estado ──────────────────────────────────────────── */
let clients     = [];
let licenses    = [];
let imports     = [];
let usuarios    = [];
let selectedClient  = null;
let selectedUsuario = null;

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
/* ═══════════════════════════════════════════════════════
   ENVIO PDF
   ═══════════════════════════════════════════════════════ */
function loadPdfSection() {
  populateClientSelects();
  $('pdfConfigPanel')?.classList.add('hidden');
  $('pdfDestinatariosList').innerHTML = '';
  loadEmailLog(null);
}

$('pdfClient')?.addEventListener('change', async () => {
  const tenantId = $('pdfClient').value;
  const panel = $('pdfConfigPanel');
  if (!tenantId) { panel.classList.add('hidden'); return; }

  // Limpa para não mostrar dados do cliente anterior enquanto carrega
  $('pdfNRetratos').value  = 8;
  $('pdfAtivo').checked    = true;
  $('pdfDestinatariosList').innerHTML = '';
  panel.classList.remove('hidden');

  // Carrega config existente do cliente selecionado
  try {
    const cfg = await window.QTQD_API_CLIENT.getPdfConfig(getToken(), tenantId);
    if (cfg) {
      $('pdfNRetratos').value = cfg.n_retratos ?? 8;
      $('pdfAtivo').checked   = cfg.ativo ?? true;
    }
  } catch {}

  // Lista destinatários do cliente
  try {
    const usrs = await window.QTQD_API_CLIENT.listUsuarios(getToken(), tenantId);
    const list  = $('pdfDestinatariosList');
    list.innerHTML = '';
    const ativos = usrs.filter(u => u.ativo);
    if (!ativos.length) { list.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhum usuário ativo.</p>'; }
    else ativos.forEach(u => {
      const card = el('article', 'entity-card');
      card.innerHTML = `
        <div class="entity-card-row">
          <strong>${u.nome}</strong>
          <span class="badge ${u.permissao}">${PERMISSAO_LABEL[u.permissao] || u.permissao}</span>
        </div>
        <span style="font-size:12px;color:var(--muted)">${u.email}</span>`;
      list.appendChild(card);
    });
  } catch {}

  loadEmailLog(tenantId);
});

$('savePdfConfigBtn')?.addEventListener('click', async () => {
  const tenantId = $('pdfClient').value;
  if (!tenantId) { fb('Selecione um cliente.', 'error'); return; }
  const payload = {
    n_retratos: parseInt($('pdfNRetratos').value || '8'),
    ativo:      $('pdfAtivo').checked,
  };
  try {
    await window.QTQD_API_CLIENT.savePdfConfig(getToken(), tenantId, payload);
    fb('Configuração de envio salva.', 'success');
  } catch (e) { fb('Erro: ' + e.message, 'error'); }
});

$('sendNowBtn')?.addEventListener('click', async () => {
  const tenantId = $('pdfClient').value;
  if (!tenantId) { fb('Selecione um cliente.', 'error'); return; }
  const emailTeste = ($('pdfEmailTeste')?.value || '').trim();
  const clientNome = clients.find(c => c.id === tenantId)?.nome || 'cliente';
  const dest = emailTeste ? `apenas para ${emailTeste}` : `todos os usuários de "${clientNome}"`;
  if (!confirm(`Enviar relatório para ${dest}?`)) return;
  fb('Enviando...', 'info');
  try {
    const res = await window.QTQD_API_CLIENT.enviarRelatorio(getToken(), tenantId, emailTeste || null);
    fb(`✓ Relatório enviado para ${res.enviado_para?.join(', ') || '?'}.`, 'success');
  } catch (e) { fb('Erro ao enviar: ' + e.message, 'error'); }
});

$('downloadPdfBtn')?.addEventListener('click', async () => {
  const tenantId = $('pdfClient').value;
  if (!tenantId) { fb('Selecione um cliente.', 'error'); return; }
  fb('Gerando PDF...', 'info');
  try {
    await window.QTQD_API_CLIENT.downloadPdf(getToken(), tenantId);
    fb('✓ PDF gerado e baixado.', 'success');
  } catch (e) { fb('Erro ao gerar PDF: ' + e.message, 'error'); }
});

/* ── Log de e-mails ──────────────────────────────────── */
const ORIGEM_LABEL = { fechar: 'Fechar lançamento', finalizar: 'Finalizar', reenviar: 'Reenviar', admin: 'Admin (manual)' };

async function loadEmailLog(tenantId) {
  const container = $('emailLogContainer');
  if (!container) return;
  container.innerHTML = '<p style="color:var(--muted);font-size:13px">Carregando...</p>';
  try {
    const logs = await window.QTQD_API_CLIENT.getEmailLog(getToken(), tenantId || null);
    if (!logs.length) {
      container.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhum envio registrado.</p>';
      return;
    }
    const rows = logs.map(l => {
      const data = new Date(l.enviado_em).toLocaleString('pt-BR');
      const dest = (l.destinatarios || []).join(', ') || '—';
      const badge = l.status === 'success'
        ? `<span class="badge ativo" style="font-size:11px">✓ Enviado</span>`
        : `<span class="badge cancelado" style="font-size:11px">✗ Erro</span>`;
      const erroHtml = l.erro ? `<br><span style="font-size:11px;color:var(--muted)">${l.erro}</span>` : '';
      const origem = ORIGEM_LABEL[l.origem] || l.origem || '—';
      const c = clients.find(c => c.id === l.tenant_id);
      const clienteNome = c ? c.nome : (l.tenant_id || '').substring(0, 8) + '…';
      return `<tr>
        <td style="padding:8px 12px;font-size:12px;white-space:nowrap">${data}</td>
        <td style="padding:8px 12px;font-size:12px">${clienteNome}</td>
        <td style="padding:8px 12px;font-size:12px">${origem}</td>
        <td style="padding:8px 12px;font-size:12px;max-width:260px">${dest}</td>
        <td style="padding:8px 12px">${badge}${erroHtml}</td>
      </tr>`;
    }).join('');
    container.innerHTML = `<table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:var(--surface-2);text-align:left">
          <th style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--muted)">Data/Hora</th>
          <th style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--muted)">Cliente</th>
          <th style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--muted)">Origem</th>
          <th style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--muted)">Destinatários</th>
          <th style="padding:8px 12px;font-size:11px;font-weight:600;color:var(--muted)">Status</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
  } catch (e) {
    container.innerHTML = `<p style="color:var(--muted);font-size:13px">Erro ao carregar log: ${e.message}</p>`;
  }
}

$('refreshEmailLogBtn')?.addEventListener('click', () => {
  loadEmailLog($('pdfClient')?.value || null);
});

const SECTION_META = {
  clientes:   { eyebrow: 'Cadastro Comercial',  title: 'Clientes da plataforma' },
  vigencias:  { eyebrow: 'Licenciamento',        title: 'Vigências e controle de acesso' },
  campos:     { eyebrow: 'Configuração',         title: 'Campos do formulário' },
  importacao: { eyebrow: 'Primeira Carga',       title: 'Importação de dados' },
  enviopdf:   { eyebrow: 'Comunicação',          title: 'Envio de relatório por e-mail' },
  usuarios:   { eyebrow: 'Acesso ao Sistema',    title: 'Usuários do cliente' },
  identidade: { eyebrow: 'Identidade Visual',    title: 'Branding por cliente' },
  admins:     { eyebrow: 'Controle de Acesso',   title: 'Administradores do sistema' },
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
  if (id === 'usuarios')   loadUsuarios();
  if (id === 'enviopdf')   loadPdfSection();
  if (id === 'identidade') loadBranding();
  if (id === 'admins')     loadAdmins();
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
      <span style="font-size:11px;color:var(--muted)">${c.contato_email || ''}</span>
      <button class="btn btn-sm" data-portal-tenant="${c.id}" data-portal-nome="${c.nome}"
        style="margin-top:8px;width:100%;font-size:12px" type="button">Acessar Portal</button>`;
    card.addEventListener('click', e => { if (!e.target.closest('[data-portal-tenant]')) selectClient(c); });
    list.appendChild(card);
  });

  // Delegação do botão Acessar Portal
  list.querySelectorAll('[data-portal-tenant]').forEach(btn => {
    btn.addEventListener('click', async e => {
      e.stopPropagation();
      const tenantId = btn.dataset.portalTenant;
      const nome     = btn.dataset.portalNome;
      btn.disabled = true;
      btn.textContent = 'Abrindo...';
      try {
        const res = await window.QTQD_API_CLIENT.abrirPortal(getToken(), tenantId);
        const url = `https://qtqd-vt2a.vercel.app/cliente?token=${encodeURIComponent(res.access_token)}&tenant_id=${encodeURIComponent(res.tenant_id)}`;
        window.open(url, '_blank');
        fb(`Portal de ${nome} aberto em nova aba.`, 'success');
      } catch (err) {
        fb(`Erro ao abrir portal: ${err.message}`, 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Acessar Portal';
      }
    });
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
  ['licenseClient', 'importClient', 'brandingClient', 'camposClient', 'templateClient',
   'usuarioClient', 'usuarioClientFilter', 'pdfClient'].forEach(id => {
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
   USUÁRIOS
   ═══════════════════════════════════════════════════════ */
const PERMISSAO_LABEL = { edita: 'Edita', visualiza: 'Visualiza', relatorio: 'Relatório' };

async function loadUsuarios() {
  const tenantId = $('usuarioClientFilter')?.value || '';
  try {
    usuarios = await window.QTQD_API_CLIENT.listUsuarios(getToken(), tenantId || undefined);
    renderUsuarios();
  } catch (e) { fb('Erro ao carregar usuários: ' + e.message, 'error'); }
}

function renderUsuarios() {
  const list = $('usuarioList');
  if (!list) return;
  if (!usuarios.length) { list.innerHTML = '<p style="color:var(--muted);font-size:13px">Nenhum usuário cadastrado.</p>'; return; }
  list.innerHTML = '';
  /* Auto-seleciona quando só há um usuário na lista */
  if (usuarios.length === 1 && !selectedUsuario) { selectUsuario(usuarios[0]); return; }
  usuarios.forEach(u => {
    const client = clients.find(c => c.id === String(u.tenant_id));
    const card = el('article', 'entity-card' + (selectedUsuario?.id === u.id ? ' selected' : ''));
    const badgeCls = u.ativo ? '' : 'bloqueado';
    card.innerHTML = `
      <div class="entity-card-row">
        <strong>${u.nome}</strong>
        <span class="badge ${u.permissao}">${PERMISSAO_LABEL[u.permissao] || u.permissao}</span>
      </div>
      <span>${u.funcao || '—'} · ${client?.nome || u.tenant_id}</span>
      <div class="entity-card-row">
        <span style="font-size:11px;color:var(--muted)">${u.email}</span>
        ${!u.ativo ? '<span class="badge bloqueado">inativo</span>' : ''}
      </div>`;
    card.addEventListener('click', () => selectUsuario(u));
    list.appendChild(card);
  });
}

function selectUsuario(u) {
  selectedUsuario = u;
  $('usuarioId').value       = u.id;
  $('usuarioClient').value   = String(u.tenant_id);
  $('usuarioNome').value     = u.nome;
  $('usuarioFuncao').value   = u.funcao || '';
  $('usuarioEmail').value    = u.email;
  $('usuarioPermissao').value = u.permissao;
  $('usuarioModeBadge').textContent = 'Editando';
  $('deleteUsuarioButton').classList.remove('hidden');
  const actions = $('usuarioActions');
  if (actions) {
    actions.classList.remove('hidden');
    actions.style.display = 'flex';
    $('btnInativar').textContent = u.ativo ? '⛔ Inativar' : '✅ Reativar';
  }
  renderUsuarios();
}

function resetUsuarioForm() {
  selectedUsuario = null;
  usuarios = [];  // evita auto-select com dados obsoletos antes do próximo loadUsuarios()
  $('usuarioId').value = '';
  $('usuarioForm').reset();
  $('usuarioModeBadge').textContent = 'Novo';
  $('deleteUsuarioButton').classList.add('hidden');
  const actions = $('usuarioActions');
  if (actions) { actions.classList.add('hidden'); actions.style.display = 'none'; }
  renderUsuarios();
}

$('usuarioForm').addEventListener('submit', async e => {
  e.preventDefault(); fbClear();
  const id = $('usuarioId').value;
  const payload = {
    tenant_id:  $('usuarioClient').value,
    nome:       $('usuarioNome').value.trim(),
    funcao:     $('usuarioFuncao').value.trim() || null,
    email:      $('usuarioEmail').value.trim(),
    permissao:  $('usuarioPermissao').value,
  };
  try {
    if (id) {
      const { tenant_id, email, ...upd } = payload;
      await window.QTQD_API_CLIENT.updateUsuario(getToken(), id, upd);
      fb('Usuário atualizado.', 'success');
    } else {
      if (!payload.tenant_id) { fb('Selecione um cliente.', 'error'); return; }
      await window.QTQD_API_CLIENT.createUsuario(getToken(), payload);
      fb('Usuário cadastrado. Envie o convite para ele instalar o sistema.', 'success');
    }
    resetUsuarioForm();
    await loadUsuarios();
  } catch (err) { fb('Erro ao salvar: ' + err.message, 'error'); }
});

$('clearUsuarioFormButton')?.addEventListener('click', resetUsuarioForm);

$('deleteUsuarioButton')?.addEventListener('click', async () => {
  if (!selectedUsuario) return;
  if (!confirm(`Excluir o usuário "${selectedUsuario.nome}"?`)) return;
  try {
    await window.QTQD_API_CLIENT.deleteUsuario(getToken(), selectedUsuario.id);
    fb('Usuário excluído.', 'success');
    resetUsuarioForm();
    await loadUsuarios();
  } catch (err) { fb('Erro ao excluir: ' + err.message, 'error'); }
});

$('btnInativar')?.addEventListener('click', async () => {
  if (!selectedUsuario) return;
  const novoStatus = !selectedUsuario.ativo;
  const acao = novoStatus ? 'reativar' : 'inativar';
  if (!confirm(`Deseja ${acao} o usuário "${selectedUsuario.nome}"?`)) return;
  try {
    await window.QTQD_API_CLIENT.updateUsuario(getToken(), selectedUsuario.id, { ativo: novoStatus });
    fb(`Usuário ${novoStatus ? 'reativado' : 'inativado'}.`, 'success');
    resetUsuarioForm();
    await loadUsuarios();
  } catch (err) { fb('Erro: ' + err.message, 'error'); }
});

$('btnResetSenha')?.addEventListener('click', () => {
  if (!selectedUsuario) { fb('Selecione um usuário na lista primeiro.', 'error'); return; }
  alert(`Para resetar a senha de "${selectedUsuario.nome}", acesse o Supabase Dashboard > Authentication > Users, localize o e-mail "${selectedUsuario.email}" e clique em "Send password reset".\n\nEm breve essa ação será automática pelo painel.`);
});

$('btnConviteApp')?.addEventListener('click', async () => {
  if (!selectedUsuario) { fb('Selecione um usuário na lista antes de enviar o convite.', 'error'); return; }
  if (!confirm(`Enviar convite de instalação para "${selectedUsuario.nome}" (${selectedUsuario.email})?`)) return;
  fb('Enviando convite...', 'info');
  try {
    await window.QTQD_API_CLIENT.enviarConvite(getToken(), selectedUsuario.id);
    fb(`✓ Convite enviado para ${selectedUsuario.email} via comercial@servicefarma.far.br`, 'success');
  } catch (e) { fb('Erro ao enviar convite: ' + e.message, 'error'); }
});

$('usuarioClientFilter')?.addEventListener('change', loadUsuarios);

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

  // Monta linhas: cabeçalho + data + campos financeiros
  const rows = [
    header,
    ['Data (DD/MM/AAAA)', ...Array(weeks).fill('')],
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
  const tenantId  = $('importClient').value;
  const fileInput = $('importFile');
  const file      = fileInput.files[0];
  if (!tenantId) { fb('Selecione um cliente destino.', 'error'); return; }
  if (!file)     { fb('Selecione o arquivo Excel preenchido.', 'error'); return; }

  fb('Processando planilha...', 'info');
  try {
    const res = await window.QTQD_API_CLIENT.processarExcel(getToken(), tenantId, file);
    let msg = `✓ ${res.criadas} avaliação(ões) importada(s) com sucesso.`;
    if (res.ignoradas) msg += ` ${res.ignoradas} já existiam (ignoradas).`;
    if (res.erros?.length) msg += ` ⚠️ ${res.erros.length} erro(s).`;
    fb(msg, res.erros?.length ? 'error' : 'success');
    $('importForm').reset();
    await loadImports();
  } catch (err) { fb('Erro ao processar: ' + err.message, 'error'); }
});

/* ═══════════════════════════════════════════════════════
   CAMPOS
   ═══════════════════════════════════════════════════════ */
let _camposApiConfig = null; // cache da config atual

function getLocalFieldConfig() {
  try { return { ...defaultFields, ...JSON.parse(localStorage.getItem(FIELD_KEY) || '{}') }; }
  catch { return { ...defaultFields }; }
}

function _buildConfigMap(apiConfig) {
  const map = {};
  if (apiConfig) apiConfig.forEach(c => { map[c.codigo_componente] = c; });
  return map;
}

function renderFieldConfig(apiConfig = null) {
  _camposApiConfig = apiConfig;
  const list = $('fieldConfigList');
  if (!list) return;
  const configMap = _buildConfigMap(apiConfig);
  list.innerHTML = '';

  // ── Grupos de campos editáveis ─────────────────────────
  Object.entries(FIELD_CATALOG).forEach(([groupKey, group]) => {
    const groupDiv = el('div', 'field-group');

    // Cabeçalho do grupo
    const hdr = el('div', 'field-group-header');
    hdr.innerHTML = `<span class="eyebrow">${group.label}</span>`;
    const addBtn = document.createElement('button');
    addBtn.className = 'secondary-button';
    addBtn.style.cssText = 'padding:4px 10px;font-size:11px';
    addBtn.textContent = '+ Novo campo';
    addBtn.addEventListener('click', () => toggleAddFieldForm(groupKey));
    hdr.appendChild(addBtn);
    groupDiv.appendChild(hdr);

    // Campos do catálogo
    Object.entries(group.fields).forEach(([key, defaultLabel]) => {
      const cfg    = configMap[key];
      const visible = cfg ? cfg.visivel !== false : true;
      const label   = cfg?.label_customizado || defaultLabel;
      groupDiv.appendChild(_makeFieldRow(key, label, defaultLabel, visible, false));
    });

    // Campos personalizados do grupo (prefix: custom_<group>_)
    if (apiConfig) {
      apiConfig.filter(c => c.codigo_componente.startsWith(`custom_${groupKey}_`)).forEach(c => {
        groupDiv.appendChild(_makeFieldRow(c.codigo_componente, c.label_customizado || '', c.label_customizado || '', true, true));
      });
    }

    // Formulário inline "Novo campo"
    const addForm = el('div', 'add-field-form');
    addForm.id = `addFieldForm_${groupKey}`;
    addForm.innerHTML = `
      <div class="add-field-form-row">
        <label class="field">
          <span>Nome do campo</span>
          <input type="text" id="newFieldLabel_${groupKey}" placeholder="Ex.: Cartão Crédito Loja">
        </label>
        <button class="primary-button" type="button" data-add-group="${groupKey}" style="margin-top:18px;white-space:nowrap">Adicionar</button>
        <button class="secondary-button" type="button" data-cancel-group="${groupKey}" style="margin-top:18px">Cancelar</button>
      </div>`;
    addForm.querySelector(`[data-add-group]`).addEventListener('click', () => addCustomField(groupKey));
    addForm.querySelector(`[data-cancel-group]`).addEventListener('click', () => toggleAddFieldForm(groupKey));
    groupDiv.appendChild(addForm);

    list.appendChild(groupDiv);
  });

  // ── Campos calculados (fórmula editável como descrição) ─
  const calcDiv = el('div', 'field-group');
  const calcHdr = el('div', 'field-group-header');
  calcHdr.innerHTML = '<span class="eyebrow">Campos Calculados — fórmula editável como descrição</span>';
  calcDiv.appendChild(calcHdr);
  getCalculatedCatalog().forEach(calc => {
    const row = el('div', 'field-config-item field-config-formula');
    row.innerHTML = `
      <div style="flex:1;min-width:0">
        <span style="font-size:13px;font-weight:700;color:var(--ink)">${calc.label}</span>
        <span class="key-tag" style="margin-left:6px">${calc.key}</span>
      </div>
      <input type="text" class="formula-input" data-calc-key="${calc.key}" value="${calc.formula.replace(/"/g,'&quot;')}" placeholder="Descrição da fórmula" style="flex:2;font-size:12px">
      <span class="badge">calculado</span>`;
    row.querySelector('.formula-input').addEventListener('change', e => {
      saveCalcFormula(calc.key, e.target.value);
      fb('Descrição da fórmula atualizada.', 'success');
    });
    calcDiv.appendChild(row);
  });
  list.appendChild(calcDiv);
}

function _makeFieldRow(key, label, placeholder, visible, isCustom) {
  const row = el('div', 'field-config-item');
  row.innerHTML = `
    <label>
      <input type="checkbox" data-key="${key}" ${visible ? 'checked' : ''}>
      <span class="key-tag">${key}${isCustom ? ' <span class="badge warn">custom</span>' : ''}</span>
    </label>
    <input type="text" data-label="${key}" value="${label}" placeholder="${placeholder}">
    ${isCustom ? `<button class="danger-button" data-delete="${key}" style="padding:4px 10px;font-size:11px;flex-shrink:0">✕</button>` : ''}`;
  if (isCustom) {
    row.querySelector('[data-delete]').addEventListener('click', () => deleteCustomField(key));
  }
  return row;
}

function toggleAddFieldForm(groupKey) {
  const form = document.getElementById(`addFieldForm_${groupKey}`);
  if (form) form.classList.toggle('visible');
}

async function addCustomField(groupKey) {
  const tenantId = $('camposClient')?.value;
  if (!tenantId) { fb('Selecione um cliente antes de criar um campo personalizado.', 'error'); return; }
  const labelInput = document.getElementById(`newFieldLabel_${groupKey}`);
  const label = labelInput?.value.trim();
  if (!label) { fb('Informe o nome do campo.', 'error'); return; }
  const slug = label.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
  const key  = `custom_${groupKey}_${slug}`;
  try {
    await window.QTQD_API_CLIENT.saveComponentesConfig(getToken(), tenantId, [{
      codigo_componente: key, label_customizado: label, visivel: true, obrigatorio: false, ordem_exibicao: 999,
    }]);
    fb(`Campo "${label}" adicionado ao grupo ${FIELD_CATALOG[groupKey].label}.`, 'success');
    await loadCamposConfig();
  } catch (e) { fb('Erro ao criar campo: ' + e.message, 'error'); }
}

async function deleteCustomField(key) {
  if (!confirm(`Excluir o campo "${key}"? Esta ação não pode ser desfeita.`)) return;
  const tenantId = $('camposClient')?.value;
  if (!tenantId || !_camposApiConfig) return;
  const remaining = _camposApiConfig.filter(c => c.codigo_componente !== key);
  try {
    if (remaining.length) {
      await window.QTQD_API_CLIENT.saveComponentesConfig(getToken(), tenantId,
        remaining.map(c => ({ codigo_componente: c.codigo_componente, label_customizado: c.label_customizado, visivel: c.visivel, obrigatorio: c.obrigatorio, ordem_exibicao: c.ordem_exibicao }))
      );
    }
    fb('Campo excluído.', 'success');
    await loadCamposConfig();
  } catch (e) { fb('Erro ao excluir: ' + e.message, 'error'); }
}

async function loadCamposConfig() {
  const tenantId = $('camposClient')?.value;
  if (!tenantId) { renderFieldConfig(null); return; }
  try {
    const data = await window.QTQD_API_CLIENT.getComponentesConfig(getToken(), tenantId);
    renderFieldConfig(data);
    fb('Configuração carregada para este cliente.', 'success');
  } catch (e) {
    renderFieldConfig(null);
    fb('Erro ao carregar campos: ' + e.message, 'error');
  }
}

function _collectFieldItens() {
  const itens = [];
  let idx = 0;
  document.querySelectorAll('#fieldConfigList .field-config-item:not(.field-config-formula)').forEach(row => {
    const cb  = row.querySelector('input[type="checkbox"]');
    const inp = row.querySelector('input[type="text"]');
    if (!cb || !inp) return;
    const key = cb.dataset.key;
    if (!key) return;
    const defaultLabel = defaultFields[key]?.label || key;
    itens.push({ codigo_componente: key, label_customizado: inp.value.trim() || defaultLabel, visivel: cb.checked, obrigatorio: false, ordem_exibicao: ++idx });
  });
  return itens;
}

function fbCampos(msg, type = 'info') {
  fb(msg, type);
  const el = $('feedbackCampos');
  if (!el) return;
  el.textContent = msg;
  el.className = 'feedback-box' + (type === 'error' ? ' error' : type === 'success' ? ' success' : '');
  el.classList.remove('hidden');
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

$('saveFieldConfigButton').addEventListener('click', async () => {
  const tenantId = $('camposClient')?.value;
  const itens    = _collectFieldItens();
  if (tenantId) {
    try {
      await window.QTQD_API_CLIENT.saveComponentesConfig(getToken(), tenantId, itens);
      fbCampos(`✓ Configuração salva com sucesso para ${itens.length} campos.`, 'success');
    } catch (e) { fbCampos('Erro ao salvar: ' + e.message, 'error'); }
  } else {
    const cfg = {};
    itens.forEach(i => { cfg[i.codigo_componente] = { label: i.label_customizado, visible: i.visivel }; });
    localStorage.setItem(FIELD_KEY, JSON.stringify(cfg));
    fbCampos('Configuração padrão salva localmente (nenhum cliente selecionado).', 'success');
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
let currentLogoUrl = '';

async function loadBranding() {
  const tenantId = $('brandingClient')?.value;
  if (!tenantId) return;
  try {
    const data = await window.QTQD_API_CLIENT.getBranding(getToken(), tenantId);
    currentLogoUrl = data?.logo_cliente_url || '';
    if (data) {
      $('brandingClientName').value = data.nome_portal || '';
      updateBrandingPreview(data.nome_portal || '', currentLogoUrl);
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

// Preview local do arquivo selecionado antes de salvar (chamado via onchange no HTML)
window.previewLogoFile = function(input) {
  const file = input.files?.[0];
  if (!file) return;
  const previewLogo = document.getElementById('brandingPreviewLogo');
  const previewFb   = document.getElementById('brandingPreviewFallback');
  if (previewLogo) {
    previewLogo.src = URL.createObjectURL(file);
    previewLogo.classList.add('visible');
    previewLogo.style.display = 'block';
  }
  if (previewFb) previewFb.style.display = 'none';
};

$('brandingForm').addEventListener('submit', async e => {
  e.preventDefault(); fbClear();
  const tenantId = $('brandingClient')?.value;
  if (!tenantId) { fb('Selecione um cliente.', 'error'); return; }

  let logoUrl = currentLogoUrl;
  const fileInput = $('brandingClientLogo');
  if (fileInput?.files?.length) {
    try {
      fb('Enviando logo...', 'info');
      const res = await window.QTQD_API_CLIENT.uploadLogo(getToken(), tenantId, fileInput.files[0]);
      logoUrl = res.url;
    } catch (err) {
      fb('Erro ao enviar logo: ' + err.message, 'error');
      return;
    }
  }

  const payload = {
    nome_portal:      $('brandingClientName').value.trim() || null,
    logo_cliente_url: logoUrl || null,
    powered_by_label: 'Powered by Service Farma',
  };
  try {
    await window.QTQD_API_CLIENT.saveBranding(getToken(), tenantId, payload);
    currentLogoUrl = logoUrl || '';
    if (fileInput) fileInput.value = '';
    fb('Identidade visual salva com sucesso.', 'success');
    updateBrandingPreview(payload.nome_portal || '', currentLogoUrl);
  } catch (err) { fb('Erro ao salvar branding: ' + err.message, 'error'); }
});

$('resetBrandingButton')?.addEventListener('click', () => {
  $('brandingForm').reset();
  currentLogoUrl = '';
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
   ADMINS
   ═══════════════════════════════════════════════════════ */
let adminsData = [];

async function loadAdmins() {
  try {
    adminsData = await window.QTQD_API_CLIENT.listAdmins(getToken());
    renderAdmins();
  } catch (e) { fb('Erro ao carregar admins: ' + e.message, 'error'); }
}

function renderAdmins() {
  const list = $('adminsList');
  const count = $('adminsCount');
  if (!list) return;

  if (count) count.textContent = `${adminsData.length} admin(s)`;

  if (!adminsData.length) {
    list.innerHTML = '<p style="color:var(--muted);font-size:13px;padding:8px 0">Nenhum admin cadastrado.</p>';
    return;
  }

  list.innerHTML = adminsData.map(a => {
    const criado = a.created_at ? new Date(a.created_at).toLocaleDateString('pt-BR') : '—';
    const badges = [
      a.is_master ? '<span class="badge ativo" style="font-size:10px">master</span>' : '',
      !a.ativo    ? '<span class="badge cancelado" style="font-size:10px">revogado</span>' : '',
    ].filter(Boolean).join(' ');
    const acoes = a.is_master ? '' : `
      <div class="action-row" style="margin-top:8px">
        ${a.ativo
          ? `<button class="action-btn" type="button" onclick="revogarAdmin('${a.id}','${a.email}')">Revogar</button>`
          : `<button class="action-btn" type="button" onclick="reativarAdmin('${a.id}','${a.email}')">Reativar</button>`
        }
        <button class="action-btn action-btn--danger" type="button" onclick="excluirAdmin('${a.id}','${a.email}')">Excluir</button>
      </div>`;
    return `
      <article class="entity-card" style="opacity:${a.ativo ? 1 : 0.6}">
        <div class="entity-card-row">
          <strong>${a.nome || a.email}</strong>
          ${badges}
        </div>
        <span style="font-size:12px;color:var(--muted)">${a.email}</span>
        <span style="font-size:11px;color:var(--muted)">Desde ${criado}</span>
        ${acoes}
      </article>`;
  }).join('');
}

async function revogarAdmin(id, email) {
  if (!confirm(`Revogar acesso de ${email}?`)) return;
  try {
    await window.QTQD_API_CLIENT.revogarAdmin(getToken(), id);
    fb(`Acesso de ${email} revogado.`, 'success');
    await loadAdmins();
  } catch (e) { fb('Erro: ' + e.message, 'error'); }
}

async function reativarAdmin(id, email) {
  try {
    await window.QTQD_API_CLIENT.reativarAdmin(getToken(), id);
    fb(`Acesso de ${email} reativado.`, 'success');
    await loadAdmins();
  } catch (e) { fb('Erro: ' + e.message, 'error'); }
}

async function excluirAdmin(id, email) {
  if (!confirm(`Excluir permanentemente o admin ${email}? Esta ação não pode ser desfeita.`)) return;
  try {
    await window.QTQD_API_CLIENT.excluirAdmin(getToken(), id);
    fb(`Admin ${email} excluído.`, 'success');
    await loadAdmins();
  } catch (e) { fb('Erro: ' + e.message, 'error'); }
}

$('adminConviteForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const email = $('adminConviteEmail').value.trim();
  const nome  = $('adminConviteNome').value.trim();
  if (!email) return;
  try {
    await window.QTQD_API_CLIENT.convidarAdmin(getToken(), { email, nome: nome || null });
    fb(`Convite enviado para ${email}.`, 'success');
    $('adminConviteForm').reset();
    await loadAdmins();
  } catch (e) { fb('Erro: ' + e.message, 'error'); }
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

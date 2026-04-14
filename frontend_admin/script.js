const storageKey = "qtqd_admin_demo_v1";
const FIELD_CONFIG_KEY = "qtqd_field_config_v1";
const BRANDING_KEY = "qtqd_branding_v1";
const THEME_KEY = "qtqd_admin_theme";
const RUNTIME_CONFIG_KEY = window.QTQD_APP_CONFIG?.runtimeConfigKey || "qtqd_runtime_config_v1";
const ADMIN_TOKEN_KEY = window.QTQD_APP_CONFIG?.adminTokenStorageKey || "qtqd_admin_token_v1";

const defaultFieldConfig = {
  saldo_bancario: { label: "Saldo bancário", visible: true },
  contas_receber: { label: "Contas a receber", visible: true },
  cartoes: { label: "Cartões", visible: true },
  convenios: { label: "Convênios", visible: true },
  cheques: { label: "Cheques", visible: true },
  trade_marketing: { label: "Trade marketing", visible: true },
  outros_qt: { label: "Outros", visible: true },
  estoque_custo: { label: "Estoque (preço custo)", visible: true },
  contas_pagar: { label: "Contas a pagar", visible: true },
  fornecedores: { label: "Fornecedores", visible: true },
  investimentos_assumidos: { label: "Investimentos assumidos", visible: true },
  outras_despesas_assumidas: { label: "Outras despesas assumidas", visible: true },
  dividas: { label: "Dívidas", visible: true },
  financiamentos: { label: "Financiamentos", visible: true },
  tributos_atrasados: { label: "Tributos atrasados", visible: true },
  acoes_processos: { label: "Ações e processos", visible: true },
  faturamento_previsto_mes: { label: "Faturamento previsto no mês", visible: true },
  compras_mes: { label: "Compras no mês", visible: true },
  entrada_mes: { label: "Entrada no mês", visible: true },
  venda_cupom_mes: { label: "Venda cupom no mês", visible: true },
  venda_custo_mes: { label: "Venda custo no mês - CMV", visible: true },
  lucro_liquido_mes: { label: "Lucro líquido - mês", visible: true },
};

const defaultBranding = {
  clientName: "Cliente Demonstração",
  clientLogoUrl: "",
};

const feedbackBox = document.getElementById("feedbackBox");
const clientList = document.getElementById("clientList");
const licenseList = document.getElementById("licenseList");
const importList = document.getElementById("importList");
const fieldConfigList = document.getElementById("fieldConfigList");
const licenseClient = document.getElementById("licenseClient");
const importClient = document.getElementById("importClient");
const clientModeBadge = document.getElementById("clientModeBadge");
const brandingPreviewLogo = document.getElementById("brandingPreviewLogo");
const brandingPreviewFallback = document.getElementById("brandingPreviewFallback");
const brandingPreviewName = document.getElementById("brandingPreviewName");

let state = {};

function getRuntimeConfig() {
  try {
    return { ...(window.QTQD_APP_CONFIG || {}), ...JSON.parse(localStorage.getItem(RUNTIME_CONFIG_KEY) || "{}") };
  } catch {
    return { ...(window.QTQD_APP_CONFIG || {}) };
  }
}

function saveRuntimeConfig(config) {
  localStorage.setItem(RUNTIME_CONFIG_KEY, JSON.stringify(config));
  window.QTQD_APP_CONFIG = { ...(window.QTQD_APP_CONFIG || {}), ...config };
}

function getAdminToken() {
  return localStorage.getItem(ADMIN_TOKEN_KEY) || "";
}

function saveAdminToken(token) {
  localStorage.setItem(ADMIN_TOKEN_KEY, token || "");
}

function isApiMode() {
  return getRuntimeConfig().mode === "api" && window.QTQD_API_CLIENT;
}

function demoState() {
  return {
    clients: [
      {
        id: crypto.randomUUID(),
        name: "Cliente Demonstração",
        slug: "cliente-demo",
        status: "ativo",
        plan: "premium",
        contact: "Andre Vanni",
        email: "andre@servicefarma.far.br",
      },
      {
        id: crypto.randomUUID(),
        name: "Rede Exemplo Sul",
        slug: "rede-exemplo-sul",
        status: "implantacao",
        plan: "enterprise",
        contact: "Raquel",
        email: "raquel@cliente.com.br",
      },
    ],
    licenses: [
      {
        id: crypto.randomUUID(),
        clientName: "Cliente Demonstração",
        clientId: "",
        plan: "premium",
        start: "2026-04-01",
        end: "2027-04-01",
        status: "ativo",
      },
    ],
    imports: [
      {
        id: crypto.randomUUID(),
        clientName: "Cliente Demonstração",
        filename: "QTQD.xlsx",
        status: "base inicial carregada na simulação",
        notes: "Histórico inicial do cliente extraído da planilha real do projeto",
        createdAt: "13/04/2026 09:10",
      },
    ],
  };
}

function saveState() {
  localStorage.setItem(storageKey, JSON.stringify(state));
}

function loadState() {
  const raw = localStorage.getItem(storageKey);
  if (!raw) {
    state = demoState();
    state.licenses[0].clientId = state.clients[0].id;
    saveState();
    return;
  }

  try {
    state = JSON.parse(raw);
  } catch {
    state = demoState();
    state.licenses[0].clientId = state.clients[0].id;
    saveState();
  }
}

function getFieldConfig() {
  try {
    return { ...defaultFieldConfig, ...JSON.parse(localStorage.getItem(FIELD_CONFIG_KEY) || "{}") };
  } catch {
    return { ...defaultFieldConfig };
  }
}

function saveFieldConfig(config) {
  localStorage.setItem(FIELD_CONFIG_KEY, JSON.stringify(config));
}

function getBranding() {
  try {
    return { ...defaultBranding, ...JSON.parse(localStorage.getItem(BRANDING_KEY) || "{}") };
  } catch {
    return { ...defaultBranding };
  }
}

function saveBranding(branding) {
  localStorage.setItem(BRANDING_KEY, JSON.stringify(branding));
}

function applyTheme(themeName = localStorage.getItem(THEME_KEY) || "dark") {
  document.body.dataset.theme = themeName;
  document.querySelectorAll("[data-theme-choice]").forEach((button) => {
    button.classList.toggle("active", button.dataset.themeChoice === themeName);
  });
}

function setFeedback(message) {
  feedbackBox.textContent = message;
  feedbackBox.classList.remove("hidden");
}

function clearFeedback() {
  feedbackBox.textContent = "";
  feedbackBox.classList.add("hidden");
}

function resetClientForm() {
  document.getElementById("clientForm").reset();
  document.getElementById("clientId").value = "";
  document.getElementById("clientPlan").value = "premium";
  clientModeBadge.textContent = "Novo";
}

function clientInitials(name) {
  return String(name || "CL")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("") || "CL";
}

function renderClientOptions() {
  const options = state.clients.map((client) => `<option value="${client.id}">${client.name}</option>`).join("");
  licenseClient.innerHTML = options;
  importClient.innerHTML = options;
}

function renderClients() {
  clientList.innerHTML = state.clients.map((client) => `
    <article class="entity-card">
      <strong>${client.name}</strong>
      <span>${client.slug}</span>
      <div class="entity-meta">
        <span class="chip">${client.status}</span>
        <span class="chip">${client.plan}</span>
        <span class="chip">${client.email || "sem e-mail"}</span>
      </div>
      <button class="action-btn" type="button" data-action="edit-client" data-id="${client.id}">Editar</button>
    </article>
  `).join("");
}

function renderLicenses() {
  licenseList.innerHTML = state.licenses.map((license) => `
    <article class="entity-card">
      <strong>${license.clientName}</strong>
      <span>${license.start} até ${license.end}</span>
      <div class="entity-meta">
        <span class="chip">${license.plan}</span>
        <span class="chip">${license.status}</span>
      </div>
    </article>
  `).join("");
}

function renderImports() {
  importList.innerHTML = state.imports.map((item) => `
    <article class="entity-card">
      <strong>${item.filename}</strong>
      <span>${item.clientName}</span>
      <div class="entity-meta">
        <span class="chip">${item.status}</span>
        <span class="chip">${item.createdAt}</span>
      </div>
      <span>${item.notes || "Sem observações"}</span>
    </article>
  `).join("");
}

function renderFieldConfig() {
  const config = getFieldConfig();
  fieldConfigList.innerHTML = Object.entries(config).map(([key, value]) => `
    <label class="field-config-row">
      <code>${key}</code>
      <input type="text" data-field-label="${key}" value="${value.label}">
      <span class="field-toggle">
        <input type="checkbox" data-field-visible="${key}" ${value.visible !== false ? "checked" : ""}>
        Exibir
      </span>
    </label>
  `).join("");
}

function renderBranding() {
  const branding = getBranding();
  document.getElementById("brandingClientName").value = branding.clientName || "";
  brandingPreviewName.textContent = branding.clientName || defaultBranding.clientName;
  brandingPreviewFallback.textContent = clientInitials(branding.clientName || defaultBranding.clientName);
  if (branding.clientLogoUrl) {
    brandingPreviewLogo.src = branding.clientLogoUrl;
    brandingPreviewLogo.classList.add("visible");
    brandingPreviewFallback.style.display = "none";
  } else {
    brandingPreviewLogo.removeAttribute("src");
    brandingPreviewLogo.classList.remove("visible");
    brandingPreviewFallback.style.display = "grid";
  }
}

function renderAll() {
  renderClientOptions();
  renderClients();
  renderLicenses();
  renderImports();
  renderFieldConfig();
  renderBranding();
  renderRuntimeConfig();
}

function renderRuntimeConfig() {
  const runtime = getRuntimeConfig();
  document.getElementById("runtimeMode").value = runtime.mode || "simulation";
  document.getElementById("runtimeApiBaseUrl").value = runtime.apiBaseUrl || "";
  document.getElementById("runtimeHealthUrl").value = runtime.healthUrl || "";
  document.getElementById("runtimeTenantId").value = runtime.tenantId || "";
  document.getElementById("runtimeAdminToken").value = getAdminToken();
  document.getElementById("runtimeModeLabel").textContent = runtime.mode === "api" ? "API real" : "Simulação";
  document.getElementById("runtimeApiBaseLabel").textContent = runtime.apiBaseUrl || "-";
  document.getElementById("runtimeTenantLabel").textContent = runtime.tenantId || "Não definido";
}

async function loadStateFromApi() {
  const adminToken = getAdminToken();
  if (!adminToken) {
    setFeedback("Defina o token administrativo na área Ambiente para conectar a API.");
    return false;
  }
  const clients = await window.QTQD_API_CLIENT.listClients(adminToken);
  state = {
    ...demoState(),
    clients: clients.map((client) => ({
      id: client.id,
      name: client.nome,
      slug: client.slug,
      status: client.status,
      plan: client.plano,
      contact: client.contato_nome || "",
      email: client.contato_email || "",
    })),
  };
  if (state.clients.length && state.licenses.length) {
    state.licenses[0].clientId = state.clients[0].id;
    state.licenses[0].clientName = state.clients[0].name;
  }
  saveState();
  return true;
}

function showSection(sectionId) {
  document.querySelectorAll(".admin-section").forEach((section) => {
    section.classList.toggle("hidden", section.id !== sectionId);
  });
  document.querySelectorAll(".nav-link").forEach((button) => {
    button.classList.toggle("active", button.dataset.section === sectionId);
  });
}

document.getElementById("clientForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  clearFeedback();

  const payload = {
    id: document.getElementById("clientId").value || crypto.randomUUID(),
    name: document.getElementById("clientName").value,
    slug: document.getElementById("clientSlug").value,
    status: document.getElementById("clientStatus").value,
    plan: document.getElementById("clientPlan").value,
    contact: document.getElementById("clientContact").value,
    email: document.getElementById("clientEmail").value,
  };

  if (isApiMode()) {
    try {
      const adminToken = getAdminToken();
      if (!adminToken) {
        setFeedback("Informe o token administrativo na área Ambiente.");
        return;
      }
      if (document.getElementById("clientId").value) {
        const response = await window.QTQD_API_CLIENT.updateClient(adminToken, payload.id, {
          nome: payload.name,
          slug: payload.slug,
          status: payload.status,
          plano: payload.plan,
          contato_nome: payload.contact,
          contato_email: payload.email || null,
        });
        const index = state.clients.findIndex((item) => item.id === payload.id);
        const normalized = {
          id: response.id,
          name: response.nome,
          slug: response.slug,
          status: response.status,
          plan: response.plano,
          contact: response.contato_nome || "",
          email: response.contato_email || "",
        };
        if (index >= 0) state.clients[index] = normalized;
        setFeedback("Cliente atualizado na API.");
      } else {
        const response = await window.QTQD_API_CLIENT.createClient(adminToken, {
          nome: payload.name,
          slug: payload.slug,
          status: payload.status,
          plano: payload.plan,
          contato_nome: payload.contact,
          contato_email: payload.email || null,
        });
        state.clients.unshift({
          id: response.id,
          name: response.nome,
          slug: response.slug,
          status: response.status,
          plan: response.plano,
          contact: response.contato_nome || "",
          email: response.contato_email || "",
        });
        setFeedback("Cliente cadastrado na API.");
      }
    } catch (error) {
      setFeedback(`Falha ao salvar cliente na API: ${error.message}`);
      return;
    }
  } else {
    const index = state.clients.findIndex((item) => item.id === payload.id);
    if (index >= 0) {
      state.clients[index] = payload;
      setFeedback("Cliente atualizado.");
    } else {
      state.clients.push(payload);
      setFeedback("Cliente cadastrado.");
    }
  }

  saveState();
  renderAll();
  resetClientForm();
});

document.getElementById("clearClientFormButton").addEventListener("click", () => {
  resetClientForm();
  clearFeedback();
});

clientList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action='edit-client']");
  if (!button) return;
  const client = state.clients.find((item) => item.id === button.dataset.id);
  if (!client) return;

  document.getElementById("clientId").value = client.id;
  document.getElementById("clientName").value = client.name;
  document.getElementById("clientSlug").value = client.slug;
  document.getElementById("clientStatus").value = client.status;
  document.getElementById("clientPlan").value = client.plan;
  document.getElementById("clientContact").value = client.contact;
  document.getElementById("clientEmail").value = client.email;
  clientModeBadge.textContent = "Editando";
  showSection("clientes");
});

document.getElementById("licenseForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const client = state.clients.find((item) => item.id === licenseClient.value);
  if (!client) {
    setFeedback("Selecione um cliente para a vigência.");
    return;
  }

  state.licenses.push({
    id: crypto.randomUUID(),
    clientName: client.name,
    clientId: client.id,
    plan: document.getElementById("licensePlan").value,
    start: document.getElementById("licenseStart").value,
    end: document.getElementById("licenseEnd").value,
    status: document.getElementById("licenseStatus").value,
  });

  saveState();
  renderLicenses();
  setFeedback("Vigência registrada.");
  event.target.reset();
});

document.getElementById("importForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const file = document.getElementById("importFile").files[0];
  const client = state.clients.find((item) => item.id === importClient.value);

  if (!client || !file) {
    setFeedback("Selecione o cliente e o arquivo da base inicial.");
    return;
  }

  state.imports.unshift({
    id: crypto.randomUUID(),
    clientName: client.name,
    filename: file.name,
    status: "arquivo recebido para processamento",
    notes: document.getElementById("importNotes").value,
    createdAt: new Date().toLocaleString("pt-BR"),
  });

  saveState();
  renderImports();
  setFeedback(`Importação inicial registrada para ${client.name}.`);
  event.target.reset();
});

document.getElementById("saveFieldConfigButton").addEventListener("click", () => {
  const config = {};
  Object.keys(defaultFieldConfig).forEach((key) => {
    config[key] = {
      label: document.querySelector(`[data-field-label="${key}"]`)?.value?.trim() || defaultFieldConfig[key].label,
      visible: document.querySelector(`[data-field-visible="${key}"]`)?.checked !== false,
    };
  });
  saveFieldConfig(config);
  setFeedback("Configuração de campos salva. O Cliente refletirá essa mudança.");
});

document.getElementById("resetFieldConfigButton").addEventListener("click", () => {
  saveFieldConfig(defaultFieldConfig);
  renderFieldConfig();
  setFeedback("Configuração de campos restaurada para o padrão.");
});

document.getElementById("brandingForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.getElementById("brandingClientLogo").files[0];
  const current = getBranding();
  const nextBranding = {
    ...current,
    clientName: document.getElementById("brandingClientName").value.trim() || defaultBranding.clientName,
  };

  if (file) {
    nextBranding.clientLogoUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  saveBranding(nextBranding);
  renderBranding();
  document.getElementById("brandingClientLogo").value = "";
  setFeedback("Identidade visual salva. O portal do Cliente já pode usar a nova configuração.");
});

document.getElementById("resetBrandingButton").addEventListener("click", () => {
  saveBranding(defaultBranding);
  renderBranding();
  document.getElementById("brandingClientLogo").value = "";
  setFeedback("Identidade visual restaurada para o padrão.");
});

document.getElementById("resetAdminButton").addEventListener("click", () => {
  state = demoState();
  state.licenses[0].clientId = state.clients[0].id;
  saveState();
  renderAll();
  resetClientForm();
  setFeedback("Painel administrativo recarregado com a base inicial da planilha QTQD.");
});

document.querySelectorAll(".nav-link").forEach((button) => {
  button.addEventListener("click", () => showSection(button.dataset.section));
});

document.querySelectorAll("[data-theme-choice]").forEach((button) => {
  button.addEventListener("click", () => {
    localStorage.setItem(THEME_KEY, button.dataset.themeChoice);
    applyTheme(button.dataset.themeChoice);
  });
});

document.getElementById("runtimeConfigForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const runtimeConfig = {
    ...getRuntimeConfig(),
    mode: document.getElementById("runtimeMode").value,
    apiBaseUrl: document.getElementById("runtimeApiBaseUrl").value.trim(),
    healthUrl: document.getElementById("runtimeHealthUrl").value.trim(),
    tenantId: document.getElementById("runtimeTenantId").value.trim(),
  };
  saveRuntimeConfig(runtimeConfig);
  saveAdminToken(document.getElementById("runtimeAdminToken").value.trim());
  renderRuntimeConfig();
  if (runtimeConfig.mode === "api") {
    try {
      await loadStateFromApi();
      renderAll();
      setFeedback("Ambiente salvo e clientes carregados da API.");
      return;
    } catch (error) {
      renderAll();
      setFeedback(`Ambiente salvo, mas a API ainda nao respondeu: ${error.message}`);
      return;
    }
  }
  setFeedback("Ambiente salvo em modo de simulacao.");
});

document.getElementById("testApiConnectionButton").addEventListener("click", async () => {
  const label = document.getElementById("runtimeHealthStatusLabel");
  label.textContent = "Testando...";
  try {
    const result = await window.QTQD_API_CLIENT.health();
    label.textContent = `${result.status} (${result.env})`;
    setFeedback("API respondeu com sucesso.");
  } catch (error) {
    label.textContent = `Falha: ${error.message}`;
    setFeedback(`Nao foi possivel validar a API: ${error.message}`);
  }
});

window.addEventListener("storage", (event) => {
  if (event.key === BRANDING_KEY) renderBranding();
});

async function initializeAdmin() {
  applyTheme();
  loadState();
  if (isApiMode()) {
    try {
      await loadStateFromApi();
    } catch (error) {
      setFeedback(`Modo API configurado, mas foi mantido fallback local: ${error.message}`);
    }
  }
  renderAll();
  showSection("clientes");
}

initializeAdmin();

(function () {
  const config = window.QTQD_APP_CONFIG || {};

  async function request(path, options) {
    const response = await fetch(path, options);
    if (!response.ok) {
      let detail = `Erro HTTP ${response.status}`;
      try {
        const payload = await response.json();
        detail = payload.detail || detail;
      } catch {}
      throw new Error(detail);
    }
    if (response.status === 204) return null;
    return response.json();
  }

  function withBase(path) {
    return `${String(config.apiBaseUrl || "").replace(/\/$/, "")}${path}`;
  }

  function adminHeaders(adminToken) {
    return {
      "Content-Type": "application/json",
      "x-admin-token": adminToken,
    };
  }

  window.QTQD_API_CLIENT = {
    health() {
      return request(config.healthUrl, { method: "GET" });
    },
    listClients(adminToken) {
      return request(withBase("/admin/clientes"), {
        method: "GET",
        headers: adminHeaders(adminToken),
      });
    },
    createClient(adminToken, payload) {
      return request(withBase("/admin/clientes"), {
        method: "POST",
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },
    updateClient(adminToken, tenantId, payload) {
      return request(withBase(`/admin/clientes/${tenantId}`), {
        method: "PATCH",
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },
    listAvaliacoes(tenantId) {
      return request(withBase(`/avaliacoes?tenant_id=${encodeURIComponent(tenantId)}`), {
        method: "GET",
      });
    },
    createAvaliacao(payload) {
      return request(withBase("/avaliacoes"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    updateAvaliacao(avaliacaoId, payload) {
      return request(withBase(`/avaliacoes/${avaliacaoId}`), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    deleteAvaliacao(avaliacaoId) {
      return request(withBase(`/avaliacoes/${avaliacaoId}`), {
        method: "DELETE",
      });
    },
  };
})();

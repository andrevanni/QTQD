/**
 * QTQD API Client
 *
 * Uso:
 *   QTQD_API_CLIENT.setJwt(token)          — armazena o JWT do Supabase Auth
 *   QTQD_API_CLIENT.clearJwt()             — remove o JWT (logout)
 *   QTQD_API_CLIENT.listAvaliacoes()        — lista avaliações do tenant autenticado
 *   QTQD_API_CLIENT.listClients(adminToken) — lista tenants (admin)
 */
(function () {
  const config = window.QTQD_APP_CONFIG || {};
  const JWT_KEY = 'qtqd_jwt_v1';

  /* ── Helpers internos ──────────────────────────────── */
  function base(path) {
    return `${String(config.apiBaseUrl || '').replace(/\/$/, '')}${path}`;
  }

  function getJwt() {
    return localStorage.getItem(JWT_KEY) || '';
  }

  function authHeaders() {
    const token = getJwt();
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  }

  function adminHeaders(adminToken) {
    return {
      'Content-Type': 'application/json',
      'x-admin-token': adminToken,
    };
  }

  async function request(url, options) {
    const res = await fetch(url, options);
    if (!res.ok) {
      let detail = `Erro HTTP ${res.status}`;
      try {
        const body = await res.json();
        if (body.detail) {
          detail = Array.isArray(body.detail)
            ? body.detail.map(e => e.msg || JSON.stringify(e)).join('; ')
            : String(body.detail);
        }
      } catch {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  /* ── API pública ───────────────────────────────────── */
  window.QTQD_API_CLIENT = {

    /* JWT management */
    setJwt(token) { localStorage.setItem(JWT_KEY, token); },
    clearJwt()    { localStorage.removeItem(JWT_KEY); },
    hasJwt()      { return !!getJwt(); },

    /* Health */
    health() {
      return request(config.healthUrl || base('/../../health'), { method: 'GET' });
    },

    /* ── Avaliações (exige JWT) ───────────────────────── */
    listAvaliacoes() {
      return request(base('/avaliacoes'), { method: 'GET', headers: authHeaders() });
    },
    getAvaliacao(id) {
      return request(base(`/avaliacoes/${id}`), { method: 'GET', headers: authHeaders() });
    },
    createAvaliacao(payload) {
      return request(base('/avaliacoes'), {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
    },
    updateAvaliacao(id, payload) {
      return request(base(`/avaliacoes/${id}`), {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
    },
    closeAvaliacao(id) {
      return request(base(`/avaliacoes/${id}/fechar`), { method: 'POST', headers: authHeaders() });
    },
    deleteAvaliacao(id) {
      return request(base(`/avaliacoes/${id}`), { method: 'DELETE', headers: authHeaders() });
    },

    /* ── Config do cliente (exige JWT) ───────────────── */
    getMyBranding() {
      return request(base('/me/branding'), { method: 'GET', headers: authHeaders() });
    },
    getMyComponentesConfig() {
      return request(base('/me/componentes-config'), { method: 'GET', headers: authHeaders() });
    },

    /* ── Admin — clientes (exige X-Admin-Token) ──────── */
    listClients(adminToken) {
      return request(base('/admin/clientes'), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    createClient(adminToken, payload) {
      return request(base('/admin/clientes'), {
        method: 'POST',
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },
    updateClient(adminToken, tenantId, payload) {
      return request(base(`/admin/clientes/${tenantId}`), {
        method: 'PATCH',
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },

    /* ── Admin — licenças ────────────────────────────── */
    listLicencas(adminToken, tenantId) {
      const qs = tenantId ? `?tenant_id=${tenantId}` : '';
      return request(base(`/admin/licencas${qs}`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    createLicenca(adminToken, payload) {
      return request(base('/admin/licencas'), {
        method: 'POST',
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },
    updateLicenca(adminToken, licencaId, payload) {
      return request(base(`/admin/licencas/${licencaId}`), {
        method: 'PATCH',
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },
    deleteLicenca(adminToken, licencaId) {
      return request(base(`/admin/licencas/${licencaId}`), {
        method: 'DELETE',
        headers: adminHeaders(adminToken),
      });
    },

    /* ── Admin — branding ────────────────────────────── */
    getBranding(adminToken, tenantId) {
      return request(base(`/admin/branding/${tenantId}`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    saveBranding(adminToken, tenantId, payload) {
      return request(base(`/admin/branding/${tenantId}`), {
        method: 'PUT',
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },

    /* ── Admin — componentes config ──────────────────── */
    getComponentesConfig(adminToken, tenantId) {
      return request(base(`/admin/componentes-config/${tenantId}`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    saveComponentesConfig(adminToken, tenantId, itens) {
      return request(base(`/admin/componentes-config/${tenantId}`), {
        method: 'PUT',
        headers: adminHeaders(adminToken),
        body: JSON.stringify({ itens }),
      });
    },

    /* ── Admin — PDF config ─────────────────────────── */
    getPdfConfig(adminToken, tenantId) {
      return request(base(`/admin/pdf-config/${tenantId}`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    savePdfConfig(adminToken, tenantId, payload) {
      return request(base(`/admin/pdf-config/${tenantId}`), { method: 'PUT', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    enviarRelatorio(adminToken, tenantId) {
      return request(base(`/admin/enviar-relatorio/${tenantId}`), { method: 'POST', headers: adminHeaders(adminToken) });
    },

    /* ── Admin — usuários ───────────────────────────── */
    listUsuarios(adminToken, tenantId) {
      const qs = tenantId ? `?tenant_id=${tenantId}` : '';
      return request(base(`/admin/usuarios${qs}`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    createUsuario(adminToken, payload) {
      return request(base('/admin/usuarios'), { method: 'POST', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    updateUsuario(adminToken, id, payload) {
      return request(base(`/admin/usuarios/${id}`), { method: 'PATCH', headers: adminHeaders(adminToken), body: JSON.stringify(payload) });
    },
    deleteUsuario(adminToken, id) {
      return request(base(`/admin/usuarios/${id}`), { method: 'DELETE', headers: adminHeaders(adminToken) });
    },
    enviarConvite(adminToken, id) {
      return request(base(`/admin/usuarios/${id}/enviar-convite`), { method: 'POST', headers: adminHeaders(adminToken) });
    },

    /* ── Admin — importações ─────────────────────────── */
    listImportacoes(adminToken, tenantId) {
      const qs = tenantId ? `?tenant_id=${tenantId}` : '';
      return request(base(`/admin/importacoes${qs}`), { method: 'GET', headers: adminHeaders(adminToken) });
    },
    createImportacao(adminToken, payload) {
      return request(base('/admin/importacoes'), {
        method: 'POST',
        headers: adminHeaders(adminToken),
        body: JSON.stringify(payload),
      });
    },
    processarExcel(adminToken, tenantId, file) {
      const form = new FormData();
      form.append('arquivo', file);
      return request(base(`/admin/importacoes/processar/${tenantId}`), {
        method: 'POST',
        headers: { 'x-admin-token': adminToken },
        body: form,
      });
    },
  };
})();

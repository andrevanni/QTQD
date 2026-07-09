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

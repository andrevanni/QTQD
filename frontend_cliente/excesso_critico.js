/**
 * Módulo Excesso Crítico — assistente que processa Excel de estoque por fabricante,
 * calcula excesso por curva (A/B/C/D) e aplica os valores a uma avaliação existente.
 *
 * Expõe window.QTQD_EXCESSO.init() — invocado quando a seção é aberta no menu lateral.
 */
(function () {
  let initialized = false;
  let lastResult = null;          // último resultado do /calcular
  let filteredProducts = [];      // produtos após filtros de curva/busca

  /* ── Helpers ──────────────────────────────────────────────── */

  const $ = (id) => document.getElementById(id);

  const fmtBRL = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v || 0));

  const fmtNum = (v) => (v === null || v === undefined || Number.isNaN(v))
    ? '-'
    : new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 }).format(Number(v));

  const fmtInt = (v) => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(Number(v || 0));

  const fmtDateBR = (iso) => {
    if (!iso || iso.length !== 10) return iso || '';
    return iso.slice(8, 10) + '/' + iso.slice(5, 7) + '/' + iso.slice(0, 4);
  };

  const canEdit = () => {
    const p = localStorage.getItem('qtqd_permissao_v1');
    return !p || p === 'edita';
  };

  const isApi = () => {
    return !!localStorage.getItem('qtqd_jwt_v1')
      && !!localStorage.getItem('qtqd_tenant_id_v1')
      && !!window.QTQD_API_CLIENT;
  };

  const setStatus = (elId, msg, isError) => {
    const el = $(elId);
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? 'var(--bad, #ef4444)' : '';
  };

  /* ── Limites ──────────────────────────────────────────────── */

  function getLimitesUI() {
    return {
      limite_a: Math.max(1, parseInt($('excLimiteA').value, 10) || 120),
      limite_b: Math.max(1, parseInt($('excLimiteB').value, 10) || 150),
      limite_c: Math.max(1, parseInt($('excLimiteC').value, 10) || 150),
      limite_d: Math.max(1, parseInt($('excLimiteD').value, 10) || 180),
    };
  }

  function setLimitesUI(lim) {
    $('excLimiteA').value = lim.limite_a;
    $('excLimiteB').value = lim.limite_b;
    $('excLimiteC').value = lim.limite_c;
    $('excLimiteD').value = lim.limite_d;
  }

  async function carregarLimites() {
    if (!isApi()) return;
    try {
      const lim = await window.QTQD_API_CLIENT.getExcessoLimites();
      setLimitesUI(lim);
    } catch (e) {
      console.warn('Excesso: falha ao carregar limites', e);
    }
  }

  async function salvarLimites() {
    if (!canEdit()) {
      setStatus('excStatus', 'Permissão insuficiente para salvar limites.', true);
      return;
    }
    if (!isApi()) {
      setStatus('excStatus', 'Disponível apenas no modo conectado (API).', true);
      return;
    }
    setStatus('excStatus', 'Salvando limites...');
    try {
      await window.QTQD_API_CLIENT.putExcessoLimites(getLimitesUI());
      setStatus('excStatus', 'Limites salvos. Use no próximo cálculo.');
    } catch (e) {
      setStatus('excStatus', 'Falha ao salvar limites: ' + e.message, true);
    }
  }

  /* ── Lista de avaliações para aplicar ─────────────────────── */

  async function carregarSemanas() {
    const sel = $('excSemanaSelect');
    sel.innerHTML = '<option value="">Carregando...</option>';
    try {
      let lista;
      if (isApi()) {
        lista = await window.QTQD_API_CLIENT.listAvaliacoes();
      } else {
        const raw = localStorage.getItem('qtqd_cliente_demo_v1');
        lista = raw ? JSON.parse(raw).map(r => ({ id: r.id, semana_referencia: r.weekDate, status: r.status })) : [];
      }
      const ordenadas = [...lista].sort((a, b) => (b.semana_referencia || '').localeCompare(a.semana_referencia || ''));
      if (!ordenadas.length) {
        sel.innerHTML = '<option value="">Nenhuma semana cadastrada</option>';
        return;
      }
      const opcoes = ordenadas.map(r => {
        const data = fmtDateBR(r.semana_referencia);
        const status = r.status || 'rascunho';
        return '<option value="' + r.id + '">' + data + ' — ' + status + '</option>';
      });
      sel.innerHTML = '<option value="">Selecione...</option>' + opcoes.join('');
    } catch (e) {
      sel.innerHTML = '<option value="">Erro ao carregar</option>';
      console.warn('Excesso: falha ao listar avaliações', e);
    }
  }

  /* ── Upload e cálculo ─────────────────────────────────────── */

  async function onArquivoSelecionado(e) {
    const file = e.target.files && e.target.files[0];
    e.target.value = ''; // permite re-selecionar o mesmo arquivo
    if (!file) return;
    if (!canEdit()) {
      setStatus('excStatus', 'Permissão insuficiente para importar arquivo.', true);
      return;
    }
    if (!isApi()) {
      setStatus('excStatus', 'Importação disponível apenas no modo conectado (API).', true);
      return;
    }

    setStatus('excStatus', 'Processando ' + file.name + '... (pode levar alguns segundos)');
    $('excResultado').classList.add('hidden');

    try {
      const limites = getLimitesUI();
      const resp = await window.QTQD_API_CLIENT.calcularExcesso(file, limites);
      lastResult = resp;
      renderResultado(resp);
      const totalCriticos = resp.resumo.total_produtos_criticos;
      const totalLinhas = resp.resumo.total_linhas_excel;
      setStatus('excStatus', 'Processado: ' + fmtInt(totalLinhas) + ' linhas, ' + fmtInt(totalCriticos) + ' produtos em excesso crítico.');
    } catch (err) {
      setStatus('excStatus', 'Erro: ' + err.message, true);
    }
  }

  /* ── Render do resultado ──────────────────────────────────── */

  function renderResultado(resp) {
    const t = resp.totais;
    const r = resp.resumo;

    const cards = [
      ['Curva A', t.excesso_curva_a, '#16a34a', r.qtd_criticos_por_curva.A],
      ['Curva B', t.excesso_curva_b, '#0891b2', r.qtd_criticos_por_curva.B],
      ['Curva C', t.excesso_curva_c, '#f59e0b', r.qtd_criticos_por_curva.C],
      ['Curva D', t.excesso_curva_d, '#ef4444', r.qtd_criticos_por_curva.D],
      ['TOTAL',   t.total,           '#2563eb', r.total_produtos_criticos],
    ];

    const cardsHtml = cards.map(c => {
      const cls = c[0] === 'TOTAL' ? 'kpi-card good' : 'kpi-card neutral';
      return '<article class="' + cls + '" style="border-left:4px solid ' + c[2] + '">'
        + '<span>' + c[0] + '</span>'
        + '<strong>' + fmtBRL(c[1]) + '</strong>'
        + '<span class="txt-muted txt-xs">' + fmtInt(c[3]) + ' produtos</span>'
        + '</article>';
    }).join('');

    $('excKpis').innerHTML = cardsHtml;

    const resumoTxt = fmtInt(r.total_linhas_excel) + ' linhas no Excel · '
      + fmtInt(r.total_produtos_unicos) + ' produtos únicos (após somar filiais) · '
      + 'Estoque total: ' + fmtBRL(r.valor_total_estoque) + ' · '
      + 'Excesso representa ' + fmtNum(r.pct_excesso) + '% do estoque';
    $('excResumo').textContent = resumoTxt;

    filteredProducts = resp.produtos.slice();
    renderTabela();

    $('excResultado').classList.remove('hidden');
    carregarSemanas();
  }

  function renderTabela() {
    const tbody = $('excTabelaBody');
    const curva = $('excFiltroCurva').value;
    const busca = ($('excFiltroBusca').value || '').toLowerCase().trim();

    let list = lastResult ? lastResult.produtos.slice() : [];
    if (curva) list = list.filter(p => p.curva === curva);
    if (busca) list = list.filter(p => p.nome.toLowerCase().includes(busca));
    filteredProducts = list;

    if (!list.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="muted" style="padding:24px;text-align:center">Nenhum produto encontrado.</td></tr>';
      return;
    }

    const linhas = list.map(p => {
      const cobertura = p.cobertura_dias === null ? '∞ (sem venda)' : fmtNum(p.cobertura_dias) + ' dias';
      const corCurva = { A: '#16a34a', B: '#0891b2', C: '#f59e0b', D: '#ef4444' }[p.curva] || '#94a3b8';
      const badge = '<span style="background:' + corCurva + '20;color:' + corCurva + ';padding:2px 8px;border-radius:6px;font-weight:700;font-size:11px">' + p.curva + '</span>';
      return '<tr>'
        + '<td style="font-size:12px">' + p.nome + '</td>'
        + '<td>' + badge + '</td>'
        + '<td class="txt-muted txt-xs">' + (p.linha || '—') + '</td>'
        + '<td style="text-align:right">' + fmtInt(p.qtd_estoque) + '</td>'
        + '<td style="text-align:right">' + fmtNum(p.media_un) + '</td>'
        + '<td style="text-align:right">' + cobertura + '</td>'
        + '<td style="text-align:right">' + fmtInt(p.excesso_un) + '</td>'
        + '<td style="text-align:right;font-weight:700">' + fmtBRL(p.excesso_valor) + '</td>'
        + '</tr>';
    });
    tbody.innerHTML = linhas.join('');
  }

  /* ── Aplicar a uma avaliação ──────────────────────────────── */

  async function aplicar() {
    if (!canEdit()) {
      setStatus('excAplicarStatus', 'Permissão insuficiente para aplicar valores.', true);
      return;
    }
    if (!lastResult) {
      setStatus('excAplicarStatus', 'Importe o Excel antes de aplicar.', true);
      return;
    }
    const avaliacaoId = $('excSemanaSelect').value;
    if (!avaliacaoId) {
      setStatus('excAplicarStatus', 'Selecione a semana que receberá os valores.', true);
      return;
    }
    if (!isApi()) {
      setStatus('excAplicarStatus', 'Disponível apenas no modo conectado (API).', true);
      return;
    }

    const t = lastResult.totais;
    const payload = {
      excesso_curva_a: t.excesso_curva_a,
      excesso_curva_b: t.excesso_curva_b,
      excesso_curva_c: t.excesso_curva_c,
      excesso_curva_d: t.excesso_curva_d,
    };

    setStatus('excAplicarStatus', 'Aplicando...');
    try {
      const resp = await window.QTQD_API_CLIENT.aplicarExcesso(avaliacaoId, payload);
      const dataSel = fmtDateBR(resp.semana_referencia);
      setStatus('excAplicarStatus', '✓ Valores aplicados à semana ' + dataSel + ' (' + resp.status + '). Total: ' + fmtBRL(t.total) + '.');

      // Recarrega os registros para refletir a mudança no painel/inspetor
      if (typeof window.loadRecordsFromSource === 'function' && typeof window.renderAll === 'function') {
        try {
          await window.loadRecordsFromSource();
          window.renderAll();
        } catch {}
      }
    } catch (e) {
      setStatus('excAplicarStatus', 'Erro: ' + e.message, true);
    }
  }

  /* ── Inicialização ────────────────────────────────────────── */

  function bindEvents() {
    $('excSalvarLimites').addEventListener('click', salvarLimites);
    $('excImportBtn').addEventListener('click', () => $('excFileInput').click());
    $('excFileInput').addEventListener('change', onArquivoSelecionado);
    $('excAplicarBtn').addEventListener('click', aplicar);
    $('excFiltroCurva').addEventListener('change', renderTabela);
    $('excFiltroBusca').addEventListener('input', renderTabela);
  }

  function applyPermissionsUI() {
    if (canEdit()) return;
    ['excSalvarLimites', 'excImportBtn', 'excAplicarBtn'].forEach(id => {
      const el = $(id);
      if (el) { el.disabled = true; el.style.opacity = 0.5; el.style.cursor = 'not-allowed'; }
    });
    ['excLimiteA', 'excLimiteB', 'excLimiteC', 'excLimiteD'].forEach(id => {
      const el = $(id);
      if (el) el.disabled = true;
    });
  }

  function init() {
    if (initialized) {
      carregarSemanas();
      return;
    }
    initialized = true;
    bindEvents();
    applyPermissionsUI();
    if (isApi()) {
      carregarLimites();
      carregarSemanas();
    } else {
      setStatus('excStatus', 'Modo simulação: importação e cálculo disponíveis apenas no portal conectado.', true);
    }
  }

  window.QTQD_EXCESSO = { init };
})();

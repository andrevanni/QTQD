/**
 * Módulo Excesso Crítico — processa Excel de estoque no PRÓPRIO BROWSER (SheetJS),
 * calcula excesso por curva (A/B/C/D) e aplica o resultado a uma avaliação existente.
 *
 * Processamento no client elimina o limite de upload do Vercel (HTTP 413 em arquivos grandes).
 * Só os 4 totais são enviados ao backend (endpoint /aplicar/{avaliacao_id}).
 *
 * Expõe window.QTQD_EXCESSO.init().
 */
(function () {
  let initialized = false;
  let lastResult = null;

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

  const normCurva = (v) => String(v || '').trim().toUpperCase().slice(0, 1);

  const isLancamento = (v) => v != null && String(v).trim().toLowerCase().startsWith('sim');

  const toFloat = (v) => {
    if (v === null || v === undefined || v === '') return 0;
    if (typeof v === 'number') return Number.isFinite(v) ? v : 0;
    let s = String(v).trim().replace('R$', '').replace(/\s/g, '');
    if (s.includes(',') && s.includes('.')) s = s.replace(/\./g, '').replace(',', '.');
    else if (s.includes(',')) s = s.replace(',', '.');
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : 0;
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

  /* ── Lista de avaliações ──────────────────────────────────── */

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

  /* ── Cálculo no browser (espelha o backend) ───────────────── */

  function findColIndex(header, candidates) {
    for (let i = 0; i < header.length; i++) {
      const h = String(header[i] || '').trim().toLowerCase();
      if (candidates.some(c => h === c.toLowerCase())) return i;
    }
    return -1;
  }

  /**
   * Calcula o excesso por curva (A/B/C/D) a partir de linhas já parseadas do Excel.
   * Função pura — não toca window/DOM. `rows` é Array<Array> (linha 0 = header).
   * Retorna { limites, totais, resumo, produtos }.
   */
  function calcularExcessoDeRows(rows, limites) {
    if (!rows || !rows.length) throw new Error('Planilha sem dados.');
    const header = rows[0].map(c => String(c || '').trim());

    const iNome  = findColIndex(header, ['Nome Completo', 'Nome']);
    const iLinha = findColIndex(header, ['Linha']);
    const iCurva = findColIndex(header, ['Curva']);
    const iMedia = findColIndex(header, ['MediaF Un', 'Media', 'Media Un', 'MediaF']);
    const iQtd   = findColIndex(header, ['Qtd Estoque', 'Qtd', 'Estoque Qtd']);
    const iValor = findColIndex(header, ['Estoque Valor', 'Valor', 'Estoque R$']);
    const iLanc  = findColIndex(header, ['lancamento', 'Lançamento', 'Lançamentos', 'Lancamentos', 'Lancamento']);

    if (iNome < 0 || iCurva < 0 || iMedia < 0 || iQtd < 0 || iValor < 0) {
      throw new Error('Cabeçalho inválido. Esperado: Nome Completo, Linha, Curva, Filial, MediaF Un, Qtd Estoque, Estoque Valor.');
    }

    const limMap = { A: limites.limite_a, B: limites.limite_b, C: limites.limite_c, D: limites.limite_d };

    // Agregação por (nome, linha, curva) — soma filiais
    const agg = new Map();
    let totalLinhas = 0;
    let totalEstoqueLancamentos = 0;
    let qtdLancamentos = 0;

    for (let r = 1; r < rows.length; r++) {
      const row = rows[r];
      if (!row || row.every(v => v === null || v === undefined || v === '')) continue;
      const nome = row[iNome];
      if (!nome) continue;

      // Lançamento: soma pura no total e sai (não entra no excesso)
      if (iLanc >= 0 && isLancamento(row[iLanc])) {
        totalEstoqueLancamentos += toFloat(row[iValor]);
        qtdLancamentos++;
        continue;
      }

      const curva = normCurva(row[iCurva]);
      if (!limMap[curva]) continue;

      const linha = iLinha >= 0 ? String(row[iLinha] || '').trim() : '';
      const media = toFloat(row[iMedia]);
      const qtd   = toFloat(row[iQtd]);
      const valor = toFloat(row[iValor]);

      const key = String(nome).trim() + '||' + linha + '||' + curva;
      const existing = agg.get(key);
      if (existing) {
        existing.qtd   += qtd;
        existing.media += media;
        existing.valor += valor;
      } else {
        agg.set(key, { nome: String(nome).trim(), linha, curva, qtd, media, valor });
      }
      totalLinhas++;
    }

    // Cálculo de excesso por produto
    const totaisCurva = { A: 0, B: 0, C: 0, D: 0 };
    const qtdCriticos = { A: 0, B: 0, C: 0, D: 0 };
    const produtosCriticos = [];
    let valorTotalEstoque = 0;

    agg.forEach(item => {
      valorTotalEstoque += item.valor;
      const { qtd, media, valor, curva } = item;
      if (qtd <= 0) return;

      const custoUn = qtd > 0 ? valor / qtd : 0;
      let excessoUn = 0;
      let coberturaDias = null;

      if (media === 0) {
        if (qtd > 1) {
          excessoUn = qtd;
          coberturaDias = null; // ∞
        }
      } else {
        coberturaDias = (qtd / media) * 30;
        const lim = limMap[curva];
        if (coberturaDias > lim) {
          const ideal = (media * lim) / 30;
          excessoUn = qtd - ideal;
        }
      }

      if (excessoUn > 0) {
        const excessoValor = excessoUn * custoUn;
        totaisCurva[curva] += excessoValor;
        qtdCriticos[curva]++;
        produtosCriticos.push({
          nome: item.nome,
          linha: item.linha,
          curva,
          qtd_estoque: Math.round(qtd * 100) / 100,
          media_un: Math.round(media * 10000) / 10000,
          cobertura_dias: coberturaDias !== null ? Math.round(coberturaDias * 10) / 10 : null,
          excesso_un: Math.round(excessoUn * 100) / 100,
          custo_un: Math.round(custoUn * 10000) / 10000,
          excesso_valor: Math.round(excessoValor * 100) / 100,
        });
      }
    });

    produtosCriticos.sort((a, b) => b.excesso_valor - a.excesso_valor);

    const round2 = v => Math.round(v * 100) / 100;
    const totalExcesso = totaisCurva.A + totaisCurva.B + totaisCurva.C + totaisCurva.D;

    return {
      limites: limMap,
      totais: {
        excesso_curva_a: round2(totaisCurva.A),
        excesso_curva_b: round2(totaisCurva.B),
        excesso_curva_c: round2(totaisCurva.C),
        excesso_curva_d: round2(totaisCurva.D),
        total: round2(totalExcesso),
        total_estoque_lancamentos: round2(totalEstoqueLancamentos),
      },
      resumo: {
        total_linhas_excel: totalLinhas,
        total_produtos_unicos: agg.size,
        total_produtos_criticos: produtosCriticos.length,
        qtd_criticos_por_curva: qtdCriticos,
        valor_total_estoque: round2(valorTotalEstoque),
        pct_excesso: valorTotalEstoque > 0 ? round2(totalExcesso / valorTotalEstoque * 100) : 0,
        qtd_lancamentos: qtdLancamentos,
      },
      produtos: produtosCriticos.slice(0, 100),
    };
  }

  /**
   * Processa o ArrayBuffer do XLSX (lê via SheetJS) e delega o cálculo à função pura.
   * Retorna o mesmo formato que o backend retornava: { limites, totais, resumo, produtos }
   */
  function processarExcelArrayBuffer(buf, limites) {
    if (!window.XLSX) {
      throw new Error('Biblioteca de leitura de Excel não carregou. Verifique sua conexão.');
    }

    const wb = window.XLSX.read(buf, { type: 'array' });
    const ws = wb.Sheets[wb.SheetNames[0]];
    if (!ws) throw new Error('Planilha vazia.');

    const rows = window.XLSX.utils.sheet_to_json(ws, { header: 1, defval: null });
    return calcularExcessoDeRows(rows, limites);
  }

  /* ── Upload e processamento ──────────────────────────────── */

  function lerArquivoComoBuffer(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error('Falha ao ler o arquivo.'));
      reader.readAsArrayBuffer(file);
    });
  }

  async function onArquivoSelecionado(e) {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;
    if (!canEdit()) {
      setStatus('excStatus', 'Permissão insuficiente para importar arquivo.', true);
      return;
    }

    const sizeMB = (file.size / 1024 / 1024).toFixed(2);
    setStatus('excStatus', 'Lendo ' + file.name + ' (' + sizeMB + ' MB)... aguarde.');
    $('excResultado').classList.add('hidden');

    try {
      const buf = await lerArquivoComoBuffer(file);
      setStatus('excStatus', 'Calculando excesso por curva...');
      // Processa em microtask para o status renderizar antes
      await new Promise(r => setTimeout(r, 50));

      const limites = getLimitesUI();
      const resp = processarExcelArrayBuffer(buf, limites);
      lastResult = resp;
      renderResultado(resp);

      const totalCriticos = resp.resumo.total_produtos_criticos;
      const totalLinhas = resp.resumo.total_linhas_excel;
      setStatus('excStatus', '✓ Processado: ' + fmtInt(totalLinhas) + ' linhas, ' + fmtInt(totalCriticos) + ' produtos em excesso crítico.');
    } catch (err) {
      console.error('Excesso: erro no processamento', err);
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

    const lancCard = '<article class="kpi-card neutral" style="border-left:4px solid #7c3aed">'
      + '<span>Estoque em Lançamentos</span>'
      + '<strong>' + fmtBRL(t.total_estoque_lancamentos || 0) + '</strong>'
      + '<span class="txt-muted txt-xs">' + fmtInt(r.qtd_lancamentos || 0) + ' itens excluídos</span>'
      + '</article>';
    $('excKpis').innerHTML = cardsHtml + lancCard;

    const resumoTxt = fmtInt(r.total_linhas_excel) + ' linhas no Excel · '
      + fmtInt(r.total_produtos_unicos) + ' produtos únicos (após somar filiais) · '
      + fmtInt(r.qtd_lancamentos || 0) + ' itens de lançamento excluídos (' + fmtBRL(t.total_estoque_lancamentos || 0) + ') · '
      + 'Estoque total: ' + fmtBRL(r.valor_total_estoque) + ' · '
      + 'Excesso representa ' + fmtNum(r.pct_excesso) + '% do estoque';
    $('excResumo').textContent = resumoTxt;

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
      total_estoque_lancamentos: t.total_estoque_lancamentos || 0,
    };

    setStatus('excAplicarStatus', 'Aplicando...');
    try {
      const resp = await window.QTQD_API_CLIENT.aplicarExcesso(avaliacaoId, payload);
      const dataSel = fmtDateBR(resp.semana_referencia);
      setStatus('excAplicarStatus', '✓ Valores aplicados à semana ' + dataSel + ' (' + resp.status + '). Total: ' + fmtBRL(t.total) + '.');

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

  if (typeof window !== 'undefined') window.QTQD_EXCESSO = { init };
  if (typeof module !== 'undefined' && module.exports) module.exports = { calcularExcessoDeRows };
})();

/* ═══════════════════════════════════════════════════════
   QTQD — Gerador de Gráficos
   Carregado após script.js. Substitui renderChartsPanel()
   ═══════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ── Constantes ─────────────────────────────────────── */
  function getStorageKey() {
    return 'qtqd_saved_charts_v2_' + (localStorage.getItem('qtqd_tenant_id_v1') || 'local');
  }

  const PALETTE = [
    '#2563eb', '#16a34a', '#dc2626', '#d97706',
    '#7c3aed', '#0891b2', '#be185d', '#65a30d',
    '#ea580c', '#0d9488', '#9333ea', '#f59e0b',
  ];

  const RANGE_DEFAULTS = { weeks: 12, months: 6, years: 3 };

  /* ── Estado do builder ──────────────────────────────── */
  let cbState = { name: '', fields: [], range: 'weeks', count: 12, type: 'line', mode: 'value' };
  let savedCharts = [];
  let cbPreviewInstance = null;
  let savedInstances = {};

  /* ── Helpers ────────────────────────────────────────── */
  function cssVar(name) {
    return getComputedStyle(document.body).getPropertyValue(name).trim();
  }

  function fmtVal(v, mode, field) {
    if (mode === 'percent') return fmtNum(v) + '%';
    if (!field) return fmtNum(v);
    if (field.format === 'percent') return fmtPercent(v);
    if (field.format === 'days')    return fmtDays(v);
    if (field.format === 'number')  return fmtNum(v);
    return fmtMoneyShort(v);
  }

  function fmtAxisTick(v, fmt, mode) {
    if (mode === 'percent') return fmtNum(v) + '%';
    if (fmt === 'percent')  return fmtPercent(v);
    if (fmt === 'days')     return fmtDays(v);
    if (fmt === 'currency') return fmtMoneyShort(v);
    return fmtNum(v);
  }

  /* Detecta quando datasets têm escalas incompatíveis (ex: dias + moeda) */
  function getDualAxisInfo(config) {
    if (config.mode === 'percent') return { needsDual: false };
    const fields = config.fields
      .map(k => chartFieldCatalog.find(f => f.key === k))
      .filter(Boolean);
    if (fields.length <= 1) return { needsDual: false };
    const fmts = fields.map(f => f.format || 'currency');
    const uniq = [...new Set(fmts)];
    if (uniq.length <= 1) return { needsDual: false };
    const prim = fmts[0];
    const sec  = uniq.find(f => f !== prim);
    return {
      needsDual: true,
      primaryFormat: prim,
      secondaryFormat: sec,
      axisId: field => (field.format || 'currency') === prim ? 'y' : 'y2',
    };
  }

  async function loadSaved() {
    if (typeof getRuntimeConfig === 'function' && getRuntimeConfig().mode === 'api' && window.QTQD_API_CLIENT) {
      try {
        const r = await window.QTQD_API_CLIENT.getChartsConfig();
        savedCharts = r.charts_config || [];
      } catch { savedCharts = []; }
    } else {
      try { savedCharts = JSON.parse(localStorage.getItem(getStorageKey()) || '[]'); }
      catch { savedCharts = []; }
    }
  }

  async function persistSaved() {
    if (typeof getRuntimeConfig === 'function' && getRuntimeConfig().mode === 'api' && window.QTQD_API_CLIENT) {
      window.QTQD_API_CLIENT.putChartsConfig(savedCharts).catch(() => {});
    } else {
      localStorage.setItem(getStorageKey(), JSON.stringify(savedCharts));
    }
  }

  /* ── Construção dos dados do gráfico ────────────────── */
  function buildChartData(config) {
    const points = aggregateRecords(config.range, Math.max(1, Number(config.count) || 12));
    const labels = points.map(p => p.label);

    const fields = config.fields
      .map(k => chartFieldCatalog.find(f => f.key === k))
      .filter(Boolean);

    const axisInfo = getDualAxisInfo(config);

    const datasets = fields.map((field, i) => {
      const raw  = points.map(p => Number((typeof matrixVal==='function'?matrixVal(p.record,field.key):p.record[field.key])||0));
      const data = config.mode === 'percent' ? toPctSeries(raw) : raw;
      const color = PALETTE[i % PALETTE.length];
      const yAxisID = axisInfo.needsDual ? axisInfo.axisId(field) : 'y';

      if (config.type === 'bar') {
        return {
          label:           getFieldLabel(field.key, field.label),
          data,
          backgroundColor: color + 'b0',
          borderColor:     color,
          borderWidth:     2,
          borderRadius:    5,
          borderSkipped:   false,
          yAxisID,
        };
      }

      return {
        label:           getFieldLabel(field.key, field.label),
        data,
        borderColor:     color,
        backgroundColor: color + '18',
        tension:         0.35,
        fill:            config.fields.length === 1,
        pointRadius:     points.length <= 20 ? 4 : 2,
        pointHoverRadius: 6,
        pointBackgroundColor: color,
        borderWidth:     2,
        yAxisID,
      };
    });

    return { labels, datasets, fields };
  }

  /* ── Opções do Chart.js ─────────────────────────────── */
  function buildChartOptions(config, showLabels) {
    const ink    = cssVar('--ink')    || '#0f172a';
    const muted  = cssVar('--muted')  || '#64748b';
    const border = cssVar('--border') || '#e2e8f0';

    const fields = config.fields
      .map(k => chartFieldCatalog.find(f => f.key === k))
      .filter(Boolean);

    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 350 },
      plugins: {
        legend: {
          position: 'top',
          align:    'start',
          labels: {
            color:           ink,
            padding:         18,
            usePointStyle:   true,
            pointStyleWidth: 10,
            font: { size: 12, family: 'Manrope, sans-serif', weight: '700' },
          },
        },
        tooltip: {
          backgroundColor: 'rgba(15,23,42,.95)',
          titleColor:      '#f1f5f9',
          bodyColor:       '#cbd5e1',
          borderColor:     'rgba(255,255,255,.1)',
          borderWidth:     1,
          padding:         12,
          cornerRadius:    8,
          callbacks: {
            label: ctx => {
              const v = ctx.parsed.y;
              const f = fields[ctx.datasetIndex];
              return '  ' + fmtVal(v, config.mode, f);
            },
          },
        },
        datalabels: showLabels ? {
          display:  'auto',
          color:    muted,
          anchor:   config.type === 'bar' ? 'end' : 'center',
          align:    config.type === 'bar' ? 'top' : function(ctx) {
            const data = ctx.dataset.data;
            const i    = ctx.dataIndex;
            if (i === 0) return 'right';
            const curr = data[i];
            const prev = data[i - 1];
            const next = i < data.length - 1 ? data[i + 1] : curr;
            return (curr >= prev && curr >= next) ? 'top' : 'bottom';
          },
          offset:   6,
          clamp:    true,
          font: { size: 10, family: 'Manrope, sans-serif', weight: '700' },
          formatter: (v, ctx) => {
            const f = fields[ctx.datasetIndex];
            if (Math.abs(v) < 0.01) return null;
            return fmtVal(v, config.mode, f);
          },
        } : { display: false },
      },
      scales: (() => {
        const axisInfo = getDualAxisInfo(config);

        /* Formato dominante do eixo Y esquerdo */
        const primaryFmt = (() => {
          if (config.mode === 'percent') return 'percent';
          if (axisInfo.needsDual) return axisInfo.primaryFormat;
          if (fields.every(f => f.format === 'percent'))  return 'percent';
          if (fields.every(f => f.format === 'days'))     return 'days';
          if (fields.every(f => !f.format || f.format === 'currency')) return 'currency';
          return 'number';
        })();

        const scalesObj = {
          x: {
            ticks: {
              color: muted,
              font:  { size: 11, family: 'Manrope, sans-serif' },
              maxRotation: 40,
              maxTicksLimit: 20,
            },
            grid: { color: border, lineWidth: 0.8 },
          },
          y: {
            position:     'left',
            beginAtZero:  false,
            ticks: {
              color: muted,
              font:  { size: 11, family: 'Manrope, sans-serif' },
              callback: v => fmtAxisTick(v, primaryFmt, config.mode),
            },
            grid: { color: border, lineWidth: 0.8 },
          },
        };

        if (axisInfo.needsDual) {
          scalesObj.y2 = {
            position:    'right',
            beginAtZero: false,
            grid: { drawOnChartArea: false },
            ticks: {
              color: PALETTE[1] || muted,
              font:  { size: 11, family: 'Manrope, sans-serif' },
              callback: v => fmtAxisTick(v, axisInfo.secondaryFormat, config.mode),
            },
          };
        }

        return scalesObj;
      })(),
    };
  }

  /* ── Render: botões de campo ────────────────────────── */
  function renderFieldButtons() {
    const el = document.getElementById('cbFieldButtons');
    if (!el) return;

    const ALWAYS = ['saldo_qt_qd', 'indice_qt_qd'];
    const impliedHeaders = {
      qt_total:    'QT — Quanto Tenho',
      qd_total:    'QD — Quanto Devo',
      saldo_qt_qd: 'Indicadores QT/QD',
    };

    let html = '';
    let inGroup = false;

    (typeof matrixRows !== 'undefined' ? matrixRows : []).forEach(row => {
      if (row.type === 'empty') return;

      if (row.type === 'section') {
        if (inGroup) html += '</div></div>';
        html += `<div class="cb-field-group"><div class="cb-field-group-label">${row.label}</div><div class="cb-field-pills">`;
        inGroup = true;
        return;
      }

      if (row.rowClass === 'row-header' && impliedHeaders[row.key]) {
        if (inGroup) html += '</div></div>';
        html += `<div class="cb-field-group"><div class="cb-field-group-label">${impliedHeaders[row.key]}</div><div class="cb-field-pills">`;
        inGroup = true;
      }

      if (!row.key) return;
      if (!ALWAYS.includes(row.key) && !isFieldVisible(row.key)) return;

      const idx = cbState.fields.indexOf(row.key);
      const sel = idx >= 0;
      html += `<button class="cb-field-btn${sel ? ' selected' : ''}" data-field="${row.key}" type="button">${sel ? `<span class="cb-order">${idx + 1}</span>` : ''}${getFieldLabel(row.key, row.label)}</button>`;
    });

    if (inGroup) html += '</div></div>';
    el.innerHTML = html;
  }

  /* ── Render: campos selecionados ────────────────────── */
  function renderSelected() {
    const el     = document.getElementById('cbSelectedFields');
    const countEl = document.getElementById('cbCount');
    if (!el) return;
    if (countEl) countEl.textContent = cbState.fields.length;

    if (!cbState.fields.length) {
      el.innerHTML = '<span class="txt-muted txt-sm">Nenhum campo selecionado. Clique nos campos acima para adicionar.</span>';
      return;
    }

    el.innerHTML = cbState.fields.map((key, i) => {
      const f = chartFieldCatalog.find(x => x.key === key);
      const lbl = f ? getFieldLabel(f.key, f.label) : key;
      return `<span class="cb-tag">
        <span class="cb-order">${i + 1}</span>
        ${lbl}
        <button class="cb-remove" data-remove="${key}" type="button" aria-label="Remover">×</button>
      </span>`;
    }).join('');
  }

  /* ── Toggle field selection ─────────────────────────── */
  function toggleField(key) {
    const idx = cbState.fields.indexOf(key);
    if (idx >= 0) cbState.fields.splice(idx, 1);
    else          cbState.fields.push(key);
    renderFieldButtons();
    renderSelected();
  }

  /* ── Render: gráficos salvos ────────────────────────── */
  function destroyAllSaved() {
    Object.values(savedInstances).forEach(c => { try { c.destroy(); } catch {} });
    savedInstances = {};
  }

  function renderSavedCharts() {
    const container = document.getElementById('savedChartsContainer');
    if (!container) return;
    destroyAllSaved();

    if (!savedCharts.length) { container.innerHTML = ''; return; }

    const total = savedCharts.length;
    container.innerHTML = savedCharts.map((ch, idx) => {
      const rangeLabel = { weeks: 'Semanas', months: 'Meses', years: 'Anos' }[ch.range] || ch.range;
      const typeLabel  = ch.type === 'line' ? 'Linha' : 'Barra';
      return `
      <div class="card saved-chart-card" data-chart-id="${ch.id}">
        <div class="card-header">
          <div>
            <p class="eyebrow">Gráfico salvo</p>
            <h2 class="card-title" id="ctitle-${ch.id}">${ch.name}</h2>
            <p class="txt-muted txt-xs">${ch.fields.length} indicador(es) · ${rangeLabel} · ${typeLabel} · ${ch.count} períodos</p>
          </div>
          <div class="card-actions" style="flex-wrap:wrap; gap:6px">
            <div class="chip-group">
              <button class="chip active" data-view="chart" data-cid="${ch.id}" type="button">Gráfico</button>
              <button class="chip"        data-view="both"  data-cid="${ch.id}" type="button">Ambos</button>
              <button class="chip"        data-view="table" data-cid="${ch.id}" type="button">Tabela</button>
            </div>
            <button class="chip${ch.showLabels ? ' active' : ''}" data-labels="${ch.id}" type="button">Rótulos</button>
            ${(typeof canEdit === 'function' ? canEdit() : true) ? `
            <button class="btn btn-ghost" data-edit="${ch.id}" type="button">✏️ Editar</button>
            <button class="btn btn-ghost" data-del="${ch.id}" type="button">Remover</button>` : ''}
          </div>
        </div>
        <div id="cedit-${ch.id}" class="chart-edit-panel hidden">
          <input type="text" class="chart-edit-name" value="${ch.name.replace(/"/g,'&quot;')}" placeholder="Nome do gráfico">
          <div class="chart-edit-period">
            <label class="chart-edit-period-label">Período</label>
            <select class="chart-edit-range">
              <option value="weeks"  ${ch.range==='weeks'  ?'selected':''}>Semanas</option>
              <option value="months" ${ch.range==='months' ?'selected':''}>Meses</option>
              <option value="years"  ${ch.range==='years'  ?'selected':''}>Anos</option>
            </select>
            <input type="number" class="chart-edit-count" value="${ch.count}" min="1" max="120" placeholder="Qtd">
          </div>
          <label class="chart-edit-pdf-label">
            <input type="checkbox" class="chart-edit-pdf"${ch.includePdf ? ' checked' : ''}> Incluir no relatório PDF
          </label>
          <div class="chart-edit-btns">
            ${idx > 0 ? `<button class="chip" data-move-up="${ch.id}" type="button">↑ Acima</button>` : ''}
            ${idx < total - 1 ? `<button class="chip" data-move-down="${ch.id}" type="button">↓ Abaixo</button>` : ''}
            <button class="btn" data-save-edit="${ch.id}" type="button">Salvar</button>
            <button class="btn btn-ghost" data-cancel-edit="${ch.id}" type="button">Cancelar</button>
          </div>
        </div>
        <div id="cw-${ch.id}" class="chart-canvas-outer">
          <canvas id="cc-${ch.id}"></canvas>
        </div>
        <div id="ct-${ch.id}" class="chart-data-table hidden"></div>
      </div>`;
    }).join('');

    savedCharts.forEach(ch => drawSaved(ch));
  }

  function drawSaved(ch) {
    if (!window.Chart) return;
    if (savedInstances[ch.id]) { try { savedInstances[ch.id].destroy(); } catch {} delete savedInstances[ch.id]; }

    /* Resetar canvas via innerHTML no container */
    const outer = document.getElementById(`cw-${ch.id}`);
    if (!outer) return;
    outer.innerHTML = `<canvas id="cc-${ch.id}"></canvas>`;

    const { labels, datasets, fields } = buildChartData(ch);
    const options = buildChartOptions(ch, ch.showLabels || false);
    const plugins = ch.showLabels && window.ChartDataLabels ? [ChartDataLabels] : [];

    /* Reflow antes de medir o canvas */
    setTimeout(() => {
      const canvas = document.getElementById(`cc-${ch.id}`);
      if (!canvas) return;
      try {
        savedInstances[ch.id] = new Chart(canvas, { type: ch.type, data: { labels, datasets }, options, plugins });
        fillTable(ch, labels, datasets, fields);
      } catch (e) { console.error('Saved chart error:', e); }
    }, 30);
  }

  function fillTable(ch, labels, datasets, fields) {
    const el = document.getElementById(`ct-${ch.id}`);
    if (!el) return;

    const headers = `<tr>
      <th>Período</th>
      ${datasets.map(d => `<th>${d.label}</th>`).join('')}
    </tr>`;

    const rows = labels.map((lbl, i) => `<tr>
      <td><strong>${lbl}</strong></td>
      ${datasets.map((d, di) => `<td>${fmtVal(d.data[i], ch.mode, fields[di])}</td>`).join('')}
    </tr>`).join('');

    el.innerHTML = `<table>
      <thead>${headers}</thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  /* ── Inicialização do builder ───────────────────────── */
  async function initBuilder() {
    await loadSaved();
    renderFieldButtons();
    renderSelected();
    const toggleNew = document.getElementById('cbToggleNew');
    if (toggleNew) toggleNew.style.display = (typeof canEdit === 'function' && !canEdit()) ? 'none' : '';
    renderSavedCharts();
  }

  /* ── Eventos do builder ─────────────────────────────── */
  function setupEvents() {
    /* Clique em campo disponível */
    const fieldBtns = document.getElementById('cbFieldButtons');
    if (fieldBtns) {
      fieldBtns.addEventListener('click', e => {
        const btn = e.target.closest('[data-field]');
        if (btn) toggleField(btn.dataset.field);
      });
    }

    /* Remover campo selecionado */
    const selectedEl = document.getElementById('cbSelectedFields');
    if (selectedEl) {
      selectedEl.addEventListener('click', e => {
        const btn = e.target.closest('[data-remove]');
        if (btn) toggleField(btn.dataset.remove);
      });
    }

    /* Chips de período */
    document.querySelectorAll('[data-cb-range]').forEach(b => b.addEventListener('click', () => {
      cbState.range = b.dataset.cbRange;
      cbState.count = RANGE_DEFAULTS[cbState.range] || 12;
      const inp = document.getElementById('cbCountInput');
      if (inp) inp.value = cbState.count;
      document.querySelectorAll('[data-cb-range]').forEach(x =>
        x.classList.toggle('active', x.dataset.cbRange === cbState.range));
    }));

    /* Chips de tipo */
    document.querySelectorAll('[data-cb-type]').forEach(b => b.addEventListener('click', () => {
      cbState.type = b.dataset.cbType;
      document.querySelectorAll('[data-cb-type]').forEach(x =>
        x.classList.toggle('active', x.dataset.cbType === cbState.type));
    }));

    /* Chips de modo */
    document.querySelectorAll('[data-cb-mode]').forEach(b => b.addEventListener('click', () => {
      cbState.mode = b.dataset.cbMode;
      document.querySelectorAll('[data-cb-mode]').forEach(x =>
        x.classList.toggle('active', x.dataset.cbMode === cbState.mode));
    }));

    /* Input de quantidade */
    const countInp = document.getElementById('cbCountInput');
    if (countInp) {
      countInp.addEventListener('input', () => {
        cbState.count = Math.max(1, Number(countInp.value) || 12);
      });
    }

    /* Pré-visualizar */
    const previewBtn = document.getElementById('cbPreview');
    if (previewBtn) {
      previewBtn.addEventListener('click', () => {
        if (!cbState.fields.length) { setFeedback('Selecione ao menos um campo para pré-visualizar.'); return; }

        /* Mostrar o wrapper */
        const wrap = document.getElementById('cbPreviewWrap');
        if (wrap) wrap.classList.remove('hidden');

        /* Destruir instância anterior via API oficial */
        if (cbPreviewInstance) { try { cbPreviewInstance.destroy(); } catch {} cbPreviewInstance = null; }

        /* Resetar o canvas via innerHTML — forma mais confiável de limpar estado do Chart.js */
        const outer = wrap ? wrap.querySelector('.chart-canvas-outer') : null;
        if (!outer || !window.Chart) return;
        outer.innerHTML = '<canvas id="cbCanvas"></canvas>';

        const { labels, datasets } = buildChartData(cbState);
        const options = buildChartOptions(cbState, false);

        /* setTimeout garante que o browser fez reflow e o canvas tem dimensões reais */
        setTimeout(() => {
          const canvas = document.getElementById('cbCanvas');
          if (!canvas) return;
          try {
            cbPreviewInstance = new Chart(canvas, { type: cbState.type, data: { labels, datasets }, options });
          } catch (e) { console.error('Preview chart error:', e); }
        }, 30);
      });
    }

    /* Salvar gráfico */
    const saveBtn = document.getElementById('cbSave');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        const nameEl = document.getElementById('cbName');
        const name   = nameEl ? nameEl.value.trim() : '';
        if (!name) {
          if (nameEl) { nameEl.focus(); nameEl.style.borderColor = 'var(--danger, #ef4444)'; setTimeout(() => nameEl.style.borderColor = '', 2000); }
          setFeedback('Informe um nome para o gráfico antes de salvar.');
          nameEl?.scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }
        if (!cbState.fields.length) { setFeedback('Selecione ao menos um campo.'); return; }

        const includePdf = document.getElementById('cbIncludePdf')?.checked ?? false;
        savedCharts.push({
          id:         crypto.randomUUID(),
          name,
          fields:     [...cbState.fields],
          range:      cbState.range,
          count:      cbState.count,
          type:       cbState.type,
          mode:       cbState.mode,
          showLabels: false,
          includePdf,
        });
        persistSaved();

        /* Reset builder */
        cbState.fields = [];
        if (nameEl) nameEl.value = '';
        renderFieldButtons();
        renderSelected();
        const wrap = document.getElementById('cbPreviewWrap');
        if (wrap) wrap.classList.add('hidden');
        if (cbPreviewInstance) { cbPreviewInstance.destroy(); cbPreviewInstance = null; }

        renderSavedCharts();
        setFeedback(`Gráfico "${name}" salvo com sucesso.`);
        if (typeof closeCbNew === 'function') closeCbNew();
      });
    }

    /* Limpar builder */
    const clearBtn = document.getElementById('cbClear');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        cbState.fields = [];
        const nameEl = document.getElementById('cbName');
        if (nameEl) nameEl.value = '';
        renderFieldButtons();
        renderSelected();
        const wrap = document.getElementById('cbPreviewWrap');
        if (wrap) wrap.classList.add('hidden');
        if (cbPreviewInstance) { cbPreviewInstance.destroy(); cbPreviewInstance = null; }
      });
    }

    /* Interações nos gráficos salvos (delegação) */
    const savedContainer = document.getElementById('savedChartsContainer');
    if (savedContainer) {
      savedContainer.addEventListener('click', e => {

        /* Alternar visualização (gráfico / ambos / tabela) */
        const viewBtn = e.target.closest('[data-view][data-cid]');
        if (viewBtn) {
          const cid   = viewBtn.dataset.cid;
          const view  = viewBtn.dataset.view;
          const wrap  = document.getElementById(`cw-${cid}`);
          const table = document.getElementById(`ct-${cid}`);

          savedContainer.querySelectorAll(`[data-view][data-cid="${cid}"]`).forEach(b =>
            b.classList.toggle('active', b === viewBtn));

          if (wrap)  wrap.classList.toggle('hidden', view === 'table');
          if (table) table.classList.toggle('hidden', view === 'chart');
          return;
        }

        /* Rótulos */
        const labelsBtn = e.target.closest('[data-labels]');
        if (labelsBtn) {
          const cid = labelsBtn.dataset.labels;
          const ch  = savedCharts.find(c => c.id === cid);
          if (ch) {
            ch.showLabels = !ch.showLabels;
            labelsBtn.classList.toggle('active', ch.showLabels);
            persistSaved();
            drawSaved(ch);
          }
          return;
        }

        /* Remover */
        const delBtn = e.target.closest('[data-del]');
        if (delBtn) {
          const cid = delBtn.dataset.del;
          const ch  = savedCharts.find(c => c.id === cid);
          if (!ch) return;
          if (!confirm(`Remover o gráfico "${ch.name}"?`)) return;
          if (savedInstances[cid]) { try { savedInstances[cid].destroy(); } catch {} delete savedInstances[cid]; }
          savedCharts = savedCharts.filter(c => c.id !== cid);
          persistSaved();
          const card = savedContainer.querySelector(`[data-chart-id="${cid}"]`);
          if (card) card.remove();
          return;
        }

        /* Editar — abrir/fechar painel de edição */
        const editBtn = e.target.closest('[data-edit]');
        if (editBtn) {
          document.getElementById(`cedit-${editBtn.dataset.edit}`)?.classList.toggle('hidden');
          return;
        }

        /* Cancelar edição */
        const cancelEditBtn = e.target.closest('[data-cancel-edit]');
        if (cancelEditBtn) {
          document.getElementById(`cedit-${cancelEditBtn.dataset.cancelEdit}`)?.classList.add('hidden');
          return;
        }

        /* Salvar edição de nome, período e quantidade */
        const saveEditBtn = e.target.closest('[data-save-edit]');
        if (saveEditBtn) {
          const cid = saveEditBtn.dataset.saveEdit;
          const ch  = savedCharts.find(c => c.id === cid);
          if (!ch) return;
          const nameInput  = document.querySelector(`#cedit-${cid} .chart-edit-name`);
          const rangeInput = document.querySelector(`#cedit-${cid} .chart-edit-range`);
          const countInput = document.querySelector(`#cedit-${cid} .chart-edit-count`);
          const newName    = nameInput?.value.trim();
          if (!newName) { if (nameInput) { nameInput.focus(); nameInput.style.borderColor = 'var(--danger,#ef4444)'; setTimeout(() => nameInput.style.borderColor = '', 2000); } return; }
          ch.name  = newName;
          if (rangeInput) ch.range = rangeInput.value;
          if (countInput) ch.count = Math.max(1, parseInt(countInput.value) || ch.count);
          const pdfInput = document.querySelector(`#cedit-${cid} .chart-edit-pdf`);
          if (pdfInput) ch.includePdf = pdfInput.checked;
          persistSaved();
          renderSavedCharts();
          return;
        }

        /* Mover para cima */
        const upBtn = e.target.closest('[data-move-up]');
        if (upBtn) {
          const cid = upBtn.dataset.moveUp;
          const idx = savedCharts.findIndex(c => c.id === cid);
          if (idx > 0) { [savedCharts[idx - 1], savedCharts[idx]] = [savedCharts[idx], savedCharts[idx - 1]]; persistSaved(); renderSavedCharts(); }
          return;
        }

        /* Mover para baixo */
        const downBtn = e.target.closest('[data-move-down]');
        if (downBtn) {
          const cid = downBtn.dataset.moveDown;
          const idx = savedCharts.findIndex(c => c.id === cid);
          if (idx >= 0 && idx < savedCharts.length - 1) { [savedCharts[idx], savedCharts[idx + 1]] = [savedCharts[idx + 1], savedCharts[idx]]; persistSaved(); renderSavedCharts(); }
          return;
        }
      });
    }
  }

  /* ── Override de renderChartsPanel ─────────────────── */
  window.renderChartsPanel = async function () { await initBuilder(); };

  /* ── Bootstrap ──────────────────────────────────────── */
  function bootstrap() {
    /* Registrar plugin de rótulos globalmente, com default desligado */
    if (window.Chart && window.ChartDataLabels) {
      Chart.register(ChartDataLabels);
      if (Chart.defaults.plugins && Chart.defaults.plugins.datalabels) {
        Chart.defaults.plugins.datalabels.display = false;
      }
    }
    setupEvents();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }

})();

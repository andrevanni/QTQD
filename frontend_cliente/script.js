const storageKey="qtqd_cliente_demo_v1";
const FIELD_CONFIG_KEY="qtqd_field_config_v1";
function canEdit(){const p=localStorage.getItem('qtqd_permissao_v1');return !p||p==='edita'}
const THEME_KEY="qtqd_cliente_theme";
const BRANDING_KEY="qtqd_branding_v1";
const defaultBranding={clientName:"Cliente Demonstração",clientLogoUrl:""};
const componentLabels=[["saldo_bancario","Saldo bancário"],["contas_receber","Contas a receber"],["cartoes","Cartões"],["convenios","Convênios"],["cheques","Cheques"],["trade_marketing","Trade marketing"],["outros_qt","Outros QT"],["estoque_custo","Estoque custo"],["contas_pagar","Contas a pagar"],["fornecedores","Fornecedores"],["investimentos_assumidos","Investimentos assumidos"],["outras_despesas_assumidas","Outras despesas assumidas"],["dividas","Dívidas"],["financiamentos","Financiamentos"],["tributos_atrasados","Tributos atrasados"],["acoes_processos","Ações e processos"],["faturamento_previsto_mes","Faturamento previsto no mês"],["compras_mes","Compras no mês"],["entrada_mes","Entrada no mês"],["venda_cupom_mes","Venda cupom no mês"],["venda_custo_mes","Venda custo no mês - CMV"],["lucro_liquido_mes","Lucro líquido no mês"],["pmp","PMP — Prazo Médio de Pagamento"],["pmv","PMV — Prazo Médio de Venda"],["pmv_avista","PMV À Vista"],["pmv_30","PMV 30 dias"],["pmv_60","PMV 60 dias"],["pmv_90","PMV 90 dias"],["pmv_120","PMV 120 dias"],["pmv_outros","PMV Outros"],["pme_excel","PME — Cobertura Média"],["cobertura_estoque_dia","Cobertura de Estoque (do Dia)"],["indice_faltas","Índice de Faltas %"],["excesso_curva_a","Excesso Curva A >90d"],["excesso_curva_b","Excesso Curva B >120d"],["excesso_curva_c","Excesso Curva C >150d"],["excesso_curva_d","Excesso Curva D >180d"]];
const defaultFieldConfig=Object.fromEntries(componentLabels.map(([k,l])=>[k,{label:l,visible:true}]));
const matrixRows=[{key:"qt_total",label:"QT (QUANTO TENHO)",format:"currency",rowClass:"row-header",icon:"💰",groupColor:"#2563eb"},{key:"saldo_bancario",label:"Saldo bancário",format:"currency"},{key:"contas_receber",label:"Contas a receber",format:"currency",rowClass:"row-subheader"},{key:"cartoes",label:"Cartões",format:"currency",subItem:true},{key:"convenios",label:"Convênios",format:"currency",subItem:true},{key:"cheques",label:"Cheques",format:"currency",subItem:true},{key:"trade_marketing",label:"Trade marketing",format:"currency",subItem:true},{key:"outros_qt",label:"Outros QT",format:"currency",subItem:true},{key:"estoque_custo",label:"Estoque (preço custo)",format:"currency"},{type:"empty"},{key:"qd_total",label:"QD (QUANTO DEVO)",format:"currency",rowClass:"row-header",icon:"📋",groupColor:"#ef4444"},{key:"contas_pagar",label:"Contas a pagar",format:"currency",rowClass:"row-subheader"},{key:"fornecedores",label:"Fornecedores",format:"currency",subItem:true},{key:"investimentos_assumidos",label:"Investimentos assumidos",format:"currency",subItem:true},{key:"outras_despesas_assumidas",label:"Outras despesas assumidas",format:"currency",subItem:true},{key:"dividas",label:"Dívidas",format:"currency",rowClass:"row-subheader"},{key:"financiamentos",label:"Financiamentos",format:"currency",subItem:true},{key:"tributos_atrasados",label:"Tributos atrasados",format:"currency",subItem:true},{key:"acoes_processos",label:"Ações e processos",format:"currency",subItem:true},{type:"empty"},{key:"saldo_qt_qd",label:"SALDO QT/QD",format:"currency",rowClass:"row-header",icon:"⚖️",groupColor:"#16a34a"},{key:"indice_qt_qd",label:"ÍNDICE QT/QD",format:"number",rowClass:"row-header",groupColor:"#16a34a"},{key:"saldo_sem_dividas",label:"Saldo sem dívidas",format:"currency"},{key:"indice_sem_dividas",label:"Índice sem dívidas",format:"number"},{key:"saldo_sem_dividas_sem_estoque",label:"Saldo sem dívidas e sem estoque",format:"currency"},{type:"empty"},{type:"section",label:"INFORMAÇÕES COMPLEMENTARES",icon:"📈",groupColor:"#7c3aed"},{key:"faturamento_previsto_mes",label:"Faturamento previsto no mês",format:"currency"},{key:"compras_mes",label:"Compras no mês",format:"currency"},{key:"entrada_mes",label:"Entrada no mês",format:"currency"},{key:"venda_cupom_mes",label:"Venda cupom no mês",format:"currency"},{key:"venda_custo_mes",label:"Venda custo no mês - CMV",format:"currency"},{key:"lucro_liquido_mes",label:"Lucro líquido no mês",format:"currency"},{type:"empty"},{type:"section",label:"INDICADORES OPERACIONAIS",icon:"⚙️",groupColor:"#0891b2"},{key:"indice_compra_venda",label:"ÍNDICE DE COMPRA/VENDA (CUSTO)",format:"percent"},{key:"indice_entrada_venda",label:"ÍNDICE DE ENTRADA/VENDA (CUSTO)",format:"percent"},{key:"margem_bruta",label:"MARGEM BRUTA NO MÊS",format:"percent"},{type:"empty"},{key:"pmp",label:"PMP — PRAZO MÉDIO DE PAGAMENTO",format:"days"},{key:"pmv",label:"PMV — PRAZO MÉDIO DE VENDA",format:"days",rowClass:"row-subheader"},{key:"pmv_avista",label:"PMV À VISTA",format:"days",subItem:true},{key:"pmv_30",label:"PMV 30 DIAS",format:"days",subItem:true},{key:"pmv_60",label:"PMV 60 DIAS",format:"days",subItem:true},{key:"pmv_90",label:"PMV 90 DIAS",format:"days",subItem:true},{key:"pmv_120",label:"PMV 120 DIAS",format:"days",subItem:true},{key:"pmv_outros",label:"PMV OUTROS",format:"days",subItem:true},{key:"pme_excel",label:"PME — COBERTURA MÉDIA",format:"days"},{key:"cobertura_estoque_dia",label:"COBERTURA DE ESTOQUE (DO DIA)",format:"days"},{key:"ciclo_financiamento",label:"CICLO DE FINANCIAMENTO",format:"days",rowClass:"row-header"},{type:"empty"},{key:"indice_faltas",label:"ÍNDICE DE FALTAS %",format:"percent"},{key:"excesso_curva_a",label:"EXCESSO CURVA A >90 DIAS",format:"currency"},{key:"excesso_curva_b",label:"EXCESSO CURVA B >120 DIAS",format:"currency"},{key:"excesso_curva_c",label:"EXCESSO CURVA C >150 DIAS",format:"currency"},{key:"excesso_curva_d",label:"EXCESSO CURVA D >180 DIAS",format:"currency"},{key:"excesso_total",label:"EXCESSO CRÍTICO TOTAL",format:"currency",rowClass:"row-header"},{key:"total_estoque_lancamentos",label:"TOTAL DE ESTOQUE EM LANÇAMENTOS",format:"currency"}];
const chartFieldCatalog=matrixRows.filter(r=>r.key).map(r=>({key:r.key,label:r.label,format:r.format||"currency"}));
const chartDefaults={weeks:12,months:3,years:2};
const chartState={range:"weeks",count:12,mode:"value",fields:["indice_qt_qd","saldo_qt_qd"]};
const form=document.getElementById("weeklyForm"),historyTable=document.getElementById("historyTable"),matrixTableWrap=document.getElementById("matrixTableWrap"),formCalculatedKpis=document.getElementById("formCalculatedKpis"),feedbackBox=document.getElementById("feedbackBox"),formModeBadge=document.getElementById("formModeBadge"),recordIdInput=document.getElementById("recordId"),connectionModeLabel=document.getElementById("connectionModeLabel"),chartFieldsGrid=document.getElementById("chartFieldsGrid"),chartRangeCountInput=document.getElementById("chartRangeCount"),chartPanelTitle=document.getElementById("chartPanelTitle");
let records=[],liquidityChartInstance=null,efficiencyChartInstance=null,financialTimelineChart=null;
window.QTQD_PORTAL = {
  applyApiRecords: function (apiRecords) {
    records = (apiRecords || []).map(apiRecordToLocal);
    saveRecords();
    renderAll();
  },
  isApiMode: function () { return isApiMode(); },
};
const $=id=>document.getElementById(id);
const getRuntimeConfig=()=>{const cfg=window.QTQD_APP_CONFIG||{mode:"simulation",tenantId:""};const storedTenant=localStorage.getItem("qtqd_tenant_id_v1");const hasJwt=!!localStorage.getItem("qtqd_jwt_v1");if(hasJwt&&storedTenant)return{...cfg,mode:"api",tenantId:storedTenant};return cfg};
const isApiMode=()=>{const r=getRuntimeConfig();return r.mode==="api"&&!!r.tenantId&&!!window.QTQD_API_CLIENT};
const parseMoney=v=>{if(typeof v==="number")return Number.isFinite(v)?v:0;const s=String(v??'').trim();if(!s)return 0;const neg=s.startsWith('-');const abs=neg?s.slice(1):s;const cleaned=abs.includes(',')?abs.replace(/\./g,'').replace(',','.'):abs;const n=Number(cleaned);return Number.isFinite(n)?(neg?-n:n):0};
const fmtNumInput=(v,dec=2)=>{const n=Number(v);return(Number.isFinite(n)&&n!==0)?n.toLocaleString('pt-BR',{minimumFractionDigits:dec,maximumFractionDigits:Math.max(dec,3)}):''};

const safeDivide=(a,b)=>b?a/b:null;
const fmtMoney=v=>new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL"}).format(Number(v||0));
const fmtMoneyShort=v=>{const n=Number(v||0),a=Math.abs(n),s=n<0?'-':'';if(a>=1e6)return`${s}R$ ${new Intl.NumberFormat("pt-BR",{maximumFractionDigits:2}).format(a/1e6)}M`;if(a>=1e3)return`${s}R$ ${new Intl.NumberFormat("pt-BR",{maximumFractionDigits:1}).format(a/1e3)}K`;return fmtMoney(v)};
const fmtNum=v=>v===null||v===undefined||Number.isNaN(v)?"-":new Intl.NumberFormat("pt-BR",{maximumFractionDigits:2}).format(v);
const fmtDays=v=>v===null||v===undefined||Number.isNaN(v)?"-":`${fmtNum(v)} dias`;
const fmtPercent=v=>v===null||v===undefined||Number.isNaN(v)?"-":`${new Intl.NumberFormat("pt-BR",{maximumFractionDigits:2}).format(Number(v)*100)}%`;
const fmtDate=v=>new Intl.DateTimeFormat("pt-BR",{dateStyle:"short"}).format(new Date(`${v}T00:00:00`));
const isoToBr=d=>d&&d.length===10?d.slice(8,10)+'/'+d.slice(5,7)+'/'+d.slice(0,4):d||'';
const brToIso=d=>d&&/^\d{2}\/\d{2}\/\d{4}$/.test(d)?d.slice(6,10)+'-'+d.slice(3,5)+'-'+d.slice(0,2):d;
const avg=arr=>arr.length?arr.reduce((s,v)=>s+Number(v||0),0)/arr.length:0;
const initials=name=>String(name||"CL").split(" ").filter(Boolean).slice(0,2).map(p=>p[0].toUpperCase()).join("")||"CL";
function renderConnectionMode(){const r=getRuntimeConfig();connectionModeLabel.textContent=r.mode==="api"&&r.tenantId?`Modo conectado: API real (${r.tenantId})`:"Modo atual: simulação local";const seedBtn=$("seedDemoButton");if(seedBtn)seedBtn.style.display=isApiMode()?"none":""}
function getBranding(){try{return {...defaultBranding,...JSON.parse(localStorage.getItem(BRANDING_KEY)||"{}")}}catch{return {...defaultBranding}}}
function getTheme(){return localStorage.getItem(THEME_KEY)||"dark"}
function applyTheme(theme=getTheme()){document.body.dataset.theme=theme;document.querySelectorAll("[data-theme-choice]").forEach(b=>b.classList.toggle("active",b.dataset.themeChoice===theme))}
function applyBranding(){const b=getBranding(),name=b.clientName||defaultBranding.clientName;document.querySelectorAll("#clientSidebarName,#clientTopName").forEach(n=>n.textContent=name);document.querySelectorAll("#clientSidebarFallback,#clientTopFallback").forEach(n=>n.textContent=initials(name));document.querySelectorAll("#clientSidebarLogo,#clientTopLogo").forEach(n=>{if(b.clientLogoUrl){n.src=b.clientLogoUrl;n.classList.add("visible")}else{n.removeAttribute("src");n.classList.remove("visible")}});document.querySelectorAll("#clientSidebarFallback,#clientTopFallback").forEach(n=>n.style.display=b.clientLogoUrl?"none":"grid")}
function getFieldConfig(){try{return {...defaultFieldConfig,...JSON.parse(localStorage.getItem(FIELD_CONFIG_KEY)||"{}")}}catch{return {...defaultFieldConfig}}}
const isFieldVisible=k=>getFieldConfig()[k]?.visible!==false;
const getFieldLabel=(k,f)=>getFieldConfig()[k]?.label?.trim()||f;
function applyFieldConfigToForm(){const cfg=getFieldConfig();componentLabels.forEach(([k,l])=>{const input=$(k),field=input?.closest(".field"),span=field?.querySelector("span");if(span)span.textContent=cfg[k]?.label?.trim()||l;if(field)field.style.display=cfg[k]?.visible===false?"none":""})}
function createRecordFromValues(v){const subCR=parseMoney(v.cartoes)+parseMoney(v.convenios)+parseMoney(v.cheques)+parseMoney(v.trade_marketing)+parseMoney(v.outros_qt);const cr=subCR>0?subCR:parseMoney(v.contas_receber);const subCP=parseMoney(v.fornecedores)+parseMoney(v.investimentos_assumidos)+parseMoney(v.outras_despesas_assumidas);const cp=subCP>0?subCP:parseMoney(v.contas_pagar);const subDiv=parseMoney(v.financiamentos)+parseMoney(v.tributos_atrasados)+parseMoney(v.acoes_processos);const divs=subDiv>0?subDiv:parseMoney(v.dividas);const qt=parseMoney(v.saldo_bancario)+cr+parseMoney(v.estoque_custo);const qd=cp+divs;const saldo=qt-qd;const pme=safeDivide(parseMoney(v.estoque_custo)*30,parseMoney(v.venda_custo_mes));const compra=safeDivide(cp*30,parseMoney(v.compras_mes));const venda=safeDivide(cr*30,parseMoney(v.venda_cupom_mes));const pmpInput=parseMoney(v.pmp);const pmvInput=parseMoney(v.pmv);const pmeExcel=parseMoney(v.pme_excel);const pmeParaCiclo=pmeExcel||pme||0;const ciclo=(pmpInput>0||pmvInput>0)?pmpInput-pmvInput-pmeParaCiclo:null;const excA=parseMoney(v.excesso_curva_a),excB=parseMoney(v.excesso_curva_b),excC=parseMoney(v.excesso_curva_c),excD=parseMoney(v.excesso_curva_d);return {...v,qt_total:qt,qd_total:qd,saldo_qt_qd:saldo,indice_qt_qd:safeDivide(qt,qd),saldo_sem_dividas:saldo+divs,indice_sem_dividas:safeDivide(qt,cp),saldo_sem_dividas_sem_estoque:saldo+divs-parseMoney(v.estoque_custo),prazo_medio_compra:compra,prazo_venda:venda,pme,ciclo_financiamento:ciclo,indice_compra_venda:safeDivide(parseMoney(v.compras_mes),parseMoney(v.venda_custo_mes)),indice_entrada_venda:safeDivide(parseMoney(v.entrada_mes),parseMoney(v.venda_custo_mes)),margem_bruta:safeDivide(parseMoney(v.venda_cupom_mes)-parseMoney(v.venda_custo_mes),parseMoney(v.venda_cupom_mes)),excesso_total:excA+excB+excC+excD}}
function seedRecords(){if(Array.isArray(window.QTQD_SEED)&&window.QTQD_SEED.length)return window.QTQD_SEED.map(i=>createRecordFromValues({...i,id:i.id||crypto.randomUUID()}));return[]}
function saveRecords(){localStorage.setItem(storageKey,JSON.stringify(records))}
function loadRecordsFromLocal(){const raw=localStorage.getItem(storageKey);if(!raw){records=seedRecords();saveRecords();return}try{records=JSON.parse(raw).map(i=>createRecordFromValues(i))}catch{records=seedRecords();saveRecords()}}
function extractComponentValues(record){const values={};componentLabels.forEach(([k])=>values[k]=parseMoney(record[k]));return values}
const apiRecordToLocal=api=>createRecordFromValues({id:api.id,weekDate:api.semana_referencia,status:api.status,...(api.valores||{})});
const localRecordToApi=record=>({tenant_id:getRuntimeConfig().tenantId,semana_referencia:record.weekDate,status:record.status,observacoes:null,...extractComponentValues(record)});
async function loadRecordsFromSource(){if(isApiMode()){records=(await window.QTQD_API_CLIENT.listAvaliacoes(getRuntimeConfig().tenantId)).map(apiRecordToLocal);saveRecords();return}loadRecordsFromLocal()}
window.loadRecordsFromSource=loadRecordsFromSource;
const publishedRecords=()=>records.filter(r=>r.status!=='rascunho');
const hasLancamentosData=()=>publishedRecords().some(r=>(r.total_estoque_lancamentos||0)>0);
function setFeedback(msg){feedbackBox.textContent=msg;feedbackBox.classList.remove("hidden")}
function clearFeedback(){feedbackBox.textContent="";feedbackBox.classList.add("hidden")}
function fillForm(record){recordIdInput.value=record.id;formModeBadge.textContent=`Editando ${fmtDate(record.weekDate)}`;$("weekDate").value=isoToBr(record.weekDate);$("recordStatus").value=record.status;componentLabels.forEach(([k])=>{const el=$(k);if(!el)return;const v=record[k];const disp=k==='indice_faltas'?(v||v===0)?fmtNumInput(v*100,2):'':(v||v===0)?fmtNumInput(v,2):'';el.value=disp;})}
function resetForm(){form.reset();recordIdInput.value="";formModeBadge.textContent="Nova semana";renderCalculatedPreview()}
function collectFormData(){const payload={id:recordIdInput.value||crypto.randomUUID(),weekDate:brToIso($("weekDate").value),status:$("recordStatus").value};componentLabels.forEach(([k])=>{const raw=parseMoney($(k).value);payload[k]=k==='indice_faltas'?raw/100:raw;});return createRecordFromValues(payload)}
const getLatestRecord=()=>[...publishedRecords()].sort((a,b)=>b.weekDate.localeCompare(a.weekDate))[0]||null;
function renderCalculatedPreview(record){const r=record||collectFormData();const items=[["Saldo QT/QD",fmtMoney(r.saldo_qt_qd),r.saldo_qt_qd>=0?"good":"bad"],["Indice QT/QD",fmtNum(r.indice_qt_qd),(r.indice_qt_qd||0)>=1?"good":"bad"],["Saldo sem dividas",fmtMoney(r.saldo_sem_dividas),"neutral"],["Indice sem dividas",fmtNum(r.indice_sem_dividas),"neutral"],["PME",fmtDays(r.pme),"neutral"],["Ciclo de financiamento",fmtDays(r.ciclo_financiamento),(r.ciclo_financiamento||0)<=0?"good":"bad"],["Índice compra/venda",fmtNum(r.indice_compra_venda),"neutral"],["Margem bruta",fmtPercent(r.margem_bruta),"neutral"]];formCalculatedKpis.innerHTML=items.map(([l,v,t])=>`<article class="kpi-card ${t}"><span>${l}</span><strong>${v}</strong></article>`).join("")}
function renderHistory(){const ordered=[...records].sort((a,b)=>b.weekDate.localeCompare(a.weekDate));const latest=getLatestRecord();historyTable.innerHTML=ordered.map(r=>`<tr class="${latest&&r.id===latest.id?"latest-row":""}"><td>${fmtDate(r.weekDate)}</td><td>${r.status}</td><td>${fmtMoney(r.qt_total)}</td><td>${fmtMoney(r.qd_total)}</td><td>${fmtMoney(r.saldo_qt_qd)}</td><td>${fmtNum(r.indice_qt_qd)}</td><td><div class="action-row"><button class="action-btn" type="button" data-action="edit" data-id="${r.id}">Editar</button><button class="action-btn" type="button" data-action="delete" data-id="${r.id}">Excluir</button><button class="action-btn" type="button" data-action="evaluate" data-id="${r.id}">Avaliar</button>${r.status==='rascunho'?`<button class="action-btn action-btn--primary" type="button" data-action="fechar" data-id="${r.id}">Fechar</button>`:''} ${isApiMode()?`<button class="action-btn" type="button" data-action="reenviar-pdf" data-id="${r.id}">Reenviar PDF</button>`:''}</div></td></tr>`).join("")}
function fmtMatrix(format,v){if(v===null||v===undefined||Number.isNaN(v))return"-";if(format==="number")return fmtNum(v);if(format==="days")return fmtDays(v);if(format==="percent")return fmtPercent(v);return fmtMoney(v)}
function matrixVal(r,key){const v=r[key];if(!v){if(key==="contas_receber")return(r.cartoes||0)+(r.convenios||0)+(r.cheques||0)+(r.trade_marketing||0)+(r.outros_qt||0);if(key==="contas_pagar")return(r.fornecedores||0)+(r.investimentos_assumidos||0)+(r.outras_despesas_assumidas||0);if(key==="dividas")return(r.financiamentos||0)+(r.tributos_atrasados||0)+(r.acoes_processos||0)}return v}
function populateYearFilter(){const sel=$("matrixYearFilter");if(!sel)return;const years=[...new Set(publishedRecords().map(r=>r.weekDate?.slice(0,4)).filter(Boolean))].sort((a,b)=>b-a);const cur=sel.value;sel.innerHTML=`<option value="">Todos os anos</option>`+years.map(y=>`<option value="${y}">${y}</option>`).join("");sel.value=years.includes(cur)?cur:""}
function renderMatrix(){const sel=$("matrixYearFilter");const yearFilter=sel?sel.value:"";let ordered=[...publishedRecords()].sort((a,b)=>b.weekDate.localeCompare(a.weekDate));if(yearFilter)ordered=ordered.filter(r=>r.weekDate?.startsWith(yearFilter));if(!ordered.length){matrixTableWrap.innerHTML=`<p class='muted' style='padding:24px'>${yearFilter?`Nenhuma semana em ${yearFilter}.`:"Nenhuma semana cadastrada."}</p>`;return}const configurableKeys=new Set(componentLabels.map(([k])=>k));const showLanc=hasLancamentosData();const visibleRows=matrixRows.filter(r=>(r.key!=="total_estoque_lancamentos"||showLanc)&&(!r.key||!configurableKeys.has(r.key)||isFieldVisible(r.key)));const rows=[];let gc='#2563eb';visibleRows.forEach(row=>{if(row.type==="empty"){rows.push(`<tr><td class="matrix-cell matrix-sticky row-empty" style="border-left:3px solid transparent"></td>${ordered.map(()=>`<td class="matrix-cell row-empty"></td>`).join("")}</tr>`);return}if(row.type==="section"){gc=row.groupColor||gc;const ico=row.icon?`<span class="matrix-icon">${row.icon}</span>`:'';rows.push(`<tr><td class="matrix-cell matrix-sticky row-section" style="border-left:3px solid ${gc}">${ico}${row.label}</td>${ordered.map(()=>`<td class="matrix-cell row-section"></td>`).join("")}</tr>`);return}if(row.rowClass==="row-header"){if(row.groupColor)gc=row.groupColor;const ico=row.icon?`<span class="matrix-icon">${row.icon}</span>`:'';const label=defaultFieldConfig[row.key]?getFieldLabel(row.key,row.label):row.label;rows.push(`<tr><td class="matrix-cell matrix-sticky row-header" style="border-left:3px solid ${gc}">${ico}${label}</td>${ordered.map(r=>`<td class="matrix-cell row-header">${fmtMatrix(row.format,matrixVal(r,row.key))}</td>`).join("")}</tr>`);return}if(row.rowClass==="row-subheader"){const label=defaultFieldConfig[row.key]?getFieldLabel(row.key,row.label):row.label;rows.push(`<tr><td class="matrix-cell matrix-sticky row-subheader" style="border-left:3px solid ${gc}80">${label}</td>${ordered.map(r=>`<td class="matrix-cell row-subheader">${fmtMatrix(row.format,matrixVal(r,row.key))}</td>`).join("")}</tr>`);return}const isDeep=row.subItem===true;const label=defaultFieldConfig[row.key]?getFieldLabel(row.key,row.label):row.label;const rc=isDeep?"matrix-cell matrix-subitem matrix-subitem-deep":"matrix-cell matrix-subitem";rows.push(`<tr><td class="${rc} matrix-sticky" style="border-left:3px solid ${gc}${isDeep?"18":"30"}">${label}</td>${ordered.map(r=>`<td class="${rc}">${fmtMatrix(row.format,matrixVal(r,row.key))}</td>`).join("")}</tr>`)});matrixTableWrap.innerHTML=`<div class="matrix-scroll"><table class="matrix-table"><thead><tr><th class="matrix-cell matrix-head matrix-sticky" style="border-left:3px solid transparent">COMPONENTES</th>${ordered.map(r=>`<th class="matrix-cell matrix-head">${fmtDate(r.weekDate)}<br><span class="muted">${r.status}</span></th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table></div>`}
function buildInspectorModel(){const ordered=[...publishedRecords()].sort((a,b)=>a.weekDate.localeCompare(b.weekDate));if(!ordered.length)return null;const latest=ordered[ordered.length-1];return{ordered,latest,qt:ordered.map(i=>i.qt_total),qd:ordered.map(i=>i.qd_total),saldo:ordered.map(i=>i.saldo_qt_qd),indice:ordered.map(i=>i.indice_qt_qd||0),pmp:ordered.map(i=>i.pmp||0),pmv:ordered.map(i=>i.pmv||0),pme:ordered.map(i=>i.pme_excel||i.pme||0),ciclo:ordered.map(i=>i.ciclo_financiamento||null)}}
function destroyInspectorCharts(){if(liquidityChartInstance)liquidityChartInstance.destroy();if(efficiencyChartInstance)efficiencyChartInstance.destroy();liquidityChartInstance=null;efficiencyChartInstance=null}
function parseInspectorMd(text){return text.split('\n').map(line=>{if(/^\*\*\d+\./.test(line))return`<div class="stream-section">${line.replace(/\*\*/g,'')}</div>`;if(line.startsWith('- '))return`<div class="stream-bullet">${line.slice(2).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')}</div>`;if(!line.trim())return'<div class="stream-spacer"></div>';return`<div class="stream-line">${line.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')}</div>`}).join('')}
function streamInspectorText(el,text){const statusEl=$('inspectorAnalysisStatus');if(statusEl){statusEl.className='insp-ai-status analyzing';statusEl.textContent='Analisando...'}el.innerHTML='<span class="insp-cursor"></span>';let i=0;const iv=setInterval(()=>{i+=5;const chunk=text.slice(0,i);el.innerHTML=parseInspectorMd(chunk)+'<span class="insp-cursor"></span>';if(i>=text.length){clearInterval(iv);el.innerHTML=parseInspectorMd(text);if(statusEl){statusEl.className='insp-ai-status done';statusEl.textContent='✓ Concluído'}}},12)}
function buildInspectorNarrative(m){
  const ordered=m.ordered, l=m.latest, n=ordered.length;
  const prev=n>=2?ordered[n-2]:null;
  const prev4=n>=5?ordered[n-5]:null;
  const idx=l.indice_qt_qd||0, pmp=l.pmp||0, pmv=l.pmv||0, pme=l.pme_excel||l.pme||0, ciclo=l.ciclo_financiamento;

  // ── Funções auxiliares ──
  const slope=(arr,w=8)=>{const d=arr.filter(v=>v!=null&&!isNaN(v)).slice(-w);const len=d.length;if(len<3)return 0;const xm=(len-1)/2,ym=d.reduce((a,b)=>a+b,0)/len;let num=0,den=0;d.forEach((y,i)=>{num+=(i-xm)*(y-ym);den+=(i-xm)**2;});return den?num/den:0;};
  const ma=(arr,w)=>{const d=arr.filter(v=>v!=null&&!isNaN(v)).slice(-w);return d.length?d.reduce((a,b)=>a+b,0)/d.length:0;};
  const pctDiff=(a,b)=>(a&&Math.abs(a)>0.01)?(b-a)/Math.abs(a):null;
  const fmtPct=v=>v===null?'':` (${v>=0?'+':''}${fmtNum(v*100)}%)`;
  const fmtDelta=v=>v===null?'':` (${v>=0?'+':''}${fmtMoneyShort(v)})`;
  const consec=(arr,dir)=>{let c=0;for(let i=arr.length-1;i>0;i--){if(dir==='up'&&arr[i]>arr[i-1])c++;else if(dir==='dn'&&arr[i]<arr[i-1])c++;else break;}return c;};

  // ── Tendências ──
  const idxSlope=slope(m.indice,8);
  const qtSlope=slope(m.qt,8);
  const qdSlope=slope(m.qd,8);
  const cicloVals=m.ciclo.filter(v=>v!=null);
  const cicloSlope=slope(cicloVals,8);
  const idxAvg4=ma(m.indice,4), idxAvg8=ma(m.indice,8);
  const pmpAvg=ma(m.pmp,8), pmvAvg=ma(m.pmv,8), pmeAvg=ma(m.pme,8);
  const idxProj4=idx+idxSlope*4;
  const idxConsecUp=consec(m.indice,'up'), idxConsecDn=consec(m.indice,'dn');

  // ── Variações semanais ──
  const dIdx=prev?idx-(prev.indice_qt_qd||0):null;
  const dQT=prev?l.qt_total-prev.qt_total:null;
  const dQD=prev?l.qd_total-prev.qd_total:null;
  const dSaldo=prev?l.saldo_qt_qd-prev.saldo_qt_qd:null;

  // Maiores movimentos nos componentes QT (semana a semana)
  const qtMoves=prev?[
    ['Cartões',       matrixVal(l,'cartoes'),    matrixVal(prev,'cartoes')],
    ['Convênios',     l.convenios||0,            prev.convenios||0],
    ['Saldo bancário',l.saldo_bancario||0,       prev.saldo_bancario||0],
    ['Estoque',       l.estoque_custo||0,        prev.estoque_custo||0],
    ['Trade marketing',l.trade_marketing||0,     prev.trade_marketing||0],
  ].map(([nm,v,p])=>[nm,v-p,pctDiff(p,v)]).filter(([,d])=>Math.abs(d)>500).sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,3):[];

  // Maiores movimentos nos componentes QD
  const qdMoves=prev?[
    ['Fornecedores',        l.fornecedores||0,              prev.fornecedores||0],
    ['Financiamentos',      l.financiamentos||0,            prev.financiamentos||0],
    ['Outras despesas',     l.outras_despesas_assumidas||0, prev.outras_despesas_assumidas||0],
    ['Investimentos',       l.investimentos_assumidos||0,   prev.investimentos_assumidos||0],
    ['Tributos atrasados',  l.tributos_atrasados||0,        prev.tributos_atrasados||0],
  ].map(([nm,v,p])=>[nm,v-p,pctDiff(p,v)]).filter(([,d])=>Math.abs(d)>500).sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,3):[];

  // ── Textos de tendência ──
  const sit=idx>=1.2?'confortável':idx>=1?'no limite do equilíbrio':idx>=0.8?'abaixo do ideal':'crítica';
  let tendTxt='';
  if(idxConsecDn>=3)tendTxt=`**${idxConsecDn}ª semana consecutiva de queda** no índice`;
  else if(idxConsecUp>=3)tendTxt=`**${idxConsecUp}ª semana consecutiva de recuperação**`;
  else if(Math.abs(idxSlope)<0.005)tendTxt='índice **estável** nas últimas semanas';
  else tendTxt=idxSlope>0?'tendência de **recuperação gradual**':'tendência de **deterioração gradual**';

  let projTxt='';
  if(n>=4&&Math.abs(idxSlope)>=0.003){
    const dir=idxSlope>0?'chegar a':'cair para';
    projTxt=`Mantida a velocidade atual, o índice deve ${dir} **${fmtNum(idxProj4)}** em 4 semanas.`;
  }

  // ── Situação do ciclo ──
  let cicloTxt='';
  if(ciclo!=null&&pmp>0&&pmv>0){
    const cicloMa=ma(cicloVals,8);
    const cicloDelta=cicloVals.length>=2?ciclo-cicloVals[cicloVals.length-2]:null;
    cicloTxt=`Ciclo de financiamento: **${fmtDays(ciclo)}** `;
    cicloTxt+=ciclo>=0?'(favorável — fornecedores financiam a operação)':'(desfavorável — farmácia financia o capital de giro)';
    if(cicloVals.length>=4)cicloTxt+=`, média histórica **${fmtDays(cicloMa)}**`;
    if(cicloDelta!=null&&Math.abs(cicloDelta)>=1)cicloTxt+=` — variou **${cicloDelta>=0?'+':''}${fmtNum(cicloDelta)} dias** na semana`;
    cicloTxt+='.';
  }

  // ── Seção de prazos comparada à média ──
  const prazosTxt=[];
  if(pmp>0){
    const diff=pmp-pmpAvg;
    prazosTxt.push('PMP **'+fmtDays(pmp)+'** '+(Math.abs(diff)>2?'(média '+fmtDays(pmpAvg)+', '+(diff>0?'+':'')+fmtNum(diff)+' dias)':'(em linha com a média)'));}
  if(pmv>0){
    const diff=pmv-pmvAvg;
    prazosTxt.push('PMV **'+fmtDays(pmv)+'** '+(Math.abs(diff)>2?'(média '+fmtDays(pmvAvg)+', '+(diff>0?'+':'')+fmtNum(diff)+' dias)':'(em linha com a média)'));}
  if(pme>0){
    const diff=pme-pmeAvg;
    prazosTxt.push('PME **'+fmtDays(pme)+'** '+(Math.abs(diff)>2?'(média '+fmtDays(pmeAvg)+', '+(diff>0?'+':'')+fmtNum(diff)+' dias)':'(em linha com a média)'));}

  // ── Riscos baseados em tendência ──
  const riscos=[];
  if(idxConsecDn>=2)riscos.push(`- **Índice em queda há ${idxConsecDn} semanas** — deterioração contínua exige ação antes que ultrapasse limites críticos.`);
  if(qdSlope>0&&qtSlope<qdSlope)riscos.push(`- **QD crescendo mais rápido que QT** — passivos avançam ${fmtMoneyShort(qdSlope)}/semana enquanto ativos crescem ${fmtMoneyShort(qtSlope)}/semana; pressão estrutural sobre o saldo.`);
  if(idx<1)riscos.push(`- **Índice abaixo de 1,0** — passivos superam ativos em **${fmtMoneyShort(Math.abs(l.saldo_qt_qd))}**. Cobertura insuficiente.`);
  if(l.saldo_bancario<0)riscos.push(`- **Saldo bancário negativo** (${fmtMoney(l.saldo_bancario)}) — saldo devedor em conta corrente, risco de inadimplência operacional.`);
  if(pme>0&&pme>pmeAvg*1.2)riscos.push(`- **PME ${fmtNum(((pme/pmeAvg)-1)*100)}% acima da média histórica** — estoque acumulando; capital imobilizado acima do padrão operacional.`);
  if(pmv>0&&pmp>0&&pmv>pmp)riscos.push(`- **PMV (${fmtDays(pmv)}) maior que PMP (${fmtDays(pmp)})** — farmácia paga antes de receber; ciclo desfavorável estruturalmente.`);
  if(ciclo!=null&&cicloSlope<-1&&cicloVals.length>=4)riscos.push(`- **Ciclo piorando ${fmtNum(Math.abs(cicloSlope))} dias/semana** nas últimas semanas — tendência de aperto no capital de giro.`);
  if((l.excesso_total||0)>0)riscos.push(`- **Excesso de estoque: ${fmtMoney(l.excesso_total)}** imobilizado acima de 90 dias — capital que poderia reduzir o QD.`);
  if((l.indice_faltas||0)>0.05)riscos.push(`- **Índice de faltas ${fmtPercent(l.indice_faltas)}** — ruptura acima de 5% impacta faturamento e fidelidade do cliente.`);
  if(!riscos.length)riscos.push('- Nenhum risco estrutural identificado nesta semana. Manter monitoramento regular.');

  // ── Recomendações data-driven ──
  const recs=[];
  if(idxConsecDn>=2)recs.push(`Identificar e reduzir o componente de **QD que mais cresceu** nas últimas ${idxConsecDn} semanas para reverter a queda do índice.`);
  if(qdSlope>0&&qdSlope>Math.abs(qtSlope))recs.push(`Conter o crescimento do QD — passivos avançam **${fmtMoneyShort(qdSlope)}/semana**; avaliar renegociação ou antecipação de pagamentos de maior custo.`);
  if(pmp>0&&pmp<45)recs.push(`Negociar extensão de prazo com fornecedores — PMP atual de **${fmtDays(pmp)}** está abaixo do referencial de 45 dias.`);
  if(pme>0&&pme>pmeAvg*1.15)recs.push(`Acelerar giro do estoque — PME ${fmtNum(((pme/pmeAvg)-1)*100)}% acima da média. Priorizar produtos de maior saída e reavaliar mix de compras.`);
  if((l.excesso_total||0)>l.qt_total*0.05)recs.push(`Trabalhar ativamente o excesso crítico de **${fmtMoney(l.excesso_total)}** — liquidação ou devolução libera capital para reduzir QD.`);
  if(recs.length<3)recs.push(`Manter monitoramento semanal do **Índice QT/QD** (atual ${fmtNum(idx)}, média 4 sem. ${fmtNum(idxAvg4)}).`);
  if(recs.length<3)recs.push(`Revisar composição do QD e priorizar quitação dos passivos de maior custo financeiro.`);

return`**1. Diagnóstico — ${fmtDate(l.weekDate)}**
Índice QT/QD de **${fmtNum(idx)}** — situação ${sit}${prev&&dIdx!==null?`, variação de **${dIdx>=0?'+':''}${fmtNum(dIdx)}** na semana`:''}.${idx!==idxAvg4&&n>=4?` Média das últimas 4 semanas: **${fmtNum(idxAvg4)}** — índice está **${idx>idxAvg4?'acima':'abaixo'} da própria média recente**.`:''}
${tendTxt}${projTxt?' — '+projTxt:''}

**2. Movimentações da Semana**
${dQT!==null?`QT ${dQT>=0?'cresceu':'recuou'} **${fmtMoneyShort(Math.abs(dQT))}**${fmtPct(pctDiff(prev.qt_total,l.qt_total))} · QD ${dQD>=0?'cresceu':'recuou'} **${fmtMoneyShort(Math.abs(dQD))}**${fmtPct(pctDiff(prev.qd_total,l.qd_total))} · Saldo ${dSaldo>=0?'melhorou':'piorou'} **${fmtMoneyShort(Math.abs(dSaldo))}**.`:'Primeira semana registrada — sem variação anterior para comparar.'}
${qtMoves.length?`Destaques no QT: ${qtMoves.map(([nm,d,p])=>`**${nm}** ${d>=0?'+':''}${fmtMoneyShort(d)}${fmtPct(p)}`).join(' · ')}.`:''}
${qdMoves.length?`Destaques no QD: ${qdMoves.map(([nm,d,p])=>`**${nm}** ${d>=0?'+':''}${fmtMoneyShort(d)}${fmtPct(p)}`).join(' · ')}.`:''}
${prev4&&idx!==null?`Em relação a 4 semanas atrás, o índice ${idx>(prev4.indice_qt_qd||0)?'avançou':'recuou'} de **${fmtNum(prev4.indice_qt_qd||0)}** para **${fmtNum(idx)}** (${(idx-(prev4.indice_qt_qd||0))>=0?'+':''}${fmtNum(idx-(prev4.indice_qt_qd||0))}).`:''}

**3. Tendência e Projeção**
${n>=4?`Velocidade média do índice: **${idxSlope>=0?'+':''}${fmtNum(idxSlope*100)}% por semana** nas últimas ${Math.min(n,8)} semanas. QT ${qtSlope>=0?'cresce':'recua'} **${fmtMoneyShort(Math.abs(qtSlope))}/semana**, QD ${qdSlope>=0?'cresce':'recua'} **${fmtMoneyShort(Math.abs(qdSlope))}/semana**.`:'Histórico insuficiente para calcular tendência (mínimo 4 semanas).'}
${projTxt}
${n>=8?`Comparando com a média de 8 semanas (índice ${fmtNum(idxAvg8)}): situação atual está **${idx>idxAvg8?'melhor':'pior'} que a média histórica recente** em **${fmtNum(Math.abs(idx-idxAvg8)*100)}%**.`:''}

**4. Prazos e Ciclo**
${prazosTxt.length?prazosTxt.join(' · ')+'.':`PMP, PMV e PME não informados para este período.`}
${cicloTxt||'Ciclo não calculado — informe PMP e PMV.'}

**5. Pontos de Atenção**
${riscos.join('\n')}

**6. Recomendações**
${recs.map((r,i)=>`- ${r}`).join('\n')}`}
function renderCompBars(elId,items,total,palette){const el=$(elId);if(!el)return;el.innerHTML=items.filter(([,v])=>v>0).map(([label,val],i)=>{const pct=total>0?(val/total*100):0;const color=palette[i%palette.length];return`<div class="comp-bar-item"><div class="comp-bar-meta"><span>${label}</span><span><strong>${fmtMoney(val)}</strong> <span class="comp-bar-pct">${fmtNum(pct)}%</span></span></div><div class="comp-bar-track"><div class="comp-bar-fill" style="width:${Math.max(pct,1)}%;background:${color}"></div></div></div>`}).join('')||'<p class="muted">Sem dados.</p>'}
function renderInspector(){const m=buildInspectorModel();if(!m){$('inspectorInitial')?.classList.remove('hidden');$('inspectorContent')?.classList.add('hidden');return}$('inspectorInitial')?.classList.add('hidden');$('inspectorContent')?.classList.remove('hidden');const l=m.latest,idx=l.indice_qt_qd||0,pmp=l.pmp||0,pmv=l.pmv||0,pme=l.pme_excel||l.pme||0,ciclo=l.ciclo_financiamento,avgIdx=avg(m.indice);const idxClass=idx>=1.1?'good':idx>=1?'warn':'bad';const cicloClass=ciclo!=null?(ciclo>=10?'good':ciclo>=-10?'warn':'bad'):'blue';$('inspectorHero').innerHTML=[['Saldo QT/QD',fmtMoneyShort(l.saldo_qt_qd),l.saldo_qt_qd>=0?'good':'bad',fmtMoney(l.saldo_qt_qd)],['Índice QT/QD',fmtNum(idx),idxClass,idx>=1?'Cobertura suficiente':'Cobertura insuficiente'],['QT Total',fmtMoneyShort(l.qt_total),'blue',`Média: ${fmtMoneyShort(avg(m.qt))}`],['QD Total',fmtMoneyShort(l.qd_total),'blue',`Média: ${fmtMoneyShort(avg(m.qd))}`]].map(([label,val,cls,sub])=>`<article class="inspector-card inspector-metric ${cls}"><span>${label}</span><strong>${val}</strong><span class="insp-kpi-sub">${sub}</span></article>`).join('');const semItems=[['Liquidez',fmtNum(idx),idx>=1.1?'good':idx>=1?'warning':'bad'],['Saldo',fmtMoneyShort(l.saldo_qt_qd),l.saldo_qt_qd>=0?'good':'bad'],['PMP',pmp>0?fmtDays(pmp):'—',pmp>=45?'good':pmp>=30?'warning':pmp>0?'bad':'neutral'],['PMV',pmv>0?fmtDays(pmv):'—',pmv>0&&pmv<=30?'good':pmv<=45?'warning':pmv>0?'bad':'neutral'],['PME',pme>0?fmtDays(pme):'—',pme>0&&pme<=60?'good':pme<=90?'warning':pme>0?'bad':'neutral'],['Ciclo',ciclo!=null?fmtDays(ciclo):'—',cicloClass]];$('inspectorSemaphore').innerHTML=semItems.map(([l2,v,s])=>`<article class="semaphore-item ${s}"><span>${l2}</span><strong>${v}</strong></article>`).join('');const QT_PALETTE=['#2563eb','#3b82f6','#60a5fa','#93c5fd','#bfdbfe','#dbeafe','#eff6ff'];const QD_PALETTE=['#ef4444','#f87171','#fca5a5','#dc2626','#b91c1c','#991b1b'];renderCompBars('inspectorQtBars',[['Estoque custo',l.estoque_custo||0],['Cartões',matrixVal(l,'cartoes')],['Convênios',matrixVal(l,'convenios')],['Saldo bancário',Math.max(l.saldo_bancario||0,0)],['Trade marketing',l.trade_marketing||0],['Cheques',l.cheques||0],['Outros QT',l.outros_qt||0]],l.qt_total,QT_PALETTE);renderCompBars('inspectorQdBars',[['Financiamentos',l.financiamentos||0],['Fornecedores',l.fornecedores||0],['Outras despesas',l.outras_despesas_assumidas||0],['Investimentos assumidos',l.investimentos_assumidos||0],['Tributos atrasados',l.tributos_atrasados||0],['Ações e processos',l.acoes_processos||0]],l.qd_total,QD_PALETTE);$('inspectorTrendTable').innerHTML=`<table><thead><tr><th>Indicador</th><th>Atual</th><th>Média</th></tr></thead><tbody>${[['QT Total',fmtMoney(l.qt_total),fmtMoney(avg(m.qt))],['QD Total',fmtMoney(l.qd_total),fmtMoney(avg(m.qd))],['Saldo QT/QD',fmtMoney(l.saldo_qt_qd),fmtMoney(avg(m.saldo))],['Índice QT/QD',fmtNum(idx),fmtNum(avgIdx)],['PMP',pmp>0?fmtDays(pmp):'—',avg(m.pmp)>0?fmtDays(avg(m.pmp)):'—'],['PMV',pmv>0?fmtDays(pmv):'—',avg(m.pmv)>0?fmtDays(avg(m.pmv)):'—'],['PME',pme>0?fmtDays(pme):'—',avg(m.pme)>0?fmtDays(avg(m.pme)):'—'],['Ciclo',ciclo!=null?fmtDays(ciclo):'—','—']].map(([lbl,cur,av])=>`<tr><td>${lbl}</td><td>${cur}</td><td>${av}</td></tr>`).join('')}</tbody></table>`;const risks=[(idx<1)?{t:'Índice QT/QD abaixo de 1,0 — passivos superam os ativos.',i:'⚠️'}:null,(l.saldo_bancario||0)<0?{t:'Saldo bancário negativo — saldo devedor em conta.',i:'🔴'}:null,ciclo!=null&&ciclo<-15?{t:`Ciclo de financiamento negativo (${fmtDays(ciclo)}) — farmácia precisa financiar ${fmtDays(Math.abs(ciclo))} de capital de giro.`,i:'⚠️'}:null,(pme||0)>90?{t:`PME elevado (${fmtDays(pme)}) — estoque com giro lento.`,i:'⚠️'}:null,(l.financiamentos||0)>(l.qd_total||0)*0.45?{t:'Financiamentos representam mais de 45% do QD.',i:'📋'}:null].filter(Boolean);$('inspectorRisks').innerHTML=risks.length?risks.map(r=>`<div class="insp-risk-item"><span class="insp-risk-icon">${r.i}</span>${r.t}</div>`).join(''):`<div class="insp-action-item">Nenhum risco crítico identificado no período atual.</div>`;const actions=[idx<1?`Priorizar aumento do **Índice QT/QD** (atual ${fmtNum(idx)}) acima de 1,0 — passivos superam os ativos.`:idx<1.2?`Manter o **Índice QT/QD** (atual ${fmtNum(idx)}) acima de 1,0 — buscar crescimento contínuo do saldo.`:`Manter o **Índice QT/QD** saudável (atual ${fmtNum(idx)}) — continuar ampliando o saldo líquido.`,pmp>0&&pmp<45?`Negociar extensão de prazo com fornecedores (PMP atual ${fmtDays(pmp)}).`:`Manter ou ampliar o prazo médio de pagamento (PMP: ${pmp>0?fmtDays(pmp):'a informar'}).`,(l.estoque_custo||0)>l.qt_total*0.45?`Avaliar giro de estoque — representa ${fmtNum((l.estoque_custo/l.qt_total)*100)}% do QT.`:'Manter giro de estoque saudável.',`Revisar composição do QD e priorizar quitação de passivos de maior custo.`];$('inspectorActions').innerHTML=actions.map((a,i)=>`<div class="insp-action-item"><span class="insp-action-num">${i+1}</span><span>${a.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')}</span></div>`).join('');$('inspectorDataTable').innerHTML=`<table><thead><tr><th>Semana</th><th>QT</th><th>QD</th><th>Saldo</th><th>Índice</th><th>PMP</th><th>PMV</th><th>PME</th><th>Ciclo</th></tr></thead><tbody>${[...m.ordered].reverse().map(r=>`<tr><td>${fmtDate(r.weekDate)}</td><td>${fmtMoney(r.qt_total)}</td><td>${fmtMoney(r.qd_total)}</td><td class="${r.saldo_qt_qd>=0?'txt-good':'txt-bad'}">${fmtMoney(r.saldo_qt_qd)}</td><td class="${(r.indice_qt_qd||0)>=1?'txt-good':'txt-bad'}">${fmtNum(r.indice_qt_qd)}</td><td>${r.pmp>0?fmtDays(r.pmp):'—'}</td><td>${r.pmv>0?fmtDays(r.pmv):'—'}</td><td>${(r.pme_excel||r.pme)>0?fmtDays(r.pme_excel||r.pme):'—'}</td><td>${r.ciclo_financiamento!=null?fmtDays(r.ciclo_financiamento):'—'}</td></tr>`).join('')}</tbody></table>`;streamInspectorText($('inspectorNarrative'),buildInspectorNarrative(m))}
function generateInspectorCharts(){const m=buildInspectorModel();if(!m||!window.Chart)return;destroyInspectorCharts();const slice=m.ordered.slice(-52);const labels=slice.map(i=>fmtDate(i.weekDate)),ink=getComputedStyle(document.body).getPropertyValue('--ink').trim(),muted=getComputedStyle(document.body).getPropertyValue('--muted').trim();efficiencyChartInstance=new Chart($('efficiencyChart'),{type:'line',data:{labels,datasets:[{label:'Índice QT/QD',data:slice.map(i=>i.indice_qt_qd||0),borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,.1)',tension:.3,fill:false,yAxisID:'y2',pointRadius:slice.length>30?1:3},{label:'QT',data:slice.map(i=>i.qt_total),borderColor:'#16a34a',backgroundColor:'rgba(22,163,74,.08)',tension:.3,fill:false,pointRadius:0},{label:'QD',data:slice.map(i=>i.qd_total),borderColor:'#ef4444',backgroundColor:'rgba(239,68,68,.08)',tension:.3,fill:false,pointRadius:0},{label:'Saldo',data:slice.map(i=>i.saldo_qt_qd),borderColor:'#f59e0b',tension:.3,fill:false,pointRadius:0}]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{labels:{color:ink,boxWidth:12,font:{size:11}}}},scales:{x:{ticks:{color:muted,maxTicksLimit:12,font:{size:10}}},y:{ticks:{color:muted,callback:v=>fmtNum(v/1e6)+'M'},position:'left'},y2:{ticks:{color:'#2563eb',callback:v=>fmtNum(v)},position:'right',grid:{drawOnChartArea:false}}}}})}
async function generateInspectorPdf(){renderInspector();generateInspectorCharts();await new Promise(r=>setTimeout(r,1000));const m=buildInspectorModel();const narrative=$("inspectorNarrative");if(m&&narrative){narrative.innerHTML=parseInspectorMd(buildInspectorNarrative(m))}const statusEl=$("inspectorAnalysisStatus");if(statusEl){statusEl.className="insp-ai-status done";statusEl.textContent="✓ Concluído"}const b=getBranding();const pName=$("printClientName"),pLogo=$("printClientLogo"),pDate=$("printDate");if(pName)pName.textContent=b.clientName||"—";if(pDate)pDate.textContent="Gerado em "+new Date().toLocaleString("pt-BR",{dateStyle:"short",timeStyle:"short"});if(pLogo){if(b.clientLogoUrl){pLogo.src=b.clientLogoUrl;pLogo.style.display="block"}else pLogo.style.display="none"}window.print()}
function setSidebarCollapsed(collapse){document.body.classList.remove("sidebar-collapsed","sidebar-open")}
function openSection(id){document.querySelectorAll(".section-view").forEach(s=>s.classList.toggle("hidden",s.id!==id));document.querySelectorAll(".nav-link[data-section]").forEach(b=>b.classList.toggle("active",b.dataset.section===id));if(id==="painel"){populateYearFilter();renderMatrix()}if(id==="graficos")renderChartsPanel();if(id==="inspetor"){renderInspector();generateInspectorCharts()}setSidebarCollapsed(id!=="cadastro")}
document.getElementById("matrixYearFilter")?.addEventListener("change",()=>renderMatrix());
function renderChartFieldOptions(){const ALWAYS=['saldo_qt_qd','indice_qt_qd'];let html='';let inGroup=false;let groupImplied='';const impliedHeaders={qt_total:'QT — Quanto Tenho',qd_total:'QD — Quanto Devo',saldo_qt_qd:'Indicadores QT/QD'};matrixRows.forEach(row=>{if(row.type==='empty')return;if(row.type==='section'){if(inGroup)html+='</div></div>';html+=`<div class="chart-field-group"><div class="chart-field-group-label">${row.label}</div><div class="chart-field-pills">`;inGroup=true;return}if(row.rowClass==='row-header'&&impliedHeaders[row.key]){if(inGroup)html+='</div></div>';html+=`<div class="chart-field-group"><div class="chart-field-group-label">${impliedHeaders[row.key]}</div><div class="chart-field-pills">`;inGroup=true}if(!row.key)return;if(!ALWAYS.includes(row.key)&&!isFieldVisible(row.key))return;const chk=chartState.fields.includes(row.key)?'checked':'';const lbl=getFieldLabel(row.key,row.label);html+=`<label class="chart-field-option"><input type="checkbox" value="${row.key}" ${chk}><span>${lbl}</span></label>`});if(inGroup)html+='</div></div>';chartFieldsGrid.innerHTML=html;chartFieldsGrid.querySelectorAll('input[type=checkbox]').forEach(cb=>cb.addEventListener('change',()=>{chartState.fields=Array.from(chartFieldsGrid.querySelectorAll('input:checked')).map(i=>i.value);renderChartsPanel()}))}
function aggregateRecords(range,count){const ordered=[...publishedRecords()].sort((a,b)=>a.weekDate.localeCompare(b.weekDate));if(range==="weeks")return ordered.slice(-count).map(i=>({label:fmtDate(i.weekDate),record:i}));const grouped=new Map();ordered.forEach(i=>{const d=new Date(`${i.weekDate}T00:00:00`);const key=range==="months"?`${String(d.getMonth()+1).padStart(2,"0")}/${d.getFullYear()}`:`${d.getFullYear()}`;grouped.set(key,i)});return Array.from(grouped.entries()).slice(-count).map(([label,record])=>({label,record}))}
function toPctSeries(values){const base=Number(values[0]||0);if(!base)return values.map(()=>0);return values.map(v=>((Number(v||0)-base)/Math.abs(base))*100)}
function destroyTimelineChart(){if(financialTimelineChart)financialTimelineChart.destroy();financialTimelineChart=null}
function renderChartsPanel(){renderChartFieldOptions();if(!window.Chart)return;const points=aggregateRecords(chartState.range,Math.max(1,Number(chartState.count)||chartDefaults[chartState.range]));const labels=points.map(p=>p.label),ink=getComputedStyle(document.body).getPropertyValue("--ink").trim(),muted=getComputedStyle(document.body).getPropertyValue("--muted").trim(),palette=["#2563eb","#ff8a7a","#ffd166","#7c9dfb","#8f6bff","#57cc99"];const fields=chartFieldCatalog.filter(f=>chartState.fields.includes(f.key));chartPanelTitle.textContent=fields.length?fields.map(f=>getFieldLabel(f.key,f.label)).join(" | "):"Selecione ao menos um campo";destroyTimelineChart();financialTimelineChart=new Chart($("financialTimelineChart"),{type:"line",data:{labels,datasets:fields.map((f,i)=>{const raw=points.map(p=>Number(p.record[f.key]||0));return{label:getFieldLabel(f.key,f.label),data:chartState.mode==="percent"?toPctSeries(raw):raw,borderColor:palette[i%palette.length],backgroundColor:`${palette[i%palette.length]}33`,tension:.28,fill:false}})},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},scales:{x:{ticks:{color:muted}},y:{ticks:{color:muted,callback:v=>chartState.mode==="percent"?`${fmtNum(v)}%`:fmtNum(v)}}}}})}
function renderAll(){renderConnectionMode();applyFieldConfigToForm();renderHistory();populateYearFilter();renderMatrix();renderCalculatedPreview(getLatestRecord()||undefined);renderInspector();generateInspectorCharts();renderChartsPanel()}
window.renderAll=renderAll;
form.addEventListener("submit",async e=>{e.preventDefault();clearFeedback();const record=collectFormData();if(!record.weekDate){setFeedback("Informe a data da semana antes de salvar.");return}const duplicate=records.find(i=>i.weekDate===record.weekDate&&i.id!==record.id);if(duplicate){setFeedback("Ja existe uma avaliacao cadastrada para esta semana.");return}const index=records.findIndex(i=>i.id===record.id);try{if(isApiMode()){if(index>=0){const previousStatus=records[index]?.status;const closing=record.status==='fechada'&&previousStatus==='rascunho';if(closing)setFeedback("Fechando semana e enviando e-mail...");const api=await window.QTQD_API_CLIENT.updateAvaliacao(record.id,{semana_referencia:record.weekDate,status:record.status,valores:extractComponentValues(record)});records[index]=apiRecordToLocal(api);setFeedback(closing?"Semana fechada. E-mail enviado para os destinatarios cadastrados.":"Semana atualizada na API com sucesso.")}else{const createPayload = localRecordToApi(record);const u = (window.QTQD_MULTILOJA && window.QTQD_MULTILOJA.activeUnit) ? window.QTQD_MULTILOJA.activeUnit() : null;if (u && (u.grupo_id || u.loja_id)) { createPayload.grupo_id = u.grupo_id || null; createPayload.loja_id = u.loja_id || null; }const api = await window.QTQD_API_CLIENT.createAvaliacao(createPayload);records.unshift(apiRecordToLocal(api));setFeedback("Semana cadastrada na API com sucesso.")}}else{if(index>=0){records[index]=record;setFeedback("Semana atualizada com sucesso.")}else{records.push(record);setFeedback("Semana cadastrada com sucesso.")}saveRecords()}}catch(error){setFeedback(`Falha ao salvar na API: ${error.message}`);return}saveRecords();renderAll();resetForm()});
$("resetFormButton").addEventListener("click",()=>{clearFeedback();resetForm()});
$("newEntryButton").addEventListener("click",()=>{openSection("cadastro");resetForm()});
$("evaluateButton").addEventListener("click",()=>{openSection("painel");setFeedback("Painel de avaliacao gerado com os dados salvos.")});
$("openInspectorButton").addEventListener("click",()=>{clearFeedback();openSection("inspetor")});
$("openGraphsButton").addEventListener("click",()=>{clearFeedback();openSection("graficos")});
$("refreshInspectorButton").addEventListener("click",()=>{renderInspector();generateInspectorCharts();setFeedback("Analise do Inspetor IA atualizada.")});
$("downloadPdfButton").addEventListener("click",()=>generateInspectorPdf());
$("seedDemoButton").addEventListener("click",()=>{if(isApiMode()){setFeedback("Recarregar base demo funciona apenas no modo de simulacao local.");return}records=seedRecords();saveRecords();renderAll();resetForm();setFeedback("Base inicial recarregada.")});
$("toggleFocusButton").addEventListener("click",()=>document.body.classList.add("focus-painel"));
$("backFromPanelButton").addEventListener("click",()=>document.body.classList.remove("focus-painel"));
document.querySelectorAll(".nav-link").forEach(b=>b.addEventListener("click",()=>{clearFeedback();openSection(b.dataset.section);if(b.dataset.section==='excesso')window.QTQD_EXCESSO?.init?.()}));
document.querySelectorAll("[data-theme-choice]").forEach(b=>b.addEventListener("click",()=>{localStorage.setItem(THEME_KEY,b.dataset.themeChoice);applyTheme(b.dataset.themeChoice);renderAll()}));
document.querySelectorAll("[data-chart-range]").forEach(b=>b.addEventListener("click",()=>{chartState.range=b.dataset.chartRange;chartState.count=chartDefaults[chartState.range];chartRangeCountInput.value=chartState.count;document.querySelectorAll("[data-chart-range]").forEach(x=>x.classList.toggle("active",x.dataset.chartRange===chartState.range));renderChartsPanel()}));
document.querySelectorAll("[data-chart-mode]").forEach(b=>b.addEventListener("click",()=>{chartState.mode=b.dataset.chartMode;document.querySelectorAll("[data-chart-mode]").forEach(x=>x.classList.toggle("active",x.dataset.chartMode===chartState.mode));renderChartsPanel()}));
chartRangeCountInput.addEventListener("input",()=>{chartState.count=Math.max(1,Number(chartRangeCountInput.value)||chartDefaults[chartState.range]);renderChartsPanel()});
chartFieldsGrid.addEventListener("change",e=>{const input=e.target.closest("input[type='checkbox']");if(!input)return;const selected=Array.from(chartFieldsGrid.querySelectorAll("input[type='checkbox']:checked")).map(i=>i.value);chartState.fields=selected.length?selected:["indice_qt_qd"];renderChartsPanel()});
// ── Instalação PWA ────────────────────────────────────
(function(){
  const KEY='qtqd_pwa_dismissed';
  const isStandalone=window.matchMedia('(display-mode: standalone)').matches||window.navigator.standalone;
  let deferredPrompt=null;

  function closeModal(){['pwaModal','pwaBanner'].forEach(id=>{const el=document.getElementById(id);if(el)el.style.display='none';});}
  function dismiss(){localStorage.setItem(KEY,'1');closeModal();}

  // Captura evento do browser (1-clique) quando disponível
  window.addEventListener('beforeinstallprompt',e=>{
    e.preventDefault();
    deferredPrompt=e;
    const btn=document.getElementById('pwaModalInstall');
    if(btn)btn.style.display='block';
  });

  window.addEventListener('appinstalled',()=>{dismiss();});

  document.getElementById('pwaModalDismiss')?.addEventListener('click',dismiss);
  document.getElementById('pwaBannerDismiss')?.addEventListener('click',dismiss);

  document.getElementById('pwaModalInstall')?.addEventListener('click',async()=>{
    if(!deferredPrompt)return;
    deferredPrompt.prompt();
    const{outcome}=await deferredPrompt.userChoice;
    deferredPrompt=null;
    if(outcome==='accepted'){dismiss();}
  });

  // Não é standalone → mostra modal na primeira visita
  if(!isStandalone&&!localStorage.getItem(KEY)){
    setTimeout(()=>{
      const m=document.getElementById('pwaModal');
      if(m)m.style.display='flex';
    },2000);
  }
})();
const sidebarRevealButton=$("sidebarRevealButton");
function openSidebarPreview(){if(window.innerWidth>1180&&document.body.classList.contains("sidebar-collapsed"))document.body.classList.add("sidebar-open")}
function closeSidebarPreview(){document.body.classList.remove("sidebar-open")}
sidebarRevealButton.addEventListener("click",()=>{if(document.body.classList.contains("sidebar-open"))closeSidebarPreview();else openSidebarPreview()});
document.querySelector(".content")?.addEventListener("click",()=>{if(document.body.classList.contains("sidebar-collapsed"))closeSidebarPreview()});
historyTable.addEventListener("click",async e=>{const button=e.target.closest("[data-action]");if(!button)return;const record=records.find(i=>i.id===button.dataset.id);if(!record)return;if(button.dataset.action==="edit"){fillForm(record);openSection("cadastro");return}if(button.dataset.action==="evaluate"){fillForm(record);openSection("painel");setFeedback(`Avaliacao preparada para a semana ${fmtDate(record.weekDate)}.`);return}if(button.dataset.action==="delete"){try{if(isApiMode())await window.QTQD_API_CLIENT.deleteAvaliacao(record.id);records=records.filter(i=>i.id!==record.id);saveRecords();renderAll();resetForm();setFeedback(`Semana ${fmtDate(record.weekDate)} excluida.`)}catch(error){setFeedback(`Falha ao excluir na API: ${error.message}`)}}if(button.dataset.action==="fechar"){try{if(isApiMode()){const api=await window.QTQD_API_CLIENT.closeAvaliacao(record.id);const idx=records.findIndex(i=>i.id===record.id);if(idx>=0)records[idx]=apiRecordToLocal(api);}else{const idx=records.findIndex(i=>i.id===record.id);if(idx>=0)records[idx]={...record,status:'fechada'};saveRecords();}renderAll();setFeedback(`Semana ${fmtDate(record.weekDate)} fechada.`);}catch(err){setFeedback(`Falha ao fechar: ${err.message}`);}}if(button.dataset.action==="reenviar-pdf"){try{button.disabled=true;button.textContent='Enviando...';const jwt=localStorage.getItem('qtqd_jwt_v1')||'';const tid=localStorage.getItem('qtqd_tenant_id_v1')||'';const res=await fetch(`${window.location.origin}/api/v1/avaliacoes/${record.id}/reenviar-relatorio`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${jwt}`,'X-Tenant-Id':tid}});const data=await res.json();if(!res.ok)throw new Error(data.detail||'Erro ao reenviar');setFeedback(`PDF reenviado para ${data.enviado_para?.join(', ')||'destinatários cadastrados'}.`);}catch(err){setFeedback(`Falha ao reenviar PDF: ${err.message}`);}finally{button.disabled=false;button.textContent='Reenviar PDF';}}});
form.addEventListener("input",()=>renderCalculatedPreview());
// ── Máscaras de input ──────────────────────────────────
(function(){
  const MONEY_IDS=['saldo_bancario','contas_receber','cartoes','convenios','cheques','trade_marketing','outros_qt','estoque_custo','contas_pagar','fornecedores','investimentos_assumidos','outras_despesas_assumidas','dividas','financiamentos','tributos_atrasados','acoes_processos','faturamento_previsto_mes','compras_mes','entrada_mes','venda_cupom_mes','venda_custo_mes','lucro_liquido_mes','excesso_curva_a','excesso_curva_b','excesso_curva_c','excesso_curva_d'];
  const NEG_IDS=new Set(['saldo_bancario','lucro_liquido_mes']);
  const DECIMAL_IDS=[
    {id:'pmp',dec:0},{id:'pmv',dec:0},{id:'pme_excel',dec:0},{id:'cobertura_estoque_dia',dec:0},
    {id:'pmv_avista',dec:0},{id:'pmv_30',dec:0},{id:'pmv_60',dec:0},{id:'pmv_90',dec:0},{id:'pmv_120',dec:0},{id:'pmv_outros',dec:0},
    {id:'indice_faltas',dec:2}
  ];
  function maskMoney(el){
    const allowNeg=NEG_IDS.has(el.id);
    const neg=allowNeg&&el.value.includes('-');
    const digits=el.value.replace(/\D/g,'');
    if(!digits){el.value='';return;}
    const n=parseInt(digits,10)/100;
    el.value=(neg?'-':'')+n.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  }
  // Máscara de data dd/mm/aaaa
  const dateEl=$('weekDate');
  if(dateEl){
    dateEl.addEventListener('input',function(){
      let v=this.value.replace(/\D/g,'');
      if(v.length>2)v=v.slice(0,2)+'/'+v.slice(2);
      if(v.length>5)v=v.slice(0,5)+'/'+v.slice(5,9);
      this.value=v;
    });
  }
  // Máscara monetária — preenche da direita (estilo calculadora)
  MONEY_IDS.forEach(id=>{
    const el=$(id);
    if(!el)return;
    el.addEventListener('focus',function(){this.select();});
    el.addEventListener('keydown',function(e){
      if(e.key==='-'&&NEG_IDS.has(this.id)){
        e.preventDefault();
        this.value=this.value.startsWith('-')?this.value.slice(1):'-'+this.value;
      }
    });
    el.addEventListener('input',function(){
      maskMoney(this);
      this.setSelectionRange(this.value.length,this.value.length);
    });
  });
  // Campos decimais — formata ao sair do campo
  DECIMAL_IDS.forEach(({id,dec})=>{
    const el=$(id);
    if(!el)return;
    el.addEventListener('blur',function(){
      const n=parseMoney(this.value);
      this.value=Number.isFinite(n)&&n!==0?fmtNumInput(n,dec):'';
    });
  });
})();
window.addEventListener("resize",()=>{if(window.innerWidth<=1180)document.body.classList.remove("sidebar-collapsed","sidebar-open");renderChartsPanel();generateInspectorCharts()});
window.addEventListener("storage",e=>{if(e.key===FIELD_CONFIG_KEY)renderAll();if(e.key===BRANDING_KEY)applyBranding();if(e.key===THEME_KEY){applyTheme();renderAll()}});
function openCbNew(){$("cbNewCard")?.classList.remove("hidden");$("cbToggleNew")?.classList.add("hidden")}
function closeCbNew(){$("cbNewCard")?.classList.add("hidden");$("cbToggleNew")?.classList.remove("hidden")}
$("cbToggleNew")?.addEventListener("click",openCbNew);
$("cbCollapseNew")?.addEventListener("click",closeCbNew);
// ── Excel download / import ────────────────────────────
$("downloadExcelBtn")?.addEventListener("click",async()=>{
  if(!isApiMode()){setFeedback("Download de template disponível apenas no modo API.");return;}
  const jwt=localStorage.getItem("qtqd_jwt_v1")||"";
  const tid=localStorage.getItem("qtqd_tenant_id_v1")||"";
  const recordId=$("recordId")?.value;
  const weekVal=$("weekDate")?.value;
  let q="";
  // Só pré-preenche se estiver editando um registro existente
  if(recordId&&weekVal&&/^\d{2}\/\d{2}\/\d{4}$/.test(weekVal))q=`?semana=${brToIso(weekVal)}`;
  const btn=$("downloadExcelBtn");
  const orig=btn.textContent;
  btn.disabled=true;btn.textContent="Gerando...";
  try{
    const resp=await fetch(`${window.location.origin}/api/v1/avaliacoes/template-excel${q}`,{headers:{"Authorization":`Bearer ${jwt}`,"X-Tenant-Id":tid}});
    if(!resp.ok)throw new Error("Falha ao gerar template.");
    const blob=await resp.blob();
    const url=URL.createObjectURL(blob);
    const a=document.createElement("a");
    a.href=url;a.download=`qtqd_${weekVal?.replace(/\//g,"-")||"template"}.xlsx`;a.click();
    URL.revokeObjectURL(url);
    setFeedback("Template baixado. Preencha e importe de volta.");
  }catch(e){setFeedback(`Erro ao baixar: ${e.message}`);}
  finally{btn.disabled=false;btn.textContent=orig;}
});
$("importExcelBtn")?.addEventListener("click",()=>{
  if(!isApiMode()){setFeedback("Importação disponível apenas no modo API.");return;}
  $("importExcelInput")?.click();
});
$("importExcelInput")?.addEventListener("change",async function(){
  const file=this.files?.[0];
  if(!file)return;
  this.value="";
  const jwt=localStorage.getItem("qtqd_jwt_v1")||"";
  const tid=localStorage.getItem("qtqd_tenant_id_v1")||"";
  const fd=new FormData();fd.append("file",file);
  const btn=$("importExcelBtn");
  const orig=btn.textContent;
  btn.disabled=true;btn.textContent="Importando...";
  try{
    setFeedback("Processando arquivo...");
    const resp=await fetch(`${window.location.origin}/api/v1/avaliacoes/import-excel`,{method:"POST",headers:{"Authorization":`Bearer ${jwt}`,"X-Tenant-Id":tid},body:fd});
    const data=await resp.json();
    if(!resp.ok)throw new Error(data.detail||"Erro ao importar.");
    const record=apiRecordToLocal(data);
    const idx=records.findIndex(r=>r.id===record.id);
    if(idx>=0)records[idx]=record;else records.unshift(record);
    saveRecords();
    fillForm(record);
    renderAll();
    setFeedback(`Semana ${fmtDate(record.weekDate)} importada com sucesso. Revise e salve.`);
  }catch(e){setFeedback(`Falha ao importar: ${e.message}`);}
  finally{btn.disabled=false;btn.textContent=orig;}
});
// Login
async function handleLogin(){const btn=$("loginBtn");const errEl=$("loginError");const email=$("loginEmail")?.value.trim();const pass=$("loginPassword")?.value;if(!email||!pass){if(errEl){errEl.textContent="Informe e-mail e senha.";errEl.classList.remove("hidden")}return}if(btn){btn.disabled=true;btn.textContent="Entrando..."}if(errEl)errEl.classList.add("hidden");try{await doLogin(email,pass);hideLoginScreen();await initializeClient()}catch(e){if(errEl){errEl.textContent=e.message||"E-mail ou senha incorretos.";errEl.classList.remove("hidden")}if(btn){btn.disabled=false;btn.textContent="Entrar"}}}
$("loginBtn")?.addEventListener("click",handleLogin);
["loginEmail","loginPassword"].forEach(id=>$( id)?.addEventListener("keydown",e=>{if(e.key==="Enter")handleLogin()}));
function showLoginScreen(){const o=$("loginOverlay");if(o)o.classList.remove("hidden");document.body.classList.add("login-active")}
function hideLoginScreen(){const o=$("loginOverlay");if(o)o.classList.add("hidden");document.body.classList.remove("login-active")}
function handleLogout(){if(!confirm("Deseja sair do portal?"))return;try{if(window.QTQD_API_CLIENT){window.QTQD_API_CLIENT.clearJwt();window.QTQD_API_CLIENT.clearTenantId();}}catch(e){}["qtqd_jwt_v1","qtqd_tenant_id_v1","qtqd_permissao_v1",BRANDING_KEY,FIELD_CONFIG_KEY].forEach(k=>{try{localStorage.removeItem(k)}catch(e){}});location.reload();}
$("logoutButton")?.addEventListener("click",handleLogout);
function isExpiredOrUnauthorized(msg){return/401|unauthorized|nao autorizado|não autorizado|expired|expirado/i.test(String(msg))}
async function doLogin(email,password){if(!window.QTQD_API_CLIENT)throw new Error("API não disponível");const data=await window.QTQD_API_CLIENT.login(email,password);if(!data?.access_token||!data?.tenant_id)throw new Error("Resposta inválida do servidor");window.QTQD_API_CLIENT.setJwt(data.access_token);window.QTQD_API_CLIENT.setTenantId(data.tenant_id);if(data.permissao)localStorage.setItem('qtqd_permissao_v1',data.permissao);if(data.clientName)localStorage.setItem(BRANDING_KEY,JSON.stringify({clientName:data.nome||defaultBranding.clientName,clientLogoUrl:''}));return data}
async function initializeClient(){applyTheme();applyBranding();openSection("inspetor");
// Sem sessão válida em deploy real (modo API) → mostrar login em vez de cair na demonstração
const hasTenant=!!localStorage.getItem("qtqd_tenant_id_v1");const hasJwt=!!localStorage.getItem("qtqd_jwt_v1");const apiDeploy=!!(window.QTQD_APP_CONFIG&&window.QTQD_APP_CONFIG.mode==="api"&&window.QTQD_API_CLIENT);if((apiDeploy&&!(hasTenant&&hasJwt))||(hasTenant&&!hasJwt)){showLoginScreen();return}
try{await loadRecordsFromSource();if(isApiMode()&&window.QTQD_API_CLIENT){try{const [b,cfg]=await Promise.all([window.QTQD_API_CLIENT.getMyBranding().catch(()=>null),window.QTQD_API_CLIENT.getMyComponentesConfig().catch(()=>null)]);if(b){const mapped={clientName:b.nome_portal||defaultBranding.clientName,clientLogoUrl:b.logo_cliente_url||''};localStorage.setItem(BRANDING_KEY,JSON.stringify(mapped));applyBranding()}if(Array.isArray(cfg)&&cfg.length){const merged={...defaultFieldConfig};cfg.forEach(c=>{const key=c.codigo_componente;if(!key)return;if(key.startsWith('custom_')){if(!chartFieldCatalog.find(f=>f.key===key))chartFieldCatalog.push({key,label:c.label_customizado||key,format:'currency'});merged[key]={label:c.label_customizado||key,visible:c.visivel!==false}}else{merged[key]={label:c.label_customizado||defaultFieldConfig[key]?.label||key,visible:c.visivel!==false}}});localStorage.setItem(FIELD_CONFIG_KEY,JSON.stringify(merged))}else{localStorage.removeItem(FIELD_CONFIG_KEY)}}catch{}}}catch(error){if(isExpiredOrUnauthorized(error.message)){localStorage.removeItem("qtqd_jwt_v1");showLoginScreen();return}loadRecordsFromLocal();setFeedback(`Modo API configurado, mas foi mantido fallback local: ${error.message}`)}if(!records.length){records=seedRecords();saveRecords()}renderAll();const latest=getLatestRecord();if(latest){fillForm(latest);renderCalculatedPreview(latest)}else renderCalculatedPreview();renderInspector();generateInspectorCharts();if(window._qtqdAutoprint){window._qtqdAutoprint=false;setTimeout(()=>generateInspectorPdf(),2500)}if (window.QTQD_MULTILOJA && window.QTQD_MULTILOJA.init) { try { await window.QTQD_MULTILOJA.init(); } catch (e) { /* multi-loja é opcional; não bloqueia o portal */ } }}
(function(){const p=new URLSearchParams(location.search);const token=p.get("token");const tenantId=p.get("tenant_id");if(p.get("autoprint")==="1"){window._qtqdAutoprint=true}if(token&&tenantId&&window.QTQD_API_CLIENT){const prevTenant=localStorage.getItem("qtqd_tenant_id_v1");if(prevTenant&&prevTenant!==tenantId){localStorage.removeItem(FIELD_CONFIG_KEY)}window.QTQD_API_CLIENT.setJwt(token);window.QTQD_API_CLIENT.setTenantId(tenantId);localStorage.setItem('qtqd_permissao_v1','edita');history.replaceState(null,"",location.pathname)}})();
initializeClient();

;(function(){
  var k='qtqd_mini', btn=document.getElementById('sidebarMiniToggle');
  if(!btn) return;
  function apply(v){ document.body.classList.toggle('sidebar-mini',v); localStorage.setItem(k,v?'1':'0'); }
  apply(localStorage.getItem(k)==='1');
  btn.addEventListener('click', function(){ apply(!document.body.classList.contains('sidebar-mini')); });
})();
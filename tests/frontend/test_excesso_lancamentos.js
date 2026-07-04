const assert = require('assert');
const { calcularExcessoDeRows } = require('../../frontend_cliente/excesso_critico.js');

const LIM = { limite_a: 120, limite_b: 150, limite_c: 150, limite_d: 180 };
const HEADER = ['Nome Completo','Linha','Curva','Filial','lancamento','MediaF Un','Qtd Estoque','Estoque Valor'];

// Produto de lançamento (deve ser excluído do excesso e somado no total)
// Produto normal sem venda com estoque > 1 (vira excesso total)
const rows = [
  HEADER,
  ['PROD LANC A','PERF','C','1','Sim - 90D', 0, 10, 500],   // lançamento → excluído
  ['PROD LANC B','PERF','D','2','Sim - 60D', 5, 3,  120],   // lançamento → excluído
  ['PROD NORMAL','PERF','D','1','Não',        0, 4,  200],   // sem venda, qtd>1 → excesso = todo o estoque (200)
];

const r = calcularExcessoDeRows(rows, LIM);

// total de lançamentos = 500 + 120 = 620, sem regra
assert.strictEqual(r.totais.total_estoque_lancamentos, 620);
assert.strictEqual(r.resumo.qtd_lancamentos, 2);
// excesso calculado só sobre o produto normal (curva D): 200
assert.strictEqual(r.totais.excesso_curva_d, 200);
assert.strictEqual(r.totais.total, 200);
// os produtos de lançamento não aparecem na lista de críticos
assert.ok(!r.produtos.some(p => p.nome.startsWith('PROD LANC')));

// Retrocompat: sem coluna lancamento → total 0, produto normal continua excesso
const HEADER2 = ['Nome Completo','Linha','Curva','Filial','MediaF Un','Qtd Estoque','Estoque Valor'];
const rows2 = [ HEADER2, ['PROD NORMAL','PERF','D','1', 0, 4, 200] ];
const r2 = calcularExcessoDeRows(rows2, LIM);
assert.strictEqual(r2.totais.total_estoque_lancamentos, 0);
assert.strictEqual(r2.totais.excesso_curva_d, 200);

console.log('OK — todos os asserts passaram');

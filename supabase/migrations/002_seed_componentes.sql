insert into qtqd_componentes_catalogo (codigo, nome, grupo, ordem_exibicao) values
('saldo_bancario', 'Saldo bancario', 'qt', 10),
('contas_receber', 'Contas a receber', 'qt', 20),
('cartoes', 'Cartoes', 'qt', 30),
('convenios', 'Convenios', 'qt', 40),
('cheques', 'Cheques', 'qt', 50),
('trade_marketing', 'Trade marketing', 'qt', 60),
('outros_qt', 'Outros', 'qt', 70),
('estoque_custo', 'Estoque (preco custo)', 'qt', 80),
('contas_pagar', 'Contas a pagar', 'qd', 90),
('fornecedores', 'Fornecedores', 'qd', 100),
('investimentos_assumidos', 'Investimentos assumidos', 'qd', 110),
('outras_despesas_assumidas', 'Outras despesas assumidas', 'qd', 120),
('dividas', 'Dividas', 'qd', 130),
('financiamentos', 'Financiamentos', 'qd', 140),
('tributos_atrasados', 'Tributos atrasados', 'qd', 150),
('acoes_processos', 'Acoes e processos', 'qd', 160),
('faturamento_previsto_mes', 'Faturamento previsto no mes', 'operacional', 170),
('compras_mes', 'Compras no mes', 'operacional', 180),
('entrada_mes', 'Entrada no mes', 'operacional', 190),
('venda_cupom_mes', 'Venda cupom no mes', 'operacional', 200),
('venda_custo_mes', 'Venda custo no mes - CMV', 'operacional', 210),
('lucro_liquido_mes', 'Lucro liquido no mes', 'operacional', 220)
on conflict (codigo) do update
set nome = excluded.nome,
    grupo = excluded.grupo,
    ordem_exibicao = excluded.ordem_exibicao;

insert into qtqd_indicadores_catalogo (codigo, nome, unidade, ordem_exibicao) values
('qt_total', 'QT Total', 'currency', 10),
('qd_total', 'QD Total', 'currency', 20),
('saldo_qt_qd', 'Saldo QT/QD', 'currency', 30),
('indice_qt_qd', 'Indice QT/QD', 'ratio', 40),
('saldo_sem_dividas', 'Saldo QT/QD sem dividas', 'currency', 50),
('indice_sem_dividas', 'Indice QT/QD sem dividas', 'ratio', 60),
('saldo_sem_dividas_sem_estoque', 'Saldo QT/QD sem dividas e sem estoque', 'currency', 70),
('pme', 'Prazo medio de estoque', 'days', 80),
('prazo_medio_compra', 'Prazo medio de compra', 'days', 90),
('prazo_venda', 'Prazo de venda', 'days', 100),
('ciclo_financiamento', 'Ciclo de financiamento', 'days', 110)
on conflict (codigo) do update
set nome = excluded.nome,
    unidade = excluded.unidade,
    ordem_exibicao = excluded.ordem_exibicao;

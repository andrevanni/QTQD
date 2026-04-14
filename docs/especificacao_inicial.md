# Especificacao Inicial - QTQD

## 1. Visao do produto

O QTQD sera a versao web do modelo de avaliacao financeira atualmente operado em Excel. O foco do MVP e converter o preenchimento manual da planilha em um fluxo digital simples, semanal e multi-cliente.

Cada cliente tera sua propria area autenticada para preencher os dados da semana e consultar os resultados. A equipe interna tera um painel administrativo para cadastro, suporte e acompanhamento.

## 2. Referencia tecnica herdada da Agenda de Compras Web

Recursos e especificacoes que devem ser reaproveitados:

- arquitetura web separada em area cliente e area admin
- Supabase como banco PostgreSQL principal
- autenticacao centralizada no Supabase
- isolamento por cliente com `tenant_id`
- Row Level Security no banco
- painel administrativo global para operacao interna
- deploy do frontend na Vercel
- backend proprio para regras de negocio, operacoes administrativas e integracoes futuras

## 3. Modulos do sistema

### 3.1 Area Cliente

Responsabilidades iniciais:

- login do cliente
- cadastro e edicao das avaliacoes semanais
- visualizacao dos resultados calculados
- consulta do historico semanal
- leitura de observacoes e analises futuras

### 3.2 Area Admin

Responsabilidades iniciais:

- cadastrar clientes
- ativar, bloquear e acompanhar vigencias
- gerenciar usuarios vinculados aos clientes
- acompanhar quantidade de avaliacoes por cliente
- configurar parametros globais do sistema

### 3.3 Backend/API

Responsabilidades iniciais:

- validar dados recebidos
- calcular indicadores da avaliacao
- consolidar resultados semanais
- expor endpoints administrativos
- expor endpoints operacionais da area cliente

## 4. Origem funcional: planilha QTQD

A planilha `QTQD.xlsx` mostra que o modelo de entrada e calculo esta organizado em componentes financeiros e indicadores derivados.

### 4.1 Componentes principais de entrada

Bloco `QT (Quanto Tenho)`:

- saldo bancario
- contas a receber
- cartoes
- convenios
- cheques
- trade marketing
- outros
- estoque a preco de custo

Bloco `QD (Quanto Devo)`:

- contas a pagar
- fornecedores
- investimentos assumidos
- outras despesas assumidas
- dividas
- financiamentos
- tributos atrasados
- acoes/processos

Bloco operacional e complementar:

- faturamento previsto no mes
- compras no mes
- entrada no mes
- venda cupom no mes
- venda custo no mes (CMV)
- lucro liquido no mes

Indicadores complementares identificados na planilha:

- saldo QT/QD
- indice QT/QD
- saldo e indice sem dividas
- saldo e indice sem dividas e sem estoque
- margem bruta no mes
- prazo medio de estoque (PME)
- cobertura de estoque
- indice de faltas
- prazo medio de pagamento
- prazo medio de venda
- ciclo de financiamento
- excesso curva A, B, C e D
- excesso total

### 4.2 Observacao importante

A planilha tambem contempla abas e indicadores complementares como `Saldo QT-QD`, `Indice QT-QD`, `Margem` e `PME`. Na web, esses resultados devem ser recalculados pelo backend e persistidos, em vez de depender de formulas no cliente.

## 5. Proposta de fluxo do MVP

1. Admin cadastra o cliente e cria o tenant.
2. Admin vincula usuarios ao cliente.
3. Cliente acessa a area autenticada.
4. Cliente cria uma avaliacao semanal informando os componentes financeiros.
5. Backend calcula os saldos e indicadores.
6. Sistema apresenta o resultado consolidado da semana.
7. Cliente consulta o historico de semanas anteriores.

## 6. Requisitos funcionais do MVP

- permitir uma avaliacao por cliente e por semana de referencia
- impedir duplicidade de fechamento semanal para a mesma semana
- armazenar os valores informados manualmente
- recalcular automaticamente todos os indicadores derivados
- manter historico das avaliacoes
- registrar usuario criador, data de criacao e ultima atualizacao
- permitir edicao enquanto a avaliacao estiver em rascunho
- permitir fechamento/publicacao da semana

## 7. Regras iniciais de negocio

- cada avaliacao pertence a um unico `tenant_id`
- cada avaliacao possui uma `semana_referencia`
- os campos monetarios devem aceitar valores decimais
- indicadores calculados nao devem ser digitados manualmente no MVP
- casos de divisao por zero devem gerar resultado controlado e exibicao amigavel
- resultados devem ser historicos e auditaveis

## 8. Indicadores sugeridos para a primeira entrega visual

Na primeira interface do cliente, mostrar pelo menos:

- saldo QT/QD
- indice QT/QD
- saldo QT/QD sem dividas
- indice QT/QD sem dividas
- saldo QT/QD sem dividas e sem estoque
- margem bruta do mes
- PME
- ciclo de financiamento

## 9. Roadmap sugerido

### Fase 1

- autenticacao
- cadastro de clientes
- cadastro da avaliacao semanal
- calculo e exibicao dos resultados

### Fase 2

- dashboards comparativos
- filtros por periodo
- graficos por indicador

### Fase 3

- analise por IA
- alertas automaticos
- recomendacoes gerenciais
- resumo executivo em linguagem natural

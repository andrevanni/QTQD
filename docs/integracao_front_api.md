# Integracao Front x API - QTQD

Esta rodada deixa o projeto em modo hibrido.

## Como funciona agora

- `shared/app_config.js` define o ambiente ativo
- `shared/api_client.js` centraliza as chamadas HTTP
- `frontend_admin` pode operar em:
  - `simulation`
  - `api`
- `frontend_cliente` pode operar em:
  - `simulation`
  - `api`, desde que exista `tenantId` configurado

## Configuracao no Admin

Na aba `Ambiente` do Admin agora e possivel definir:

- modo de execucao
- base da API
- URL de health
- tenant padrao do Cliente
- token administrativo

Esses dados sao gravados em `localStorage`:

- `qtqd_runtime_config_v1`
- `qtqd_admin_token_v1`

## O que ja usa API

### Admin

- listar clientes
- criar cliente
- atualizar cliente
- testar `health`

### Cliente

- listar avaliacoes semanais
- criar avaliacao
- atualizar avaliacao
- excluir avaliacao

## O que ainda permanece em simulacao

- vigencias
- primeira carga de Excel
- branding persistido em banco
- configuracao de campos persistida em banco
- autenticacao real com Supabase

## Backend ajustado nesta rodada

- `AvaliacaoResponse` agora retorna `valores`
- `DELETE /api/v1/avaliacoes/{avaliacao_id}` foi adicionado

## Proxima evolucao recomendada

- substituir `localStorage` administrativo por tabelas reais
- criar autenticacao Supabase para admin e cliente
- mover branding e configuracao de campos para o banco
- implementar importacao Excel via backend

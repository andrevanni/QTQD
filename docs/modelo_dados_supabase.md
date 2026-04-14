# Modelo de Dados Supabase - QTQD

## Objetivo

Adaptar o modelo multi-tenant validado na `Agenda de Compras Web` para o contexto do QTQD.

## 1. Estrutura multi-tenant

### `tenants`

Representa cada cliente da plataforma.

Campos sugeridos:

- `id`
- `nome`
- `slug`
- `status`
- `plano`
- `contato_nome`
- `contato_email`
- `observacoes`
- `created_at`
- `updated_at`

### `tenant_users`

Relaciona usuarios autenticados no Supabase com um tenant.

Campos sugeridos:

- `id`
- `tenant_id`
- `user_id`
- `role`
- `ativo`
- `created_at`
- `updated_at`

Perfis iniciais:

- `owner`
- `admin`
- `analyst`
- `viewer`

### `tenant_profiles`

Perfil complementar do usuario dentro do tenant.

Campos sugeridos:

- `id`
- `tenant_id`
- `user_id`
- `nome_exibicao`
- `email`
- `avatar_url`
- `cargo`
- `telefone`
- `ultimo_acesso_em`
- `created_at`
- `updated_at`

### `tenant_licencas`

Vigencias e limites comerciais do cliente.

Campos sugeridos:

- `id`
- `tenant_id`
- `plano`
- `status`
- `inicio_vigencia`
- `fim_vigencia`
- `limite_usuarios`
- `limite_avaliacoes_mes`
- `observacoes`
- `created_by`
- `created_at`
- `updated_at`

### `tenant_branding`

Configuracao visual do portal do cliente.

Campos sugeridos:

- `tenant_id`
- `nome_portal`
- `logo_cliente_url`
- `tema`
- `cor_primaria`
- `cor_secundaria`
- `powered_by_label`
- `created_at`
- `updated_at`

## 2. Tabelas operacionais do QTQD

### `tenant_componentes_config`

Configuracao por cliente dos campos exibidos no portal.

Campos sugeridos:

- `id`
- `tenant_id`
- `codigo_componente`
- `label_customizado`
- `visivel`
- `obrigatorio`
- `ordem_exibicao`
- `created_at`
- `updated_at`

### `avaliacoes_semanais`

Cabecalho da avaliacao financeira semanal.

Campos sugeridos:

- `id`
- `tenant_id`
- `semana_referencia`
- `status`
- `observacoes`
- `created_by`
- `created_at`
- `updated_at`
- `published_at`

Status sugeridos:

- `rascunho`
- `fechada`
- `publicada`

Restricao recomendada:

- unico registro por `tenant_id + semana_referencia`

### `avaliacao_componentes`

Armazena os valores informados pelo cliente em cada avaliacao.

Campos sugeridos:

- `id`
- `tenant_id`
- `avaliacao_id`
- `codigo_componente`
- `nome_componente`
- `grupo`
- `valor`
- `ordem_exibicao`
- `created_at`
- `updated_at`

Grupos iniciais:

- `qt`
- `qd`
- `operacional`
- `complementar`

Codigos iniciais sugeridos:

- `saldo_bancario`
- `contas_receber`
- `cartoes`
- `convenios`
- `cheques`
- `trade_marketing`
- `outros_qt`
- `estoque_custo`
- `contas_pagar`
- `fornecedores`
- `investimentos_assumidos`
- `outras_despesas_assumidas`
- `dividas`
- `financiamentos`
- `tributos_atrasados`
- `acoes_processos`
- `faturamento_previsto_mes`
- `compras_mes`
- `entrada_mes`
- `venda_cupom_mes`
- `venda_custo_mes`
- `lucro_liquido_mes`

### `avaliacao_indicadores`

Armazena resultados calculados pelo backend.

Campos sugeridos:

- `id`
- `tenant_id`
- `avaliacao_id`
- `codigo_indicador`
- `nome_indicador`
- `valor_numerico`
- `valor_texto`
- `unidade`
- `faixa_status`
- `created_at`
- `updated_at`

Indicadores iniciais sugeridos:

- `saldo_qt_qd`
- `indice_qt_qd`
- `saldo_qt_qd_sem_dividas`
- `indice_qt_qd_sem_dividas`
- `saldo_qt_qd_sem_dividas_sem_estoque`
- `indice_qt_qd_sem_dividas_sem_estoque`
- `margem_bruta_mes`
- `pme`
- `cobertura_estoque`
- `indice_faltas`
- `prazo_medio_pagamento`
- `prazo_medio_venda`
- `ciclo_financiamento`
- `excesso_curva_a`
- `excesso_curva_b`
- `excesso_curva_c`
- `excesso_curva_d`
- `excesso_total`

### `avaliacao_analises`

Reservada para comentarios humanos e, depois, analise por IA.

Campos sugeridos:

- `id`
- `tenant_id`
- `avaliacao_id`
- `origem`
- `titulo`
- `conteudo`
- `created_by`
- `created_at`

Origem sugerida:

- `manual`
- `ia`

### `tenant_importacoes`

Controle da primeira carga e demais importacoes administrativas.

Campos sugeridos:

- `id`
- `tenant_id`
- `tipo`
- `origem_arquivo_nome`
- `origem_arquivo_url`
- `status`
- `observacoes`
- `registros_processados`
- `registros_com_erro`
- `payload_resumo`
- `created_by`
- `created_at`
- `updated_at`
- `finished_at`

Status sugeridos:

- `recebido`
- `processando`
- `concluido`
- `concluido_parcial`
- `erro`

## 3. Regras de seguranca

Assim como na Agenda de Compras Web:

- todas as tabelas operacionais devem conter `tenant_id`
- o usuario autenticado acessa apenas registros do proprio tenant
- a `service_role` opera globalmente em tarefas administrativas
- RLS deve ser habilitado em todas as tabelas de negocio
- tabelas de configuracao por cliente tambem devem respeitar `tenant_id`

## 4. Politicas RLS sugeridas

- leitura e escrita condicionadas a `tenant_id`
- admin global operando via backend/token administrativo
- area admin nunca acessa o banco diretamente no navegador com privilegios elevados

## 5. Integracao com o backend

Endpoints minimos sugeridos:

- `GET /health`
- `GET /api/v1/admin/clientes`
- `POST /api/v1/admin/clientes`
- `PATCH /api/v1/admin/clientes/{tenant_id}`
- `GET /api/v1/avaliacoes`
- `GET /api/v1/avaliacoes/{avaliacao_id}`
- `POST /api/v1/avaliacoes`
- `PATCH /api/v1/avaliacoes/{avaliacao_id}`
- `DELETE /api/v1/avaliacoes/{avaliacao_id}`
- `POST /api/v1/avaliacoes/{avaliacao_id}/fechar`
- `GET /api/v1/avaliacoes/{avaliacao_id}/indicadores`
- `GET /api/v1/admin/licencas`
- `POST /api/v1/admin/licencas`
- `GET /api/v1/admin/importacoes`
- `POST /api/v1/admin/importacoes`
- `GET /api/v1/admin/branding/{tenant_id}`
- `PUT /api/v1/admin/branding/{tenant_id}`
- `GET /api/v1/admin/componentes-config/{tenant_id}`
- `PUT /api/v1/admin/componentes-config/{tenant_id}`

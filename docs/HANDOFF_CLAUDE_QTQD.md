# Handoff QTQD

Data: 2026-04-15

## Situação geral

O projeto `QTQD` está publicado e com base técnica montada, mas o frontend do Cliente ficou com um bloqueio importante no `Painel de Avaliação`: a primeira coluna fixa não está se comportando corretamente no navegador do usuário.

## Links atuais

- Produção Vercel: `https://qtqd-vt2a.vercel.app/`
- Cliente: `https://qtqd-vt2a.vercel.app/cliente`
- Admin: `https://qtqd-vt2a.vercel.app/admin`
- Health: `https://qtqd-vt2a.vercel.app/health`
- GitHub: `https://github.com/andrevanni/QTQD`

## Infra já pronta

- GitHub criado e publicado
- Supabase criado
- Tabelas principais criadas no Supabase
- Vercel criada e conectada ao GitHub
- Deploy automático funcionando

## Backend / banco já existentes

- API FastAPI publicada pela Vercel
- Schema do Supabase já criado
- Rotas de:
  - clientes
  - avaliações
  - branding
  - licenças
  - campos configuráveis
  - importações

## O que está operacional

- Projeto online
- Área Cliente abre
- Área Admin abre
- `/health` responde
- Simulação local híbrida ainda existe no Cliente

## Bloqueio principal

O usuário pediu que o `Painel de Avaliação` tivesse:

- primeira coluna congelada verticalmente
- navegação horizontal nas datas/indicadores
- funcionamento igual no modo normal e maximizado

Foram tentadas várias abordagens e nenhuma funcionou satisfatoriamente no navegador do usuário:

1. tabela HTML com `position: sticky` na primeira coluna
2. duas tabelas sincronizadas
3. transposição do painel
4. grid CSS com coluna fixa

O usuário informou repetidamente que:

- a coluna não congelava corretamente
- às vezes a rolagem ficava conceitualmente errada
- houve desalinhamento
- a lateral também ficou inconsistente em algumas rodadas

## Expectativa correta do usuário

Manter o painel com:

- `COMPONENTES` como primeira coluna fixa
- datas nas colunas à direita
- rolagem horizontal apenas na parte dos dados
- primeira coluna realmente fixa visualmente

## Últimos commits relevantes

- `a1c0adb` Troca painel para grid com coluna fixa
- `4d2e431` Reforça coluna fixa do painel
- `0d2e2c5` Restaura painel fixo e textos do cliente
- `df2dce8` Ajusta lateral e transpõe painel
- `933c962` Corrige lateral e painel do cliente
- `206cc17` Ajusta painel e gráficos do cliente

## Arquivos mais importantes para retomar

- `frontend_cliente/index.html`
- `frontend_cliente/styles.css`
- `frontend_cliente/script.js`
- `docs/STATUS_ATUAL_QTQD.md`
- `README.md`

## Observação importante para a próxima IA

O usuário ficou frustrado principalmente com o painel fixo e com regressões laterais. A melhor estratégia provavelmente é:

- parar de fazer ajustes incrementais pequenos
- escolher uma implementação única e robusta
- validar especificamente o congelamento da primeira coluna no navegador alvo antes de mexer em outros pontos

## Segurança

Nesta conversa foram compartilhados segredos reais. Recomenda-se trocar depois:

- senha do banco
- `SUPABASE_SERVICE_ROLE_KEY`
- tokens GitHub já usados


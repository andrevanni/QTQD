# Status Atual - QTQD

Atualizado em: 2026-04-14

## Links de validacao

- Raiz: `https://qtqd-vt2a.vercel.app/`
- Cliente: `https://qtqd-vt2a.vercel.app/cliente`
- Admin: `https://qtqd-vt2a.vercel.app/admin`
- Health: `https://qtqd-vt2a.vercel.app/health`

## O que ja esta pronto

- Projeto publicado no GitHub:
  - `https://github.com/andrevanni/QTQD`
- Projeto publicado na Vercel
- Projeto criado no Supabase
- Schema principal executado no Supabase
- Seed de componentes executado no Supabase
- Backend FastAPI publicado via Vercel
- Front Cliente publicado
- Front Admin publicado
- Integracao inicial front/API preparada

## Tabelas ja criadas no Supabase

- `tenants`
- `tenant_users`
- `tenant_profiles`
- `tenant_licencas`
- `tenant_branding`
- `qtqd_componentes_catalogo`
- `qtqd_indicadores_catalogo`
- `tenant_componentes_config`
- `avaliacoes_semanais`
- `avaliacao_indicadores`
- `avaliacao_analises`
- `tenant_importacoes`

## O que ja esta operacional

- Rotas principais da Vercel funcionando
- `health` publicado
- Estrutura multi-tenant do banco criada
- Endpoints backend para:
  - clientes
  - avaliacoes
  - licencas
  - branding
  - configuracao de campos
  - importacoes

## O que ainda nao esta 100% real

- Front Admin ainda usa bastante `localStorage`
- Front Cliente ainda mistura demo + API
- Branding/fields/licencas/importacoes ainda nao estao conectados ponta a ponta no front
- Autenticacao real Supabase ainda nao foi fechada
- Importacao real de Excel ainda nao processa o arquivo no backend
- Ajustes finos de UX do painel ficaram para a proxima versao

## Ultimos ajustes feitos

- `requirements.txt` da raiz corrigido para a Vercel
- `vercel.json` ajustado para publicar `validar_fronts.html`
- API com imports corrigidos para execucao pela raiz
- Adicionados endpoints administrativos para tabelas novas do Supabase

## Proximo passo recomendado

1. Conectar o Front Admin real ao backend para:
   - branding
   - campos configuraveis
   - vigencias
   - importacoes
2. Depois conectar o Front Cliente real as avaliacoes
3. Fechar autenticacao Supabase
4. Voltar aos ajustes finos de frontend e backend

## Observacoes de seguranca

- Regenerar a `SUPABASE_SERVICE_ROLE_KEY`
- Trocar a senha do banco
- Revogar os tokens GitHub usados nesta implantacao

## Handoff

- Resumo especifico para continuidade em outra IA: `docs/HANDOFF_CLAUDE_QTQD.md`

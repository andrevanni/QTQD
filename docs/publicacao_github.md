# Publicacao no GitHub - QTQD

Este projeto ja esta preparado para subir primeiro no GitHub e depois conectar na Vercel.

## O que ja ficou pronto

- `.gitignore` configurado
- arquivos sensiveis excluidos do versionamento
- modelos de ambiente mantidos:
  - `backend/.env.example`
  - `.env.vercel.example`
- schema e migracoes Supabase no repositorio
- front e backend na mesma base do projeto

## O que nao deve ir para o GitHub

- `backend/.env`
- qualquer `.env` real com credenciais
- `.vercel/`
- ambientes virtuais
- arquivos temporarios locais

## Ordem recomendada

1. Criar o repositorio `QTQD` no GitHub.
2. Inicializar o git na pasta do projeto.
3. Fazer o primeiro commit.
4. Conectar o repositorio na Vercel.
5. Configurar as variaveis de ambiente na Vercel.
6. Fazer o primeiro deploy.

## Comandos sugeridos

No diretorio do projeto:

```powershell
git init
git add .
git commit -m "Inicializa projeto QTQD"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/QTQD.git
git push -u origin main
```

## Antes do push

Revise especialmente:

- se nenhum `.env` real foi criado dentro do projeto
- se a `secret key` do Supabase nao foi salva em arquivos locais
- se a senha do banco nao foi escrita em nenhum arquivo do repo

## Depois do GitHub

Na Vercel, conecte o repositorio e cadastre:

- `APP_ENV`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ADMIN_TOKEN`
- `CORS_ORIGINS`
- `FRONTEND_CLIENT_URL`
- `FRONTEND_ADMIN_URL`
- `VERCEL_PROJECT_URL`

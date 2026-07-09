-- Multi-loja / Grupo Econômico — DDL idempotente
-- Rodar no Supabase SQL Editor. Seguro: só adiciona; não altera dados existentes.

-- 1) Flag opt-in por cliente
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS modo_rede boolean DEFAULT false;

-- 2) Grupos econômicos
CREATE TABLE IF NOT EXISTS grupos_economicos (
  id                  uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tenant_id           uuid        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome                text        NOT NULL,
  nivel_preenchimento text        NOT NULL DEFAULT 'loja',  -- 'loja' | 'grupo'
  ordem               integer     DEFAULT 0,
  ativo               boolean     DEFAULT true,
  created_at          timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_grupos_tenant ON grupos_economicos(tenant_id);

-- 3) Lojas
CREATE TABLE IF NOT EXISTS lojas (
  id           uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
  tenant_id    uuid        NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  grupo_id     uuid        NOT NULL REFERENCES grupos_economicos(id) ON DELETE CASCADE,
  nome         text        NOT NULL,
  cnpj         text,
  filial_excel integer,
  ordem        integer     DEFAULT 0,
  ativo        boolean     DEFAULT true,
  created_at   timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_lojas_tenant ON lojas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_lojas_grupo ON lojas(grupo_id);

-- 4) Dimensão nas avaliações
ALTER TABLE avaliacoes_semanais ADD COLUMN IF NOT EXISTS grupo_id uuid REFERENCES grupos_economicos(id) ON DELETE CASCADE;
ALTER TABLE avaliacoes_semanais ADD COLUMN IF NOT EXISTS loja_id  uuid REFERENCES lojas(id) ON DELETE CASCADE;

-- 5) Unicidade sem regressão:
--    0) REMOVER a constraint antiga que trava multi-loja (bloqueava 2 lojas na mesma
--       semana). Segura: o índice parcial (a) abaixo mantém a garantia p/ clientes sem rede.
ALTER TABLE avaliacoes_semanais DROP CONSTRAINT IF EXISTS avaliacoes_semanais_tenant_id_semana_referencia_key;
--    a) registros SEM unidade (clientes atuais) permanecem únicos por (tenant, semana)
CREATE UNIQUE INDEX IF NOT EXISTS uq_aval_tenant_semana_sem_unidade
  ON avaliacoes_semanais(tenant_id, semana_referencia)
  WHERE grupo_id IS NULL AND loja_id IS NULL;
--    b) registros de rede: únicos por (tenant, semana, grupo, loja) usando COALESCE
--       para tratar loja_id NULL (grupo nivel='grupo') como chave estável
CREATE UNIQUE INDEX IF NOT EXISTS uq_aval_rede
  ON avaliacoes_semanais(
    tenant_id, semana_referencia, grupo_id,
    COALESCE(loja_id, '00000000-0000-0000-0000-000000000000'::uuid)
  )
  WHERE grupo_id IS NOT NULL;

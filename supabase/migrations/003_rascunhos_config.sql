-- Migration 003 — tenant_pdf_config + colunas de acompanhamento semanal
-- Execute no Supabase SQL Editor: https://supabase.com/dashboard/project/ludbgghdknwfzcrqfdge

-- 1. Cria a tabela se ainda não existir (inclui colunas originais)
CREATE TABLE IF NOT EXISTS tenant_pdf_config (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        UUID UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  n_retratos       INT     NOT NULL DEFAULT 8,
  incluir_inspetor BOOLEAN NOT NULL DEFAULT false,
  incluir_graficos BOOLEAN NOT NULL DEFAULT false,
  envio_timing     TEXT    NOT NULL DEFAULT 'imediato',
  dias_apos        INT     NOT NULL DEFAULT 0,
  ativo            BOOLEAN NOT NULL DEFAULT true,
  created_at       TIMESTAMPTZ DEFAULT now(),
  updated_at       TIMESTAMPTZ DEFAULT now()
);

-- 2. Adiciona colunas de acompanhamento (seguro se já existirem)
ALTER TABLE tenant_pdf_config
  ADD COLUMN IF NOT EXISTS rascunhos_ativo      BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS rascunhos_dia_semana INTEGER NOT NULL DEFAULT 1;

COMMENT ON COLUMN tenant_pdf_config.rascunhos_ativo
  IS 'Ativa envio semanal automático do relatório de acompanhamento de rascunhos';
COMMENT ON COLUMN tenant_pdf_config.rascunhos_dia_semana
  IS 'Dia da semana para envio (1=Segunda … 7=Domingo)';

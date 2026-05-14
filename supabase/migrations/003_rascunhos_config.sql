-- Migration 003: Acompanhamento semanal de rascunhos
-- Execute no Supabase SQL Editor

ALTER TABLE tenant_pdf_config
  ADD COLUMN IF NOT EXISTS rascunhos_ativo      boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS rascunhos_dia_semana integer NOT NULL DEFAULT 1; -- 1=Seg ... 7=Dom

COMMENT ON COLUMN tenant_pdf_config.rascunhos_ativo      IS 'Ativa envio semanal automático do relatório de acompanhamento de rascunhos';
COMMENT ON COLUMN tenant_pdf_config.rascunhos_dia_semana IS 'Dia da semana para envio (1=Segunda … 7=Domingo, padrão=1)';

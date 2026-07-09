-- Nível do relatório por e-mail (multi-loja). Rodar no Supabase SQL Editor.
ALTER TABLE tenant_pdf_config ADD COLUMN IF NOT EXISTS nivel_relatorio text DEFAULT 'loja';
-- valores esperados: 'loja' | 'grupo' | 'rede'

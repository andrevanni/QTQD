-- Rodar no Supabase Dashboard > SQL Editor
CREATE TABLE IF NOT EXISTS tenant_pdf_config (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        UUID UNIQUE NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  n_retratos       INT  NOT NULL DEFAULT 8,
  incluir_inspetor BOOLEAN NOT NULL DEFAULT false,
  incluir_graficos BOOLEAN NOT NULL DEFAULT false,
  envio_timing     TEXT NOT NULL DEFAULT 'imediato', -- 'imediato' | 'agendado'
  dias_apos        INT  NOT NULL DEFAULT 0,
  ativo            BOOLEAN NOT NULL DEFAULT true,
  created_at       TIMESTAMPTZ DEFAULT now(),
  updated_at       TIMESTAMPTZ DEFAULT now()
);

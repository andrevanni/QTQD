-- Rodar no Supabase Dashboard > SQL Editor
CREATE TABLE IF NOT EXISTS tenant_usuarios (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  nome        TEXT NOT NULL,
  funcao      TEXT,
  email       TEXT NOT NULL,
  permissao   TEXT NOT NULL DEFAULT 'visualiza', -- 'edita' | 'visualiza' | 'relatorio'
  ativo       BOOLEAN DEFAULT true,
  user_id     UUID,   -- vinculado ao Supabase Auth quando o usuário se cadastrar
  created_at  TIMESTAMPTZ DEFAULT now(),
  updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tenant_usuarios_tenant ON tenant_usuarios(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_usuarios_email  ON tenant_usuarios(email);

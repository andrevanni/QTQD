-- QTQD - Schema principal Supabase
-- Base multi-tenant para area cliente, area admin e historico semanal.

create extension if not exists pgcrypto;

create schema if not exists app;

create or replace function app.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists tenants (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  slug text not null unique,
  status text not null default 'implantacao' check (status in ('ativo', 'implantacao', 'bloqueado', 'inativo')),
  plano text not null default 'basico',
  contato_nome text,
  contato_email text,
  observacoes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists tenant_users (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'analyst', 'viewer')),
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);

create table if not exists tenant_profiles (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  nome_exibicao text,
  email text,
  avatar_url text,
  cargo text,
  telefone text,
  ultimo_acesso_em timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, user_id)
);

create table if not exists tenant_licencas (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  plano text not null default 'basico',
  status text not null default 'ativo' check (status in ('ativo', 'implantacao', 'bloqueado', 'inativo', 'expirado')),
  inicio_vigencia date not null,
  fim_vigencia date,
  limite_usuarios integer,
  limite_avaliacoes_mes integer,
  observacoes text,
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists tenant_branding (
  tenant_id uuid primary key references tenants(id) on delete cascade,
  nome_portal text,
  logo_cliente_url text,
  tema text not null default 'dark' check (tema in ('dark', 'light')),
  cor_primaria text,
  cor_secundaria text,
  powered_by_label text not null default 'Powered by Service Farma',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists qtqd_componentes_catalogo (
  codigo text primary key,
  nome text not null,
  grupo text not null check (grupo in ('qt', 'qd', 'operacional')),
  ordem_exibicao integer not null,
  ativo boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists qtqd_indicadores_catalogo (
  codigo text primary key,
  nome text not null,
  unidade text not null,
  ordem_exibicao integer not null,
  created_at timestamptz not null default now()
);

create table if not exists tenant_componentes_config (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  codigo_componente text not null references qtqd_componentes_catalogo(codigo) on delete cascade,
  label_customizado text,
  visivel boolean not null default true,
  obrigatorio boolean not null default false,
  ordem_exibicao integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, codigo_componente)
);

create table if not exists avaliacoes_semanais (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  semana_referencia date not null,
  status text not null default 'rascunho' check (status in ('rascunho', 'fechada', 'publicada')),
  observacoes text,
  valores jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  published_at timestamptz,
  unique (tenant_id, semana_referencia)
);

create table if not exists avaliacao_indicadores (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  avaliacao_id uuid not null references avaliacoes_semanais(id) on delete cascade,
  codigo_indicador text not null references qtqd_indicadores_catalogo(codigo),
  nome_indicador text not null,
  valor_numerico numeric(18, 4),
  unidade text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (avaliacao_id, codigo_indicador)
);

create table if not exists avaliacao_analises (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  avaliacao_id uuid not null references avaliacoes_semanais(id) on delete cascade,
  origem text not null check (origem in ('manual', 'ia')),
  titulo text not null,
  conteudo text not null,
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now()
);

create table if not exists tenant_importacoes (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references tenants(id) on delete cascade,
  tipo text not null default 'primeira_carga' check (tipo in ('primeira_carga', 'recarga', 'ajuste_manual')),
  origem_arquivo_nome text not null,
  origem_arquivo_url text,
  status text not null default 'recebido' check (status in ('recebido', 'processando', 'concluido', 'concluido_parcial', 'erro')),
  observacoes text,
  registros_processados integer not null default 0,
  registros_com_erro integer not null default 0,
  payload_resumo jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  finished_at timestamptz
);

create index if not exists idx_tenant_users_tenant on tenant_users(tenant_id);
create index if not exists idx_tenant_users_user on tenant_users(user_id);
create index if not exists idx_tenant_profiles_tenant on tenant_profiles(tenant_id);
create index if not exists idx_tenant_licencas_tenant on tenant_licencas(tenant_id, inicio_vigencia desc);
create index if not exists idx_tenant_componentes_config_tenant on tenant_componentes_config(tenant_id);
create index if not exists idx_avaliacoes_tenant_semana on avaliacoes_semanais(tenant_id, semana_referencia desc);
create index if not exists idx_indicadores_avaliacao on avaliacao_indicadores(avaliacao_id);
create index if not exists idx_tenant_importacoes_tenant on tenant_importacoes(tenant_id, created_at desc);

create or replace function app.is_service_role()
returns boolean
language sql
stable
as $$
  select coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    ''
  ) = 'service_role';
$$;

create or replace function app.user_belongs_to_tenant(target_tenant uuid)
returns boolean
language sql
stable
as $$
  select
    app.is_service_role()
    or exists (
      select 1
      from tenant_users tu
      where tu.tenant_id = target_tenant
        and tu.user_id = auth.uid()
        and tu.ativo = true
    );
$$;

alter table tenants enable row level security;
alter table tenant_users enable row level security;
alter table tenant_profiles enable row level security;
alter table tenant_licencas enable row level security;
alter table tenant_branding enable row level security;
alter table avaliacoes_semanais enable row level security;
alter table avaliacao_indicadores enable row level security;
alter table avaliacao_analises enable row level security;
alter table qtqd_componentes_catalogo enable row level security;
alter table qtqd_indicadores_catalogo enable row level security;
alter table tenant_componentes_config enable row level security;
alter table tenant_importacoes enable row level security;

drop policy if exists "tenant read access" on tenants;
create policy "tenant read access" on tenants
for select
using (app.user_belongs_to_tenant(id));

drop policy if exists "tenant update access" on tenants;
create policy "tenant update access" on tenants
for update
using (app.user_belongs_to_tenant(id))
with check (app.user_belongs_to_tenant(id));

drop policy if exists "tenant membership access" on tenant_users;
create policy "tenant membership access" on tenant_users
for select
using (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "tenant profiles access" on tenant_profiles;
create policy "tenant profiles access" on tenant_profiles
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "tenant licenses access" on tenant_licencas;
create policy "tenant licenses access" on tenant_licencas
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "tenant branding access" on tenant_branding;
create policy "tenant branding access" on tenant_branding
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "avaliacoes tenant access" on avaliacoes_semanais;
create policy "avaliacoes tenant access" on avaliacoes_semanais
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "indicadores tenant access" on avaliacao_indicadores;
create policy "indicadores tenant access" on avaliacao_indicadores
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "analises tenant access" on avaliacao_analises;
create policy "analises tenant access" on avaliacao_analises
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "component config tenant access" on tenant_componentes_config;
create policy "component config tenant access" on tenant_componentes_config
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "tenant import access" on tenant_importacoes;
create policy "tenant import access" on tenant_importacoes
for all
using (app.user_belongs_to_tenant(tenant_id))
with check (app.user_belongs_to_tenant(tenant_id));

drop policy if exists "componentes read access" on qtqd_componentes_catalogo;
create policy "componentes read access" on qtqd_componentes_catalogo
for select
using (true);

drop policy if exists "indicadores catalog read access" on qtqd_indicadores_catalogo;
create policy "indicadores catalog read access" on qtqd_indicadores_catalogo
for select
using (true);

drop trigger if exists trg_tenants_updated_at on tenants;
create trigger trg_tenants_updated_at
before update on tenants
for each row execute function app.set_updated_at();

drop trigger if exists trg_tenant_users_updated_at on tenant_users;
create trigger trg_tenant_users_updated_at
before update on tenant_users
for each row execute function app.set_updated_at();

drop trigger if exists trg_tenant_profiles_updated_at on tenant_profiles;
create trigger trg_tenant_profiles_updated_at
before update on tenant_profiles
for each row execute function app.set_updated_at();

drop trigger if exists trg_tenant_licencas_updated_at on tenant_licencas;
create trigger trg_tenant_licencas_updated_at
before update on tenant_licencas
for each row execute function app.set_updated_at();

drop trigger if exists trg_tenant_branding_updated_at on tenant_branding;
create trigger trg_tenant_branding_updated_at
before update on tenant_branding
for each row execute function app.set_updated_at();

drop trigger if exists trg_tenant_componentes_config_updated_at on tenant_componentes_config;
create trigger trg_tenant_componentes_config_updated_at
before update on tenant_componentes_config
for each row execute function app.set_updated_at();

drop trigger if exists trg_avaliacoes_semanais_updated_at on avaliacoes_semanais;
create trigger trg_avaliacoes_semanais_updated_at
before update on avaliacoes_semanais
for each row execute function app.set_updated_at();

drop trigger if exists trg_avaliacao_indicadores_updated_at on avaliacao_indicadores;
create trigger trg_avaliacao_indicadores_updated_at
before update on avaliacao_indicadores
for each row execute function app.set_updated_at();

drop trigger if exists trg_tenant_importacoes_updated_at on tenant_importacoes;
create trigger trg_tenant_importacoes_updated_at
before update on tenant_importacoes
for each row execute function app.set_updated_at();

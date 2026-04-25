from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QTQD API"
    app_env: str = "local"

    # Banco de dados
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/qtqd"
    # Senha separada para evitar problema de encoding de caracteres especiais na URL
    db_password: str | None = None

    # Supabase
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None

    # SMTP — e-mail da Service Farma
    smtp_host:      str = "mail.servicefarma.far.br"
    smtp_port:      int = 465
    smtp_user:      str = "comercial@servicefarma.far.br"
    smtp_password:  str = ""
    smtp_from_name: str = "QTQD – Service Farma"

    # Token administrativo para endpoints de admin (X-Admin-Token header)
    admin_token: str = "trocar-este-token"

    # Credenciais do usuário admin do portal cliente (para geração de token via /admin/abrir-portal)
    portal_admin_email: str = "andre@servicefarma.far.br"
    portal_admin_password: str = ""

    # CORS — origens separadas por vírgula
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    frontend_client_url: str | None = None
    frontend_admin_url: str | None = None
    vercel_project_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = {o.strip() for o in self.cors_origins.split(",") if o.strip()}
        for url in (self.frontend_client_url, self.frontend_admin_url, self.vercel_project_url):
            if url:
                origins.add(url.rstrip("/"))
        return sorted(origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

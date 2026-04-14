from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "QTQD API"
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/qtqd"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    admin_token: str = "trocar-este-token"
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    frontend_client_url: str | None = None
    frontend_admin_url: str | None = None
    vercel_project_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = {origin.strip() for origin in self.cors_origins.split(",") if origin.strip()}
        for origin in (self.frontend_client_url, self.frontend_admin_url, self.vercel_project_url):
            if origin:
                origins.add(origin.rstrip("/"))
        return sorted(origins)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

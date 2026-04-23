from collections.abc import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings


def _build_engine_url() -> tuple[str | URL, dict]:
    # Supabase Transaction Pooler requires SSL
    connect_args: dict = {"sslmode": "require"}
    if settings.db_password:
        parsed = urlparse(settings.database_url)
        url = URL.create(
            drivername=parsed.scheme or "postgresql+psycopg",
            username=parsed.username,
            password=settings.db_password,
            host=parsed.hostname,
            port=parsed.port,
            database=(parsed.path or "/postgres").lstrip("/"),
        )
        return url, connect_args
    return settings.database_url, connect_args


_url, _connect_args = _build_engine_url()
engine = create_engine(_url, future=True, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

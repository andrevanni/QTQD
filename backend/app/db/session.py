from collections.abc import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings


def _build_engine_url() -> str | URL:
    # If DB_PASSWORD is set separately, avoid URL-encoding issues with special chars
    if settings.db_password:
        parsed = urlparse(settings.database_url)
        return URL.create(
            drivername=parsed.scheme or "postgresql+psycopg",
            username=parsed.username,
            password=settings.db_password,
            host=parsed.hostname,
            port=parsed.port,
            database=(parsed.path or "/postgres").lstrip("/"),
        )
    return settings.database_url


engine = create_engine(_build_engine_url(), future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

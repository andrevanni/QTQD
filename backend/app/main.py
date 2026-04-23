from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    import os
    keys = [k for k in os.environ if not k.startswith("AWS") and "SECRET" not in k and "PASSWORD" not in k]
    db_url = settings.database_url or ""
    # Show only host part (no password)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        db_host = f"{parsed.hostname}:{parsed.port}"
        db_user = parsed.username or ""
    except Exception:
        db_host = "parse-error"
        db_user = ""
    # Try a quick DB connect using the same engine as the app
    db_ok = False
    db_err = ""
    db_pw_len = len(settings.db_password) if settings.db_password else 0
    try:
        from backend.app.db.session import engine
        import sqlalchemy
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_err = str(e)[:300]
    return {
        "status": "ok",
        "env": settings.app_env,
        "token_is_default": settings.admin_token == "trocar-este-token",
        "db_host": db_host,
        "db_user": db_user,
        "db_pw_len": db_pw_len,
        "db_ok": db_ok,
        "db_err": db_err,
        "os_env_keys": sorted(keys),
    }


app.include_router(api_router)

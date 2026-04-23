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
    db_pw_len = len(settings.db_password) if settings.db_password else 0
    # Try each pooler region to find which one accepts the credentials
    import psycopg
    regions = ["us-east-1", "us-west-1", "eu-west-1", "eu-central-1", "ap-southeast-1", "sa-east-1"]
    # Test sa-east-1 with full error + show supabase_url prefix
    import psycopg
    pw = settings.db_password or ""
    user = f"postgres.{db_user.split('.')[-1]}" if "." in db_user else db_user
    sb_url = settings.supabase_url or ""
    sb_url_prefix = sb_url[:50] if sb_url else "NOT SET"
    db_ok = False
    db_err = ""
    try:
        conn = psycopg.connect(
            host="aws-0-sa-east-1.pooler.supabase.com", port=6543,
            user=user, password=pw, dbname="postgres",
            sslmode="require", connect_timeout=8
        )
        conn.close()
        db_ok = True
    except Exception as e:
        db_err = str(e)[:400]
    return {
        "status": "ok",
        "env": settings.app_env,
        "token_is_default": settings.admin_token == "trocar-este-token",
        "db_user": user,
        "db_pw_len": db_pw_len,
        "supabase_url_prefix": sb_url_prefix,
        "db_ok": db_ok,
        "db_err": db_err,
    }


app.include_router(api_router)

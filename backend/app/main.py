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
    region_results = {}
    pw = settings.db_password or ""
    user = f"postgres.{db_user.split('.')[-1]}" if "." in db_user else db_user
    for r in regions:
        host = f"aws-0-{r}.pooler.supabase.com"
        try:
            conn = psycopg.connect(
                host=host, port=6543, user=user, password=pw,
                dbname="postgres", sslmode="require", connect_timeout=5
            )
            conn.close()
            region_results[r] = "OK"
        except Exception as e:
            msg = str(e)[:80]
            region_results[r] = msg
    return {
        "status": "ok",
        "env": settings.app_env,
        "token_is_default": settings.admin_token == "trocar-este-token",
        "db_user": db_user,
        "db_pw_len": db_pw_len,
        "region_scan": region_results,
        "os_env_keys": sorted(keys),
    }


app.include_router(api_router)

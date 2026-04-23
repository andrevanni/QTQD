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
    sb_ok = False
    sb_err = ""
    try:
        from backend.app.db.client import get_supabase
        sb = get_supabase()
        result = sb.table("tenants").select("id").limit(1).execute()
        sb_ok = True
    except Exception as e:
        sb_err = str(e)[:200]
    return {
        "status": "ok",
        "env": settings.app_env,
        "token_is_default": settings.admin_token == "trocar-este-token",
        "supabase_ok": sb_ok,
        "supabase_err": sb_err,
    }


app.include_router(api_router)

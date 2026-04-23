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
    return {
        "status": "ok",
        "env": settings.app_env,
        "has_db": bool(settings.database_url and "supabase" in settings.database_url),
        "has_token": bool(settings.admin_token and settings.admin_token != "trocar-este-token"),
        "token_len": len(settings.admin_token),
        "os_token_len": len(os.environ.get("ADMIN_TOKEN", "")),
    }


app.include_router(api_router)

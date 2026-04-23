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
    return {
        "status": "ok",
        "env": settings.app_env,
        "token_is_default": settings.admin_token == "trocar-este-token",
        "os_env_keys": sorted(keys),
    }


app.include_router(api_router)

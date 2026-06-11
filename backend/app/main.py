from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import api

settings = get_settings()

app = FastAPI(title="Akenai VPN — Mini App BFF", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)


@app.get("/health")
async def health():
    return {"ok": True, "mock": settings.remnawave_mock}


# Раздача собранного фронтенда (npm run build → ../dist) тем же origin'ом,
# чтобы для тестов в Telegram хватило одного HTTPS-туннеля.
_dist = Path(__file__).resolve().parent.parent.parent / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="webapp")

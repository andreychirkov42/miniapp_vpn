import json
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import db
from .config import get_settings
from .routers import admin, api

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Открываем SQLite-хранилище обращений и держим одно соединение на всё
    # время жизни приложения (см. db.get_db).
    app.state.db = await db.connect(settings.db_path)
    try:
        yield
    finally:
        await app.state.db.close()


app = FastAPI(title="Akenai VPN — Mini App BFF", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)
app.include_router(admin.router)


# CSP, разрешающий встраивание в Telegram Web (он грузит мини-апп в iframe с
# CSP-enforcement: без своего Content-Security-Policy страница блокируется → чёрный
# экран в браузерном Telegram, хотя в десктоп/iOS-webview всё работает).
# Источники сужены под наш фронт: скрипт telegram-web-app.js, шрифты Google, /api.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://telegram.org; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors https://web.telegram.org https://telegram.org; "
    "base-uri 'self'; "
    "form-action 'self'"
)
_SECURITY_HEADERS = {
    "Content-Security-Policy": _CSP,
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@app.middleware("http")
async def security_and_cache(request, call_next):
    """index.html не кешируем (иначе WebView держит старую разметку), и на HTML
    вешаем CSP/security-заголовки — без CSP Telegram Web не встраивает мини-апп.
    Исключение — /open: он открывается отдельной вкладкой (не во фрейме) и
    использует inline-script для редиректа в клиент, который CSP бы заблокировал."""
    response = await call_next(request)
    if request.url.path.startswith("/open"):
        return response
    if response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-store, must-revalidate"
        for name, value in _SECURITY_HEADERS.items():
            response.headers[name] = value
    return response


@app.get("/health")
async def health():
    return {"ok": True, "mock": settings.remnawave_mock}


# Схемы импорта подписки, которым разрешено редиректить (защита от javascript:/data:).
_ALLOWED_SCHEMES = {
    "rabbithole", "sing-box", "flclashx", "clash", "clashmeta",
    "happ", "hiddify", "v2raytun", "streisand", "v2rayng",
    "koala-clash", "prizrak-box", "exclave", "stash", "sub",
}


@app.get("/open", response_class=HTMLResponse)
async def open_deeplink(to: str):
    """HTTPS-мост к deeplink клиента. Telegram WebView не пускает кастомные схемы
    напрямую, но http(s) открывает в системном браузере — а уже эта страница
    делает location.replace(scheme://…), и ОС открывает приложение с импортом."""
    target = unquote(to)
    scheme = target.split("://", 1)[0].lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise HTTPException(status_code=400, detail="scheme not allowed")
    # Передаём deeplink в JS как безопасный строковый литерал (json.dumps),
    # в HTML-разметку он не попадает — значит инъекция невозможна.
    target_js = json.dumps(target)
    html = f"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Открываем приложение…</title>
<style>
  body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
       background:#0b1f17;color:#eafff5;text-align:center;padding:48px 20px;margin:0}}
  .ic{{font-size:42px;margin-bottom:12px}}
  h1{{font-size:20px;margin:0 0 8px}}
  p{{color:#9fc7b5;font-size:14px;line-height:1.5;margin:0 0 24px}}
  button{{appearance:none;border:0;border-radius:14px;padding:14px 22px;
         font-size:16px;font-weight:600;color:#fff;cursor:pointer;
         background:linear-gradient(160deg,#0ea257,#0b7a42)}}
</style></head>
<body>
  <div class="ic">🚀</div>
  <h1>Открываем приложение…</h1>
  <p>Если приложение не открылось автоматически — нажмите кнопку.<br>
     Клиент должен быть установлен.</p>
  <button onclick="go()">Открыть приложение</button>
  <script>
    var target = {target_js};
    function go() {{ window.location.href = target; }}
    window.location.replace(target);
    setTimeout(go, 400);
  </script>
</body></html>"""
    return HTMLResponse(html)


# Раздача собранного фронтенда (npm run build → ../dist) тем же origin'ом,
# чтобы для тестов в Telegram хватило одного HTTPS-туннеля.
_dist = Path(__file__).resolve().parent.parent.parent / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="webapp")

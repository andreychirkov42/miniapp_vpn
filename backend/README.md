# Akenai VPN — Backend (BFF + бот)

FastAPI-прослойка между мини-аппом и панелью **Remnawave** + Telegram-бот (aiogram).
Фронт никогда не ходит в панель напрямую — токен панели живёт только здесь.

## Поток данных

```
Telegram Mini App ──(Authorization: tma <initData>)──▶ FastAPI BFF ──(Bearer <token>)──▶ Remnawave /api
        ▲                                                   │
        └──────────────── Telegram Bot (aiogram) ───────────┘
```

- `security.py` — проверяет HMAC `initData` по `BOT_TOKEN`, достаёт `telegramId`.
- `remnawave.py` — async-клиент панели + mock (в памяти) под `REMNAWAVE_MOCK=true`.
- `service.py` — маппинг user панели → схему фронта, логика триала/продления, deeplinks.
- `routers/api.py` — REST для мини-аппа.
- `bot/main.py` — бот: `/start`, кнопки, открытие мини-аппа (web_app).

## Эндпоинты (для фронта)

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/me` | подписки текущего пользователя |
| POST | `/api/trial` | активировать пробный период (создать юзера) |
| POST | `/api/subscriptions/{uuid}/renew` | продлить (`expireAt += RENEW_DAYS`) |
| GET | `/api/subscriptions/{uuid}/config` | `subscriptionUrl` + deeplinks |
| GET | `/health` | проверка живости |

Маппинг на Remnawave: `POST /api/users`, `GET /api/users/by-telegram-id/{id}`,
`PATCH /api/users`, поля `usedTrafficBytes/trafficLimitBytes/expireAt/hwidDeviceLimit/subscriptionUrl`.

## Запуск

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate — Linux/macOS
pip install -r requirements.txt
copy .env.example .env            # затем впиши свои значения

# API
uvicorn app.main:app --reload --port 8000
# Бот (в отдельном терминале)
python -m bot.main
```

> Требуется **Python 3.11+** (проверено на 3.14). Пока нет панели — оставь `REMNAWAVE_MOCK=true`.

## Переключение на реальную панель

В `.env`: `REMNAWAVE_MOCK=false`, заполнить `REMNAWAVE_BASE_URL`, `REMNAWAVE_TOKEN`,
`REMNAWAVE_SQUAD_UUID`. Код не меняется — `make_client()` сам выберет реальный клиент.

> Если структура ответа твоей версии Remnawave отличается (теги/название тарифа),
> правится только `service.map_subscription()` и `build_*_payload()`.

# Akenai VPN — Telegram Mini App

Telegram-мини-приложение «Akenai VPN», воссозданное по скриншотам из `screenshots/`.
Состоит из двух частей:

- **Фронтенд** (`src/`) — **React + Vite + TypeScript**, UI как на скринах.
- **Бэкенд** (`backend/`) — **FastAPI** BFF + **Telegram-бот** (aiogram), интеграция с панелью **Remnawave**.

Фронт ходит только в свой бэкенд; бэкенд хранит токен панели и проверяет Telegram `initData`.
Пока панели нет — работает mock-режим (синтетика, как на скринах).

## Что внутри

3 вкладки нижнего меню + модалка:

- **🏠 Главная** — горизонтальная карусель подписок (свайп / стрелки / точки):
  - `Основная` — тариф **Pro** с кнопками «Продлить» и «Установить и настроить»;
  - `Подписка #100564` — тариф **Whitelist** (0/5 GB, устройства, дата окончания);
  - `Создать подписку` — карточка добавления новой подписки.
  - Сверху — баннер «Привяжите Email».
- **💬 Поддержка** — «Новое обращение», «FAQ», «Установка на другом устройстве»,
  табы Открытые/История, пустое состояние.
- **👤 Профиль** — список разделов (Промокод, Новости, Канал, Политика, Соглашение,
  Рефералка, Партнёрка, На рабочий стол, FAQ, Вход в систему, Платежи).
- **Модалка** «Пробный период активирован» (показывается при запуске).

## Запуск (полный стек)

**1. Бэкенд + бот** (см. `backend/README.md`):
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env            # впиши значения (mock работает сразу)
uvicorn app.main:app --reload --port 8000
python -m bot.main                # бот — в отдельном терминале
```

**2. Фронтенд:**
```bash
npm install
npm run dev      # дев-сервер (Vite); порт 5173 или: npm run dev -- --port 5180
npm run build    # production-сборка в dist/
```

`src/.env` → `VITE_API_BASE` указывает на бэкенд (по умолчанию `http://localhost:8000`).
В браузере (вне Telegram) бэкенд подставляет `DEV_TELEGRAM_ID` из `.env`, поэтому
данные грузятся без реального `initData`.

### Что нужно для боевого запуска
Список значений (`BOT_TOKEN`, `REMNAWAVE_*`, публичные HTTPS-URL и т.д.) — в `backend/.env.example`.
Mini App обязан отдаваться по HTTPS и быть прописан в @BotFather как Web App.

## Структура

```
src/
  App.tsx              # вкладки, загрузка данных, модалки
  data.ts              # статичные данные (поддержка, пункты профиля)
  icons.tsx            # SVG-иконки + логотип AK
  index.css            # дизайн-токены и стили
  lib/
    api.ts             # клиент бэкенда (fetch + Authorization: tma)
    telegram.ts        # обёртка над Telegram WebApp SDK
    types.ts           # типы ответов API
  hooks/
    useSubscriptions.ts# загрузка/триал/продление
  components/
    Header.tsx, BottomNav.tsx, EmailNotice.tsx
    TrialModal.tsx     # пробный период (вызывает /api/trial)
    ConfigModal.tsx    # ссылка подписки + deeplinks (/api/.../config)
  screens/
    HomeScreen.tsx     # карусель подписок (реальные данные)
    SupportScreen.tsx, ProfileScreen.tsx

backend/
  app/                 # FastAPI: config, security (initData), remnawave, service, routers
  bot/                 # aiogram-бот (/start, web_app кнопки)
  requirements.txt, .env.example
```

## Статус сценариев

- ✅ Просмотр подписок (`GET /api/me`), трафик/срок/устройства/статус.
- ✅ Активация пробного периода (`POST /api/trial` → создание юзера на 3 дня).
- ✅ Конфиг/ссылка подписки + deeplinks в клиенты (`GET /api/.../config`).
- ✅ Продление (`POST /api/.../renew`, сдвиг `expireAt`; оплата пока не подключена).
- ⏳ Реальная панель Remnawave — включается флагом `REMNAWAVE_MOCK=false` + токен.
- ⏳ Платежи и реферальная система — точки расширения в `backend/app/service.py`.

"""Проверка реального доступа к панели Remnawave.

Запуск из каталога backend/ (с заполненным .env, REMNAWAVE_MOCK=false):

    .venv/bin/python -m scripts.check_panel [telegram_id]

Что проверяет:
  1. Авторизацию (статичный токен или логин/пароль) и доступность панели.
  2. Что выдача подписок по telegram_id работает (GET /api/users/by-telegram-id).
  3. Для найденного пользователя — наличие subscriptionUrl (то, что отдаём клиенту).

Скрипт только читает данные — ничего в панели не создаёт и не меняет.
"""

from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.remnawave import RealRemnawave, RemnawaveError
from app import service


async def main() -> int:
    settings = get_settings()

    print(f"BASE_URL : {settings.remnawave_base_url}")
    print(f"MOCK     : {settings.remnawave_mock}")
    print(f"AUTH     : {'token' if settings.remnawave_token else 'login/password' if settings.remnawave_username else 'НЕ НАСТРОЕНО'}")
    print("-" * 50)

    if settings.remnawave_mock:
        print("⚠️  REMNAWAVE_MOCK=true — это mock, а не реальная панель. Поставь false в .env.")
        return 1
    if "example.com" in settings.remnawave_base_url:
        print("⚠️  REMNAWAVE_BASE_URL всё ещё плейсхолдер. Впиши реальный адрес панели.")
        return 1
    if not (settings.remnawave_token or (settings.remnawave_username and settings.remnawave_password)):
        print("⚠️  Нет ни REMNAWAVE_TOKEN, ни REMNAWAVE_USERNAME/PASSWORD.")
        return 1

    telegram_id = int(sys.argv[1]) if len(sys.argv) > 1 else int(settings.dev_telegram_id or 0)
    client = RealRemnawave(settings)

    try:
        users = await client.get_users_by_telegram_id(telegram_id)
    except RemnawaveError as exc:
        print(f"❌ Ошибка панели: {exc}")
        return 2

    print(f"✅ Панель ответила. Подписок у telegram_id={telegram_id}: {len(users)}")
    for i, raw in enumerate(users):
        sub = service.map_subscription(raw, i)
        url = sub.subscription_url or "(пусто!)"
        print(f"  [{i}] {sub.label} · {sub.name} · до {sub.expire_text} · {sub.status}")
        print(f"      subscriptionUrl: {url}")
        if not sub.subscription_url:
            print("      ⚠️  Панель не вернула subscriptionUrl — клиенту нечего отдать.")

    if not users:
        print("  (подписок нет — это нормально для нового юзера; проверь на id с активной подпиской)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

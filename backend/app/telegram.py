"""Доставка сообщений в Telegram через Bot API.

Используется для обращений из мини-аппа: пользователь пишет внутри приложения,
бэкенд отправляет текст в чат поддержки (support_chat_id) от имени бота.
"""

from __future__ import annotations

import html
from pathlib import Path

import httpx

# Telegram обрезает подпись к фото на 1024 символах — длинный текст уедет в
# мини-апп, в подпись кладём усечённую версию.
CAPTION_LIMIT = 1024


class TelegramSendError(RuntimeError):
    pass


async def send_message(bot_token: str, chat_id: str, text: str) -> None:
    """Отправляет сообщение в чат. Бросает TelegramSendError при сбое."""
    if not bot_token:
        raise TelegramSendError("BOT_TOKEN не настроен")
    if not chat_id:
        raise TelegramSendError("SUPPORT_CHAT_ID не настроен")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )
    if resp.status_code >= 400:
        raise TelegramSendError(f"sendMessage -> {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if not data.get("ok"):
        raise TelegramSendError(f"sendMessage not ok: {data}")


async def send_photo(bot_token: str, chat_id: str, photo_path: str, caption: str) -> None:
    """Отправляет картинку с подписью в чат. Бросает TelegramSendError при сбое."""
    if not bot_token:
        raise TelegramSendError("BOT_TOKEN не настроен")
    if not chat_id:
        raise TelegramSendError("SUPPORT_CHAT_ID не настроен")

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    path = Path(photo_path)
    async with httpx.AsyncClient(timeout=30) as client:
        with path.open("rb") as fh:
            resp = await client.post(
                url,
                data={"chat_id": chat_id, "caption": caption[:CAPTION_LIMIT], "parse_mode": "HTML"},
                files={"photo": (path.name, fh)},
            )
    if resp.status_code >= 400:
        raise TelegramSendError(f"sendPhoto -> {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if not data.get("ok"):
        raise TelegramSendError(f"sendPhoto not ok: {data}")


def build_alert_text(
    *, ticket_id: int, username: str | None, first_name: str | None, message: str
) -> str:
    """Короткий алерт в чат поддержки: только сигнал «есть новое», без всего диалога.
    Полный диалог админ открывает в мини-аппе → раздел «Заявки»."""
    who = html.escape(first_name or "пользователь")
    handle = f" (@{html.escape(username)})" if username else ""
    preview = html.escape(message.strip())
    if len(preview) > 160:
        preview = preview[:160] + "…"
    return (
        f"🆘 <b>Новое обращение #{ticket_id}</b>\n"
        f"<b>От:</b> {who}{handle}\n\n"
        f"{preview}\n\n"
        "<i>Ответить: откройте «Кабинет» в боте → Поддержка → Заявки.</i>"
    )


def build_user_reply_text(*, ticket_id: int, message: str) -> str:
    """Уведомление пользователю в личку об ответе поддержки."""
    body = html.escape(message.strip())
    return (
        f"💬 <b>Ответ поддержки по обращению #{ticket_id}</b>\n\n"
        f"{body}\n\n"
        "<i>Продолжить переписку можно в мини-аппе → Поддержка.</i>"
    )

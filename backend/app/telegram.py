"""Доставка сообщений в Telegram через Bot API.

Используется для обращений из мини-аппа: пользователь пишет внутри приложения,
бэкенд отправляет текст в чат поддержки (support_chat_id) от имени бота.
"""

from __future__ import annotations

import html

import httpx


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


def build_support_text(
    *, telegram_id: int, username: str | None, first_name: str | None, message: str
) -> str:
    """Форматирует обращение для чата поддержки (с экранированием пользовательского текста)."""
    who = html.escape(first_name or "пользователь")
    handle = f"@{html.escape(username)}" if username else "—"
    body = html.escape(message.strip())
    return (
        "🆘 <b>Новое обращение из мини-аппа</b>\n\n"
        f"<b>От:</b> {who} ({handle})\n"
        f"<b>Telegram ID:</b> <code>{telegram_id}</code>\n\n"
        f"<b>Сообщение:</b>\n{body}"
    )

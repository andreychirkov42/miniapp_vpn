"""Akenai VPN Telegram bot (aiogram 3).

Replicates the /start welcome from the screenshots and opens the mini app.
Run:  python -m bot.main      (from the backend/ directory)
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MenuButtonDefault,
    ReplyKeyboardRemove,
    WebAppInfo,
)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402

settings = get_settings()
logging.basicConfig(level=logging.INFO)

# Версия мини-аппа в URL — для сброса кеша WebView Telegram (он кеширует контент
# по полному URL; смена ?v= заставляет загрузить свежую сборку). Бампать при деплое.
WEBAPP_VERSION = "20260613f"


def webapp_info() -> WebAppInfo:
    sep = "&" if "?" in settings.webapp_url else "?"
    return WebAppInfo(url=f"{settings.webapp_url}{sep}v={WEBAPP_VERSION}")

WELCOME = (
    "<b>Добро пожаловать в Akenai VPN!</b>\n\n"
    "Сервис поможет вам\n"
    "— с обходом <b>белых списков</b>\n"
    "— с <b>безопасным и анонимным</b> использованием интернета\n"
    "— а также <b>блокирует рекламу на YouTube!</b>\n\n"
    "🔗 <b>Как подключиться:</b>\n"
    'Жмите кнопку <b>"Попробовать за 0 ₽"</b>, чтобы активировать пробный '
    "период на месяц за 0 рублей.\n"
    'Или переходите в <b>"Личный кабинет"</b> для подключения тарифа.'
)


def main_keyboard() -> InlineKeyboardMarkup:
    webapp = webapp_info()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Попробовать за 0 ₽", web_app=webapp)],
            [InlineKeyboardButton(text="👤 Личный кабинет", web_app=webapp)],
            [InlineKeyboardButton(text="💬 Чат с поддержкой", url=settings.support_url)],
        ]
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    # ReplyKeyboardRemove — убираем старую reply-кнопку «Кабинет» из чата.
    # Кабинет открывается только inline-кнопками (валидный initData).
    await message.answer(WELCOME, reply_markup=ReplyKeyboardRemove())
    await message.answer("Выберите действие:", reply_markup=main_keyboard())


@dp.message(F.text == "🗄 Кабинет")
async def on_cabinet(message: Message) -> None:
    await message.answer("Открываю личный кабинет 👇", reply_markup=main_keyboard())


async def run() -> None:
    if not settings.bot_token or settings.bot_token.startswith("123456:"):
        raise SystemExit("BOT_TOKEN не задан в backend/.env")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Меню-кнопка web_app даёт пустой initData (особенно в Telegram Desktop) → 401.
    # Кабинет открываем только inline-кнопками из /start, а меню-кнопку сбрасываем
    # на дефолт (список команд), чтобы её больше не было.
    await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
    logging.info("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())

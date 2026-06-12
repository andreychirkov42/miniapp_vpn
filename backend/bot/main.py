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
    KeyboardButton,
    Message,
    MenuButtonWebApp,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402

settings = get_settings()
logging.basicConfig(level=logging.INFO)

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
    webapp = WebAppInfo(url=settings.webapp_url)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Попробовать за 0 ₽", web_app=webapp)],
            [InlineKeyboardButton(text="👤 Личный кабинет", web_app=webapp)],
            [InlineKeyboardButton(text="💬 Чат с поддержкой", url=settings.support_url)],
        ]
    )


def cabinet_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🗄 Кабинет", web_app=WebAppInfo(url=settings.webapp_url))]],
        resize_keyboard=True,
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=cabinet_keyboard())
    await message.answer("Выберите действие:", reply_markup=main_keyboard())


@dp.message(F.text == "🗄 Кабинет")
async def on_cabinet(message: Message) -> None:
    await message.answer("Открываю личный кабинет 👇", reply_markup=main_keyboard())


async def run() -> None:
    if not settings.bot_token or settings.bot_token.startswith("123456:"):
        raise SystemExit("BOT_TOKEN не задан в backend/.env")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Кнопка-меню рядом с полем ввода открывает мини-апп
    await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Кабинет", web_app=WebAppInfo(url=settings.webapp_url)))
    logging.info("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())

"""Akenai VPN Telegram bot (aiogram 3).

Replicates the /start welcome from the screenshots and opens the mini app.
Run:  python -m bot.main      (from the backend/ directory)
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MenuButtonDefault,
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
WEBAPP_VERSION = "20260613j"


def webapp_info() -> WebAppInfo:
    sep = "&" if "?" in settings.webapp_url else "?"
    return WebAppInfo(url=f"{settings.webapp_url}{sep}v={WEBAPP_VERSION}")

WELCOME = (
    "🇰🇬 <b>Платежный сервер (Кыргызстан)</b>\n"
    "Ваш личный сервер для бесперебойных оплат и интернета.\n\n"
    "🔥 <b>Почему он нужен:</b>\n"
    "1️⃣ <b>Гарантия оплат:</b> Платежные системы видят вас внутри Кыргызстана. "
    "Карты МБАНК работают на 100%, без ложных блокировок со стороны систем "
    "безопасности + экономите на НДС.\n"
    "2️⃣ <b>Стабильный доступ:</b> Обеспечьте бесперебойное подключение к "
    "международным рабочим сервисам, корпоративным сайтам, подпискам и "
    "мессенджерам без сбоев и потери скорости.\n\n"
    "🔥 <b>Тестовый режим: 1 месяц — БЕСПЛАТНО!</b> Чтобы вы лично убедились в "
    "стабильности сервера. Нам важно ваше мнение! Напишите нам отзыв или "
    "предложение по работе сервера.\n\n"
    "<b>ВЫБЕРИТЕ ДЕЙСТВИЕ</b>👇\n"
    "🎁 <b>Попробовать бесплатно</b> — как подключить\n"
    "👤 <b>Личный кабинет</b> — подписка и срок действия\n"
    "💬 <b>Отзывы и предложения</b> — напишите нам\n"
    "🆘 <b>Техподдержка</b> — если что-то не работает"
)


def main_keyboard() -> InlineKeyboardMarkup:
    # Все кнопки открывают мини-апп (валидный initData приходит только из inline
    # web_app-кнопок). Отзывы и техподдержка ведут на экран «Поддержка» мини-аппа,
    # где обращение доставляется в чат поддержки.
    webapp = webapp_info()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Попробовать бесплатно", web_app=webapp)],
            [InlineKeyboardButton(text="👤 Личный кабинет", web_app=webapp)],
            [InlineKeyboardButton(text="💬 Отзывы и предложения", web_app=webapp)],
            [InlineKeyboardButton(text="🆘 Техподдержка", web_app=webapp)],
        ]
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    # Одно сообщение: приветствие с меню действий внутри текста + inline-кнопки.
    # Кабинет открывается только inline-кнопками (валидный initData).
    await message.answer(WELCOME, reply_markup=main_keyboard())


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

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
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageOriginHiddenUser,
    MessageOriginUser,
    MenuButtonDefault,
    WebAppInfo,
)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402
from app import service  # noqa: E402
from app.remnawave import RemnawaveError, get_client  # noqa: E402

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("akenai.bot")

# Версия мини-аппа в URL — для сброса кеша WebView Telegram (он кеширует контент
# по полному URL; смена ?v= заставляет загрузить свежую сборку). Бампать при деплое.
WEBAPP_VERSION = "20260622a"


def webapp_info() -> WebAppInfo:
    sep = "&" if "?" in settings.webapp_url else "?"
    return WebAppInfo(url=f"{settings.webapp_url}{sep}v={WEBAPP_VERSION}")


def _plural_days(n: int) -> str:
    """Русское склонение слова «день» для числа n."""
    m10, m100 = n % 10, n % 100
    if m10 == 1 and m100 != 11:
        word = "день"
    elif 2 <= m10 <= 4 and not 12 <= m100 <= 14:
        word = "дня"
    else:
        word = "дней"
    return f"{n} {word}"


# Срок триала подставляется из настроек (TRIAL_DAYS), чтобы текст не расходился
# с реальной выдачей подписки.
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
    f"🔥 <b>Тестовый режим: {_plural_days(settings.trial_days)} — БЕСПЛАТНО!</b> "
    "Чтобы вы лично убедились в "
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


@dp.message(Command("my_id"))
async def on_my_id(message: Message) -> None:
    """Показывает Telegram ID отправителя — нужно для заполнения ADMIN_IDS."""
    if message.from_user is None:
        return
    await message.answer(
        f"🆔 Ваш Telegram ID:\n<code>{message.from_user.id}</code>\n\n"
        "Нажмите на число, чтобы скопировать."
    )


# ===================== Продление подписки оператором =====================
# Оператор (Telegram ID из ADMIN_IDS) пересылает боту сообщение пользователя →
# бот находит подписку по Telegram ID → карточка с кнопкой «Продлить на N мес.».

def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_id_list


def _months_word(n: int) -> str:
    m10, m100 = n % 10, n % 100
    if m10 == 1 and m100 != 11:
        return "месяц"
    if 2 <= m10 <= 4 and not 12 <= m100 <= 14:
        return "месяца"
    return "месяцев"


def _fmt_expire(raw: dict) -> str:
    dt = service._parse_dt(raw.get("expireAt"))
    return dt.strftime("%d.%m.%Y") if dt else "—"


def _renew_keyboard(telegram_id: int, months: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"➡️ Продлить на {months} мес.",
                    callback_data=f"renew:{telegram_id}",
                )
            ]
        ]
    )


@dp.message(F.forward_origin)
async def on_forward(message: Message) -> None:
    # Фича только для операторов; обычным пользователям молчим.
    if message.from_user is None or not _is_admin(message.from_user.id):
        return

    origin = message.forward_origin
    if isinstance(origin, MessageOriginHiddenUser):
        await message.answer(
            "🔒 Пользователь скрыл аккаунт при пересылке — Telegram не отдаёт его ID.\n"
            "Попросите прислать сообщение ещё раз, отключив приватность пересылки."
        )
        return
    if not isinstance(origin, MessageOriginUser):
        await message.answer(
            "↪️ Это не пересланное сообщение от пользователя.\n"
            "Перешлите сообщение того, кому нужно продлить подписку."
        )
        return

    target = origin.sender_user
    months = settings.renew_months
    try:
        users = await get_client().get_users_by_telegram_id(target.id)
    except RemnawaveError as exc:
        logger.warning("renew lookup failed tg=%s: %s", target.id, exc)
        await message.answer("⚠️ Не удалось получить данные из панели. Попробуйте позже.")
        return

    name = target.first_name or "пользователь"
    handle = f" (@{target.username})" if target.username else ""
    if not users:
        await message.answer(
            f"🔎 Подписка не найдена.\n\n👤 <b>{name}</b>{handle}\n🆔 <code>{target.id}</code>\n\n"
            "В панели нет пользователя с этим Telegram ID."
        )
        return

    lines = [
        "🧾 <b>Продление подписки</b>",
        "",
        f"👤 <b>{name}</b>{handle}",
        f"🆔 <code>{target.id}</code>",
        "",
    ]
    for i, u in enumerate(users, 1):
        prefix = f"{i}. " if len(users) > 1 else "Действует до: "
        lines.append(f"{prefix}{_fmt_expire(u)}")
    lines.append("")
    lines.append(f"Нажмите кнопку, чтобы продлить на <b>{months} {_months_word(months)}</b>.")
    await message.answer("\n".join(lines), reply_markup=_renew_keyboard(target.id, months))


@dp.callback_query(F.data.startswith("renew:"))
async def on_renew(callback: CallbackQuery) -> None:
    if callback.from_user is None or not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    try:
        target_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer()
        return

    months = settings.renew_months
    client = get_client()
    try:
        users = await client.get_users_by_telegram_id(target_id)
        renewed = []
        for u in users:
            if u.get("uuid"):
                updated = await client.update_user(
                    service.build_renew_months_payload(u, months)
                )
                renewed.append(updated or u)
    except RemnawaveError as exc:
        logger.warning("renew failed tg=%s: %s", target_id, exc)
        await callback.answer("⚠️ Не удалось продлить, попробуйте ещё раз", show_alert=True)
        return

    if not renewed:
        await callback.answer("У пользователя нет подписки для продления", show_alert=True)
        return

    await callback.answer("✅ Подписка продлена")
    until = _fmt_expire(renewed[0])
    if callback.message is not None:
        try:
            await callback.message.edit_text(
                f"✅ Продлено на <b>{months} {_months_word(months)}</b>.\n\n"
                f"<b>Новая дата окончания:</b> {until}\n\n"
                "Пользователь получил уведомление в личку."
            )
        except TelegramBadRequest:
            pass
    logger.info("RENEW admin=%s target=%s months=%s until=%s",
                callback.from_user.id, target_id, months, until)
    # Уведомление пользователю в личку (молча гасим, если он не писал боту).
    try:
        await callback.bot.send_message(
            target_id,
            "✅ <b>Ваша подписка продлена!</b>\n\n"
            f"Доступ активен до <b>{until}</b>.\nСпасибо, что остаётесь с нами 🙌",
        )
    except (TelegramForbiddenError, TelegramBadRequest) as exc:
        logger.info("не удалось уведомить юзера tg=%s: %s", target_id, exc)


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

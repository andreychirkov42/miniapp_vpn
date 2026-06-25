"""Akenai VPN Telegram bot (aiogram 3).

Replicates the /start welcome from the screenshots and opens the mini app.
Run:  python -m bot.main      (from the backend/ directory)
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone

from typing import Any, Awaitable, Callable

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
    TelegramObject,
    User,
    WebAppInfo,
)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402
from app import service  # noqa: E402
from app.remnawave import RemnawaveError, get_client  # noqa: E402
from bot import notify_store  # noqa: E402

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("akenai.bot")

# Версия мини-аппа в URL — для сброса кеша WebView Telegram (он кеширует контент
# по полному URL; смена ?v= заставляет загрузить свежую сборку). Бампать при деплое.
WEBAPP_VERSION = "20260624a"


def webapp_info(screen: str | None = None) -> WebAppInfo:
    sep = "&" if "?" in settings.webapp_url else "?"
    url = f"{settings.webapp_url}{sep}v={WEBAPP_VERSION}"
    if screen:
        # Фронт читает ?screen= и открывает соответствующую вкладку.
        url = f"{url}&screen={screen}"
    return WebAppInfo(url=url)


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


# ===================== Сброс застрявшей персональной menu-кнопки =====================
# История проблемы: раньше у части пользователей персонально стояла web_app-кнопка ☰
# на СТАРЫЙ сайт. Глобальный сброс на дефолт (set_chat_menu_button без chat_id, см. run())
# такие персональные кнопки НЕ перетирает. Поэтому при ЛЮБОМ контакте пользователя с
# ботом разово (за процесс) сбрасываем его персональную menu-кнопку на дефолт.
_menu_reset_done: set[int] = set()


async def _reset_personal_menu(bot: Bot, user: User | None) -> None:
    """Один раз за процесс гасит персональную menu-кнопку пользователя (приватный чат)."""
    if user is None or user.is_bot or user.id in _menu_reset_done:
        return
    _menu_reset_done.add(user.id)
    try:
        # В приватном диалоге chat_id == user.id.
        await bot.set_chat_menu_button(chat_id=user.id, menu_button=MenuButtonDefault())
    except (TelegramBadRequest, TelegramForbiddenError) as exc:
        logger.info("не удалось сбросить menu-кнопку tg=%s: %s", user.id, exc)


async def _menu_reset_middleware(
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
) -> Any:
    await _reset_personal_menu(data["bot"], data.get("event_from_user"))
    return await handler(event, data)


# Вешаем на сообщения и колбэки — покрывает /start, любой текст, нажатия inline-кнопок.
dp.message.outer_middleware(_menu_reset_middleware)
dp.callback_query.outer_middleware(_menu_reset_middleware)


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    # Одно сообщение: приветствие с меню действий внутри текста + inline-кнопки.
    # Кабинет открывается только inline-кнопками (валидный initData).
    # Доп. страховка к middleware: гарантированно гасим персональную menu-кнопку.
    await _reset_personal_menu(message.bot, message.from_user)
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


async def _offer_renewal(
    message: Message, *, target_id: int, name: str, handle: str, not_found_hint: str
) -> None:
    """Карточка продления по Telegram ID: ищет подписки и рисует кнопку.

    Общая для двух входов — пересылки сообщения и ввода @username оператором.
    """
    months = settings.renew_months
    try:
        users = await get_client().get_users_by_telegram_id(target_id)
    except RemnawaveError as exc:
        logger.warning("renew lookup failed tg=%s: %s", target_id, exc)
        await message.answer("⚠️ Не удалось получить данные из панели. Попробуйте позже.")
        return

    if not users:
        await message.answer(
            f"🔎 Подписка не найдена.\n\n👤 <b>{name}</b>{handle}\n🆔 <code>{target_id}</code>\n\n"
            f"{not_found_hint}"
        )
        return

    lines = [
        "🧾 <b>Продление подписки</b>",
        "",
        f"👤 <b>{name}</b>{handle}",
        f"🆔 <code>{target_id}</code>",
        "",
    ]
    for i, u in enumerate(users, 1):
        prefix = f"{i}. " if len(users) > 1 else "Действует до: "
        lines.append(f"{prefix}{_fmt_expire(u)}")
    lines.append("")
    lines.append(f"Нажмите кнопку, чтобы продлить на <b>{months} {_months_word(months)}</b>.")
    await message.answer("\n".join(lines), reply_markup=_renew_keyboard(target_id, months))


@dp.message(F.forward_origin)
async def on_forward(message: Message) -> None:
    # Фича только для операторов; обычным пользователям молчим.
    if message.from_user is None or not _is_admin(message.from_user.id):
        return

    origin = message.forward_origin
    if isinstance(origin, MessageOriginHiddenUser):
        await message.answer(
            "🔒 Пользователь скрыл аккаунт при пересылке — Telegram не отдаёт его ID.\n"
            "Отправьте его <b>@username</b> (через собаку) — найдём по нему."
        )
        return
    if not isinstance(origin, MessageOriginUser):
        await message.answer(
            "↪️ Это не пересланное сообщение от пользователя.\n"
            "Перешлите сообщение того, кому нужно продлить подписку, или отправьте его @username."
        )
        return

    target = origin.sender_user
    await _offer_renewal(
        message,
        target_id=target.id,
        name=target.first_name or "пользователь",
        handle=f" (@{target.username})" if target.username else "",
        not_found_hint="В панели нет пользователя с этим Telegram ID.",
    )


# Оператор шлёт «@ivan_petrov», когда пересылка скрывает ID. Требуем ведущую
# собаку, чтобы не реагировать на обычные текстовые сообщения. Telegram-хэндл —
# [A-Za-z0-9_], 5-32 симв.; панель хранит его как username, допускаем от 4.
_USERNAME_RE = re.compile(r"^@([A-Za-z0-9_]{4,32})$")


@dp.message(F.text)
async def on_username(message: Message) -> None:
    # Только операторам; остальным молчим (как и forward-хендлер).
    if message.from_user is None or not _is_admin(message.from_user.id):
        return

    match = _USERNAME_RE.match((message.text or "").strip())
    if match is None:
        return  # не «@username» — не наш кейс, молчим
    username = match.group(1)

    try:
        user = await get_client().get_user_by_username(username)
    except RemnawaveError as exc:
        logger.warning("renew lookup by username failed @%s: %s", username, exc)
        await message.answer("⚠️ Не удалось получить данные из панели. Попробуйте позже.")
        return

    if not user:
        await message.answer(
            f"🔎 Пользователь <b>@{username}</b> не найден в панели.\n"
            "Проверьте написание хэндла или перешлите сообщение пользователя."
        )
        return

    tg_id = user.get("telegramId")
    if not tg_id:
        # Подписка есть, но без Telegram ID — продлить через кнопку (она ищет по ID)
        # нельзя. Такое почти не случается, т.к. юзеры заводятся со своим tg-id.
        await message.answer(
            f"🔎 Нашёл <b>@{username}</b>, но у подписки не привязан Telegram ID — "
            "продлить кнопкой не получится. Перешлите сообщение пользователя."
        )
        return

    await _offer_renewal(
        message,
        target_id=int(tg_id),
        name=user.get("username") or username,
        handle=f" (@{username})",
        not_found_hint="В панели нет активной подписки для этого пользователя.",
    )


@dp.callback_query(F.data == "how_to_pay")
async def on_how_to_pay(callback: CallbackQuery) -> None:
    """Показывает реквизиты и инструкцию по оплате (кнопка из напоминания)."""
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer(HOW_TO_PAY_TEXT)


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


# ===================== Напоминание об окончании подписки =====================
# Фоновый цикл рядом с polling: раз в notify_check_interval_hours сканирует панель
# и пишет пользователям, у кого подписка истекает в ближайшие notify_before_days.

# Текст с реквизитами и инструкцией по оплате продления (показывается по кнопке
# «Как оплатить?»). Реквизиты статичные — при смене карты/тарифа править здесь.
HOW_TO_PAY_TEXT = (
    '🇰🇬 Продление "Сервер КИРГИЗИЯ"\n'
    "▪️Срок действия - 6 месяцев\n"
    "▪️Стоимость - $19 (1.450₽)\n"
    "▪️Способ оплаты: Перевод через приложение МБАНК на карту МБАНК.\n\n"
    '🇰🇬 Инструкция для оплаты "Сервер КИРГИЗИЯ":\n'
    "1️⃣ Откройте приложение МБАНК.\n"
    "2️⃣ Перейдите в раздел «Переводы» → «По номеру карты».\n"
    "3️⃣ Укажите:\n"
    # <code> в Telegram копируется по нажатию — номер без пробелов для чистой вставки.
    "▪️номер карты: <code>4177490182015059</code> (нажмите, чтобы скопировать)\n"
    "▪️валюта: USD\n"
    "▪️размер перевода: $19\n"
    "▫️Получатель: Мирошников В.\n"
    '4️⃣ Нажмите "Перевести" и отправьте скриншот чека в поддержку прямо в приложении '
    "(раздел «Поддержка» → «Новое обращение»)."
)


def _expiry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Как оплатить?", callback_data="how_to_pay")]
        ]
    )


def _expiry_text(days_left: int) -> str:
    return (
        f"⏳ <b>Подписка заканчивается через {_plural_days(days_left)}</b>\n\n"
        "Продлите её заранее, чтобы не потерять доступ к серверу — без обрывов "
        "оплат и интернета.\n\n"
        "Нажмите кнопку ниже, чтобы узнать, как оплатить 👇"
    )


async def run_expiry_notifications(bot: Bot, conn) -> None:
    within = settings.notify_before_days
    try:
        users = await get_client().get_all_users()
    except RemnawaveError as exc:
        logger.warning("expiry scan failed: %s", exc)
        return

    now = datetime.now(timezone.utc)
    sent = 0
    for u in users:
        if not service.is_expiring_soon(u, within, now):
            continue
        tg_id = u.get("telegramId")
        uuid = u.get("uuid")
        expire_at = u.get("expireAt")
        if not tg_id or not uuid or not expire_at:
            continue
        if await notify_store.was_notified(conn, uuid, expire_at):
            continue

        left = service.days_until_expiry(u, now) or 0
        try:
            await bot.send_message(int(tg_id), _expiry_text(left), reply_markup=_expiry_keyboard())
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest) as exc:
            # Юзер не писал боту или чат недоступен — доставка невозможна. Всё равно
            # помечаем, чтобы не долбить панель/Telegram каждый цикл этого периода.
            logger.info("напоминание не доставлено tg=%s: %s", tg_id, exc)
        await notify_store.mark_notified(conn, uuid, expire_at, int(tg_id))
        await asyncio.sleep(0.05)  # бережём лимиты Telegram при массовой рассылке

    if sent:
        logger.info("EXPIRY reminders sent=%s within=%sd", sent, within)


async def notify_loop(bot: Bot) -> None:
    conn = await notify_store.connect(notify_store.notify_db_path(settings.db_path))
    interval = max(1, settings.notify_check_interval_hours) * 3600
    while True:
        try:
            await run_expiry_notifications(bot, conn)
        except Exception:  # noqa: BLE001 — цикл не должен падать из-за разовой ошибки
            logger.exception("expiry notification cycle failed")
        await asyncio.sleep(interval)


async def run() -> None:
    if not settings.bot_token or settings.bot_token.startswith("123456:"):
        raise SystemExit("BOT_TOKEN не задан в backend/.env")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Меню-кнопка web_app даёт пустой initData (особенно в Telegram Desktop) → 401.
    # Кабинет открываем только inline-кнопками из /start, а меню-кнопку сбрасываем
    # на дефолт (список команд), чтобы её больше не было.
    await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
    # Фоновое напоминание об окончании подписки крутится рядом с polling.
    asyncio.create_task(notify_loop(bot))
    logging.info("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())

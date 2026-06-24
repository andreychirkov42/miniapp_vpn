"""Разовая рассылка свежего /start всем пользователям из панели.

Зачем: у старых юзеров в истории чата висят сообщения с web_app-кнопкой на старый
сайт, а удалить их Bot API не даёт (deleteMessage только <48ч, перечислить историю
нельзя). Рассылка кладёт каждому свежее приветствие с актуальными inline-кнопками —
оно становится последним сообщением в чате. Текст и клавиатура переиспользуются из
bot.main, поэтому рассылка всегда совпадает с тем, что отдаёт /start.

Запуск (из каталога backend/):
    python -m bot.broadcast

Env-флаги (необязательные):
    BROADCAST_DRY_RUN=1          — не отправлять, только посчитать аудиторию
    BROADCAST_ONLY_IDS=1,2,3     — отправить только этим Telegram ID (тест на себе)
    BROADCAST_CAMPAIGN=<id>      — id кампании для дедупа (по умолчанию fresh-start-20260624)

Дедуп: успешно/окончательно обработанные ID пишутся в broadcast.db (рядом с
support.db, на том же volume). Повторный запуск той же кампании пропускает уже
обработанных — безопасно перезапускать после обрыва.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402
from app.remnawave import RemnawaveError, get_client  # noqa: E402
from bot.main import WELCOME, main_keyboard  # noqa: E402

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("akenai.broadcast")

# ~20 сообщений/сек — с запасом под лимит Telegram (~30/сек на разных получателей).
SEND_INTERVAL_SEC = 0.05
PROGRESS_EVERY = 50
CAMPAIGN = os.getenv("BROADCAST_CAMPAIGN", "fresh-start-20260624")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS broadcast_sent (
    campaign     TEXT NOT NULL,
    telegram_id  INTEGER NOT NULL,
    status       TEXT NOT NULL,
    sent_at      TEXT NOT NULL,
    PRIMARY KEY (campaign, telegram_id)
);
"""


def _db_path() -> str:
    """broadcast.db рядом с support.db (тот же каталог/volume), как notify.db."""
    return str(Path(settings.db_path).with_name("broadcast.db"))


async def _connect() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(_db_path())
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.executescript(_SCHEMA)
    await conn.commit()
    return conn


async def _already_sent(conn: aiosqlite.Connection, tg_id: int) -> bool:
    cur = await conn.execute(
        "SELECT 1 FROM broadcast_sent WHERE campaign = ? AND telegram_id = ?",
        (CAMPAIGN, tg_id),
    )
    return await cur.fetchone() is not None


async def _mark(conn: aiosqlite.Connection, tg_id: int, status: str) -> None:
    await conn.execute(
        "INSERT OR REPLACE INTO broadcast_sent "
        "(campaign, telegram_id, status, sent_at) VALUES (?, ?, ?, ?)",
        (CAMPAIGN, tg_id, status, datetime.now(timezone.utc).isoformat()),
    )
    await conn.commit()


def _parse_only_ids() -> set[int]:
    raw = os.getenv("BROADCAST_ONLY_IDS", "").strip()
    if not raw:
        return set()
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


async def _collect_audience() -> list[int]:
    """Уникальные Telegram ID из панели (у юзера может быть несколько подписок)."""
    users = await get_client().get_all_users()
    ids: set[int] = set()
    for u in users:
        tg = u.get("telegramId")
        if not tg:
            continue
        try:
            ids.add(int(tg))
        except (TypeError, ValueError):
            continue
    return sorted(ids)


async def _send_one(bot: Bot, tg_id: int) -> str:
    """Отправляет свежее приветствие. Возвращает статус: sent / blocked / failed.

    При flood-control (429) ждёт указанное время и ретраит один раз.
    """
    for _ in range(2):
        try:
            await bot.send_message(tg_id, WELCOME, reply_markup=main_keyboard())
            return "sent"
        except TelegramRetryAfter as exc:
            wait = exc.retry_after + 1
            logger.warning("flood control tg=%s — ждём %sс", tg_id, wait)
            await asyncio.sleep(wait)
            continue
        except TelegramForbiddenError:
            # Пользователь заблокировал бота или удалил чат — доставка невозможна.
            return "blocked"
        except TelegramBadRequest as exc:
            logger.info("не доставлено tg=%s: %s", tg_id, exc)
            return "failed"
    return "failed"


async def run() -> None:
    if not settings.bot_token or settings.bot_token.startswith("123456:"):
        raise SystemExit("BOT_TOKEN не задан в backend/.env")

    dry_run = os.getenv("BROADCAST_DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
    only_ids = _parse_only_ids()

    try:
        audience = await _collect_audience()
    except RemnawaveError as exc:
        raise SystemExit(f"Не удалось получить пользователей из панели: {exc}")

    if only_ids:
        audience = [i for i in audience if i in only_ids]
        logger.info("BROADCAST_ONLY_IDS активен → получателей: %s", len(audience))

    logger.info("Кампания '%s': в аудитории %s уникальных Telegram ID", CAMPAIGN, len(audience))

    if dry_run:
        logger.info("DRY RUN — ничего не отправляю. Первые 10 ID: %s", audience[:10])
        return

    conn = await _connect()
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    sent = blocked = failed = skipped = 0
    try:
        for tg_id in audience:
            if await _already_sent(conn, tg_id):
                skipped += 1
                continue
            status = await _send_one(bot, tg_id)
            await _mark(conn, tg_id, status)
            if status == "sent":
                sent += 1
            elif status == "blocked":
                blocked += 1
            else:
                failed += 1
            processed = sent + blocked + failed
            if processed % PROGRESS_EVERY == 0:
                logger.info(
                    "прогресс: sent=%s blocked=%s failed=%s skipped=%s",
                    sent, blocked, failed, skipped,
                )
            await asyncio.sleep(SEND_INTERVAL_SEC)
    finally:
        await bot.session.close()
        await conn.close()

    logger.info(
        "ГОТОВО. sent=%s blocked=%s failed=%s skipped(уже обработаны)=%s — всего в аудитории %s",
        sent, blocked, failed, skipped, len(audience),
    )


if __name__ == "__main__":
    asyncio.run(run())

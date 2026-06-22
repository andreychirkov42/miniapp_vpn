"""Дедуп напоминаний об окончании подписки (SQLite, владелец — процесс бота).

Хранится в отдельном файле рядом с БД обращений (support.db), чтобы не нарушать
инвариант «в support.db пишет только API-процесс» (см. app/db.py). Ключ записи —
(uuid подписки, дата окончания): после продления expireAt меняется, и тот же
пользователь снова станет кандидатом на напоминание в следующем цикле подписки.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS expiry_notifications (
    subscription_uuid  TEXT NOT NULL,
    expire_at          TEXT NOT NULL,
    telegram_id        INTEGER NOT NULL,
    notified_at        TEXT NOT NULL,
    PRIMARY KEY (subscription_uuid, expire_at)
);
"""


def notify_db_path(support_db_path: str) -> str:
    """Путь к notify.db рядом с support.db (тот же каталог/volume)."""
    return str(Path(support_db_path).with_name("notify.db"))


async def connect(path: str) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(path)
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.executescript(_SCHEMA)
    await conn.commit()
    return conn


async def was_notified(conn: aiosqlite.Connection, uuid: str, expire_at: str) -> bool:
    cur = await conn.execute(
        "SELECT 1 FROM expiry_notifications WHERE subscription_uuid = ? AND expire_at = ?",
        (uuid, expire_at),
    )
    return await cur.fetchone() is not None


async def mark_notified(
    conn: aiosqlite.Connection, uuid: str, expire_at: str, telegram_id: int
) -> None:
    await conn.execute(
        "INSERT OR IGNORE INTO expiry_notifications "
        "(subscription_uuid, expire_at, telegram_id, notified_at) VALUES (?, ?, ?, ?)",
        (uuid, expire_at, telegram_id, datetime.now(timezone.utc).isoformat()),
    )
    await conn.commit()

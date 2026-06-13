"""Репозиторий обращений: вся работа с таблицами tickets/ticket_messages.

Функции принимают соединение явно (см. db.get_db) и возвращают простые dict —
маппинг в Pydantic-схемы делает роутер. Время хранится в ISO-8601 UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite

# Статусы тикета.
STATUS_OPEN = "open"  # юзер написал, админ ещё не ответил
STATUS_ANSWERED = "answered"  # админ ответил, тикет в работе
STATUS_CLOSED = "closed"  # обращение закрыто
ACTIVE_STATUSES = (STATUS_OPEN, STATUS_ANSWERED)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_ticket(
    conn: aiosqlite.Connection,
    *,
    user_telegram_id: int,
    username: str | None,
    first_name: str | None,
    message: str,
) -> int:
    """Создаёт тикет с первым сообщением пользователя. Возвращает id тикета."""
    ts = _now()
    cur = await conn.execute(
        "INSERT INTO tickets (user_telegram_id, username, first_name, status, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_telegram_id, username, first_name, STATUS_OPEN, ts, ts),
    )
    ticket_id = cur.lastrowid
    await conn.execute(
        "INSERT INTO ticket_messages (ticket_id, author, admin_telegram_id, text, "
        "created_at) VALUES (?, 'user', NULL, ?, ?)",
        (ticket_id, message.strip(), ts),
    )
    await conn.commit()
    return int(ticket_id)


async def add_user_message(conn: aiosqlite.Connection, ticket_id: int, text: str) -> None:
    """Добавляет сообщение пользователя и возвращает тикет в статус open."""
    ts = _now()
    await conn.execute(
        "INSERT INTO ticket_messages (ticket_id, author, admin_telegram_id, text, "
        "created_at) VALUES (?, 'user', NULL, ?, ?)",
        (ticket_id, text.strip(), ts),
    )
    await conn.execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (STATUS_OPEN, ts, ticket_id),
    )
    await conn.commit()


async def add_admin_message(
    conn: aiosqlite.Connection, ticket_id: int, admin_telegram_id: int, text: str
) -> None:
    """Добавляет ответ админа и переводит тикет в статус answered."""
    ts = _now()
    await conn.execute(
        "INSERT INTO ticket_messages (ticket_id, author, admin_telegram_id, text, "
        "created_at) VALUES (?, 'admin', ?, ?, ?)",
        (ticket_id, admin_telegram_id, text.strip(), ts),
    )
    await conn.execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (STATUS_ANSWERED, ts, ticket_id),
    )
    await conn.commit()


async def set_status(conn: aiosqlite.Connection, ticket_id: int, status: str) -> None:
    await conn.execute(
        "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
        (status, _now(), ticket_id),
    )
    await conn.commit()


async def get_ticket(conn: aiosqlite.Connection, ticket_id: int) -> dict | None:
    cur = await conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = await cur.fetchone()
    return dict(row) if row else None


async def _messages(conn: aiosqlite.Connection, ticket_id: int) -> list[dict]:
    cur = await conn.execute(
        "SELECT id, author, admin_telegram_id, text, created_at FROM ticket_messages "
        "WHERE ticket_id = ? ORDER BY id ASC",
        (ticket_id,),
    )
    return [dict(r) for r in await cur.fetchall()]


async def get_with_messages(conn: aiosqlite.Connection, ticket_id: int) -> dict | None:
    """Тикет вместе со всеми сообщениями переписки, либо None."""
    ticket = await get_ticket(conn, ticket_id)
    if ticket is None:
        return None
    ticket["messages"] = await _messages(conn, ticket_id)
    return ticket


async def list_by_user(conn: aiosqlite.Connection, user_telegram_id: int) -> list[dict]:
    """Тикеты пользователя (свежие сверху) с превью последнего сообщения."""
    return await _list("WHERE t.user_telegram_id = ?", (user_telegram_id,), conn)


async def list_all(conn: aiosqlite.Connection, *, only_active: bool) -> list[dict]:
    """Все тикеты для админа. only_active=True исключает закрытые."""
    if only_active:
        placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
        return await _list(f"WHERE t.status IN ({placeholders})", ACTIVE_STATUSES, conn)
    return await _list("", (), conn)


async def _list(where: str, params: tuple, conn: aiosqlite.Connection) -> list[dict]:
    cur = await conn.execute(
        "SELECT t.*, "
        "  (SELECT text FROM ticket_messages m WHERE m.ticket_id = t.id "
        "   ORDER BY m.id DESC LIMIT 1) AS last_message, "
        "  (SELECT author FROM ticket_messages m WHERE m.ticket_id = t.id "
        "   ORDER BY m.id DESC LIMIT 1) AS last_author "
        f"FROM tickets t {where} ORDER BY t.updated_at DESC",
        params,
    )
    return [dict(r) for r in await cur.fetchall()]

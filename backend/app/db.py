"""SQLite-хранилище обращений (aiosqlite).

Одно соединение на время жизни приложения хранится в `app.state.db`. Пишет в БД
только API-процесс (бот к ней не обращается), поэтому конкурентной записи из
разных процессов нет. Включён WAL для устойчивости при параллельных чтениях.
"""

from __future__ import annotations

import aiosqlite
from fastapi import Request

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_telegram_id   INTEGER NOT NULL,
    username           TEXT,
    first_name         TEXT,
    status             TEXT NOT NULL DEFAULT 'open',  -- open | answered | closed
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_messages (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id          INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author             TEXT NOT NULL,                 -- user | admin
    admin_telegram_id  INTEGER,
    text               TEXT NOT NULL,                 -- может быть пустым, если есть вложение
    attachment_path    TEXT,                          -- имя файла-картинки в папке attachments
    attachment_mime    TEXT,                          -- image/jpeg | image/png | image/webp
    created_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_telegram_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_messages_ticket ON ticket_messages(ticket_id);
"""


async def connect(path: str) -> aiosqlite.Connection:
    """Открывает соединение, включает WAL/FK и создаёт схему (идемпотентно)."""
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.execute("PRAGMA foreign_keys=ON")
    await conn.executescript(_SCHEMA)
    await _migrate(conn)
    await conn.commit()
    return conn


async def _migrate(conn: aiosqlite.Connection) -> None:
    """Доводит схему уже существующих БД до текущей (ADD COLUMN идемпотентно).

    CREATE TABLE IF NOT EXISTS не добавляет колонки в созданную ранее таблицу,
    поэтому новые поля прикручиваем явно — на боевой support.db в volume.
    """
    cur = await conn.execute("PRAGMA table_info(ticket_messages)")
    columns = {row["name"] for row in await cur.fetchall()}
    if "attachment_path" not in columns:
        await conn.execute("ALTER TABLE ticket_messages ADD COLUMN attachment_path TEXT")
    if "attachment_mime" not in columns:
        await conn.execute("ALTER TABLE ticket_messages ADD COLUMN attachment_mime TEXT")


async def get_db(request: Request) -> aiosqlite.Connection:
    """FastAPI dependency: соединение из app.state (создаётся в lifespan)."""
    return request.app.state.db

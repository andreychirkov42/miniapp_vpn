"""Общие фикстуры тестов: in-memory SQLite, ASGI-клиент с подменёнными зависимостями."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app import db as db_module
from app import telegram
from app.db import get_db
from app.security import TelegramUser, require_admin, require_telegram_user

USER_ID = 555001
ADMIN_ID = 683135069


@pytest.fixture
async def conn():
    """Изолированное in-memory соединение (одно на тест, схема создаётся в connect)."""
    connection = await db_module.connect(":memory:")
    yield connection
    await connection.close()


@pytest.fixture(autouse=True)
def _no_telegram(monkeypatch):
    """Глушим реальную отправку в Telegram во всех тестах."""

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(telegram, "send_message", _noop)


@pytest.fixture
async def client(conn):
    from app.main import app

    app.dependency_overrides[require_telegram_user] = lambda: TelegramUser(USER_ID, "user", "User")
    app.dependency_overrides[require_admin] = lambda: TelegramUser(ADMIN_ID, "admin", "Admin")
    app.dependency_overrides[get_db] = lambda: conn

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

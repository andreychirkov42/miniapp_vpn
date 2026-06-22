"""Поиск подписки по username в mock-клиенте Remnawave (вход «@username» бота)."""

from __future__ import annotations

from app.config import Settings
from app.remnawave import MockRemnawave


async def test_get_user_by_username_found():
    client = MockRemnawave(Settings())
    created = await client.create_user(
        {"telegramId": 700, "username": "ivan_petrov", "expireAt": "2030-01-01T00:00:00Z"}
    )
    found = await client.get_user_by_username("ivan_petrov")
    assert found is not None
    assert found["uuid"] == created["uuid"]
    assert found["telegramId"] == 700


async def test_get_user_by_username_missing():
    client = MockRemnawave(Settings())
    assert await client.get_user_by_username("no_such_handle") is None

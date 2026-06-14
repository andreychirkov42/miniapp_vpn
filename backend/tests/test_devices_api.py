"""Тесты раздела «Устройства» (HWID): список и удаление через mock-панель."""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.remnawave import MockRemnawave
from app.routers.api import _client

from conftest import USER_ID


@pytest.fixture
def mock_client():
    return MockRemnawave(get_settings())


@pytest.fixture
async def devices_client(client, mock_client):
    """ASGI-клиент с подменённой панелью на изолированный mock (общий с тестом)."""
    from app.main import app

    app.dependency_overrides[_client] = lambda: mock_client
    return client  # очистку overrides делает фикстура client на teardown


async def _primary_uuid(mock_client: MockRemnawave) -> str:
    users = await mock_client.get_users_by_telegram_id(USER_ID)
    return users[0]["uuid"]


async def test_list_devices_returns_seeded(devices_client, mock_client):
    uuid = await _primary_uuid(mock_client)

    resp = await devices_client.get(f"/api/subscriptions/{uuid}/devices")

    assert resp.status_code == 200
    devices = resp.json()["devices"]
    assert len(devices) == 3
    assert {d["platform"] for d in devices} == {"iOS", "macOS", "Android"}
    assert all(d["hwid"] for d in devices)


async def test_delete_device_removes_one(devices_client, mock_client):
    uuid = await _primary_uuid(mock_client)
    devices = (await devices_client.get(f"/api/subscriptions/{uuid}/devices")).json()["devices"]
    target = devices[0]["hwid"]

    resp = await devices_client.post(
        f"/api/subscriptions/{uuid}/devices/delete", json={"hwid": target}
    )

    assert resp.status_code == 200
    remaining = resp.json()["devices"]
    assert len(remaining) == 2
    assert all(d["hwid"] != target for d in remaining)


async def test_delete_requires_hwid(devices_client, mock_client):
    uuid = await _primary_uuid(mock_client)

    resp = await devices_client.post(f"/api/subscriptions/{uuid}/devices/delete", json={"hwid": ""})

    assert resp.status_code == 422  # пустой hwid отвергается схемой


async def test_devices_foreign_subscription_404(devices_client):
    # uuid, не принадлежащий пользователю → 404 (нельзя смотреть/удалять чужое)
    resp = await devices_client.get("/api/subscriptions/not-my-uuid/devices")

    assert resp.status_code == 404

"""Thin async client for the Remnawave panel API + an in-memory mock.

Remnawave wraps every payload in {"response": ...}. All methods here return the
already-unwrapped `response` value. Switch behaviour with REMNAWAVE_MOCK.
"""

from __future__ import annotations

import uuid as uuidlib
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import httpx

from .config import Settings, get_settings


class RemnawaveError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------------------- #
# Real client                                                                 #
# --------------------------------------------------------------------------- #
class RealRemnawave:
    def __init__(self, settings: Settings):
        self._base = settings.api_base
        self._headers = {
            "Authorization": f"Bearer {settings.remnawave_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, json: dict | None = None):
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.request(
                method, f"{self._base}{path}", headers=self._headers, json=json
            )
        if resp.status_code >= 400:
            raise RemnawaveError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        if not resp.content:
            return None
        data = resp.json()
        return data.get("response", data) if isinstance(data, dict) else data

    async def get_users_by_telegram_id(self, telegram_id: int) -> list[dict]:
        res = await self._request("GET", f"/users/by-telegram-id/{telegram_id}")
        if res is None:
            return []
        return res if isinstance(res, list) else [res]

    async def get_user(self, uuid: str) -> dict:
        return await self._request("GET", f"/users/{uuid}")

    async def create_user(self, payload: dict) -> dict:
        return await self._request("POST", "/users", json=payload)

    async def update_user(self, payload: dict) -> dict:
        # Remnawave PATCH /users carries the uuid inside the body
        return await self._request("PATCH", "/users", json=payload)


# --------------------------------------------------------------------------- #
# Mock client (in-memory, per Telegram id)                                    #
# --------------------------------------------------------------------------- #
class MockRemnawave:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._db: dict[int, list[dict]] = {}

    def _seed(self, telegram_id: int) -> list[dict]:
        domain = self._settings.subscription_domain or "https://sub.akenai.example"
        gb = 1024**3
        users = [
            self._make(
                telegram_id,
                label="Основная",
                name="Pro",
                traffic_limit=0,
                used=0,
                expire=_now() + timedelta(days=3),
                device_limit=0,
                domain=domain,
            ),
            self._make(
                telegram_id,
                label="Подписка #100564",
                name="Whitelist",
                traffic_limit=5 * gb,
                used=0,
                expire=_now() + timedelta(days=3),
                device_limit=0,
                domain=domain,
            ),
        ]
        self._db[telegram_id] = users
        return users

    def _make(self, telegram_id, *, label, name, traffic_limit, used, expire, device_limit, domain):
        full = str(uuidlib.uuid4())
        short = full.split("-")[0]
        sub_url = self._settings.mock_subscription_url or f"{domain}/{short}"
        return {
            "uuid": full,
            "shortUuid": short,
            "username": f"tg_{telegram_id}_{short}",
            "telegramId": telegram_id,
            "status": "ACTIVE",
            "trafficLimitBytes": traffic_limit,
            "usedTrafficBytes": used,
            "expireAt": _iso(expire),
            "hwidDeviceLimit": device_limit,
            "subscriptionUrl": f"{domain}/{short}",
            "_label": label,
            "_name": name,
        }

    async def get_users_by_telegram_id(self, telegram_id: int) -> list[dict]:
        return self._db.get(telegram_id) or self._seed(telegram_id)

    async def get_user(self, uuid: str) -> dict:
        for users in self._db.values():
            for u in users:
                if u["uuid"] == uuid:
                    return u
        raise RemnawaveError(f"user {uuid} not found (mock)")

    async def create_user(self, payload: dict) -> dict:
        telegram_id = int(payload["telegramId"])
        domain = self._settings.subscription_domain or "https://sub.akenai.example"
        expire = datetime.fromisoformat(payload["expireAt"].replace("Z", "+00:00"))
        user = self._make(
            telegram_id,
            label=payload.get("_label", "Новая подписка"),
            name=payload.get("_name", "Trial"),
            traffic_limit=payload.get("trafficLimitBytes", 0),
            used=0,
            expire=expire,
            device_limit=payload.get("hwidDeviceLimit", 0),
            domain=domain,
        )
        self._db.setdefault(telegram_id, [])
        self._db[telegram_id].append(user)
        return user

    async def update_user(self, payload: dict) -> dict:
        target = await self.get_user(payload["uuid"])
        for key in ("expireAt", "trafficLimitBytes", "hwidDeviceLimit", "status"):
            if key in payload:
                target[key] = payload[key]
        return target


def make_client(settings: Settings):
    return MockRemnawave(settings) if settings.remnawave_mock else RealRemnawave(settings)


@lru_cache
def get_client():
    """Cached singleton — keeps the in-memory mock state across requests."""
    return make_client(get_settings())

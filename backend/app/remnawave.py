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


def _extract_users(payload) -> list[dict]:
    """Достаёт список пользователей из ответа панели, устойчиво к форме.

    Remnawave может вернуть подписки как голый список, как один объект или
    завёрнутыми в {"users": [...], "total": N}. Повторяет логику бота
    vpn_payment_bot, проверенную на живой панели.
    """
    if payload is None:
        return []
    if isinstance(payload, list):
        return [u for u in payload if isinstance(u, dict)]
    if isinstance(payload, dict):
        users = payload.get("users")
        if isinstance(users, list):
            return [u for u in users if isinstance(u, dict)]
        return [payload]
    return []


def _extract_devices(payload) -> list[dict]:
    """Достаёт список устройств (HWID) из ответа панели, устойчиво к форме.

    Панель может вернуть {"devices": [...], "total": N}, голый список или один
    объект. Берём только записи с непустым hwid.
    """
    if isinstance(payload, dict):
        devices = payload.get("devices")
        if isinstance(devices, list):
            return [d for d in devices if isinstance(d, dict) and d.get("hwid")]
        return [payload] if payload.get("hwid") else []
    if isinstance(payload, list):
        return [d for d in payload if isinstance(d, dict) and d.get("hwid")]
    return []


def _clean_payload(payload: dict) -> dict:
    """Убирает служебные mock-поля (с префиксом «_») перед отправкой в панель.

    Remnawave валидирует тело запроса и может отклонить неизвестные поля.
    """
    return {k: v for k, v in payload.items() if not k.startswith("_")}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# --------------------------------------------------------------------------- #
# Real client                                                                 #
# --------------------------------------------------------------------------- #
class RealRemnawave:
    """Talks to a live Remnawave panel.

    Auth: prefers a static API token (REMNAWAVE_TOKEN). If absent, logs in with
    admin username/password (REMNAWAVE_USERNAME/PASSWORD) via POST /auth/login,
    caches the returned JWT, and re-authenticates once on a 401.
    """

    def __init__(self, settings: Settings):
        self._base = settings.api_base
        self._static_token = settings.remnawave_token or None
        self._username = settings.remnawave_username or None
        self._password = settings.remnawave_password or None
        self._token: str | None = self._static_token

    async def _login(self, client: httpx.AsyncClient) -> str:
        if not (self._username and self._password):
            raise RemnawaveError(
                "no REMNAWAVE_TOKEN and no REMNAWAVE_USERNAME/PASSWORD configured"
            )
        resp = await client.post(
            f"{self._base}/auth/login",
            json={"username": self._username, "password": self._password},
        )
        if resp.status_code >= 400:
            raise RemnawaveError(f"auth/login -> {resp.status_code}: {resp.text}")
        data = resp.json()
        body = data.get("response", data) if isinstance(data, dict) else {}
        token = body.get("accessToken") or body.get("token")
        if not token:
            raise RemnawaveError("login succeeded but no accessToken in response")
        return token

    async def _ensure_token(self, client: httpx.AsyncClient) -> str:
        if self._token is None:
            self._token = await self._login(client)
        return self._token

    async def _request(self, method: str, path: str, json: dict | None = None):
        async with httpx.AsyncClient(timeout=20) as client:
            token = await self._ensure_token(client)
            resp = await client.request(
                method,
                f"{self._base}{path}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json,
            )
            # JWT expired / revoked — re-login once (only when using login auth)
            if resp.status_code == 401 and self._static_token is None:
                self._token = await self._login(client)
                resp = await client.request(
                    method,
                    f"{self._base}{path}",
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Content-Type": "application/json",
                    },
                    json=json,
                )
        # Нет привязанных подписок — панель отвечает 404. Это не ошибка, а
        # «пользователь ещё не оформлен»: возвращаем пусто, чтобы сработал
        # сценарий нового юзера (триал/оплата), а не 502.
        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            raise RemnawaveError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        if not resp.content:
            return None
        data = resp.json()
        return data.get("response", data) if isinstance(data, dict) else data

    async def get_users_by_telegram_id(self, telegram_id: int) -> list[dict]:
        res = await self._request("GET", f"/users/by-telegram-id/{telegram_id}")
        return _extract_users(res)

    async def get_user_by_username(self, username: str) -> dict | None:
        """Поиск по username панели (= Telegram-хэндлу). Один юзер или None."""
        res = await self._request("GET", f"/users/by-username/{username}")
        users = _extract_users(res)
        return users[0] if users else None

    async def get_all_users(self, page_size: int = 500) -> list[dict]:
        """Все подписки панели (постранично). Для напоминаний об окончании."""
        users: list[dict] = []
        start = 0
        while True:
            res = await self._request("GET", f"/users?size={page_size}&start={start}")
            batch = _extract_users(res)
            if not batch:
                break
            users.extend(batch)
            total = res.get("total") if isinstance(res, dict) else None
            start += len(batch)
            if total is not None and start >= int(total):
                break
            if len(batch) < page_size:
                break
        return users

    async def get_user(self, uuid: str) -> dict:
        return await self._request("GET", f"/users/{uuid}")

    async def create_user(self, payload: dict) -> dict:
        return await self._request("POST", "/users", json=_clean_payload(payload))

    async def update_user(self, payload: dict) -> dict:
        # Remnawave PATCH /users carries the uuid inside the body
        return await self._request("PATCH", "/users", json=_clean_payload(payload))

    async def get_hwid_count(self, uuid: str) -> int:
        res = await self._request("GET", f"/hwid/devices/{uuid}")
        if isinstance(res, dict):
            return int(res.get("total") or 0)
        return 0

    async def get_devices(self, uuid: str) -> list[dict]:
        res = await self._request("GET", f"/hwid/devices/{uuid}")
        return _extract_devices(res)

    async def delete_device(self, uuid: str, hwid: str) -> None:
        await self._request(
            "POST", "/hwid/devices/delete", json={"userUuid": uuid, "hwid": hwid}
        )


# --------------------------------------------------------------------------- #
# Mock client (in-memory, per Telegram id)                                    #
# --------------------------------------------------------------------------- #
class MockRemnawave:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._db: dict[int, list[dict]] = {}
        self._devices: dict[str, list[dict]] = {}  # uuid -> список устройств (HWID)

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
                expire=_now() + timedelta(days=self._settings.trial_days),
                device_limit=0,
                domain=domain,
            ),
            self._make(
                telegram_id,
                label="Подписка #100564",
                name="Whitelist",
                traffic_limit=5 * gb,
                used=0,
                expire=_now() + timedelta(days=self._settings.trial_days),
                device_limit=0,
                domain=domain,
            ),
        ]
        self._db[telegram_id] = users
        return users

    def _make(self, telegram_id, *, label, name, traffic_limit, used, expire, device_limit,
              domain, username=None):
        full = str(uuidlib.uuid4())
        short = full.split("-")[0]
        sub_url = self._settings.mock_subscription_url or f"{domain}/{short}"
        return {
            "uuid": full,
            "shortUuid": short,
            "username": username or f"tg_{telegram_id}_{short}",
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

    async def get_user_by_username(self, username: str) -> dict | None:
        for users in self._db.values():
            for u in users:
                if u.get("username") == username:
                    return u
        return None

    async def get_all_users(self, page_size: int = 500) -> list[dict]:
        return [u for users in self._db.values() for u in users]

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
            username=payload.get("username"),
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

    def _seed_devices(self, uuid: str) -> list[dict]:
        """Демо-устройства, чтобы раздел «Устройства» был наполнен на моке."""
        base = _now()
        short = uuid.split("-")[0]
        devices = [
            {"hwid": f"{short}-ios", "platform": "iOS", "deviceModel": "iPhone 14 Pro",
             "createdAt": _iso(base - timedelta(days=6))},
            {"hwid": f"{short}-macos", "platform": "macOS", "deviceModel": "MacBook Air",
             "createdAt": _iso(base - timedelta(days=2))},
            {"hwid": f"{short}-android", "platform": "Android", "deviceModel": "Pixel 7",
             "createdAt": _iso(base - timedelta(hours=5))},
        ]
        self._devices[uuid] = devices
        return devices

    async def get_devices(self, uuid: str) -> list[dict]:
        return self._devices[uuid] if uuid in self._devices else self._seed_devices(uuid)

    async def delete_device(self, uuid: str, hwid: str) -> None:
        current = self._devices[uuid] if uuid in self._devices else self._seed_devices(uuid)
        self._devices[uuid] = [d for d in current if d.get("hwid") != hwid]

    async def get_hwid_count(self, uuid: str) -> int:
        return len(self._devices[uuid] if uuid in self._devices else self._seed_devices(uuid))


def make_client(settings: Settings):
    return MockRemnawave(settings) if settings.remnawave_mock else RealRemnawave(settings)


@lru_cache
def get_client():
    """Cached singleton — keeps the in-memory mock state across requests."""
    return make_client(get_settings())

"""Maps raw Remnawave user objects to the frontend Subscription schema and
implements the trial / renew business logic."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .config import Settings
from .schemas import Subscription

GB = 1024**3


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fmt_gb(n: int) -> str:
    val = n / GB
    return f"{val:.0f}" if val == int(val) else f"{val:.1f}"


def map_subscription(raw: dict, index: int) -> Subscription:
    used = int(raw.get("usedTrafficBytes") or 0)
    limit = int(raw.get("trafficLimitBytes") or 0)
    device_limit = int(raw.get("hwidDeviceLimit") or 0)
    devices_used = int(raw.get("activeDevicesCount") or raw.get("_devices_used") or 0)

    expire_dt = _parse_dt(raw.get("expireAt"))
    now = datetime.now(timezone.utc)
    status = str(raw.get("status") or "ACTIVE").upper()
    expired = status == "EXPIRED" or (expire_dt is not None and expire_dt < now)

    name = raw.get("_name") or raw.get("tag") or raw.get("description") or "VPN"
    label = raw.get("_label") or ("Основная" if index == 0 else f"Подписка #{raw.get('shortUuid', '')}")
    pro = bool(raw.get("_name") == "Pro" or name == "Pro" or (limit == 0 and index == 0))

    traffic_text = None if limit == 0 else f"{_fmt_gb(used)}/{_fmt_gb(limit)} GB"
    devices_text = (
        f"{devices_used}/∞ устройств" if device_limit == 0 else f"{devices_used}/{device_limit} устройств"
    )
    expire_text = expire_dt.strftime("%d.%m.%Y") if expire_dt else "—"

    return Subscription(
        id=str(raw.get("shortUuid") or raw.get("uuid")),
        uuid=str(raw.get("uuid")),
        label=label,
        name=name,
        status=status,
        pro=pro,
        used_traffic_bytes=used,
        traffic_limit_bytes=limit,
        traffic_text=traffic_text,
        expire_at=raw.get("expireAt") or "",
        expire_text=expire_text,
        expired=expired,
        devices_used=devices_used,
        device_limit=device_limit,
        devices_text=devices_text,
        subscription_url=str(raw.get("subscriptionUrl") or ""),
    )


def map_all(raws: list[dict]) -> list[Subscription]:
    return [map_subscription(r, i) for i, r in enumerate(raws)]


def build_trial_payload(settings: Settings, telegram_id: int) -> dict:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.trial_days)
    payload: dict = {
        "username": f"tg{telegram_id}_{int(datetime.now().timestamp())}",
        "telegramId": telegram_id,
        "status": "ACTIVE",
        "trafficLimitBytes": settings.trial_traffic_gb * GB,
        "trafficLimitStrategy": "NO_RESET",
        "expireAt": expire.isoformat().replace("+00:00", "Z"),
        "hwidDeviceLimit": 0,
        # carried through by the mock so the demo matches the screenshots
        "_label": "Подписка #100564",
        "_name": "Whitelist",
    }
    if settings.remnawave_squad_uuid:
        payload["activeInternalSquads"] = [settings.remnawave_squad_uuid]
    return payload


def build_renew_payload(raw: dict, settings: Settings) -> dict:
    current = _parse_dt(raw.get("expireAt"))
    now = datetime.now(timezone.utc)
    base = current if current and current > now else now
    new_expire = base + timedelta(days=settings.renew_days)
    return {
        "uuid": raw["uuid"],
        "expireAt": new_expire.isoformat().replace("+00:00", "Z"),
        "status": "ACTIVE",
    }


def build_deeplinks(subscription_url: str) -> dict[str, str]:
    if not subscription_url:
        return {}
    return {
        "v2raytun": f"v2raytun://import/{subscription_url}",
        "happ": f"happ://add/{subscription_url}",
        "streisand": f"streisand://import/{subscription_url}",
        "hiddify": f"hiddify://import/{subscription_url}",
        "clash": f"clash://install-config?url={subscription_url}",
    }

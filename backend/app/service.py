"""Maps raw Remnawave user objects to the frontend Subscription schema and
implements the trial / renew business logic."""

from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta, timezone

from .config import Settings
from .schemas import Device, Subscription

GB = 1024**3

# Панель отдаёт время с наносекундами (.123456789Z), а datetime.fromisoformat
# понимает максимум микросекунды (6 знаков) — обрезаем хвост.
_SUBSECOND_RE = re.compile(r"(\.\d{6})\d+")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    text = _SUBSECOND_RE.sub(r"\1", text)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


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

    name = raw.get("_name") or raw.get("tag") or raw.get("description") or "Доступ"
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


def map_device(raw: dict) -> Device:
    return Device(
        hwid=str(raw.get("hwid") or ""),
        platform=str(raw.get("platform") or ""),
        device_model=str(raw.get("deviceModel") or ""),
        created_at=raw.get("createdAt") or None,
    )


def map_devices(raws: list[dict]) -> list[Device]:
    return [map_device(r) for r in raws if r.get("hwid")]


# Remnawave username: 6-34 символа, латиница/цифры/_/- . Telegram-хэндл (после @)
# состоит из [a-zA-Z0-9_], 5-32 симв. — почти всегда подходит; короткие (<6) и
# отсутствующие отправляем под запасным tg{id}, иначе панель отвергнет создание.
_PANEL_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{6,34}$")


def panel_username(telegram_id: int, username: str | None) -> str:
    """Имя для панели: Telegram-хэндл, если валиден; иначе запасной tg{id}."""
    if username and _PANEL_USERNAME_RE.match(username):
        return username
    return f"tg{telegram_id}"


def build_trial_payload(settings: Settings, telegram_id: int, username: str | None = None) -> dict:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.trial_days)
    payload: dict = {
        "username": panel_username(telegram_id, username),
        "telegramId": telegram_id,
        "status": "ACTIVE",
        "trafficLimitBytes": settings.trial_traffic_gb * GB,
        "trafficLimitStrategy": "NO_RESET",
        "expireAt": expire.isoformat().replace("+00:00", "Z"),
        "hwidDeviceLimit": settings.trial_device_limit,
        # carried through by the mock so the demo matches the screenshots
        "_label": "Подписка #100564",
        "_name": "Whitelist",
    }
    if settings.remnawave_squad_uuid:
        payload["activeInternalSquads"] = [settings.remnawave_squad_uuid]
    return payload


def days_until_expiry(raw: dict, now: datetime | None = None) -> int | None:
    """Сколько полных суток осталось до окончания подписки (округление вверх).

    None — если даты нет. Отрицательное — подписка уже истекла.
    """
    expire = _parse_dt(raw.get("expireAt"))
    if expire is None:
        return None
    moment = now or datetime.now(timezone.utc)
    seconds = (expire - moment).total_seconds()
    return -(-seconds // 86400) if seconds >= 0 else int(seconds // 86400)


def is_expiring_soon(raw: dict, within_days: int, now: datetime | None = None) -> bool:
    """True, если подписка активна и истекает в ближайшие `within_days` суток.

    Уже истёкшие (status EXPIRED или дата в прошлом) исключаются — напоминать о
    продлении поздно, для них другой сценарий.
    """
    if str(raw.get("status") or "").upper() == "EXPIRED":
        return False
    expire = _parse_dt(raw.get("expireAt"))
    if expire is None:
        return False
    moment = now or datetime.now(timezone.utc)
    remaining = expire - moment
    return timedelta(0) < remaining <= timedelta(days=within_days)


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


def _add_months(moment: datetime, months: int) -> datetime:
    """Прибавляет calendar-месяцы (переход года, обрезка коротких месяцев)."""
    month_index = moment.month - 1 + months
    year = moment.year + month_index // 12
    month = month_index % 12 + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])
    return moment.replace(year=year, month=month, day=day)


def build_renew_months_payload(raw: dict, months: int) -> dict:
    """Продление на N календарных месяцев (для ручного продления оператором).

    База = max(текущее окончание, сейчас) — остаток активной подписки не теряется.
    """
    current = _parse_dt(raw.get("expireAt"))
    now = datetime.now(timezone.utc)
    base = current if current and current > now else now
    new_expire = _add_months(base, months)
    return {
        "uuid": raw["uuid"],
        "expireAt": new_expire.isoformat().replace("+00:00", "Z"),
        "status": "ACTIVE",
    }

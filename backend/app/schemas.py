"""Response models the frontend consumes (decoupled from Remnawave's raw shape)."""

from __future__ import annotations

from pydantic import BaseModel


class Subscription(BaseModel):
    id: str  # shortUuid — stable public id used by the frontend
    uuid: str  # full uuid — used for actions (renew/config)
    label: str  # "Основная" / "Подписка #100564"
    name: str  # tariff: "Pro" / "Whitelist"
    status: str  # ACTIVE | DISABLED | LIMITED | EXPIRED
    pro: bool

    used_traffic_bytes: int
    traffic_limit_bytes: int  # 0 = unlimited
    traffic_text: str | None  # "0/5 GB" or None when unlimited

    expire_at: str  # ISO
    expire_text: str  # "14.06.2026"
    expired: bool

    devices_used: int
    device_limit: int  # 0 = unlimited
    devices_text: str  # "0/∞ устройств"

    subscription_url: str


class MeResponse(BaseModel):
    telegram_id: int
    subscriptions: list[Subscription]


class ConfigResponse(BaseModel):
    subscription_url: str
    deeplinks: dict[str, str]

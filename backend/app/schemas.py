"""Response models the frontend consumes (decoupled from Remnawave's raw shape)."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
    is_admin: bool = False
    trial_days: int  # срок пробного периода (для текстов на фронте)


class ConfigResponse(BaseModel):
    subscription_url: str


class Device(BaseModel):
    hwid: str
    platform: str = ""
    device_model: str = ""
    created_at: str | None = None  # ISO


class DeviceListResponse(BaseModel):
    devices: list[Device]


class DeviceDeleteRequest(BaseModel):
    hwid: str = Field(min_length=1)


class SupportResponse(BaseModel):
    ok: bool
    ticket_id: int


class TicketMessage(BaseModel):
    id: int
    author: str  # user | admin
    text: str
    created_at: str
    # URL защищённого эндпоинта с картинкой-вложением, либо None
    attachment_url: str | None = None


class Ticket(BaseModel):
    id: int
    status: str  # open | answered | closed
    created_at: str
    updated_at: str
    last_message: str | None = None
    last_author: str | None = None
    # заполняется только в админских ответах — кто автор обращения
    user_telegram_id: int | None = None
    username: str | None = None
    first_name: str | None = None


class TicketDetail(Ticket):
    messages: list[TicketMessage] = Field(default_factory=list)


class TicketListResponse(BaseModel):
    tickets: list[Ticket]

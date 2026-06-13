import logging

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..db import get_db
from ..remnawave import RemnawaveError, get_client
from ..schemas import (
    ConfigResponse,
    MeResponse,
    Subscription,
    SupportRequest,
    SupportResponse,
    Ticket,
    TicketDetail,
    TicketListResponse,
)
from ..security import TelegramUser, is_admin, require_telegram_user
from .. import service, support_store, telegram

logger = logging.getLogger("akenai.api")

router = APIRouter(prefix="/api", tags=["subscriptions"])


def _client():
    return get_client()


async def _find_user(client, telegram_id: int, uuid: str) -> dict:
    users = await client.get_users_by_telegram_id(telegram_id)
    for u in users:
        if u.get("uuid") == uuid or u.get("shortUuid") == uuid:
            return u
    raise HTTPException(status_code=404, detail="subscription not found")


@router.get("/me", response_model=MeResponse)
async def get_me(
    user: TelegramUser = Depends(require_telegram_user),
    client=Depends(_client),
):
    try:
        raws = await client.get_users_by_telegram_id(user.telegram_id)
        # подмешиваем число подключённых устройств (HWID) в каждую подписку
        for r in raws:
            try:
                r["_devices_used"] = await client.get_hwid_count(r.get("uuid"))
            except RemnawaveError:
                r["_devices_used"] = 0
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc
    return MeResponse(
        telegram_id=user.telegram_id,
        subscriptions=service.map_all(raws),
        is_admin=is_admin(user.telegram_id),
    )


@router.post("/trial", response_model=Subscription)
async def activate_trial(
    user: TelegramUser = Depends(require_telegram_user),
    client=Depends(_client),
    settings: Settings = Depends(get_settings),
):
    try:
        existing = await client.get_users_by_telegram_id(user.telegram_id)
        if existing:
            # already has a subscription — return the first instead of duplicating
            return service.map_subscription(existing[0], 0)
        payload = service.build_trial_payload(settings, user.telegram_id, user.username)
        created = await client.create_user(payload)
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc
    return service.map_subscription(created, 0)


@router.post("/subscriptions/{uuid}/renew", response_model=Subscription)
async def renew(
    uuid: str,
    user: TelegramUser = Depends(require_telegram_user),
    client=Depends(_client),
    settings: Settings = Depends(get_settings),
):
    try:
        raw = await _find_user(client, user.telegram_id, uuid)
        updated = await client.update_user(service.build_renew_payload(raw, settings))
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc
    return service.map_subscription(updated, 0)


@router.get("/subscriptions/{uuid}/config", response_model=ConfigResponse)
async def get_config(
    uuid: str,
    user: TelegramUser = Depends(require_telegram_user),
    client=Depends(_client),
):
    try:
        raw = await _find_user(client, user.telegram_id, uuid)
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc
    url = str(raw.get("subscriptionUrl") or "")
    return ConfigResponse(subscription_url=url, deeplinks=service.build_deeplinks(url))


@router.post("/support", response_model=SupportResponse)
async def send_support(
    payload: SupportRequest,
    user: TelegramUser = Depends(require_telegram_user),
    settings: Settings = Depends(get_settings),
    conn: aiosqlite.Connection = Depends(get_db),
):
    """Создаёт новое обращение или дописывает в существующий тикет пользователя.

    Обращение сохраняется в БД (источник истины для раздела «Заявки»), а в чат
    поддержки уходит только короткий алерт — без падения запроса, если чат
    недоступен/не настроен (тикет уже сохранён, админ увидит его в мини-аппе).
    """
    if payload.ticket_id is None:
        ticket_id = await support_store.create_ticket(
            conn,
            user_telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            message=payload.message,
        )
    else:
        ticket = await support_store.get_ticket(conn, payload.ticket_id)
        if ticket is None or ticket["user_telegram_id"] != user.telegram_id:
            raise HTTPException(status_code=404, detail="ticket not found")
        await support_store.add_user_message(conn, payload.ticket_id, payload.message)
        ticket_id = payload.ticket_id

    if settings.support_chat_id and settings.bot_token:
        alert = telegram.build_alert_text(
            ticket_id=ticket_id,
            username=user.username,
            first_name=user.first_name,
            message=payload.message,
        )
        try:
            await telegram.send_message(settings.bot_token, settings.support_chat_id, alert)
        except telegram.TelegramSendError as exc:
            logger.warning("support alert delivery failed for ticket %s: %s", ticket_id, exc)

    return SupportResponse(ok=True, ticket_id=ticket_id)


@router.get("/support/tickets", response_model=TicketListResponse)
async def my_tickets(
    user: TelegramUser = Depends(require_telegram_user),
    conn: aiosqlite.Connection = Depends(get_db),
):
    rows = await support_store.list_by_user(conn, user.telegram_id)
    return TicketListResponse(tickets=[Ticket.model_validate(r) for r in rows])


@router.get("/support/tickets/{ticket_id}", response_model=TicketDetail)
async def my_ticket(
    ticket_id: int,
    user: TelegramUser = Depends(require_telegram_user),
    conn: aiosqlite.Connection = Depends(get_db),
):
    ticket = await support_store.get_with_messages(conn, ticket_id)
    if ticket is None or ticket["user_telegram_id"] != user.telegram_id:
        raise HTTPException(status_code=404, detail="ticket not found")
    return TicketDetail.model_validate(ticket)

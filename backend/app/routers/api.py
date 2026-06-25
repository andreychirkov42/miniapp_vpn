import logging

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config import Settings, get_settings
from ..db import get_db
from ..remnawave import RemnawaveError, get_client
from ..schemas import (
    ConfigResponse,
    DeviceDeleteRequest,
    DeviceListResponse,
    MeResponse,
    Subscription,
    SupportResponse,
    Ticket,
    TicketDetail,
    TicketListResponse,
)
from ..security import TelegramUser, is_admin, require_telegram_user
from .. import attachments, service, support_store, telegram

logger = logging.getLogger("akenai.api")

# Лимит длины текста обращения (совпадает с maxLength на фронте).
MESSAGE_MAX = 2000

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
    settings: Settings = Depends(get_settings),
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
        trial_days=settings.trial_days,
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
    return ConfigResponse(subscription_url=url)


@router.get("/subscriptions/{uuid}/devices", response_model=DeviceListResponse)
async def list_devices(
    uuid: str,
    user: TelegramUser = Depends(require_telegram_user),
    client=Depends(_client),
):
    try:
        raw = await _find_user(client, user.telegram_id, uuid)
        devices = await client.get_devices(raw["uuid"])
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc
    return DeviceListResponse(devices=service.map_devices(devices))


@router.post("/subscriptions/{uuid}/devices/delete", response_model=DeviceListResponse)
async def delete_device(
    uuid: str,
    payload: DeviceDeleteRequest,
    user: TelegramUser = Depends(require_telegram_user),
    client=Depends(_client),
):
    """Удаляет одно устройство (HWID) и возвращает обновлённый список.

    Владелец подписки проверяется через _find_user (uuid привязан к telegram_id),
    поэтому удалить можно только своё устройство.
    """
    try:
        raw = await _find_user(client, user.telegram_id, uuid)
        await client.delete_device(raw["uuid"], payload.hwid)
        devices = await client.get_devices(raw["uuid"])
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc
    return DeviceListResponse(devices=service.map_devices(devices))


@router.post("/support", response_model=SupportResponse)
async def send_support(
    message: str = Form(default=""),
    ticket_id: int | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    user: TelegramUser = Depends(require_telegram_user),
    settings: Settings = Depends(get_settings),
    conn: aiosqlite.Connection = Depends(get_db),
):
    """Создаёт новое обращение или дописывает в существующий тикет пользователя.

    Принимает multipart-форму: текст и/или картинку-вложение. Обращение
    сохраняется в БД (источник истины для раздела «Заявки»), а в чат поддержки
    уходит короткий алерт (фото — через sendPhoto) — без падения запроса, если
    чат недоступен/не настроен (тикет уже сохранён, виден в мини-аппе).
    """
    text = message.strip()
    if len(text) > MESSAGE_MAX:
        raise HTTPException(status_code=422, detail="message too long")

    attach_name = attach_mime = None
    if file is not None and file.filename:
        try:
            attach_name, attach_mime = await attachments.save_upload(
                file, db_path=settings.db_path
            )
        except attachments.AttachmentError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not text and attach_name is None:
        raise HTTPException(status_code=422, detail="empty message")

    if ticket_id is None:
        ticket_id = await support_store.create_ticket(
            conn,
            user_telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            message=text,
            attachment_path=attach_name,
            attachment_mime=attach_mime,
        )
    else:
        ticket = await support_store.get_ticket(conn, ticket_id)
        if ticket is None or ticket["user_telegram_id"] != user.telegram_id:
            raise HTTPException(status_code=404, detail="ticket not found")
        await support_store.add_user_message(
            conn, ticket_id, text,
            attachment_path=attach_name,
            attachment_mime=attach_mime,
        )

    if settings.support_chat_id and settings.bot_token:
        alert = telegram.build_alert_text(
            ticket_id=ticket_id,
            username=user.username,
            first_name=user.first_name,
            message=text or "(скриншот)",
        )
        try:
            if attach_name:
                path = attachments.resolve(attach_name, db_path=settings.db_path)
                await telegram.send_photo(
                    settings.bot_token, settings.support_chat_id, str(path), alert
                )
            else:
                await telegram.send_message(settings.bot_token, settings.support_chat_id, alert)
        except telegram.TelegramSendError as exc:
            logger.warning("support alert delivery failed for ticket %s: %s", ticket_id, exc)

    return SupportResponse(ok=True, ticket_id=ticket_id)


@router.get("/support/attachments/{message_id}")
async def get_attachment(
    message_id: int,
    user: TelegramUser = Depends(require_telegram_user),
    settings: Settings = Depends(get_settings),
    conn: aiosqlite.Connection = Depends(get_db),
):
    """Отдаёт картинку-вложение. Доступ: владелец тикета или админ.

    Картинку фронт догружает отдельным запросом с initData в заголовке (тег
    <img> заголовки слать не умеет), поэтому это обычный защищённый GET.
    """
    msg = await support_store.get_message(conn, message_id)
    if msg is None or not msg.get("attachment_path"):
        raise HTTPException(status_code=404, detail="attachment not found")

    ticket = await support_store.get_ticket(conn, msg["ticket_id"])
    if ticket is None:
        raise HTTPException(status_code=404, detail="attachment not found")
    if not is_admin(user.telegram_id) and ticket["user_telegram_id"] != user.telegram_id:
        raise HTTPException(status_code=404, detail="attachment not found")

    path = attachments.resolve(msg["attachment_path"], db_path=settings.db_path)
    if path is None:
        raise HTTPException(status_code=404, detail="attachment not found")

    return FileResponse(
        path,
        media_type=msg.get("attachment_mime") or "application/octet-stream",
        content_disposition_type="inline",
    )


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

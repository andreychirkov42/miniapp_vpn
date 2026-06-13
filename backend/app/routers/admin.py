"""Админский раздел «Заявки»: список обращений, диалог, ответ, закрытие.

Доступ только для telegram_id из ADMIN_IDS (Depends(require_admin)). Ответ админа
сохраняется в БД и отправляется пользователю в личку бота (best-effort — если
доставка не удалась, ответ всё равно сохранён и виден в мини-аппе при поллинге).
"""

from __future__ import annotations

import logging

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..db import get_db
from ..schemas import AdminReplyRequest, Ticket, TicketDetail, TicketListResponse
from ..security import TelegramUser, require_admin
from .. import support_store, telegram

logger = logging.getLogger("akenai.admin")

router = APIRouter(prefix="/api/admin", tags=["admin-support"])


@router.get("/support/tickets", response_model=TicketListResponse)
async def list_tickets(
    only_active: bool = True,
    _admin: TelegramUser = Depends(require_admin),
    conn: aiosqlite.Connection = Depends(get_db),
):
    rows = await support_store.list_all(conn, only_active=only_active)
    return TicketListResponse(tickets=[Ticket.model_validate(r) for r in rows])


@router.get("/support/tickets/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: int,
    _admin: TelegramUser = Depends(require_admin),
    conn: aiosqlite.Connection = Depends(get_db),
):
    ticket = await support_store.get_with_messages(conn, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    return TicketDetail.model_validate(ticket)


@router.post("/support/tickets/{ticket_id}/reply", response_model=TicketDetail)
async def reply(
    ticket_id: int,
    payload: AdminReplyRequest,
    admin: TelegramUser = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    conn: aiosqlite.Connection = Depends(get_db),
):
    ticket = await support_store.get_ticket(conn, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")

    await support_store.add_admin_message(conn, ticket_id, admin.telegram_id, payload.message)

    if settings.bot_token:
        text = telegram.build_user_reply_text(ticket_id=ticket_id, message=payload.message)
        try:
            await telegram.send_message(
                settings.bot_token, str(ticket["user_telegram_id"]), text
            )
        except telegram.TelegramSendError as exc:
            # Юзер мог не стартовать бота (нет приватного чата) — не роняем ответ.
            logger.warning("reply delivery failed for ticket %s: %s", ticket_id, exc)

    updated = await support_store.get_with_messages(conn, ticket_id)
    return TicketDetail.model_validate(updated)


@router.post("/support/tickets/{ticket_id}/close", response_model=TicketDetail)
async def close(
    ticket_id: int,
    _admin: TelegramUser = Depends(require_admin),
    conn: aiosqlite.Connection = Depends(get_db),
):
    ticket = await support_store.get_ticket(conn, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket not found")
    await support_store.set_status(conn, ticket_id, support_store.STATUS_CLOSED)
    updated = await support_store.get_with_messages(conn, ticket_id)
    return TicketDetail.model_validate(updated)

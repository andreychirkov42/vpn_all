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
from ..remnawave import RemnawaveError, get_client
from ..schemas import (
    AdminReplyRequest,
    RemnawaveStatusResponse,
    RemnawaveUserLookupResponse,
    Ticket,
    TicketDetail,
    TicketListResponse,
)
from ..security import TelegramUser, require_admin
from .. import service, support_store, telegram

logger = logging.getLogger("akenai.admin")

router = APIRouter(prefix="/api/admin", tags=["admin-support"])


def _client():
    return get_client()


@router.get("/remnawave/status", response_model=RemnawaveStatusResponse)
async def remnawave_status(
    _admin: TelegramUser = Depends(require_admin),
    client=Depends(_client),
    settings: Settings = Depends(get_settings),
):
    try:
        stats = await client.ping()
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc

    return RemnawaveStatusResponse(
        ok=True,
        mock=settings.remnawave_mock,
        base_url=settings.remnawave_public_base,
        api_base=settings.api_base,
        auth_mode=settings.remnawave_auth_mode,
        stats=stats,
    )


@router.get(
    "/remnawave/users/by-telegram-id/{telegram_id}",
    response_model=RemnawaveUserLookupResponse,
)
async def remnawave_users_by_telegram_id(
    telegram_id: int,
    _admin: TelegramUser = Depends(require_admin),
    client=Depends(_client),
):
    try:
        raws = await client.get_users_by_telegram_id(telegram_id)
        for raw in raws:
            uuid = raw.get("uuid")
            if not uuid:
                raw["_devices_used"] = 0
                continue
            try:
                raw["_devices_used"] = await client.get_hwid_count(uuid)
            except RemnawaveError:
                raw["_devices_used"] = 0
    except RemnawaveError as exc:
        raise HTTPException(status_code=502, detail=f"panel error: {exc}") from exc

    return RemnawaveUserLookupResponse(
        telegram_id=telegram_id,
        count=len(raws),
        subscriptions=service.map_all(raws),
    )


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

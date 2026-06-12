from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..remnawave import RemnawaveError, get_client
from ..schemas import (
    ConfigResponse,
    MeResponse,
    Subscription,
    SupportRequest,
    SupportResponse,
)
from ..security import TelegramUser, require_telegram_user
from .. import service, telegram

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
    return MeResponse(telegram_id=user.telegram_id, subscriptions=service.map_all(raws))


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
        payload = service.build_trial_payload(settings, user.telegram_id)
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
):
    if not settings.support_chat_id:
        raise HTTPException(status_code=503, detail="support is not configured")
    text = telegram.build_support_text(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        message=payload.message,
    )
    try:
        await telegram.send_message(settings.bot_token, settings.support_chat_id, text)
    except telegram.TelegramSendError as exc:
        raise HTTPException(status_code=502, detail=f"support delivery failed: {exc}") from exc
    return SupportResponse(ok=True)

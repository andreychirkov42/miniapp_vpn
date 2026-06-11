from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..remnawave import RemnawaveError, get_client
from ..schemas import ConfigResponse, MeResponse, Subscription
from ..security import TelegramUser, require_telegram_user
from .. import service

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

"""Validation of Telegram Mini App initData.

Docs: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
The frontend sends initData (the raw query string from Telegram.WebApp.initData)
in the `Authorization: tma <initData>` header. We verify the HMAC signature with
the bot token and extract the authenticated Telegram user id.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException, status

from .config import get_settings

logger = logging.getLogger("akenai.auth")


def is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_id_list


class TelegramUser:
    def __init__(self, telegram_id: int, username: str | None, first_name: str | None):
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name


def _check_signature(init_data: str, bot_token: str) -> dict[str, str]:
    pairs = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("no hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise ValueError("bad signature")
    return pairs


def parse_init_data(init_data: str, bot_token: str) -> TelegramUser:
    pairs = _check_signature(init_data, bot_token)
    user_raw = pairs.get("user")
    if not user_raw:
        raise ValueError("no user in initData")
    user = json.loads(user_raw)
    return TelegramUser(
        telegram_id=int(user["id"]),
        username=user.get("username"),
        first_name=user.get("first_name"),
    )


async def require_telegram_user(authorization: str | None = Header(default=None)) -> TelegramUser:
    """FastAPI dependency: returns the authenticated Telegram user.

    Accepts `Authorization: tma <initData>`. In dev, if DEV_TELEGRAM_ID is set and
    no valid initData is provided, falls back to that id (never enable in prod).
    """
    settings = get_settings()

    init_data = None
    scheme = ""
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() in ("tma", "twa", "bearer") and value:
            init_data = value

    if init_data and settings.bot_token:
        try:
            return parse_init_data(init_data, settings.bot_token)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            # Логируем причину и безопасный «отпечаток» initData (ключи, без значений),
            # чтобы отличать «битая подпись» от «не те поля / пустой user».
            keys = [p.split("=", 1)[0] for p in init_data.split("&")]
            logger.warning(
                "initData rejected: %s | len=%d keys=%s", exc, len(init_data), keys
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"invalid initData: {exc}",
            ) from exc

    # Dev fallback
    if settings.dev_telegram_id:
        return TelegramUser(
            telegram_id=int(settings.dev_telegram_id),
            username="dev_user",
            first_name="Dev",
        )

    logger.warning(
        "no initData: header_present=%s scheme=%r init_data_len=%d",
        bool(authorization),
        scheme,
        len(init_data or ""),
    )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="missing Telegram initData",
    )


async def require_admin(
    user: TelegramUser = Depends(require_telegram_user),
) -> TelegramUser:
    """FastAPI dependency: пропускает только админов (telegram_id ∈ ADMIN_IDS)."""
    if not is_admin(user.telegram_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return user

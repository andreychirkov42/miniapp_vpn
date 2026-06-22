"""Юнит-тесты построения имени пользователя для панели."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.service import (
    build_renew_months_payload,
    days_until_expiry,
    is_expiring_soon,
    panel_username,
)


def test_uses_telegram_handle_when_valid():
    assert panel_username(123, "ivan_petrov") == "ivan_petrov"


def test_fallback_when_no_handle():
    assert panel_username(923153874, None) == "tg923153874"
    assert panel_username(42, "") == "tg42"


def test_fallback_when_handle_too_short():
    # Remnawave требует >= 6 символов
    assert panel_username(7, "abc") == "tg7"


def test_fallback_when_handle_has_invalid_chars():
    assert panel_username(9, "bad-name!") == "tg9"


def test_renew_months_extends_from_active_expiry():
    """Активная подписка продлевается от текущего окончания (остаток сохраняется)."""
    raw = {"uuid": "u1", "expireAt": "2030-06-20T00:00:00.000Z"}
    payload = build_renew_months_payload(raw, 6)
    assert payload["uuid"] == "u1"
    assert payload["status"] == "ACTIVE"
    assert payload["expireAt"] == "2030-12-20T00:00:00Z"


def test_renew_months_clamps_short_month():
    """31 декабря + 6 мес → 30 июня (день обрезается до последнего в месяце)."""
    raw = {"uuid": "u2", "expireAt": "2030-12-31T00:00:00.000Z"}
    assert build_renew_months_payload(raw, 6)["expireAt"] == "2031-06-30T00:00:00Z"


def test_renew_months_expired_extends_from_now():
    """Истёкшая подписка продлевается от текущего момента, а не от старой даты."""
    raw = {"uuid": "u3", "expireAt": "2020-01-01T00:00:00Z"}
    payload = build_renew_months_payload(raw, 6)
    expire = datetime.fromisoformat(payload["expireAt"].replace("Z", "+00:00"))
    expected = datetime.now(timezone.utc)
    # ~6 месяцев от сейчас (с запасом на границы месяца)
    assert timedelta(days=175) < (expire - expected) < timedelta(days=190)


# --------------------- Напоминание об окончании подписки ---------------------

NOW = datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def test_expiring_soon_within_window():
    raw = {"expireAt": _iso(NOW + timedelta(days=2, hours=12))}
    assert is_expiring_soon(raw, 3, NOW) is True


def test_not_expiring_when_far_away():
    raw = {"expireAt": _iso(NOW + timedelta(days=10))}
    assert is_expiring_soon(raw, 3, NOW) is False


def test_not_expiring_when_already_expired():
    raw = {"expireAt": _iso(NOW - timedelta(days=1))}
    assert is_expiring_soon(raw, 3, NOW) is False


def test_not_expiring_when_status_expired():
    raw = {"status": "EXPIRED", "expireAt": _iso(NOW + timedelta(days=1))}
    assert is_expiring_soon(raw, 3, NOW) is False


def test_not_expiring_when_no_date():
    assert is_expiring_soon({}, 3, NOW) is False


def test_days_until_expiry_rounds_up():
    raw = {"expireAt": _iso(NOW + timedelta(days=2, hours=12))}
    assert days_until_expiry(raw, NOW) == 3


def test_days_until_expiry_none_without_date():
    assert days_until_expiry({}, NOW) is None

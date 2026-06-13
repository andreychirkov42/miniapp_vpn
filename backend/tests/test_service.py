"""Юнит-тесты построения имени пользователя для панели."""

from __future__ import annotations

from app.service import panel_username


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

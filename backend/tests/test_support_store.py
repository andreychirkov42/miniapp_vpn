"""Юнит-тесты репозитория обращений."""

from __future__ import annotations

from app import support_store as store


async def test_create_ticket_opens_with_first_message(conn):
    ticket_id = await store.create_ticket(
        conn, user_telegram_id=42, username="ivan", first_name="Иван", message="  не работает  "
    )

    ticket = await store.get_with_messages(conn, ticket_id)
    assert ticket["status"] == store.STATUS_OPEN
    assert ticket["user_telegram_id"] == 42
    assert len(ticket["messages"]) == 1
    assert ticket["messages"][0]["author"] == "user"
    assert ticket["messages"][0]["text"] == "не работает"  # trimmed


async def test_admin_reply_sets_answered(conn):
    ticket_id = await store.create_ticket(
        conn, user_telegram_id=1, username=None, first_name=None, message="вопрос"
    )

    await store.add_admin_message(conn, ticket_id, admin_telegram_id=99, text="ответ")

    ticket = await store.get_with_messages(conn, ticket_id)
    assert ticket["status"] == store.STATUS_ANSWERED
    assert [m["author"] for m in ticket["messages"]] == ["user", "admin"]
    assert ticket["messages"][1]["admin_telegram_id"] == 99


async def test_user_message_reopens_ticket(conn):
    ticket_id = await store.create_ticket(
        conn, user_telegram_id=1, username=None, first_name=None, message="q"
    )
    await store.add_admin_message(conn, ticket_id, admin_telegram_id=99, text="a")

    await store.add_user_message(conn, ticket_id, "ещё вопрос")

    ticket = await store.get_ticket(conn, ticket_id)
    assert ticket["status"] == store.STATUS_OPEN


async def test_list_by_user_filters_and_previews(conn):
    t1 = await store.create_ticket(
        conn, user_telegram_id=1, username=None, first_name=None, message="первое"
    )
    await store.create_ticket(
        conn, user_telegram_id=2, username=None, first_name=None, message="чужое"
    )
    await store.add_admin_message(conn, t1, admin_telegram_id=9, text="последнее")

    rows = await store.list_by_user(conn, 1)
    assert len(rows) == 1
    assert rows[0]["last_message"] == "последнее"
    assert rows[0]["last_author"] == "admin"


async def test_list_all_only_active_excludes_closed(conn):
    open_id = await store.create_ticket(
        conn, user_telegram_id=1, username=None, first_name=None, message="a"
    )
    closed_id = await store.create_ticket(
        conn, user_telegram_id=2, username=None, first_name=None, message="b"
    )
    await store.set_status(conn, closed_id, store.STATUS_CLOSED)

    active = await store.list_all(conn, only_active=True)
    all_rows = await store.list_all(conn, only_active=False)

    assert {r["id"] for r in active} == {open_id}
    assert {r["id"] for r in all_rows} == {open_id, closed_id}


async def test_get_ticket_missing_returns_none(conn):
    assert await store.get_ticket(conn, 999) is None
    assert await store.get_with_messages(conn, 999) is None

"""Интеграционные тесты эндпоинтов обращений (юзер + админ)."""

from __future__ import annotations

from conftest import USER_ID


async def test_create_ticket_via_api(client):
    resp = await client.post("/api/support", json={"message": "не подключается"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    ticket_id = body["ticket_id"]

    listed = await client.get("/api/support/tickets")
    assert listed.status_code == 200
    tickets = listed.json()["tickets"]
    assert len(tickets) == 1
    assert tickets[0]["id"] == ticket_id
    assert tickets[0]["status"] == "open"


async def test_append_to_existing_ticket(client):
    first = (await client.post("/api/support", json={"message": "вопрос 1"})).json()
    ticket_id = first["ticket_id"]

    second = await client.post(
        "/api/support", json={"message": "вопрос 2", "ticket_id": ticket_id}
    )
    assert second.json()["ticket_id"] == ticket_id

    detail = (await client.get(f"/api/support/tickets/{ticket_id}")).json()
    assert len(detail["messages"]) == 2


async def test_append_to_foreign_ticket_rejected(client):
    body = (await client.post("/api/support", json={"message": "моё"})).json()
    ticket_id = body["ticket_id"]

    resp = await client.post(
        "/api/support", json={"message": "чужое", "ticket_id": ticket_id + 999}
    )
    assert resp.status_code == 404


async def test_admin_reply_flow(client):
    ticket_id = (await client.post("/api/support", json={"message": "помогите"})).json()[
        "ticket_id"
    ]

    reply = await client.post(
        f"/api/admin/support/tickets/{ticket_id}/reply", json={"message": "перезагрузите"}
    )
    assert reply.status_code == 200
    detail = reply.json()
    assert detail["status"] == "answered"
    assert detail["messages"][-1]["author"] == "admin"
    assert detail["messages"][-1]["text"] == "перезагрузите"

    # юзер видит ответ в своём треде
    user_view = (await client.get(f"/api/support/tickets/{ticket_id}")).json()
    assert user_view["messages"][-1]["text"] == "перезагрузите"


async def test_admin_close_ticket(client):
    ticket_id = (await client.post("/api/support", json={"message": "x"})).json()["ticket_id"]

    closed = await client.post(f"/api/admin/support/tickets/{ticket_id}/close")
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    # закрытый тикет исчезает из активных у админа
    active = (await client.get("/api/admin/support/tickets")).json()["tickets"]
    assert all(t["id"] != ticket_id for t in active)
    all_rows = (await client.get("/api/admin/support/tickets?only_active=false")).json()["tickets"]
    assert any(t["id"] == ticket_id for t in all_rows)


async def test_admin_list_shows_all_users_tickets(client):
    await client.post("/api/support", json={"message": "от юзера"})

    admin_list = (await client.get("/api/admin/support/tickets")).json()["tickets"]
    assert len(admin_list) == 1
    assert admin_list[0]["user_telegram_id"] == USER_ID

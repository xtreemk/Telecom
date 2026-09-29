from __future__ import annotations

from app.services.ticket_service import create_ticket


def complaint_create(phone: str, message: str):
    ticket = create_ticket(phone=phone, message=message)
    return {"ok": True, "result": ticket}

from __future__ import annotations

from datetime import datetime, timezone

from app.db import get_db


def get_tickets() -> list[dict]:
    with get_db() as db:
        rows = db.execute("SELECT id, phone, message, status, created FROM tickets ORDER BY created").fetchall()
    return [dict(row) for row in rows]


def create_ticket(phone: str, message: str, status: str = "AI REVIEW") -> dict:
    ticket_id = f"LB-{len(get_tickets()) + 1001}"
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ticket = {"id": ticket_id, "phone": phone, "message": message, "status": status, "created": created}
    with get_db() as db:
        db.execute(
            "INSERT INTO tickets(id, phone, message, status, created) VALUES (?, ?, ?, ?, ?)",
            (ticket["id"], ticket["phone"], ticket["message"], ticket["status"], ticket["created"]),
        )
    return ticket

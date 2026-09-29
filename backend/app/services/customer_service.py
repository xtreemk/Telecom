from __future__ import annotations

import json
from typing import Any

from app.db import get_db


def get_customer(phone: str) -> dict[str, Any] | None:
    with get_db() as db:
        row = db.execute("SELECT profile_json FROM customers WHERE phone = ?", (phone,)).fetchone()
    if not row:
        return None
    return json.loads(row["profile_json"])


def save_customer(phone: str, profile: dict[str, Any]) -> None:
    with get_db() as db:
        db.execute("UPDATE customers SET profile_json = ? WHERE phone = ?", (json.dumps(profile), phone))


def get_customer_list() -> list[dict[str, Any]]:
    with get_db() as db:
        rows = db.execute("SELECT phone, profile_json FROM customers ORDER BY phone").fetchall()
    return [{"phone": row["phone"], **json.loads(row["profile_json"])} for row in rows]

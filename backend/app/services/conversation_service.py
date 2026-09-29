from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.db import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def start_conversation(phone: str, channel: str = "chat", language: str = "en") -> dict[str, Any]:
    created = _now()
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO conversations(phone, created, updated, channel, language) VALUES (?, ?, ?, ?, ?)",
            (phone, created, created, channel, language),
        )
        return {
            "id": cursor.lastrowid,
            "phone": phone,
            "channel": channel,
            "language": language,
            "created": created,
            "updated": created,
        }


def get_conversation(conversation_id: int) -> dict[str, Any] | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    return dict(row) if row else None


def get_or_start_conversation(phone: str, conversation_id: int | None = None, channel: str = "chat", language: str = "en") -> dict[str, Any]:
    if conversation_id is not None:
        conversation = get_conversation(conversation_id)
        if conversation and conversation["phone"] == phone:
            return conversation
    return start_conversation(phone, channel, language)


def append_message(conversation_id: int, role: str, message: str, language: str = "en") -> dict[str, Any]:
    created = _now()
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO messages(conversation_id, role, message, created, language) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, role, message, created, language),
        )
        db.execute("UPDATE conversations SET updated = ?, language = ? WHERE id = ?", (created, language, conversation_id))
    return {"id": cursor.lastrowid, "conversation_id": conversation_id, "role": role, "message": message, "created": created, "language": language}


def get_messages(conversation_id: int, limit: int = 12) -> list[dict[str, Any]]:
    with get_db() as db:
        rows = db.execute(
            "SELECT id, conversation_id, role, message, created, language FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
            (conversation_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]

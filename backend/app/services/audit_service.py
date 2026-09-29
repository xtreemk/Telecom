from __future__ import annotations

import json
from datetime import datetime, timezone

from app.db import get_db


def log_audit(actor: str, agent: str, tool: str, action: str, customer_phone: str, status: str, metadata: dict) -> dict:
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "actor": actor,
        "agent": agent,
        "tool": tool,
        "action": action,
        "customer_phone": customer_phone,
        "status": status,
        "created": created,
        "metadata": metadata,
    }
    with get_db() as db:
        db.execute(
            "INSERT INTO audit_events(actor, agent, tool, action, customer_phone, status, created, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                actor,
                agent,
                tool,
                action,
                customer_phone,
                status,
                created,
                json.dumps(metadata),
            ),
        )
    return record


def get_audit_events(limit: int = 100) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT actor, agent, tool, action, customer_phone, status, created, metadata_json FROM audit_events ORDER BY created DESC LIMIT ?",
            (limit,),
        ).fetchall()
    events = []
    for row in rows:
        event = dict(row)
        event["metadata"] = json.loads(event["metadata_json"])
        del event["metadata_json"]
        events.append(event)
    return events

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db import get_db
from app.services.audit_service import log_audit


class EscalationAgent:
    """Creates human exception records for cases that require a person or higher authorization."""

    name = "escalation_agent"

    def create_escalation(
        self,
        customer_phone: str,
        conversation_ref: str,
        reason: str,
        priority: str = "MEDIUM",
        status: str = "OPEN",
        ai_actions_attempted: list[str] | None = None,
        recommended_next_action: str = "Review and authorize a human decision.",
        attempted_tool: str = "unknown",
        actor: str = "system",
    ) -> dict[str, Any]:
        created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        updated = created
        escalation = {
            "id": f"ESC-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "customer_phone": customer_phone,
            "conversation_ref": conversation_ref,
            "reason": reason,
            "priority": priority,
            "status": status,
            "ai_actions_attempted": ai_actions_attempted or [],
            "recommended_next_action": recommended_next_action,
            "created": created,
            "updated": updated,
            "attempted_tool": attempted_tool,
        }

        with get_db() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS escalations (
                    id TEXT PRIMARY KEY,
                    customer_phone TEXT NOT NULL,
                    conversation_ref TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    ai_actions_attempted TEXT NOT NULL,
                    recommended_next_action TEXT NOT NULL,
                    created TEXT NOT NULL,
                    updated TEXT NOT NULL,
                    attempted_tool TEXT NOT NULL
                )
                """
            )
            db.execute(
                "INSERT INTO escalations(id, customer_phone, conversation_ref, reason, priority, status, ai_actions_attempted, recommended_next_action, created, updated, attempted_tool) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    escalation["id"],
                    escalation["customer_phone"],
                    escalation["conversation_ref"],
                    escalation["reason"],
                    escalation["priority"],
                    escalation["status"],
                    str(escalation["ai_actions_attempted"]),
                    escalation["recommended_next_action"],
                    escalation["created"],
                    escalation["updated"],
                    escalation["attempted_tool"],
                ),
            )

        log_audit(
            actor=actor,
            agent="escalation_agent",
            tool="escalation_create",
            action="escalation",
            customer_phone=customer_phone,
            status="open",
            metadata={
                "escalation_id": escalation["id"],
                "reason": reason,
                "conversation_ref": conversation_ref,
                "priority": priority,
                "recommended_next_action": recommended_next_action,
            },
        )
        return escalation

    def get_queue(self) -> list[dict[str, Any]]:
        with get_db() as db:
            rows = db.execute(
                "SELECT id, customer_phone, conversation_ref, reason, priority, status, ai_actions_attempted, recommended_next_action, created, updated, attempted_tool FROM escalations ORDER BY created DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def update_escalation(self, escalation_id: str, status: str, recommended_next_action: str | None = None) -> dict[str, Any]:
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM escalations WHERE id = ?",
                (escalation_id,),
            ).fetchone()
            if row is None:
                raise ValueError(f"Escalation not found: {escalation_id}")

            updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            if recommended_next_action is not None:
                db.execute(
                    "UPDATE escalations SET status = ?, updated = ?, recommended_next_action = ? WHERE id = ?",
                    (status, updated, recommended_next_action, escalation_id),
                )
            else:
                db.execute(
                    "UPDATE escalations SET status = ?, updated = ? WHERE id = ?",
                    (status, updated, escalation_id),
                )

            refreshed = db.execute("SELECT * FROM escalations WHERE id = ?", (escalation_id,)).fetchone()
            return dict(refreshed)

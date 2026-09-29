from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.audit_service import get_audit_events
from app.services.customer_service import get_customer_list
from app.services.ticket_service import get_tickets


class ReportingAgent:
    """Read-only analytics agent for operational summaries and admin dashboard data."""

    name = "reporting_agent"

    def overview(self) -> dict[str, Any]:
        events = get_audit_events(limit=5000)
        customers = get_customer_list()
        tickets = get_tickets()

        intents = Counter(event["metadata"].get("intent", "unknown") for event in events if event.get("metadata"))
        agents = Counter(event["agent"] for event in events)
        tools = Counter(event["tool"] for event in events)
        statuses = Counter(event["status"] for event in events)
        unresolved = sum(1 for ticket in tickets if ticket.get("status") not in {"RESOLVED", "CLOSED"})

        return {
            "total_customers": len(customers),
            "total_interactions": len(events),
            "total_tickets": len(tickets),
            "intents": dict(intents),
            "agents": dict(agents),
            "tool_usage": dict(tools),
            "status_counts": dict(statuses),
            "unresolved_cases": unresolved,
            "complaint_volume": sum(1 for ticket in tickets if ticket.get("message")),
            "escalation_count": sum(1 for event in events if event.get("tool") == "escalation_create" or event.get("action") == "escalation"),
            "successful_resolutions": sum(1 for event in events if event.get("status") == "success"),
            "failed_actions": sum(1 for event in events if event.get("status") == "failed"),
        }

    def intents(self) -> list[dict[str, Any]]:
        events = get_audit_events(limit=5000)
        counts = Counter(event["metadata"].get("intent", "unknown") for event in events if event.get("metadata"))
        return [{"intent": name, "count": count} for name, count in counts.most_common()]

    def agents(self) -> list[dict[str, Any]]:
        events = get_audit_events(limit=5000)
        counts = Counter(event["agent"] for event in events)
        return [{"agent": name, "count": count} for name, count in counts.most_common()]

    def escalations(self) -> list[dict[str, Any]]:
        events = get_audit_events(limit=5000)
        escalation_events = [event for event in events if event.get("action") == "escalation" or event.get("tool") == "escalation_create"]
        return [{
            "customer_phone": event["customer_phone"],
            "agent": event["agent"],
            "tool": event["tool"],
            "status": event["status"],
            "created": event["created"],
            "metadata": event["metadata"],
        } for event in escalation_events]

    def transactions(self) -> dict[str, Any]:
        events = get_audit_events(limit=5000)
        all_transactions = [event for event in events if event.get("tool") in {"transaction_lookup", "bundle_remediation"}]
        return {
            "total": len(all_transactions),
            "by_status": dict(Counter(event["status"] for event in all_transactions)),
            "by_agent": dict(Counter(event["agent"] for event in all_transactions)),
        }

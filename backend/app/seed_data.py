from __future__ import annotations

from datetime import datetime, timezone


SEED_CUSTOMERS = {
    "08030000001": {
        "name": "Aisha Bello",
        "airtime": 2350,
        "data": 1.8,
        "bundle": "10GB Monthly",
        "expiry": "2026-10-02",
        "network": "normal",
        "last": {"amount": 3500, "type": "10GB bundle", "status": "SUCCESS"},
        "marketing_consent": True,
    },
    "08030000002": {
        "name": "Musa Ibrahim",
        "airtime": 850,
        "data": 0.2,
        "bundle": "1.5GB Daily",
        "expiry": "2026-09-25",
        "network": "outage",
        "last": {"amount": 1500, "type": "Recharge", "status": "SUCCESS"},
        "marketing_consent": False,
    },
    "08030000003": {
        "name": "Chinedu Okafor",
        "airtime": 1200,
        "data": 5.4,
        "bundle": "15GB Monthly",
        "expiry": "2026-10-18",
        "network": "normal",
        "last": {"amount": 5000, "type": "15GB bundle", "status": "PENDING"},
        "marketing_consent": False,
    },
}


def seed_customers() -> dict[str, dict]:
    return SEED_CUSTOMERS


def seed_knowledge() -> list[dict]:
    created = datetime.now(timezone.utc).isoformat()
    return [
        {
            "category": "product",
            "title": "Data bundle policy",
            "content": "Bundle activation should be confirmed only after a successful authorized transaction. Data balance can be checked from customer profile data.",
            "created": created,
        },
        {
            "category": "troubleshooting",
            "title": "Network outage guidance",
            "content": "If the account is in an outage state, advise the customer to toggle mobile data and retry. Record the network diagnostic if an outage is detected.",
            "created": created,
        },
        {
            "category": "complaints",
            "title": "Complaint intake",
            "content": "Complaints should be logged as a ticket with clear case status and included in the audit trail.",
            "created": created,
        },
    ]

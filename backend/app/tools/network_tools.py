from __future__ import annotations

from app.services.customer_service import get_customer


def network_diagnostic(phone: str):
    customer = get_customer(phone)
    if not customer:
        return {"ok": False, "error": "customer_not_found"}
    if customer.get("network") == "outage":
        return {
            "ok": True,
            "result": {
                "status": "outage_detected",
                "message": "The diagnostic found a simulated service outage affecting this account's service area.",
            },
        }
    return {
        "ok": True,
        "result": {
            "status": "normal",
            "message": "The account is active and no simulated area outage is detected.",
        },
    }

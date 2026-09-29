from __future__ import annotations

from app.services.customer_service import get_customer


def customer_lookup(phone: str):
    customer = get_customer(phone)
    if not customer:
        return {"ok": False, "error": "customer_not_found"}
    return {"ok": True, "customer": {"phone": phone, **customer}}


def data_balance_lookup(phone: str):
    customer = get_customer(phone)
    if not customer:
        return {"ok": False, "error": "customer_not_found"}
    return {
        "ok": True,
        "result": {
            "phone": phone,
            "data": customer.get("data"),
            "bundle": customer.get("bundle"),
            "expiry": customer.get("expiry"),
        },
    }


def transaction_lookup(phone: str):
    customer = get_customer(phone)
    if not customer:
        return {"ok": False, "error": "customer_not_found"}
    return {"ok": True, "result": customer.get("last", {})}

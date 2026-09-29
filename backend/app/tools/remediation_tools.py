from __future__ import annotations

from app.services.customer_service import get_customer, save_customer


def bundle_remediation(phone: str):
    customer = get_customer(phone)
    if not customer:
        return {"ok": False, "error": "customer_not_found"}
    if "bundle" in customer["last"]["type"].lower() and customer["last"]["status"] == "PENDING":
        customer["last"]["status"] = "SUCCESS"
        customer["data"] += 15
        save_customer(phone, customer)
        return {
            "ok": True,
            "result": {
                "status": "completed",
                "message": f"Pending bundle activation completed. Updated data balance: {customer['data']:.1f} GB.",
                "updated_data": customer["data"],
            },
        }
    return {
        "ok": True,
        "result": {
            "status": "already_resolved",
            "message": "The latest transaction is already marked successful. No additional simulated remediation was needed.",
        },
    }

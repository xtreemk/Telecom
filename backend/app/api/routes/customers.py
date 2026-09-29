from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.customer_service import get_customer
from app.services.proactive_engagement import set_customer_consent

router = APIRouter()


class MarketingConsentUpdate(BaseModel):
    marketing_consent: bool


@router.get("/api/customer/{phone}")
def customer(phone: str):
    customer_data = get_customer(phone)
    if not customer_data:
        return {"error": "customer_not_found"}
    return {"phone": phone, **customer_data}


@router.patch("/api/customer/{phone}/consent")
def update_marketing_consent(phone: str, update: MarketingConsentUpdate):
    customer_data = get_customer(phone)
    if not customer_data:
        raise HTTPException(status_code=404, detail="Customer not found")
    set_customer_consent(phone, update.marketing_consent)
    return {"phone": phone, "marketing_consent": update.marketing_consent}

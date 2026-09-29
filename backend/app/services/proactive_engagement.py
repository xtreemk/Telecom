from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db import get_db
from app.services.customer_service import get_customer, save_customer
from app.config import settings


@dataclass
class ProactiveOffer:
    id: str
    title: str
    description: str
    target_bundle: str | None = None
    min_data_balance: float | None = None
    max_data_balance: float | None = None
    required_consent: bool = True


PROACTIVE_OFFERS: list[ProactiveOffer] = [
    ProactiveOffer(
        id="data_boost_1gb",
        title="1GB Data Boost",
        description="Add 1GB to your current plan for just NGN 500.",
        target_bundle=None,
        min_data_balance=0,
        max_data_balance=2.0,
        required_consent=True,
    ),
    ProactiveOffer(
        id="bundle_upgrade_10gb",
        title="10GB Monthly Bundle",
        description="Upgrade to 10GB monthly for NGN 3,500 - great value!",
        target_bundle="1.5GB Daily",
        min_data_balance=None,
        max_data_balance=None,
        required_consent=True,
    ),
    ProactiveOffer(
        id="night_data_5gb",
        title="5GB Night Data",
        description="5GB for night browsing (11pm-6am) for NGN 1,000.",
        target_bundle=None,
        min_data_balance=None,
        max_data_balance=None,
        required_consent=True,
    ),
    ProactiveOffer(
        id="social_bundle",
        title="Social Media Bundle",
        description="Unlimited WhatsApp, Facebook, Instagram for NGN 500/week.",
        target_bundle=None,
        min_data_balance=None,
        max_data_balance=None,
        required_consent=True,
    ),
]


def get_customer_consent(phone: str) -> bool:
    customer = get_customer(phone)
    if not customer:
        return False
    return customer.get("marketing_consent", False)


def set_customer_consent(phone: str, consent: bool) -> None:
    customer = get_customer(phone)
    if customer:
        customer["marketing_consent"] = consent
        save_customer(phone, customer)


def get_eligible_offers(phone: str) -> list[ProactiveOffer]:
    if not settings.PROACTIVE_OFFERS_ENABLED:
        return []
    
    if not get_customer_consent(phone):
        return []
    
    customer = get_customer(phone)
    if not customer:
        return []
    
    data_balance = customer.get("data", 0)
    current_bundle = customer.get("bundle", "")
    
    eligible = []
    for offer in PROACTIVE_OFFERS:
        if offer.target_bundle and current_bundle != offer.target_bundle:
            continue
        if offer.min_data_balance is not None and data_balance < offer.min_data_balance:
            continue
        if offer.max_data_balance is not None and data_balance > offer.max_data_balance:
            continue
        eligible.append(offer)
    
    return eligible


def select_best_offer(phone: str, recent_intent: str) -> ProactiveOffer | None:
    eligible = get_eligible_offers(phone)
    if not eligible:
        return None
    
    intent_offer_map = {
        "data_balance": ["data_boost_1gb", "night_data_5gb"],
        "bundle_issue": ["bundle_upgrade_10gb"],
        "network": [],
        "transaction": [],
        "complaint": [],
    }
    
    preferred_ids = intent_offer_map.get(recent_intent, [])
    for offer_id in preferred_ids:
        for offer in eligible:
            if offer.id == offer_id:
                return offer

    if recent_intent in intent_offer_map:
        return None

    return eligible[0] if eligible else None


def format_offer_message(offer: ProactiveOffer, language: str = "en") -> str:
    messages = {
        "en": f"By the way, you might like our {offer.title}: {offer.description}",
        "pid": f"By the way, you fit like our {offer.title}: {offer.description}",
        "yo": f"Nitorina, ẹ le fẹ {offer.title}: {offer.description}",
        "ha": f"Kuma, ka iya so {offer.title}: {offer.description}",
        "ig": f"Maka naabọ, ị chọrọ {offer.title}: {offer.description}",
    }
    return messages.get(language, messages["en"])


def should_make_proactive_offer(
    phone: str,
    intent: str,
    tool_result: dict | None,
    conversation_turn: int,
) -> ProactiveOffer | None:
    if not settings.PROACTIVE_OFFERS_ENABLED:
        return None
    
    if conversation_turn < 2:
        return None
    
    if not get_customer_consent(phone):
        return None
    
    if not tool_result or not tool_result.get("ok"):
        return None

    if intent not in {"data_balance", "bundle_issue"}:
        return None
    
    return select_best_offer(phone, intent)


def claim_proactive_offer(phone: str, conversation_id: int, offer: ProactiveOffer) -> bool:
    """Record an offer only if consent and the published frequency limits allow it."""
    if not settings.PROACTIVE_OFFERS_ENABLED or not get_customer_consent(phone):
        return False

    now = datetime.now(timezone.utc)
    now_text = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
    cooldown_start = (now - timedelta(hours=4)).isoformat().replace("+00:00", "Z")

    with get_db() as db:
        db.execute("BEGIN IMMEDIATE")
        already_in_conversation = db.execute(
            "SELECT 1 FROM proactive_offer_events WHERE phone = ? AND conversation_id = ? LIMIT 1",
            (phone, conversation_id),
        ).fetchone()
        offers_today = db.execute(
            "SELECT COUNT(*) FROM proactive_offer_events WHERE phone = ? AND offered_at >= ?",
            (phone, day_start),
        ).fetchone()[0]
        recent_offer = db.execute(
            "SELECT 1 FROM proactive_offer_events WHERE phone = ? AND offered_at >= ? LIMIT 1",
            (phone, cooldown_start),
        ).fetchone()
        if already_in_conversation or offers_today >= 3 or recent_offer:
            return False
        db.execute(
            "INSERT INTO proactive_offer_events(phone, conversation_id, offer_id, offered_at) VALUES (?, ?, ?, ?)",
            (phone, conversation_id, offer.id, now_text),
        )
    return True

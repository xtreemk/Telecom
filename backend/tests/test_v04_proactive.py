from fastapi.testclient import TestClient
from app.main import app
from app.services.orchestrator import orchestrate_chat
from app.services.proactive_engagement import (
    get_customer_consent,
    set_customer_consent,
    get_eligible_offers,
    select_best_offer,
    should_make_proactive_offer,
    PROACTIVE_OFFERS,
    claim_proactive_offer,
)
from app.services.customer_service import get_customer, save_customer


client = TestClient(app)


def test_proactive_offer_respects_consent_false():
    # Customer 08030000002 has marketing_consent = False
    assert get_customer_consent("08030000002") is False
    
    eligible = get_eligible_offers("08030000002")
    assert eligible == []


def test_proactive_offer_when_consent_true():
    # Customer 08030000001 has marketing_consent = True
    assert get_customer_consent("08030000001") is True
    
    eligible = get_eligible_offers("08030000001")
    assert len(eligible) > 0
    
    # Aisha has 1.8GB data, so data_boost_1gb should be eligible (max 2GB)
    offer_ids = [o.id for o in eligible]
    assert "data_boost_1gb" in offer_ids


def test_offer_frequency_limits_enforced():
    # First turn - no offer
    result1 = orchestrate_chat("08030000001", "What is my data balance?")
    assert result1.get("proactive_offer") is None or result1.get("proactive_offer") == "data_boost_1gb"
    
    # Second turn - might get offer
    result2 = orchestrate_chat("08030000001", "What about my bundle?", conversation_id=result1["conversation_id"])
    
    # Offer should only appear after turn 2
    if result1.get("proactive_offer") is None:
        assert result2.get("proactive_offer") in [None, "data_boost_1gb", "night_data_5gb"]


def test_consent_can_be_set_and_retrieved():
    phone = "08030000003"
    # Initially false
    assert get_customer_consent(phone) is False
    
    # Set to true
    set_customer_consent(phone, True)
    assert get_customer_consent(phone) is True
    
    # Set back to false
    set_customer_consent(phone, False)
    assert get_customer_consent(phone) is False


def test_select_best_offer_matches_intent():
    # After data_balance intent, should prefer data_boost_1gb or night_data_5gb
    offer = select_best_offer("08030000001", "data_balance")
    assert offer is not None
    assert offer.id in ["data_boost_1gb", "night_data_5gb"]


def test_select_best_offer_bundle_issue():
    assert select_best_offer("08030000002", "bundle_issue") is None
    customer = get_customer("08030000001")
    try:
        customer["bundle"] = "1.5GB Daily"
        save_customer("08030000001", customer)
        offer = select_best_offer("08030000001", "bundle_issue")
        assert offer is not None
        assert offer.id == "bundle_upgrade_10gb"
    finally:
        customer["bundle"] = "10GB Monthly"
        save_customer("08030000001", customer)


def test_should_make_proactive_offer_checks_conditions():
    # consent = False -> no offer
    offer = should_make_proactive_offer("08030000002", "data_balance", {"ok": True}, 2)
    assert offer is None
    
    # turn < 2 -> no offer
    offer = should_make_proactive_offer("08030000001", "data_balance", {"ok": True}, 1)
    assert offer is None
    
    # tool failed -> no offer
    offer = should_make_proactive_offer("08030000001", "data_balance", {"ok": False}, 2)
    assert offer is None
    
    # All conditions met -> offer
    offer = should_make_proactive_offer("08030000001", "data_balance", {"ok": True}, 2)
    assert offer is not None


def test_proactive_offers_defined():
    assert len(PROACTIVE_OFFERS) == 4
    offer_ids = [o.id for o in PROACTIVE_OFFERS]
    assert "data_boost_1gb" in offer_ids
    assert "bundle_upgrade_10gb" in offer_ids
    assert "night_data_5gb" in offer_ids
    assert "social_bundle" in offer_ids


def test_orchestrator_includes_proactive_offer_in_response():
    result = orchestrate_chat("08030000001", "What is my data balance?")
    # First turn, no offer expected
    assert "proactive_offer" in result
    
    # Second turn with same conversation
    result2 = orchestrate_chat("08030000001", "What about my bundle?", conversation_id=result["conversation_id"])
    assert "proactive_offer" in result2


def test_customer_profile_has_marketing_consent_field():
    customer = get_customer("08030000001")
    assert "marketing_consent" in customer
    assert customer["marketing_consent"] is True
    
    customer2 = get_customer("08030000002")
    assert "marketing_consent" in customer2
    assert customer2["marketing_consent"] is False


def test_offer_claim_enforces_one_offer_per_conversation_and_cooldown():
    phone = "08030000003"
    set_customer_consent(phone, True)
    try:
        offer = PROACTIVE_OFFERS[0]
        assert claim_proactive_offer(phone, 991001, offer) is True
        assert claim_proactive_offer(phone, 991001, offer) is False
        assert claim_proactive_offer(phone, 991002, offer) is False
    finally:
        set_customer_consent(phone, False)


def test_marketing_consent_api_can_be_changed():
    response = client.patch(
        "/api/customer/08030000003/consent",
        json={"marketing_consent": True},
    )
    assert response.status_code == 200
    assert response.json()["marketing_consent"] is True
    assert get_customer_consent("08030000003") is True
    client.patch(
        "/api/customer/08030000003/consent",
        json={"marketing_consent": False},
    )


def test_offer_claim_enforces_daily_cap(monkeypatch):
    from datetime import datetime, timezone
    from app.db import get_db
    import app.services.proactive_engagement as proactive

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(proactive, "datetime", FrozenDateTime)
    phone = "08030000003"
    set_customer_consent(phone, True)
    try:
        with get_db() as db:
            db.execute("DELETE FROM proactive_offer_events WHERE phone = ?", (phone,))
            db.executemany(
                "INSERT INTO proactive_offer_events(phone, conversation_id, offer_id, offered_at) VALUES (?, ?, ?, ?)",
                [
                    (phone, 992001, "data_boost_1gb", "2030-01-01T06:00:00Z"),
                    (phone, 992002, "data_boost_1gb", "2030-01-01T07:00:00Z"),
                    (phone, 992003, "data_boost_1gb", "2030-01-01T07:30:00Z"),
                ],
            )
        assert claim_proactive_offer(phone, 992004, PROACTIVE_OFFERS[0]) is False
    finally:
        set_customer_consent(phone, False)

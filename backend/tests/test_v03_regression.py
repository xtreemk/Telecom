from fastapi.testclient import TestClient

from app.agents.escalation_agent import EscalationAgent
from app.agents.reporting_agent import ReportingAgent
from app.main import app
from app.services.orchestrator import orchestrate_chat


client = TestClient(app)


def test_reporting_agent_overview_has_expected_sections():
    overview = ReportingAgent().overview()
    assert "total_customers" in overview
    assert "total_interactions" in overview
    assert "unresolved_cases" in overview
    assert "intents" in overview


def test_orchestrator_creates_escalation_for_unknown_intent():
    result = orchestrate_chat("08030000001", "This is an emergency and needs a person")
    assert result["escalate"] is True
    assert "escalation" in result
    assert result["escalation"]["customer_phone"] == "08030000001"
    assert result["escalation"]["status"] == "OPEN"


def test_escalation_queue_returns_created_records():
    escalation = EscalationAgent().create_escalation(
        customer_phone="08030000002",
        conversation_ref="chat:test:queue",
        reason="manual_review_required",
        priority="HIGH",
    )
    queue = EscalationAgent().get_queue()
    assert any(item["id"] == escalation["id"] for item in queue)


def test_reporting_routes_are_accessible():
    response = client.get("/api/reports/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_customers" in data

    response = client.get("/api/escalations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_chat_endpoint_returns_reply():
    response = client.post("/api/chat", json={"phone": "08030000001", "message": "What is my data balance?"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "intent" in data
    assert data["intent"] == "data_balance"


def test_customer_lookup_endpoint():
    response = client.get("/api/customer/08030000001")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Aisha Bello"
    assert data["phone"] == "08030000001"


def test_tickets_endpoint():
    response = client.get("/api/tickets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "livebox-ai-v0.4"


def test_orchestrator_data_balance():
    result = orchestrate_chat("08030000001", "What is my data balance?")
    assert result["intent"] == "data_balance"
    assert "reply" in result
    assert "1.8" in result["reply"] or "10GB" in result["reply"]


def test_orchestrator_network_diagnostic():
    result = orchestrate_chat("08030000002", "My internet is not working")
    assert result["intent"] == "network"
    assert "reply" in result


def test_orchestrator_bundle_issue():
    result = orchestrate_chat("08030000003", "I bought a bundle but data not showing")
    assert result["intent"] == "bundle_issue"
    assert "reply" in result


def test_orchestrator_transaction_lookup():
    result = orchestrate_chat("08030000001", "What was my last transaction?")
    assert result["intent"] == "transaction"
    assert "reply" in result


def test_orchestrator_complaint():
    result = orchestrate_chat("08030000001", "I want to complain about slow speed")
    assert result["intent"] == "complaint"
    assert "reply" in result
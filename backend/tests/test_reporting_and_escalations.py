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

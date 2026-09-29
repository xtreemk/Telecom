from fastapi.testclient import TestClient
from app.main import app
from app.services.orchestrator import orchestrate_chat
from app.services.conversation_context import get_conversation_by_phone, load_conversation


client = TestClient(app)


def test_multi_turn_conversation_maintains_context():
    # First message
    result1 = orchestrate_chat("08030000001", "What is my data balance?")
    assert result1["intent"] == "data_balance"
    conv_id = result1["conversation_id"]
    assert conv_id is not None

    # Second message - follow up
    result2 = orchestrate_chat("08030000001", "What about my bundle expiry?", conversation_id=conv_id)
    assert result2["conversation_id"] == conv_id
    assert "expiry" in result2["reply"].lower() or "expire" in result2["reply"].lower()


def test_conversation_context_retention_followup():
    # Ask about transaction
    result1 = orchestrate_chat("08030000001", "What was my last transaction?")
    assert result1["intent"] == "transaction"
    conv_id = result1["conversation_id"]

    # Follow up about data
    result2 = orchestrate_chat("08030000001", "And my data balance?", conversation_id=conv_id)
    assert result2["intent"] == "data_balance"
    assert result2["conversation_id"] == conv_id


def test_customer_name_greeting_on_first_message():
    result = orchestrate_chat("08030000001", "Hello")
    assert "Aisha" in result["reply"] or "Aisha Bello" in result["reply"]
    assert "LiveBox AI" in result["reply"]


def test_conversation_id_returned_in_response():
    result = orchestrate_chat("08030000001", "Test message")
    assert "conversation_id" in result
    assert isinstance(result["conversation_id"], int)


def test_conversation_persists_in_db():
    # Start a conversation
    result1 = orchestrate_chat("08030000002", "What is my data balance?")
    conv_id = result1["conversation_id"]

    # Retrieve from DB
    conv = get_conversation_by_phone("08030000002")
    assert conv is not None
    assert conv.conversation_id == conv_id
    assert len(conv.messages) >= 2  # user + assistant


def test_chat_endpoint_with_conversation_id():
    # First request
    resp1 = client.post("/api/chat", json={"phone": "08030000001", "message": "What is my data balance?"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    conv_id = data1["conversation_id"]

    # Second request with conversation_id
    resp2 = client.post("/api/chat", json={"phone": "08030000001", "message": "What about my bundle?", "conversation_id": conv_id})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["conversation_id"] == conv_id


def test_conversation_language_persists_and_id_is_customer_scoped():
    first = orchestrate_chat("08030000003", "What is my data balance?")
    conversation_id = first["conversation_id"]
    switched = orchestrate_chat(
        "08030000003", "Wetin be my data balance?", conversation_id=conversation_id
    )
    assert switched["language"] == "pid"
    persisted = load_conversation(conversation_id)
    assert persisted.language == "pid"
    assert persisted.customer_name == "Chinedu Okafor"
    assert persisted.intent_history[-1] == "data_balance"
    assert persisted.tool_results

    wrong_customer = orchestrate_chat(
        "08030000002", "What is my data balance?", conversation_id=conversation_id
    )
    assert wrong_customer["error"] == "conversation_not_found"

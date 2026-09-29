from fastapi.testclient import TestClient
from app.main import app
from app.services.voice_session import (
    create_voice_session,
    get_voice_session,
    end_voice_session,
    VoiceSessionState,
    handle_speech_input,
    handle_barge_in,
    handle_call_end,
)
from app.services.orchestrator import orchestrate_voice
from app.services.speech_io import MockSpeechSynthesizer


client = TestClient(app)


def test_voice_session_start_creates_session_with_greeting():
    response = client.post("/api/voice/start", json={"phone": "08030000001"})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"].startswith("voice_")
    assert "greeting" in data
    assert "Aisha" in data["greeting"] or "Aisha Bello" in data["greeting"]
    assert "LiveBox AI" in data["greeting"]
    assert "ssml" in data
    assert "phonetic_markers" in data
    assert data["language"] == "en"
    assert data["customer_name"] == "Aisha Bello"


def test_voice_session_speech_input_processes_message():
    # Start session
    start_resp = client.post("/api/voice/start", json={"phone": "08030000001"})
    session_id = start_resp.json()["session_id"]

    # Send speech
    speech_resp = client.post("/api/voice/speech", json={"session_id": session_id, "text": "What is my data balance?"})
    assert speech_resp.status_code == 200
    data = speech_resp.json()
    assert "reply" in data
    assert "ssml" in data
    assert "phonetic_markers" in data
    assert data["intent"] == "data_balance"
    assert "1.8" in data["reply"] or "10GB" in data["reply"]


def test_voice_session_end_closes_session():
    start_resp = client.post("/api/voice/start", json={"phone": "08030000001"})
    session_id = start_resp.json()["session_id"]

    end_resp = client.post("/api/voice/end", json={"session_id": session_id})
    assert end_resp.status_code == 200
    data = end_resp.json()
    assert data["state"] == "ended"
    assert "farewell" in data
    assert data["session_id"] == session_id

    # Verify session is ended
    session = get_voice_session(session_id)
    assert session.state == VoiceSessionState.ENDED


def test_barge_in_handling():
    start_resp = client.post("/api/voice/start", json={"phone": "08030000001"})
    session_id = start_resp.json()["session_id"]

    # Barge in during response
    barge_resp = client.post("/api/voice/barge", json={"session_id": session_id})
    assert barge_resp.status_code == 200
    data = barge_resp.json()
    assert data["barge_in"] is True
    assert "reply" in data
    assert "ssml" in data
    conversation_id = get_voice_session(session_id).conversation.conversation_id
    from app.services.conversation_context import load_conversation
    assert load_conversation(conversation_id).interrupted is True

    continued = client.post(
        "/api/voice/speech",
        json={"session_id": session_id, "text": "What is my data balance?"},
    )
    assert continued.status_code == 200
    assert load_conversation(conversation_id).interrupted is False


def test_voice_session_lifecycle():
    # Initializing -> Active -> Ended
    session = create_voice_session("08030000001")
    assert session.state == VoiceSessionState.ACTIVE
    assert session.conversation is not None
    assert session.phone == "08030000001"

    # Process speech
    result = handle_speech_input(session.session_id, "What is my data balance?")
    assert "reply" in result
    assert result["intent"] == "data_balance"

    # End session
    ended = end_voice_session(session.session_id)
    assert ended.state == VoiceSessionState.ENDED
    assert ended.ended is not None


def test_voice_session_with_different_customer():
    session = create_voice_session("08030000002")
    assert session.phone == "08030000002"
    assert session.conversation.customer_name == "Musa Ibrahim"


def test_voice_session_invalid_phone_raises():
    try:
        create_voice_session("99999999999")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Customer not found" in str(e)


def test_voice_sessions_list():
    create_voice_session("08030000001")
    create_voice_session("08030000002")
    
    resp = client.get("/api/voice/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert len(data["sessions"]) >= 2


def test_voice_speech_returns_ssml_and_phonetic_markers():
    start_resp = client.post("/api/voice/start", json={"phone": "08030000001"})
    session_id = start_resp.json()["session_id"]

    speech_resp = client.post("/api/voice/speech", json={"session_id": session_id, "text": "Hello"})
    data = speech_resp.json()
    
    assert "ssml" in data
    assert data["ssml"].startswith("<speak")
    assert "phonetic_markers" in data
    assert isinstance(data["phonetic_markers"], list)
    assert len(data["phonetic_markers"]) > 0


def test_orchestrate_voice_returns_spoken_response():
    session = create_voice_session("08030000001")
    result = orchestrate_voice(session.session_id, "08030000001", "What is my data balance?")
    
    assert "reply" in result
    assert "ssml" in result
    assert "phonetic_markers" in result
    assert result["intent"] == "data_balance"


def test_no_input_endpoint_returns_one_nudge_then_waits():
    start = client.post("/api/voice/start", json={"phone": "08030000002"})
    session_id = start.json()["session_id"]

    first = client.post("/api/voice/no-input", json={"session_id": session_id})
    assert first.status_code == 200
    assert "data balance" in first.json()["reply"].lower()
    assert first.json()["ssml"].startswith("<speak")
    session = get_voice_session(session_id)
    from app.services.conversation_context import load_conversation
    history = load_conversation(session.conversation.conversation_id)
    assert any("how may I help" in item.content for item in history.messages)
    assert any("data balance" in item.content for item in history.messages)

    second = client.post("/api/voice/no-input", json={"session_id": session_id})
    assert second.status_code == 200
    assert second.json()["proactive_offer"] is None


def test_no_input_endpoint_rejects_missing_session():
    response = client.post("/api/voice/no-input", json={"session_id": "missing"})
    assert response.status_code == 404


def test_ssml_escapes_customer_text():
    ssml = MockSpeechSynthesizer("test").synthesize("A < B & C", "en").ssml
    assert "A &lt; B &amp; C" in ssml

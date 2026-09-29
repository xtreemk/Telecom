from fastapi.testclient import TestClient
from app.main import app
from app.services.orchestrator import orchestrate_chat
from app.services.language_detector import (
    detect_language,
    is_mixed_language,
    get_primary_language,
    LANGUAGE_MARKERS,
)


client = TestClient(app)


def test_english_detection():
    assert detect_language("Hello, how are you?") == "en"
    assert detect_language("What is my data balance?") == "en"
    assert detect_language("I want to check my balance") == "en"


def test_nigerian_pidgin_detection():
    assert detect_language("Wetin happen?") == "pid"
    assert detect_language("How far, abeg help me") == "pid"
    assert detect_language("Wahala dey, my data no dey work") == "pid"
    assert detect_language("Na so e be") == "pid"
    assert detect_language("I no know wetin you talk") == "pid"


def test_yoruba_detection():
    assert detect_language("Bawo ni?") == "yo"
    assert detect_language("Ṣé wá dá?") == "yo"
    assert detect_language("Mo fẹ́ ràn ẹ") == "yo"
    assert detect_language("Ẹ káàbọ̀") == "yo"


def test_hausa_detection():
    assert detect_language("Ina kwana?") == "ha"
    assert detect_language("Yaya ake?") == "ha"
    assert detect_language("Na gode") == "ha"
    assert detect_language("Sannu, yaya zan taimake?") == "ha"


def test_igbo_detection():
    assert detect_language("Nnoọ, kedu?") == "ig"
    assert detect_language("Biko, nye m aka") == "ig"
    assert detect_language("Kedu ka ị mere?") == "ig"
    assert detect_language("Dalụ") == "ig"


def test_english_to_pidgin_switching():
    # First message in English
    result1 = orchestrate_chat("08030000001", "What is my data balance?")
    assert result1["language"] == "en"
    conv_id = result1["conversation_id"]

    # Second message in Pidgin
    result2 = orchestrate_chat("08030000001", "Wetin be my data balance?", conversation_id=conv_id)
    assert result2["language"] == "pid"


def test_english_to_yoruba_switching():
    result1 = orchestrate_chat("08030000001", "What is my data balance?")
    conv_id = result1["conversation_id"]
    result2 = orchestrate_chat("08030000001", "Bawo ni data mi?", conversation_id=conv_id)
    assert result2["language"] == "yo"


def test_english_to_hausa_switching():
    result1 = orchestrate_chat("08030000001", "What is my data balance?")
    conv_id = result1["conversation_id"]
    result2 = orchestrate_chat("08030000001", "Ina data na?", conversation_id=conv_id)
    assert result2["language"] == "ha"


def test_english_to_igbo_switching():
    result1 = orchestrate_chat("08030000001", "What is my data balance?")
    conv_id = result1["conversation_id"]
    result2 = orchestrate_chat("08030000001", "Kedu data m?", conversation_id=conv_id)
    assert result2["language"] == "ig"


def test_mixed_language_code_switching():
    # Mixed English and Pidgin
    text = "My data balance na 2GB, wetin happen?"
    assert is_mixed_language(text) is True
    
    # Primary should be detected
    primary = get_primary_language(text)
    assert primary in ["en", "pid"]


def test_unknown_language_fallback():
    # Text with no known markers
    result = orchestrate_chat("08030000001", "Xyzabc defghi jklmno")
    assert result["language"] == "en"
    assert "LiveBox AI" in result["reply"]


def test_language_detected_per_message_in_response():
    result = orchestrate_chat("08030000001", "Wetin be my data balance?")
    assert "language" in result
    assert result["language"] == "pid"


def test_all_language_markers_defined():
    for lang, markers in LANGUAGE_MARKERS.items():
        assert len(markers) > 0, f"Language {lang} has no markers"
        for marker in markers:
            assert isinstance(marker, str)
            assert len(marker) > 0


def test_chat_endpoint_returns_language():
    resp = client.post("/api/chat", json={"phone": "08030000001", "message": "Wetin be my data balance?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "language" in data
    assert data["language"] == "pid"
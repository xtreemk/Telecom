from __future__ import annotations

from collections import Counter
from typing import Any

SUPPORTED_LANGUAGES = {
    "en": "English",
    "pcm": "Nigerian Pidgin",
    "yo": "Yoruba",
    "ha": "Hausa",
    "ig": "Igbo",
}

_MARKERS = {
    "pcm": {"abeg", "dey", "wetin", "una", "wahala", "no vex", "fit", "don"},
    "yo": {"bawo", "ẹ jọ", "mo", "data mi", "ṣe", "ki lo", "o ṣe"},
    "ha": {"sannu", "don Allah", "yaya", "baturi", "ina", "na gode", "matsala"},
    "ig": {"ndewo", "biko", "kedu", "ego", "data m", "ọ dị", "daalụ"},
}


def detect_language(text: str, previous_language: str = "en") -> dict[str, Any]:
    normalized = text.casefold()
    scores = Counter()
    for language, markers in _MARKERS.items():
        scores[language] = sum(1 for marker in markers if marker.casefold() in normalized)

    language, score = scores.most_common(1)[0] if scores else ("en", 0)
    if score == 0:
        language = previous_language if previous_language in SUPPORTED_LANGUAGES else "en"
    return {
        "language": language,
        "language_name": SUPPORTED_LANGUAGES[language],
        "confidence": min(1.0, score / 2) if score else 0.35,
        "detected": score > 0,
        "scores": dict(scores),
    }


def localize_reply(reply: str, language: str, intent: str) -> str:
    if language == "en":
        return reply
    prefixes = {
        "pcm": {"greeting": "How far! ", "default": "No wahala. "},
        "yo": {"greeting": "Bawo! ", "default": "Mo ye. "},
        "ha": {"greeting": "Sannu! ", "default": "Na fahimta. "},
        "ig": {"greeting": "Ndewo! ", "default": "Aghotago. "},
    }
    return prefixes.get(language, prefixes["en"] if "en" in prefixes else {"default": ""}).get(intent, prefixes.get(language, {}).get("default", "")) + reply

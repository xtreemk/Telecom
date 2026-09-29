from __future__ import annotations

import re
from typing import Literal

LanguageCode = Literal["en", "pid", "yo", "ha", "ig"]

LANGUAGE_MARKERS: dict[LanguageCode, list[str]] = {
    "en": ["hello", "please", "thank you", "could you", "would you", "want", "check"],
    "pid": [
        "wetin", "abeg", "pikin", "how far", "wahala",
        "no be", "e be", "e don", "e dey", "make i", "you sabi",
        "i no know", "na so", "na wa", "which kind", "na you",
        "na me", "i go", "i wan", "i fit", "i no fit", "sabi",
        "dey", "don", "fit", "no fit", "abi", "sha",
        "how you dey", "wetin happen", "wetin you want",
        "na ", " de ", " no ", " e ",
    ],
    "yo": [
        "ṣé", "bà", "rẹ̀", "ẹni", "ṣe", "ní", "kí", "lò", "wá",
        "báwo", "ṣé", "dára", "òdì", "wáyé", "mọ́", "kò",
        "fẹ́", "ràn", "wá", "níbí", "nígbà", "ṣì", "kí",
        "báwo ni", "kí lò ṣẹlẹ̀", "ṣé wá dà", "mọ́ fẹ́",
        "ràn mí", "ẹ káàbọ̀", "bawo ni", "se wa", "o wa",
        "nkò", "ni bo", "ni gba", "fẹ́", "ṣeun",
    ],
    "ha": [
        "ina kwana", "yaya ake", "na gode", "kafin", "kuma", "don", "sune",
        "musa", "iya", "mata", "bari", "yau", "gobe", "tafiya", "zo",
        "ba ni", "a'a", "ya kamata", "na so", "gani", "ji",
        "yadda", "wane", "tafiya", "gida", "ina", "yaya",
    ],
    "ig": [
        "nna", "gị", "ka", "ị", "chere", "nke", "ụfọdụ",
        "biko", "kedu", "ọ dị", "mma", "ezigbo", "ụtụtụ",
        "ehihie", "abali", "i mere", "ị mere", "achọrọ",
        "chọrọ", "nwere", "enwere", "ihe", "ọ bụ", "ebee",
        "ole", "gịnị", "kedu ka ị mere", "dalụ",
        "nnoọ", "ka ị dị mma", "achọrọ m", "chere m",
    ],
}

LANGUAGE_NAMES: dict[LanguageCode, str] = {
    "en": "English",
    "pid": "Nigerian Pidgin",
    "yo": "Yoruba",
    "ha": "Hausa",
    "ig": "Igbo",
}

LANGUAGE_GREETINGS: dict[LanguageCode, str] = {
    "en": "Hello",
    "pid": "How far",
    "yo": "Bawo ni",
    "ha": "Sannu",
    "ig": "Nnoọ",
}

LANGUAGE_FAREWELLS: dict[LanguageCode, str] = {
    "en": "Goodbye",
    "pid": "Bye bye",
    "yo": "Ọdàbọ",
    "ha": "Sai anjima",
    "ig": "Ka ọ dị",
}

def detect_language(text: str) -> LanguageCode:
    """Detect the language of the input text using keyword/marker matching."""
    text_lower = text.lower()
    
    scores: dict[LanguageCode, int] = {lang: 0 for lang in LANGUAGE_MARKERS}
    
    for lang, markers in LANGUAGE_MARKERS.items():
        for marker in markers:
            pattern = rf"(?<!\w){re.escape(marker.casefold())}(?!\w)"
            if re.search(pattern, text_lower.casefold()):
                scores[lang] += 1
    
    max_score = max(scores.values())
    if max_score == 0:
        return "en"
    
    best_langs = [lang for lang, score in scores.items() if score == max_score]
    non_english = [lang for lang in best_langs if lang != "en"]
    return non_english[0] if non_english else best_langs[0]


def get_language_name(code: LanguageCode) -> str:
    return LANGUAGE_NAMES.get(code, "English")


def get_greeting(code: LanguageCode) -> str:
    return LANGUAGE_GREETINGS.get(code, "Hello")


def get_farewell(code: LanguageCode) -> str:
    return LANGUAGE_FAREWELLS.get(code, "Goodbye")


def is_mixed_language(text: str) -> bool:
    """Check if the text contains markers from multiple languages."""
    text_lower = text.casefold()
    detected = set()
    for lang, markers in LANGUAGE_MARKERS.items():
        for marker in markers:
            pattern = rf"(?<!\w){re.escape(marker.casefold())}(?!\w)"
            if re.search(pattern, text_lower):
                detected.add(lang)
    english_words = {"my", "data", "balance", "what", "is", "the", "how", "much", "want", "check"}
    if len(set(re.findall(r"[\w']+", text_lower)) & english_words) >= 2:
        detected.add("en")
    return len(detected) > 1


def get_primary_language(text: str) -> LanguageCode:
    """Get the primary language, handling code-switching."""
    return detect_language(text)
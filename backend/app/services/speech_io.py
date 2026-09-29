from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from xml.sax.saxutils import escape


@dataclass
class SpeechInput:
    text: str
    language: str = "en"
    confidence: float = 1.0
    is_final: bool = True
    session_id: str | None = None


@dataclass
class SpeechOutput:
    text: str
    language: str = "en"
    ssml: str | None = None
    phonetic_markers: list[dict] | None = None
    session_id: str | None = None


class MockSpeechRecognizer:
    """Mock ASR - simulates speech recognition by accepting text input."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
    
    async def recognize(self, audio_data: bytes | None = None, text: str | None = None) -> SpeechInput:
        if text is None:
            text = ""
        return SpeechInput(
            text=text,
            language="en",
            confidence=1.0,
            is_final=True,
            session_id=self.session_id,
        )
    
    async def recognize_streaming(self, audio_chunk: bytes) -> SpeechInput:
        return SpeechInput(text="", language="en", confidence=0.0, is_final=False, session_id=self.session_id)


class MockSpeechSynthesizer:
    """Mock TTS - simulates speech synthesis by returning text with voice markers."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
    
    def synthesize(self, text: str, language: str = "en") -> SpeechOutput:
        ssml = self._to_ssml(text, language)
        return SpeechOutput(
            text=text,
            language=language,
            ssml=ssml,
            phonetic_markers=self._generate_phonetic_markers(text),
            session_id=self.session_id,
        )
    
    def _to_ssml(self, text: str, language: str) -> str:
        lang_map = {
            "en": "en-US",
            "pid": "en-NG",
            "yo": "yo-NG",
            "ha": "ha-NG",
            "ig": "ig-NG",
        }
        lang_code = lang_map.get(language, "en-US")
        
        ssml_text = escape(text)
        ssml_text = ssml_text.replace(". ", '. <break time="300ms"/> ')
        ssml_text = ssml_text.replace("? ", '? <break time="400ms"/> ')
        ssml_text = ssml_text.replace("! ", '! <break time="400ms"/> ')
        ssml_text = ssml_text.replace(", ", ', <break time="150ms"/> ')
        
        return f'<speak xml:lang="{lang_code}">{ssml_text}</speak>'
    
    def _generate_phonetic_markers(self, text: str) -> list[dict]:
        markers = []
        words = text.split()
        time_offset = 0
        for i, word in enumerate(words):
            markers.append({
                "word": word,
                "start_ms": time_offset,
                "end_ms": time_offset + len(word) * 80,
            })
            time_offset += len(word) * 80 + 50
        return markers


class SpeechIOManager:
    """Manages speech I/O for a voice session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.recognizer = MockSpeechRecognizer(session_id)
        self.synthesizer = MockSpeechSynthesizer(session_id)
    
    async def process_speech_input(self, text: str) -> SpeechInput:
        return await self.recognizer.recognize(text=text)
    
    def generate_speech_output(self, text: str, language: str = "en") -> SpeechOutput:
        return self.synthesizer.synthesize(text, language)
    
    def synthesize_ssml(self, ssml: str) -> SpeechOutput:
        return SpeechOutput(
            text=ssml,
            language="en",
            ssml=ssml,
            session_id=self.session_id,
        )

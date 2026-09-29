from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.config import settings
from app.services.conversation_context import (
    ConversationContext, ConversationMessage, create_conversation, save_conversation,
)
from app.services.customer_service import get_customer
from app.services.orchestrator import orchestrate_voice
from app.services.speech_io import SpeechIOManager
from app.services.responder import generate_farewell, generate_barge_in_response
from app.services.proactive_engagement import (
    claim_proactive_offer,
    format_offer_message,
    get_customer_consent,
    select_best_offer,
)


class VoiceSessionState(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    RESPONDING = "responding"
    INTERRUPTED = "interrupted"
    ENDED = "ended"


@dataclass
class VoiceSession:
    session_id: str
    phone: str
    state: VoiceSessionState = VoiceSessionState.INITIALIZING
    conversation: ConversationContext | None = None
    current_response: str | None = None
    is_speaking: bool = False
    barge_in_detected: bool = False
    no_input_nudge_sent: bool = False
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    ended: str | None = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "phone": self.phone,
            "state": self.state.value,
            "conversation_id": self.conversation.conversation_id if self.conversation else None,
            "current_response": self.current_response,
            "is_speaking": self.is_speaking,
            "barge_in_detected": self.barge_in_detected,
            "created": self.created,
            "updated": self.updated,
            "ended": self.ended,
        }


_voice_sessions: dict[str, VoiceSession] = {}


def create_voice_session(phone: str) -> VoiceSession:
    customer = get_customer(phone)
    if not customer:
        raise ValueError(f"Customer not found: {phone}")
    
    customer_name = customer.get("name", "Customer")
    conversation = create_conversation(phone, customer_name, "en")
    conversation.customer_profile_snapshot = {"name": customer_name, "phone": phone}
    
    session_id = f"voice_{uuid.uuid4().hex[:12]}"
    session = VoiceSession(
        session_id=session_id,
        phone=phone,
        state=VoiceSessionState.ACTIVE,
        conversation=conversation,
    )
    _voice_sessions[session_id] = session
    return session


def get_voice_session(session_id: str) -> VoiceSession | None:
    return _voice_sessions.get(session_id)


def update_voice_session(session_id: str, **kwargs) -> VoiceSession | None:
    session = _voice_sessions.get(session_id)
    if not session:
        return None
    
    for key, value in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, value)
    session.updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return session


def end_voice_session(session_id: str) -> VoiceSession | None:
    session = _voice_sessions.get(session_id)
    if not session:
        return None
    
    session.state = VoiceSessionState.ENDED
    session.ended = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    session.updated = session.ended
    
    if session.conversation:
        save_conversation(session.conversation)
    
    return session


def handle_speech_input(session_id: str, text: str) -> dict[str, Any]:
    session = get_voice_session(session_id)
    if not session:
        return {"error": "session_not_found"}
    
    if session.state == VoiceSessionState.ENDED:
        return {"error": "session_ended"}

    if session.conversation:
        session.conversation.interrupted = False

    result = orchestrate_voice(session_id, session.phone, text)
    
    if "error" in result:
        return result
    
    return result


def handle_barge_in(session_id: str) -> dict[str, Any]:
    session = get_voice_session(session_id)
    if not session:
        return {"error": "session_not_found"}
    
    if session.state in (VoiceSessionState.ACTIVE, VoiceSessionState.RESPONDING) and session.current_response:
        update_voice_session(session_id, state=VoiceSessionState.INTERRUPTED, barge_in_detected=True, is_speaking=False)
        
        language = session.conversation.language if session.conversation else "en"
        response = generate_barge_in_response(language)
        if session.conversation:
            session.conversation.interrupted = True
            session.conversation.add_message(ConversationMessage(
                role="assistant", content=response, language=language, intent="barge_in"
            ))
            save_conversation(session.conversation)
        
        speech_io = SpeechIOManager(session_id)
        speech_output = speech_io.generate_speech_output(response, language)
        
        update_voice_session(session_id, state=VoiceSessionState.ACTIVE, current_response=response, barge_in_detected=False)
        
        return {
            "reply": response,
            "ssml": speech_output.ssml,
            "phonetic_markers": speech_output.phonetic_markers,
            "language": language,
            "barge_in": True,
            "interrupted": True,
        }
    
    return {"reply": "", "barge_in": False, "interrupted": False}


def handle_no_input(session_id: str) -> dict[str, Any]:
    """Return one short silence prompt; offers require consent and pass frequency caps."""
    session = get_voice_session(session_id)
    if not session:
        return {"error": "session_not_found"}
    if session.state == VoiceSessionState.ENDED:
        return {"error": "session_ended"}
    if session.no_input_nudge_sent:
        language = session.conversation.language if session.conversation else "en"
        reply = "I'm here when you're ready. Tell me what you'd like help with."
        if session.conversation:
            session.conversation.add_message(ConversationMessage(role="assistant", content=reply, language=language))
            save_conversation(session.conversation)
        return {"reply": reply, "language": language, "proactive_offer": None}

    language = session.conversation.language if session.conversation else "en"
    reply = "I can check your data balance, airtime, recent transactions, or help with a network issue. What would you like me to check?"
    offer_id = None
    if get_customer_consent(session.phone) and session.conversation:
        offer = select_best_offer(session.phone, "data_balance")
        if offer and claim_proactive_offer(session.phone, session.conversation.conversation_id, offer):
            reply = f"{reply} {format_offer_message(offer, language)}"
            offer_id = offer.id

    session.no_input_nudge_sent = True
    session.current_response = reply
    session.updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if session.conversation:
        session.conversation.add_message(ConversationMessage(role="assistant", content=reply, language=language))
        save_conversation(session.conversation)
    speech_output = SpeechIOManager(session_id).generate_speech_output(reply, language)
    return {
        "reply": reply,
        "ssml": speech_output.ssml,
        "phonetic_markers": speech_output.phonetic_markers,
        "language": language,
        "proactive_offer": offer_id,
    }


def handle_call_end(session_id: str) -> dict[str, Any]:
    session = end_voice_session(session_id)
    if not session:
        return {"error": "session_not_found"}
    
    language = session.conversation.language if session.conversation else "en"
    farewell = generate_farewell(language)
    
    return {
        "session_id": session.session_id,
        "state": session.state.value,
        "ended": session.ended,
        "farewell": farewell,
        "message": "Call ended. Thank you for calling LiveBox.",
    }


def list_voice_sessions() -> list[dict]:
    return [s.to_dict() for s in _voice_sessions.values()]


def cleanup_expired_sessions() -> int:
    now = datetime.now(timezone.utc)
    expired = []
    for session_id, session in _voice_sessions.items():
        updated = datetime.fromisoformat(session.updated.replace("Z", "+00:00"))
        if (now - updated).total_seconds() > settings.VOICE_SESSION_TIMEOUT_MINUTES * 60:
            expired.append(session_id)
    
    for session_id in expired:
        session = _voice_sessions.pop(session_id)
        if session.conversation:
            save_conversation(session.conversation)
    
    return len(expired)

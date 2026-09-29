"""Service layer for orchestrated workflows and system operations."""

from app.services.audit_service import log_audit, get_audit_events
from app.services.conversation_context import (
    ConversationContext,
    ConversationMessage,
    create_conversation,
    save_conversation,
    load_conversation,
    get_conversation_by_phone,
    get_or_create_conversation,
)
from app.services.customer_service import get_customer, save_customer, get_customer_list
from app.services.intent_router import classify_intent
from app.services.knowledge_service import get_knowledge_entries
from app.services.language_detector import (
    detect_language,
    get_language_name,
    get_greeting,
    get_farewell,
    is_mixed_language,
    get_primary_language,
    LANGUAGE_MARKERS,
    LANGUAGE_NAMES,
)
from app.services.voice_session import (
    VoiceSession,
    VoiceSessionState,
    create_voice_session,
    get_voice_session,
    update_voice_session,
    end_voice_session,
    list_voice_sessions,
    cleanup_expired_sessions,
    handle_speech_input,
    handle_barge_in,
    handle_call_end,
)
from app.services.proactive_engagement import (
    ProactiveOffer,
    get_customer_consent,
    set_customer_consent,
    get_eligible_offers,
    select_best_offer,
    format_offer_message,
    should_make_proactive_offer,
)
from app.services.proactive_engagement import (
    ProactiveOffer,
    get_customer_consent,
    set_customer_consent,
    get_eligible_offers,
    select_best_offer,
    format_offer_message,
    should_make_proactive_offer,
)
from app.services.responder import build_spoken_response, generate_greeting, generate_farewell
from app.services.speech_io import (
    SpeechInput,
    SpeechOutput,
    MockSpeechRecognizer,
    MockSpeechSynthesizer,
    SpeechIOManager,
)
from app.services.ticket_service import get_tickets, create_ticket
from app.services.voice_session import (
    VoiceSession,
    VoiceSessionState,
    create_voice_session,
    get_voice_session,
    update_voice_session,
    end_voice_session,
    list_voice_sessions,
    cleanup_expired_sessions,
)

__all__ = [
    "log_audit",
    "get_audit_events",
    "ConversationContext",
    "ConversationMessage",
    "create_conversation",
    "save_conversation",
    "load_conversation",
    "get_conversation_by_phone",
    "get_or_create_conversation",
    "get_customer",
    "save_customer",
    "get_customer_list",
    "classify_intent",
    "get_knowledge_entries",
    "detect_language",
    "get_language_name",
    "get_greeting",
    "get_farewell",
    "is_mixed_language",
    "get_primary_language",
    "LANGUAGE_MARKERS",
    "LANGUAGE_NAMES",
    "build_spoken_response",
    "generate_greeting",
    "generate_farewell",
    "ProactiveOffer",
    "get_customer_consent",
    "set_customer_consent",
    "get_eligible_offers",
    "select_best_offer",
    "format_offer_message",
    "should_make_proactive_offer",
    "SpeechInput",
    "SpeechOutput",
    "MockSpeechRecognizer",
    "MockSpeechSynthesizer",
    "SpeechIOManager",
    "get_tickets",
    "create_ticket",
    "VoiceSession",
    "VoiceSessionState",
    "create_voice_session",
    "get_voice_session",
    "update_voice_session",
    "end_voice_session",
    "list_voice_sessions",
    "cleanup_expired_sessions",
    "handle_speech_input",
    "handle_barge_in",
    "handle_call_end",
]
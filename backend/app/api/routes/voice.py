from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.voice_session import (
    create_voice_session,
    get_voice_session,
    update_voice_session,
    end_voice_session,
    list_voice_sessions,
    VoiceSessionState,
    handle_no_input,
    handle_barge_in,
)
from app.services.orchestrator import orchestrate_voice
from app.services.speech_io import SpeechIOManager
from app.services.responder import generate_farewell
from app.services.conversation_context import ConversationMessage, save_conversation

router = APIRouter()


class VoiceStartRequest(BaseModel):
    phone: str


class VoiceSpeechRequest(BaseModel):
    session_id: str
    text: str


class VoiceBargeRequest(BaseModel):
    session_id: str


class VoiceNoInputRequest(BaseModel):
    session_id: str


class VoiceEndRequest(BaseModel):
    session_id: str


@router.post("/api/voice/start")
def voice_start(req: VoiceStartRequest):
    try:
        session = create_voice_session(req.phone)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    customer = session.conversation.customer_name if session.conversation else "Customer"
    language = session.conversation.language if session.conversation else "en"
    
    from app.services.responder import generate_greeting, generate_ai_identity
    greeting = generate_greeting(customer, language, is_returning=False)
    ai_identity = generate_ai_identity(language)
    full_greeting = f"{greeting} {ai_identity}"
    if session.conversation:
        session.conversation.add_message(
            ConversationMessage(role="assistant", content=full_greeting, language=language)
        )
        save_conversation(session.conversation)
    
    speech_io = SpeechIOManager(session.session_id)
    speech_output = speech_io.generate_speech_output(full_greeting, language)
    
    update_voice_session(session.session_id, state=VoiceSessionState.ACTIVE, current_response=full_greeting)
    
    return {
        "session_id": session.session_id,
        "phone": session.phone,
        "greeting": full_greeting,
        "ssml": speech_output.ssml,
        "phonetic_markers": speech_output.phonetic_markers,
        "language": language,
        "customer_name": customer,
    }


@router.post("/api/voice/speech")
def voice_speech(req: VoiceSpeechRequest):
    session = get_voice_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.state == VoiceSessionState.ENDED:
        raise HTTPException(status_code=400, detail="Session has ended")
    
    result = orchestrate_voice(req.session_id, session.phone, req.text)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/api/voice/barge")
def voice_barge(req: VoiceBargeRequest):
    result = handle_barge_in(req.session_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/api/voice/no-input")
def voice_no_input(req: VoiceNoInputRequest):
    result = handle_no_input(req.session_id)
    if result.get("error") == "session_not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    if result.get("error") == "session_ended":
        raise HTTPException(status_code=400, detail="Session has ended")
    return result


@router.post("/api/voice/end")
def voice_end(req: VoiceEndRequest):
    session = end_voice_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "state": session.state.value,
        "ended": session.ended,
        "farewell": generate_farewell(session.conversation.language if session.conversation else "en"),
        "message": "Call ended. Thank you for calling LiveBox.",
    }


@router.get("/api/voice/sessions")
def voice_sessions():
    return {"sessions": list_voice_sessions()}

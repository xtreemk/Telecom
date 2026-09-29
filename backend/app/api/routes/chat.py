from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.orchestrator import orchestrate_chat

router = APIRouter()


class ChatRequest(BaseModel):
    phone: str
    message: str
    conversation_id: Optional[int] = None
    session_id: Optional[str] = None


@router.post("/api/chat")
def chat(req: ChatRequest):
    result = orchestrate_chat(
        phone=req.phone,
        message=req.message,
        actor="user",
        conversation_id=req.conversation_id,
        session_id=req.session_id,
    )
    if result.get("error") == "conversation_not_found":
        raise HTTPException(status_code=404, detail="Conversation not found for this customer")
    return result

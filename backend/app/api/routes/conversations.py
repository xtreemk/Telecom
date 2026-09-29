from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.conversation_context import (
    get_conversation_by_phone,
    load_conversation,
    ConversationContext,
)
from app.services.customer_service import get_customer

router = APIRouter()


@router.get("/api/conversations/{phone}")
def conversation_history(phone: str):
    customer = get_customer(phone)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    conversation = get_conversation_by_phone(phone)
    if not conversation:
        return {"phone": phone, "messages": [], "conversation_id": None}
    
    messages = []
    for msg in conversation.messages:
        messages.append({
            "role": msg.role,
            "content": msg.content,
            "language": msg.language,
            "intent": msg.intent,
            "tool_called": msg.tool_called,
            "created": msg.created,
        })
    
    return {
        "phone": phone,
        "customer_name": conversation.customer_name,
        "conversation_id": conversation.conversation_id,
        "language": conversation.language,
        "messages": messages,
        "intent_history": conversation.intent_history,
        "tool_results": conversation.tool_results,
        "created": conversation.created,
        "updated": conversation.updated,
    }


@router.get("/api/conversations/{phone}/context")
def conversation_context(phone: str):
    customer = get_customer(phone)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    conversation = get_conversation_by_phone(phone)
    if not conversation:
        return {
            "phone": phone,
            "has_conversation": False,
            "summary": "No previous conversation",
        }
    
    return {
        "phone": phone,
        "customer_name": conversation.customer_name,
        "conversation_id": conversation.conversation_id,
        "has_conversation": True,
        "summary": conversation.get_context_summary(),
        "message_count": len(conversation.messages),
        "current_language": conversation.language,
        "intent_history": conversation.intent_history[-5:] if conversation.intent_history else [],
        "last_tool_result": conversation.tool_results[-1] if conversation.tool_results else None,
        "customer_profile_snapshot": conversation.customer_profile_snapshot,
        "interrupted": conversation.interrupted,
    }
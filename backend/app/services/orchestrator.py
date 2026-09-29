from __future__ import annotations

from typing import Any

from app.agents.billing_agent import BillingAgent
from app.agents.complaint_agent import ComplaintAgent
from app.agents.network_agent import NetworkAgent
from app.agents.support_agent import SupportAgent
from app.agent_config import get_agent_for_intent
from app.auth.permissions import can_use_tool
from app.services.audit_service import log_audit
from app.services.conversation_context import (
    ConversationContext,
    ConversationMessage,
    create_conversation,
    get_or_create_conversation,
    save_conversation,
)
from app.services.customer_service import get_customer
from app.services.intent_router import classify_intent
from app.services.language_detector import detect_language, is_mixed_language
from app.services.proactive_engagement import (
    should_make_proactive_offer,
    format_offer_message,
    claim_proactive_offer,
)
from app.services.responder import build_spoken_response, generate_greeting
from app.tools.complaint_tools import complaint_create
from app.tools.customer_tools import customer_lookup, data_balance_lookup, transaction_lookup
from app.tools.network_tools import network_diagnostic
from app.tools.remediation_tools import bundle_remediation


def _get_escalation_agent():
    from app.agents.escalation_agent import EscalationAgent
    return EscalationAgent()


AGENT_MAP = {
    "data_balance": "support_agent",
    "bundle_issue": "billing_agent",
    "network": "network_agent",
    "transaction": "billing_agent",
    "complaint": "complaint_agent",
    "greeting": "support_agent",
    "unknown": "support_agent",
}


TOOLS = {
    "customer_lookup": customer_lookup,
    "data_balance_lookup": data_balance_lookup,
    "transaction_lookup": transaction_lookup,
    "network_diagnostic": network_diagnostic,
    "complaint_create": complaint_create,
    "bundle_remediation": bundle_remediation,
}


def build_agent(agent_name: str):
    registry = {
        "support_agent": SupportAgent,
        "billing_agent": BillingAgent,
        "network_agent": NetworkAgent,
        "complaint_agent": ComplaintAgent,
    }
    agent_cls = registry.get(agent_name)
    if agent_cls is None:
        raise ValueError(f"Unknown agent: {agent_name}")
    return agent_cls(tool_registry=TOOLS)


def build_escalation_payload(
    phone: str,
    conversation_ref: str,
    reason: str,
    priority: str,
    attempted_tool: str,
    recommended_next_action: str,
    actor: str,
):
    escalation_agent = _get_escalation_agent()
    return escalation_agent.create_escalation(
        customer_phone=phone,
        conversation_ref=conversation_ref,
        reason=reason,
        priority=priority,
        ai_actions_attempted=[attempted_tool],
        recommended_next_action=recommended_next_action,
        attempted_tool=attempted_tool,
        actor=actor,
    )


def orchestrate_chat(
    phone: str,
    message: str,
    actor: str = "user",
    context: list[dict] | None = None,
    conversation_id: int | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    intent = classify_intent(message, context)
    agent_name = get_agent_for_intent(intent)
    agent = build_agent(agent_name)

    customer = get_customer(phone)
    if not customer:
        escalation = build_escalation_payload(
            phone,
            f"chat:{phone}:{message[:32]}",
            "customer_not_found",
            "HIGH",
            "customer_lookup",
            "Verify the customer record before proceeding.",
            actor,
        )
        audit = log_audit(
            actor=actor,
            agent=agent_name,
            tool="customer_lookup",
            action="customer_lookup",
            customer_phone=phone,
            status="failed",
            metadata={"message": message, "reason": "customer_not_found", "escalation_id": escalation["id"]},
        )
        return {
            "reply": "I could not verify that customer record.",
            "escalate": True,
            "intent": intent,
            "action": "customer_lookup",
            "audit": audit,
            "escalation": escalation,
        }

    customer_name = customer.get("name", "Customer")
    try:
        conversation = (
            get_or_create_conversation(phone, customer_name, "en", conversation_id=conversation_id)
            if conversation_id is not None
            else create_conversation(phone, customer_name, "en")
        )
    except ValueError:
        return {"error": "conversation_not_found", "reply": "Conversation not found for this customer."}
    
    is_first_message = len(conversation.messages) == 0
    conversation.interrupted = False
    conversation.customer_profile_snapshot = {
        "name": customer_name,
        "phone": phone,
    }
    
    detected_lang = detect_language(message)
    if detected_lang != conversation.language:
        conversation.language = detected_lang
    
    mixed = is_mixed_language(message)
    
    conversation.add_message(ConversationMessage(
        role="user",
        content=message,
        language=detected_lang,
        intent=intent,
    ))
    
    conversation_turn = len([m for m in conversation.messages if m.role == "user"])

    def check_authorization(tool_name: str) -> tuple[bool, dict | None]:
        if not can_use_tool(agent_name, tool_name):
            escalation = build_escalation_payload(
                phone,
                f"chat:{phone}:{message[:32]}",
                "insufficient_authorization",
                "HIGH" if tool_name != "network_diagnostic" else "MEDIUM",
                tool_name,
                f"Request human authorization before performing {tool_name}.",
                actor,
            )
            audit = log_audit(
                actor=actor,
                agent=agent_name,
                tool=tool_name,
                action="escalation",
                customer_phone=phone,
                status="failed",
                metadata={"intent": intent, "message": message, "reason": "insufficient_authorization", "escalation_id": escalation["id"]},
            )
            return False, {
                "reply": "I cannot perform this action under the current authorization scope. A human review is required.",
                "escalate": True,
                "intent": intent,
                "action": "escalation",
                "audit": audit,
                "escalation": escalation,
            }
        return True, None

    tool_result = None
    action = ""
    response = ""
    tool_name = ""

    if intent == "data_balance":
        tool_name = "data_balance_lookup"
        authorized, error = check_authorization(tool_name)
        if not authorized:
            return error
        tool_result = agent.call_tool(tool_name, phone=phone)
        action = "check_data_balance"

    elif intent == "bundle_issue":
        tool_name = "bundle_remediation"
        authorized, error = check_authorization(tool_name)
        if not authorized:
            return error
        tool_result = agent.call_tool(tool_name, phone=phone)
        action = "check_transaction_and_activation"

    elif intent == "network":
        tool_name = "network_diagnostic"
        authorized, error = check_authorization(tool_name)
        if not authorized:
            return error
        tool_result = agent.call_tool(tool_name, phone=phone)
        action = "network_diagnostic"

    elif intent == "transaction":
        tool_name = "transaction_lookup"
        authorized, error = check_authorization(tool_name)
        if not authorized:
            return error
        tool_result = agent.call_tool(tool_name, phone=phone)
        action = "get_transaction"

    elif intent == "complaint":
        tool_name = "complaint_create"
        authorized, error = check_authorization(tool_name)
        if not authorized:
            return error
        tool_result = agent.call_tool(tool_name, phone=phone, message=message)
        action = "complaint_intake"

    elif intent == "greeting":
        tool_name = "customer_lookup"
        authorized, error = check_authorization(tool_name)
        if not authorized:
            return error
        tool_result = agent.call_tool(tool_name, phone=phone)
        customer = tool_result.get("customer", {})
        customer_name = customer.get("name", "Customer")
        response = generate_greeting(customer_name, conversation.language, is_returning=not is_first_message)
        action = "greeting"

    else:
        escalation = build_escalation_payload(
            phone,
            f"chat:{phone}:{message[:32]}",
            "unknown_intent",
            "MEDIUM",
            "intent_router",
            "Route this request to a human specialist for manual handling.",
            actor,
        )
        response = "I'm LiveBox AI. I understand that this request is outside the current MVP toolset. I would route it for controlled handling rather than invent an answer."
        action = "unknown_intent"
        tool_name = "intent_router"
        tool_result = {"ok": True, "customer": {"phone": phone, **get_customer(phone)}}
        audit = log_audit(
            actor=actor,
            agent=agent_name,
            tool=tool_name,
            action="escalation",
            customer_phone=phone,
            status="escalated",
            metadata={"intent": intent, "message": message, "reason": "unknown_intent", "escalation_id": escalation["id"]},
        )
        conversation.add_message(ConversationMessage(
            role="assistant",
            content=response,
            language=conversation.language,
            intent=intent,
            tool_called=tool_name,
            tool_result=tool_result,
        ))
        save_conversation(conversation)
        return {
            "reply": response,
            "intent": intent,
            "action": action,
            "escalate": True,
            "audit": audit,
            "escalation": escalation,
            "conversation_id": conversation.conversation_id,
            "language": conversation.language,
        }

    proactive_offer = None
    if tool_result and tool_result.get("ok"):
        proactive_offer = should_make_proactive_offer(phone, intent, tool_result, conversation_turn)
        if proactive_offer and not claim_proactive_offer(phone, conversation.conversation_id, proactive_offer):
            proactive_offer = None
        if proactive_offer:
            offer_msg = format_offer_message(proactive_offer, conversation.language)
            response = build_spoken_response(
                language=conversation.language,
                intent=intent,
                tool_result=tool_result,
                customer_name=customer_name,
                is_first_message=is_first_message,
                proactive_offer=offer_msg,
            )
        else:
            response = build_spoken_response(
                language=conversation.language,
                intent=intent,
                tool_result=tool_result,
                customer_name=customer_name,
                is_first_message=is_first_message,
            )
    else:
        response = build_spoken_response(
            language=conversation.language,
            intent=intent,
            tool_result=tool_result,
            customer_name=customer_name,
            is_first_message=is_first_message,
        )

    conversation.add_message(ConversationMessage(
        role="assistant",
        content=response,
        language=conversation.language,
        intent=intent,
        tool_called=tool_name,
        tool_result=tool_result,
    ))

    audit = log_audit(
        actor=actor,
        agent=agent_name,
        tool=tool_name,
        action=action,
        customer_phone=phone,
        status="success" if intent != "unknown" else "escalated",
        metadata={"intent": intent, "message": message, "tool_result": tool_result, "language": conversation.language},
    )

    save_conversation(conversation)

    return {
        "reply": response,
        "intent": intent,
        "action": action,
        "escalate": intent == "unknown",
        "audit": audit,
        "conversation_id": conversation.conversation_id,
        "language": conversation.language,
        "proactive_offer": proactive_offer.id if proactive_offer else None,
    }


def orchestrate_voice(
    session_id: str,
    phone: str,
    speech_text: str,
    actor: str = "user",
) -> dict[str, Any]:
    from app.services.voice_session import get_voice_session, update_voice_session, VoiceSessionState
    from app.services.speech_io import SpeechIOManager

    session = get_voice_session(session_id)
    if not session:
        return {"error": "session_not_found", "reply": "Session not found."}

    if session.state == VoiceSessionState.ENDED:
        return {"error": "session_ended", "reply": "This call has ended."}

    if session.conversation:
        session.conversation.interrupted = False

    update_voice_session(session_id, state=VoiceSessionState.RESPONDING, is_speaking=False)
    
    result = orchestrate_chat(
        phone=phone,
        message=speech_text,
        actor=actor,
        conversation_id=session.conversation.conversation_id if session.conversation else None,
        session_id=session_id,
    )

    if result.get("error"):
        return result

    from app.services.conversation_context import load_conversation
    updated_conversation = load_conversation(result["conversation_id"])
    if updated_conversation:
        session.conversation = updated_conversation

    speech_io = SpeechIOManager(session_id)
    speech_output = speech_io.generate_speech_output(result["reply"], result.get("language", "en"))

    update_voice_session(session_id, state=VoiceSessionState.ACTIVE, current_response=result["reply"])

    return {
        "reply": result["reply"],
        "ssml": speech_output.ssml,
        "phonetic_markers": speech_output.phonetic_markers,
        "language": result.get("language", "en"),
        "intent": result.get("intent"),
        "action": result.get("action"),
        "escalate": result.get("escalate", False),
        "conversation_id": result.get("conversation_id"),
        "proactive_offer": result.get("proactive_offer"),
    }


def handle_barge_in(session_id: str) -> dict[str, Any]:
    from app.services.voice_session import handle_barge_in as handle_voice_barge_in

    return handle_voice_barge_in(session_id)

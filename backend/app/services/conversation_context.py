from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from app.db import get_db


@dataclass
class ConversationMessage:
    role: str
    content: str
    language: str = "en"
    intent: str | None = None
    tool_called: str | None = None
    tool_result: dict | None = None
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationMessage":
        return cls(**data)


@dataclass
class ConversationContext:
    conversation_id: int
    phone: str
    customer_name: str
    language: str = "en"
    messages: list[ConversationMessage] = field(default_factory=list)
    intent_history: list[str] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    customer_profile_snapshot: dict = field(default_factory=dict)
    active_tool: str | None = None
    interrupted: bool = False
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    def add_message(self, message: ConversationMessage) -> None:
        self.messages.append(message)
        self.updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if message.intent:
            self.intent_history.append(message.intent)
        if message.tool_called and message.tool_result:
            self.tool_results.append({
                "tool": message.tool_called,
                "result": message.tool_result,
                "timestamp": message.created,
            })

    def get_recent_messages(self, limit: int = 10) -> list[ConversationMessage]:
        return self.messages[-limit:]

    def get_context_summary(self) -> str:
        if not self.messages:
            return "New conversation"
        recent = self.get_recent_messages(5)
        parts = []
        for msg in recent:
            prefix = "Customer" if msg.role == "user" else "Assistant"
            parts.append(f"{prefix}: {msg.content[:100]}")
        return " | ".join(parts)

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "phone": self.phone,
            "customer_name": self.customer_name,
            "language": self.language,
            "messages": [m.to_dict() for m in self.messages],
            "intent_history": self.intent_history,
            "tool_results": self.tool_results,
            "customer_profile_snapshot": self.customer_profile_snapshot,
            "active_tool": self.active_tool,
            "interrupted": self.interrupted,
            "created": self.created,
            "updated": self.updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationContext":
        messages = [ConversationMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            conversation_id=data["conversation_id"],
            phone=data["phone"],
            customer_name=data["customer_name"],
            language=data.get("language", "en"),
            messages=messages,
            intent_history=data.get("intent_history", []),
            tool_results=data.get("tool_results", []),
            customer_profile_snapshot=data.get("customer_profile_snapshot", {}),
            active_tool=data.get("active_tool"),
            interrupted=data.get("interrupted", False),
            created=data.get("created", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            updated=data.get("updated", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
        )


def create_conversation(phone: str, customer_name: str, language: str = "en") -> ConversationContext:
    with get_db() as db:
        created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        cursor = db.execute(
            "INSERT INTO conversations(phone, created, updated, language, customer_name) VALUES (?, ?, ?, ?, ?)",
            (phone, created, created, language, customer_name),
        )
        conversation_id = cursor.lastrowid
    
    context = ConversationContext(
        conversation_id=conversation_id,
        phone=phone,
        customer_name=customer_name,
        language=language,
    )
    return context


def save_conversation(context: ConversationContext) -> None:
    with get_db() as db:
        db.execute(
            "UPDATE conversations SET updated = ?, language = ?, customer_name = ?, interrupted = ? WHERE id = ?",
            (context.updated, context.language, context.customer_name, int(context.interrupted), context.conversation_id),
        )
        for msg in context.messages:
            if msg.role in ("user", "assistant"):
                existing = db.execute(
                    "SELECT id FROM messages WHERE conversation_id = ? AND role = ? AND message = ? AND created = ?",
                    (context.conversation_id, msg.role, msg.content, msg.created),
                ).fetchone()
                if not existing:
                    db.execute(
                    "INSERT INTO messages(conversation_id, role, message, created, language, intent, tool_called, tool_result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (context.conversation_id, msg.role, msg.content, msg.created, msg.language, msg.intent, msg.tool_called,
                     json.dumps(msg.tool_result) if msg.tool_result is not None else None),
                    )


def load_conversation(conversation_id: int) -> ConversationContext | None:
    with get_db() as db:
        row = db.execute(
            "SELECT phone, created, updated, language, customer_name, interrupted FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        if not row:
            return None
        
        msg_rows = db.execute(
            "SELECT role, message, created, language, intent, tool_called, tool_result_json FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    
    messages = [
        ConversationMessage(
            role=row["role"], content=row["message"], created=row["created"], language=row["language"],
            intent=row["intent"], tool_called=row["tool_called"],
            tool_result=json.loads(row["tool_result_json"]) if row["tool_result_json"] else None,
        )
        for row in msg_rows
    ]
    
    context = ConversationContext(
        conversation_id=conversation_id,
        phone=row["phone"],
        customer_name=row["customer_name"],
        language=row["language"],
        created=row["created"],
        messages=messages,
        intent_history=[message.intent for message in messages if message.intent],
        tool_results=[
            {"tool": message.tool_called, "result": message.tool_result, "timestamp": message.created}
            for message in messages if message.tool_called and message.tool_result
        ],
        customer_profile_snapshot={"name": row["customer_name"], "phone": row["phone"]},
        interrupted=bool(row["interrupted"]),
        updated=row["updated"],
    )
    return context


def get_conversation_by_phone(phone: str) -> ConversationContext | None:
    with get_db() as db:
        row = db.execute(
            "SELECT id FROM conversations WHERE phone = ? ORDER BY updated DESC LIMIT 1",
            (phone,),
        ).fetchone()
        if not row:
            return None
        return load_conversation(row["id"])


def get_or_create_conversation(
    phone: str,
    customer_name: str,
    language: str = "en",
    conversation_id: int | None = None,
) -> ConversationContext:
    if conversation_id is not None:
        existing = load_conversation(conversation_id)
        if existing is None or existing.phone != phone:
            raise ValueError("Conversation not found for this customer")
    else:
        existing = get_conversation_by_phone(phone)
    if existing:
        if not existing.customer_name and customer_name:
            existing.customer_name = customer_name
        return existing
    return create_conversation(phone, customer_name, language)

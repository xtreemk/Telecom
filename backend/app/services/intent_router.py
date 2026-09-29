from __future__ import annotations

import re

def classify_intent(query: str, history: list[dict] | None = None) -> str:
    q = query.lower()
    if any(re.search(rf"\b{re.escape(x)}\b", q) for x in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings", "bawo", "sannu", "ndewo", "kedu"]):
        return "greeting"
    if "expiry" in q or "expire" in q:
        return "data_balance"
    if "what about" in q and "bundle" in q:
        return "data_balance"
    if any(x in q for x in ["data balance", "data left", "how much data", "balance"]):
        return "data_balance"
    if ("bought" in q or "purchase" in q or "bundle" in q) and ("data" in q or "not" in q or "missing" in q):
        return "bundle_issue"
    if any(x in q for x in ["internet", "network", "connection", "data no work", "matsala", "wahala"]):
        return "network"
    if any(x in q for x in ["transaction", "payment", "last payment", "recharge", "ego"]):
        return "transaction"
    if any(x in q for x in ["complaint", "complain", "report", "biko", "abeg"]):
        return "complaint"
    if history:
        previous_intents = [item.get("intent") for item in reversed(history) if item.get("role") == "assistant" and item.get("intent")]
        if previous_intents and any(x in q for x in ["what about", "how about", "and the", "expiry", "that"]):
            return previous_intents[0]
    return "unknown"

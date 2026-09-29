from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentConfig:
    name: str
    allowed_tools: list[str]
    description: str
    system_prompt: str
    supported_languages: list[str] = None
    
    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = ["en", "pid", "yo", "ha", "ig"]


AGENT_CONFIGS: dict[str, AgentConfig] = {
    "support_agent": AgentConfig(
        name="support_agent",
        allowed_tools=["customer_lookup", "data_balance_lookup", "transaction_lookup"],
        description="General customer support and data balance inquiries",
        system_prompt="You are a helpful telecom support assistant. You can check data balances, look up customer info, and view recent transactions.",
    ),
    "billing_agent": AgentConfig(
        name="billing_agent",
        allowed_tools=["customer_lookup", "transaction_lookup", "data_balance_lookup", "bundle_remediation"],
        description="Billing, transactions, and bundle management",
        system_prompt="You are a billing specialist. You can check transactions, apply bundle remediations, and view data balances.",
    ),
    "network_agent": AgentConfig(
        name="network_agent",
        allowed_tools=["customer_lookup", "network_diagnostic"],
        description="Network troubleshooting and diagnostics",
        system_prompt="You are a network specialist. You can run network diagnostics and check customer connectivity status.",
    ),
    "complaint_agent": AgentConfig(
        name="complaint_agent",
        allowed_tools=["customer_lookup", "complaint_create"],
        description="Complaint intake and ticketing",
        system_prompt="You are a complaint specialist. You can create complaint tickets with full context.",
    ),
    "escalation_agent": AgentConfig(
        name="escalation_agent",
        allowed_tools=["escalation_create"],
        description="Human escalation for complex cases",
        system_prompt="You handle escalations to human agents when AI cannot resolve the issue.",
    ),
    "reporting_agent": AgentConfig(
        name="reporting_agent",
        allowed_tools=[],
        description="Operational reporting and analytics",
        system_prompt="You provide operational reports and analytics.",
    ),
}


INTENT_AGENT_MAP: dict[str, str] = {
    "data_balance": "support_agent",
    "bundle_issue": "billing_agent",
    "network": "network_agent",
    "transaction": "billing_agent",
    "complaint": "complaint_agent",
    "unknown": "support_agent",
}


CONSENT_RULES = {
    "marketing_consent_required": True,
    "proactive_offers_enabled": True,
    "opt_in_by_default": False,
    "consent_per_channel": {
        "voice": True,
        "chat": True,
        "sms": False,
        "email": False,
    },
    "offer_frequency_limit": {
        "max_per_session": 1,
        "max_per_day": 3,
        "cooldown_hours": 4,
    },
}


LANGUAGE_CONFIG = {
    "en": {
        "name": "English",
        "native_name": "English",
        "voice": "en-US",
        "tts_voice": "en-US-Neural",
        "direction": "ltr",
    },
    "pid": {
        "name": "Nigerian Pidgin",
        "native_name": "Naija",
        "voice": "en-NG",
        "tts_voice": "en-NG-Neural",
        "direction": "ltr",
    },
    "yo": {
        "name": "Yoruba",
        "native_name": "Yorùbá",
        "voice": "yo-NG",
        "tts_voice": "yo-NG-Neural",
        "direction": "ltr",
    },
    "ha": {
        "name": "Hausa",
        "native_name": "Hausa",
        "voice": "ha-NG",
        "tts_voice": "ha-NG-Neural",
        "direction": "ltr",
    },
    "ig": {
        "name": "Igbo",
        "native_name": "Igbo",
        "voice": "ig-NG",
        "tts_voice": "ig-NG-Neural",
        "direction": "ltr",
    },
}


TOOL_DESCRIPTIONS = {
    "customer_lookup": "Look up customer profile by phone number",
    "data_balance_lookup": "Check customer's current data balance and bundle info",
    "transaction_lookup": "View customer's most recent transaction",
    "network_diagnostic": "Run network diagnostic for customer's area",
    "complaint_create": "Create a complaint ticket with customer's message",
    "bundle_remediation": "Apply bundle remediation for pending activations",
    "escalation_create": "Create escalation to human agent",
}


def get_agent_config(agent_name: str) -> AgentConfig | None:
    return AGENT_CONFIGS.get(agent_name)


def get_agent_for_intent(intent: str) -> str:
    return INTENT_AGENT_MAP.get(intent, "support_agent")


def get_supported_languages() -> list[str]:
    return list(LANGUAGE_CONFIG.keys())


def get_language_config(lang_code: str) -> dict | None:
    return LANGUAGE_CONFIG.get(lang_code)


def get_tool_description(tool_name: str) -> str:
    return TOOL_DESCRIPTIONS.get(tool_name, "")
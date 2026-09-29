from __future__ import annotations

from typing import Iterable

PERMISSIONS = {
    "support_agent": {
        "customer_lookup",
        "data_balance_lookup",
        "transaction_lookup",
    },
    "billing_agent": {
        "customer_lookup",
        "transaction_lookup",
        "data_balance_lookup",
        "bundle_remediation",
    },
    "network_agent": {
        "customer_lookup",
        "network_diagnostic",
    },
    "complaint_agent": {
        "customer_lookup",
        "complaint_create",
    },
    "admin": {
        "customer_lookup",
        "data_balance_lookup",
        "transaction_lookup",
        "network_diagnostic",
        "complaint_create",
        "bundle_remediation",
    },
}


def can_use_tool(agent_name: str, tool_name: str) -> bool:
    return tool_name in PERMISSIONS.get(agent_name, set())


def get_allowed_tools(agent_name: str) -> Iterable[str]:
    return sorted(PERMISSIONS.get(agent_name, set()))

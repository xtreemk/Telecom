from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.auth.permissions import PERMISSIONS


class BillingAgent(BaseAgent):
    name = "billing_agent"
    allowed_tools = PERMISSIONS["billing_agent"]

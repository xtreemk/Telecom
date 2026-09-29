from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.auth.permissions import PERMISSIONS


class SupportAgent(BaseAgent):
    name = "support_agent"
    allowed_tools = PERMISSIONS["support_agent"]

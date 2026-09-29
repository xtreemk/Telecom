from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.auth.permissions import PERMISSIONS


class NetworkAgent(BaseAgent):
    name = "network_agent"
    allowed_tools = PERMISSIONS["network_agent"]

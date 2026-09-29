from __future__ import annotations

from app.agents.base_agent import BaseAgent
from app.auth.permissions import PERMISSIONS


class ComplaintAgent(BaseAgent):
    name = "complaint_agent"
    allowed_tools = PERMISSIONS["complaint_agent"]

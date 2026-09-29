from __future__ import annotations

from typing import Any


class BaseAgent:
    name: str = "base_agent"
    allowed_tools: set[str] | None = None

    def __init__(self, tool_registry: dict[str, Any] | None = None):
        self.tool_registry = tool_registry or {}

    def can_use(self, tool_name: str) -> bool:
        if self.allowed_tools is None:
            return True
        return tool_name in self.allowed_tools

    def call_tool(self, tool_name: str, **kwargs):
        if not self.can_use(tool_name):
            raise PermissionError(f"Agent '{self.name}' is not allowed to call tool '{tool_name}'.")
        if tool_name not in self.tool_registry:
            raise KeyError(f"Unknown tool '{tool_name}'.")
        return self.tool_registry[tool_name](**kwargs)

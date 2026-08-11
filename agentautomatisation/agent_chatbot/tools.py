from __future__ import annotations

from smolagents import DuckDuckGoSearchTool

from agentautomatisation.toolss import SendMail


def build_chatbot_tools():
    return [DuckDuckGoSearchTool()]


__all__ = ["SendMail", "build_chatbot_tools"]

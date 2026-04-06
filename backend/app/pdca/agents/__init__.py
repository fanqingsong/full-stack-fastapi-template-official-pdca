"""Agent executors for PDCA workflow management."""

from .base import BaseAgentExecutor
from .openai_agent import OpenAIAgentExecutor
from .registry import AgentRegistry

# Register OpenAI agent
AgentRegistry.register("openai")(OpenAIAgentExecutor)

__all__ = ["BaseAgentExecutor", "AgentRegistry", "OpenAIAgentExecutor"]
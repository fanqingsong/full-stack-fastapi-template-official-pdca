"""Agent executors for PDCA workflow management."""
from .base import BaseAgentExecutor
from .openai_agent import OpenAIAgentExecutor
from .zhipu_agent import ZhipuAIAgentExecutor
from .registry import AgentRegistry

# Register OpenAI agent
AgentRegistry.register("openai")(OpenAIAgentExecutor)

# Register Zhipu AI (GLM) agent
AgentRegistry.register("zhipu")(ZhipuAIAgentExecutor)

__all__ = ["BaseAgentExecutor", "AgentRegistry", "OpenAIAgentExecutor", "ZhipuAIAgentExecutor"]

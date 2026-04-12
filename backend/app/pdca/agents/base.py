"""Base agent executor abstract class."""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.core.metrics import (
    ai_requests_total,
    ai_request_duration_seconds,
    ai_tokens_used_total,
    ai_cost_usd_total,
)


class BaseAgentExecutor(ABC):
    """Abstract base class for all agent executors."""

    def __init__(self, provider: str, model: str):
        """
        Initialize base agent.

        Args:
            provider: AI provider name (e.g., 'openai', 'zhipu')
            model: Model name (e.g., 'gpt-4', 'glm-4')
        """
        self.provider = provider
        self.model = model

    def _record_ai_metrics(
        self,
        status: str,
        duration: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost_usd: float = 0.0
    ):
        """
        Record AI agent metrics.

        Args:
            status: Request status ('success' or 'error')
            duration: Request duration in seconds
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            cost_usd: Estimated cost in USD
        """
        try:
            ai_requests_total.labels(
                provider=self.provider,
                model=self.model,
                status=status
            ).inc()

            ai_request_duration_seconds.labels(
                provider=self.provider,
                model=self.model
            ).observe(duration)

            if prompt_tokens > 0:
                ai_tokens_used_total.labels(
                    provider=self.provider,
                    model=self.model,
                    type='prompt'
                ).inc(prompt_tokens)

            if completion_tokens > 0:
                ai_tokens_used_total.labels(
                    provider=self.provider,
                    model=self.model,
                    type='completion'
                ).inc(completion_tokens)

            if cost_usd > 0:
                ai_cost_usd_total.labels(
                    provider=self.provider,
                    model=self.model
                ).inc(cost_usd)

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to record AI metric: {e}")

    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an agent task with the given context.

        Args:
            task: The task description or prompt to execute
            context: Optional context dictionary containing additional information

        Returns:
            Dictionary containing the execution results
        """
        pass

    @abstractmethod
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate the input parameters for the agent executor.

        Args:
            task: The task description or prompt to validate
            context: Optional context dictionary to validate

        Returns:
            True if input is valid, False otherwise
        """
        pass
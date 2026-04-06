"""OpenAI Agent Executor implementation."""

import logging
from typing import Any, Dict, Optional

from openai import AsyncOpenAI
from openai import OpenAIError

from ..core.config import settings
from .base import BaseAgentExecutor

logger = logging.getLogger(__name__)


class OpenAIAgentExecutor(BaseAgentExecutor):
    """OpenAI agent executor that calls OpenAI's chat completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the OpenAI agent executor.

        Args:
            api_key: OpenAI API key. If None, uses settings.OPENAI_API_KEY
            model: Model name. If None, uses settings.OPENAI_MODEL
            max_tokens: Maximum tokens. If None, uses settings.OPENAI_MAX_TOKENS
            temperature: Temperature. If None, uses settings.OPENAI_TEMPERATURE
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
        self.temperature = temperature or settings.OPENAI_TEMPERATURE

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = AsyncOpenAI(api_key=self.api_key)

    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate the input parameters for the OpenAI agent executor.

        Args:
            task: The task description or prompt to validate
            context: Optional context dictionary to validate

        Returns:
            True if input is valid, False otherwise
        """
        if not task or not isinstance(task, str) or not task.strip():
            return False

        if context is not None and not isinstance(context, dict):
            return False

        return True

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an agent task with the given context using OpenAI API.

        Args:
            task: The task description or prompt to execute
            context: Optional context dictionary containing additional information

        Returns:
            Dictionary containing the execution results
        """
        if not self.validate_input(task, context):
            return {
                "status": "error",
                "error": "Invalid input: task must be a non-empty string",
                "output": None,
                "usage": None
            }

        try:
            # Prepare messages
            messages = [{"role": "user", "content": task}]

            # Add context if provided
            if context:
                context_message = f"Context information:\n{context}"
                messages.insert(-1, {"role": "system", "content": context_message})

            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # Extract response
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            return {
                "status": "success",
                "output": content,
                "error": None,
                "usage": usage
            }

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": f"OpenAI API error: {str(e)}",
                "usage": None
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": f"Unexpected error: {str(e)}",
                "usage": None
            }
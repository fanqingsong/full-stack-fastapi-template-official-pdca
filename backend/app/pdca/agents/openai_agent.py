"""OpenAI Agent Executor implementation."""

import logging
import time
from typing import Any, Dict, Optional

from openai import AsyncOpenAI
from openai import OpenAIError

from app.core.config import settings
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

        Raises:
            ValueError: If api_key is missing or if parameters are invalid
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS
        self.temperature = temperature or settings.OPENAI_TEMPERATURE

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Validate temperature (must be between 0 and 2)
        if not 0 <= self.temperature <= 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")

        # Validate max_tokens (must be positive)
        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")

        self.client = AsyncOpenAI(api_key=self.api_key)

        # Initialize base agent
        super().__init__(provider='openai', model=self.model)

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
        start_time = time.time()
        status = 'success'
        prompt_tokens = 0
        completion_tokens = 0
        cost_usd = 0.0

        if not self.validate_input(task, context):
            status = 'error'
            return {
                "status": "error",
                "error": "Invalid input: task must be a non-empty string and context must be a dictionary if provided",
                "output": None,
                "usage": None
            }

        try:
            # Prepare messages
            messages = []

            # Add context if provided (system message first)
            if context:
                context_message = f"Context information:\n{context}"
                messages.append({"role": "system", "content": context_message})

            # Add user task message
            messages.append({"role": "user", "content": task})

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

            # Extract token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            # Estimate cost (GPT-4 pricing as of 2024)
            if self.model.startswith('gpt-4'):
                cost_usd = (prompt_tokens * 0.00003 + completion_tokens * 0.00006)

            return {
                "status": "success",
                "output": content,
                "error": None,
                "usage": usage
            }

        except OpenAIError as e:
            status = 'error'
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": f"OpenAI API error: {str(e)}",
                "usage": None
            }
        except Exception as e:
            status = 'error'
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": f"Unexpected error: {str(e)}",
                "usage": None
            }
        finally:
            duration = time.time() - start_time
            self._record_ai_metrics(
                status=status,
                duration=duration,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd
            )
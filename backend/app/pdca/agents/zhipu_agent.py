"""Zhipu AI (GLM) Agent Executor implementation.

This agent uses Zhipu AI's API for chat completions.
Zhipu API Documentation: https://open.bigmodel.cn/dev/api#chat
"""
import logging
import time
from typing import Any, Dict, Optional
from datetime import datetime

from zhipuai import ZhipuAI
from app.core.config import settings
from .base import BaseAgentExecutor


logger = logging.getLogger(__name__)


class ZhipuAIAgentExecutor(BaseAgentExecutor):
    """Zhipu AI agent executor that calls Zhipu AI's API for chat completions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """Initialize Zhipu AI agent executor.

        Args:
            api_key: Zhipu AI API key. If None, uses settings.ZHIPU_API_KEY
            model: Model name. If None, uses settings.ZHIPU_MODEL
            max_tokens: Maximum tokens. If None, uses settings.ZHIPU_MAX_TOKENS
            temperature: Temperature. If None, uses settings.ZHIPU_TEMPERATURE

        Raises:
            ValueError: If api_key is missing or if parameters are invalid
        """
        self.api_key = api_key or settings.ZHIPU_API_KEY
        self.model = model or settings.ZHIPU_MODEL
        self.max_tokens = max_tokens or settings.ZHIPU_MAX_TOKENS
        self.temperature = temperature or settings.ZHIPU_TEMPERATURE

        # Validate parameters
        if not self.api_key:
            raise ValueError("Zhipu AI API key is required")

        # Validate temperature (must be between 0 and 2)
        if not 0 <= self.temperature <= 2:
            raise ValueError(f"Temperature must be between 0 and 2, got {self.temperature}")

        # Validate max_tokens (must be positive)
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")

        # Initialize Zhipu AI client
        self.client = ZhipuAI(api_key=self.api_key)

        # Initialize base agent
        super().__init__(provider='zhipu', model=self.model)
    
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate input parameters for Zhipu AI agent executor.
        
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
        """Execute an agent task with given context using Zhipu AI API.

        Args:
            task: The task description or prompt to execute
            context: Optional context dictionary containing additional information

        Returns:
            Dictionary containing execution results
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
            response = await self.client.chat.completions_async(
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

            # Estimate cost (GLM-4 pricing approximation)
            cost_usd = (prompt_tokens + completion_tokens) * 0.00001

            return {
                "status": "success",
                "output": content,
                "error": None,
                "usage": usage
            }

        except Exception as e:
            status = 'error'
            logger.error(f"Zhipu AI API error: {str(e)}")
            return {
                "status": "error",
                "output": None,
                "error": f"Zhipu AI API error: {str(e)}",
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

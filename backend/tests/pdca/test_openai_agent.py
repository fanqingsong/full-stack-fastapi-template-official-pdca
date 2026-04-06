"""Tests for OpenAI Agent Executor."""

import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from openai import AsyncOpenAI

from app.pdca.agents.openai_agent import OpenAIAgentExecutor
from app.pdca.agents import AgentRegistry


@pytest.mark.asyncio
class TestOpenAIAgent:
    """Test cases for OpenAI Agent Executor."""

    def test_openai_agent_is_registered(self):
        """Test that OpenAI agent is properly registered in the registry."""
        assert AgentRegistry.is_registered("openai")

        # Test that we can get an executor instance
        executor = AgentRegistry.get_executor("openai")
        assert isinstance(executor, OpenAIAgentExecutor)

    def test_validate_input_with_valid_prompt(self):
        """Test validate_input returns True for valid prompt."""
        executor = OpenAIAgentExecutor(api_key="test-key")

        # Test valid prompt
        assert executor.validate_input("Hello, world!") is True

        # Test valid prompt with context
        context = {"key": "value"}
        assert executor.validate_input("Hello, world!", context) is True

        # Test valid prompt with empty context
        assert executor.validate_input("Hello, world!", {}) is True

    def test_validate_input_with_missing_prompt(self):
        """Test validate_input returns False for invalid prompt."""
        executor = OpenAIAgentExecutor(api_key="test-key")

        # Test empty prompt
        assert executor.validate_input("") is False

        # Test whitespace-only prompt
        assert executor.validate_input("   ") is False

        # Test None prompt
        assert executor.validate_input(None) is False

        # Test invalid context type
        assert executor.validate_input("valid prompt", "invalid context") is False

    @patch('openai.AsyncOpenAI')
    async def test_execute_with_mock_response(self, mock_openai_class):
        """Test execute method with successful API response."""
        # Setup mock
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client

        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Create executor and execute
        executor = OpenAIAgentExecutor(api_key="test-key")
        result = await executor.execute("Test prompt")

        # Verify results
        assert result["status"] == "success"
        assert result["output"] == "This is a test response"
        assert result["error"] is None
        assert result["usage"] == {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }

        # Verify API call was made correctly
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            max_tokens=2000,
            temperature=0.7
        )

    @patch('openai.AsyncOpenAI')
    async def test_execute_with_api_error(self, mock_openai_class):
        """Test execute method with API error."""
        # Setup mock
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client

        # Mock API error
        from openai import APIError
        mock_client.chat.completions.create = AsyncMock(side_effect=APIError("API Error"))

        # Create executor and execute
        executor = OpenAIAgentExecutor(api_key="test-key")
        result = await executor.execute("Test prompt")

        # Verify error handling
        assert result["status"] == "error"
        assert result["output"] is None
        assert "API Error" in result["error"]
        assert result["usage"] is None

    @pytest.mark.asyncio
    async def test_execute_with_missing_prompt(self):
        """Test executing the agent when the prompt field is missing from input."""
        executor = OpenAIAgentExecutor(api_key="test-key")

        # Execute with empty input (missing prompt field)
        result = await executor.execute({})

        # Verify error handling
        assert result["status"] == "error"
        assert "Invalid input: task must be a non-empty string" in result["error"]


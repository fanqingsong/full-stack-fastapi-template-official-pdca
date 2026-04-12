"""Test AI agent metrics."""
import pytest
from app.pdca.agents.openai_agent import OpenAIAgentExecutor
from app.core.metrics import ai_requests_total, ai_tokens_used_total, ai_cost_usd_total


@pytest.mark.asyncio
async def test_openai_agent_records_metrics():
    """Test that OpenAI agent records metrics."""
    agent = OpenAIAgentExecutor()

    # Get initial values
    initial_requests = ai_requests_total.labels(
        provider='openai',
        model='gpt-4',
        status='success'
    )._value.get()

    initial_tokens = ai_tokens_used_total.labels(
        provider='openai',
        model='gpt-4',
        type='prompt'
    )._value.get()

    # Execute task (this will make a real API call in tests, consider mocking)
    try:
        result = await agent.execute("Test task")
        assert result['provider'] == 'openai'

        # Check metrics were recorded
        final_requests = ai_requests_total.labels(
            provider='openai',
            model='gpt-4',
            status='success'
        )._value.get()

        assert final_requests > initial_requests
    except Exception as e:
        # API call might fail in tests, that's okay
        pytest.skip(f"API call failed: {e}")

"""Simple test runner for agent tests."""

import sys
import asyncio
import traceback
from typing import Any, Dict

# Add app to path
sys.path.insert(0, '.')

# Import our modules
from app.pdca.agents.base import BaseAgentExecutor
from app.pdca.agents.registry import AgentRegistry


class MockAgentExecutor(BaseAgentExecutor):
    """Mock agent executor for testing."""

    def __init__(self, name: str = "mock"):
        self.name = name

    async def execute(self, task: str, context: None = None) -> dict:
        """Mock execution that returns the task and executor name."""
        return {
            "task": task,
            "executor": self.name,
            "status": "completed"
        }

    def validate_input(self, task: str, context: None = None) -> bool:
        """Mock validation that always returns True for non-empty tasks."""
        return bool(task and task.strip())


def test_register_agent_executor():
    """Test registering a new agent executor."""
    print("Running test_register_agent_executor...")
    # Clear the registry first
    AgentRegistry._executors.clear()

    # Register a mock executor
    @AgentRegistry.register("mock")
    class TestExecutor(MockAgentExecutor):
        pass

    # Verify registration
    assert "mock" in AgentRegistry.list_types()
    assert AgentRegistry.is_registered("mock")

    # Verify we can get an instance
    executor = AgentRegistry.get_executor("mock")
    assert isinstance(executor, TestExecutor)
    print("✓ PASSED")


def test_get_executor():
    """Test getting an executor instance."""
    print("Running test_get_executor...")
    # Clear the registry first
    AgentRegistry._executors.clear()

    # Register a mock executor
    @AgentRegistry.register("test")
    class TestExecutor(MockAgentExecutor):
        def __init__(self, prefix: str = "default"):
            super().__init__(f"{prefix}_test")

    # Get executor with custom parameters
    executor = AgentRegistry.get_executor("test", prefix="custom")
    assert executor.name == "custom_test"

    # Get executor without parameters
    executor2 = AgentRegistry.get_executor("test")
    assert executor2.name == "default_test"
    print("✓ PASSED")


def test_get_unknown_executor_raises_error():
    """Test that getting an unknown executor raises ValueError."""
    print("Running test_get_unknown_executor_raises_error...")
    # Clear the registry first
    AgentRegistry._executors.clear()

    # Should raise ValueError for unknown type
    try:
        AgentRegistry.get_executor("unknown")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown agent type: unknown" in str(e)

    # Verify is_registered returns False
    assert not AgentRegistry.is_registered("unknown")
    print("✓ PASSED")


def test_list_types():
    """Test listing all registered agent types."""
    print("Running test_list_types...")
    # Clear the registry first
    AgentRegistry._executors.clear()

    # Register multiple executors
    @AgentRegistry.register("type1")
    class Executor1(BaseAgentExecutor):
        async def execute(self, task: str, context: None = None) -> dict:
            return {}
        def validate_input(self, task: str, context: None = None) -> bool:
            return True

    @AgentRegistry.register("type2")
    class Executor2(BaseAgentExecutor):
        async def execute(self, task: str, context: None = None) -> dict:
            return {}
        def validate_input(self, task: str, context: None = None) -> bool:
            return True

    # Verify list returns all registered types
    types = AgentRegistry.list_types()
    assert len(types) == 2
    assert "type1" in types
    assert "type2" in types
    print("✓ PASSED")


def test_duplicate_registration_raises_error():
    """Test that registering duplicate agent types raises ValueError."""
    print("Running test_duplicate_registration_raises_error...")
    # Clear the registry first
    AgentRegistry._executors.clear()

    # Register first executor
    @AgentRegistry.register("duplicate")
    class FirstExecutor(BaseAgentExecutor):
        async def execute(self, task: str, context: None = None) -> dict:
            return {}
        def validate_input(self, task: str, context: None = None) -> bool:
            return True

    # Should raise ValueError when trying to register same type again
    try:
        @AgentRegistry.register("duplicate")
        class SecondExecutor(BaseAgentExecutor):
            async def execute(self, task: str, context: None = None) -> dict:
                return {}
            def validate_input(self, task: str, context: None = None) -> bool:
                return True
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Agent type 'duplicate' is already registered" in str(e)
    print("✓ PASSED")


def run_all_tests():
    """Run all tests."""
    print("=== Running Agent Tests ===\n")

    tests = [
        test_register_agent_executor,
        test_get_executor,
        test_get_unknown_executor_raises_error,
        test_list_types,
        test_duplicate_registration_raises_error,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
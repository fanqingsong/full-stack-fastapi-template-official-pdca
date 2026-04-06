"""Tests for agent executors and registry."""

import pytest
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


class TestAgentRegistry:
    """Test suite for AgentRegistry."""
    
    def test_register_agent_executor(self):
        """Test registering a new agent executor."""
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
    
    def test_get_executor(self):
        """Test getting an executor instance."""
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
    
    def test_get_unknown_executor_raises_error(self):
        """Test that getting an unknown executor raises ValueError."""
        # Clear the registry first
        AgentRegistry._executors.clear()
        
        # Should raise ValueError for unknown type
        with pytest.raises(ValueError, match="Unknown agent type: unknown"):
            AgentRegistry.get_executor("unknown")
        
        # Verify is_registered returns False
        assert not AgentRegistry.is_registered("unknown")
    
    def test_list_types(self):
        """Test listing all registered agent types."""
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
    
    def test_duplicate_registration_raises_error(self):
        """Test that registering duplicate agent types raises ValueError."""
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
        with pytest.raises(ValueError, match="Agent type 'duplicate' is already registered"):
            
            @AgentRegistry.register("duplicate")
            class SecondExecutor(BaseAgentExecutor):
                async def execute(self, task: str, context: None = None) -> dict:
                    return {}
                def validate_input(self, task: str, context: None = None) -> bool:
                    return True
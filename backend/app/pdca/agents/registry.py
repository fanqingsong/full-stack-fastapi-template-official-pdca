"""Agent registry for managing agent executor types."""

from typing import Dict, Type, Any
from .base import BaseAgentExecutor


class AgentRegistry:
    """Registry for managing agent executor types."""

    _executors: Dict[str, Type[BaseAgentExecutor]] = {}

    @classmethod
    def register(cls, agent_type: str) -> callable:
        """
        Decorator to register a new agent executor type.
        
        Args:
            agent_type: The type identifier for the agent
            
        Returns:
            Decorator function
        """
        def decorator(executor_class: Type[BaseAgentExecutor]) -> Type[BaseAgentExecutor]:
            if not issubclass(executor_class, BaseAgentExecutor):
                raise TypeError(f"Executor class must inherit from BaseAgentExecutor")
            if agent_type in cls._executors:
                raise ValueError(f"Agent type '{agent_type}' is already registered")
            
            cls._executors[agent_type] = executor_class
            return executor_class
        
        return decorator

    @classmethod
    def get_executor(cls, agent_type: str, **kwargs: Any) -> BaseAgentExecutor:
        """
        Get an executor instance for the specified agent type.
        
        Args:
            agent_type: The type identifier for the agent
            **kwargs: Additional arguments to pass to the executor constructor
            
        Returns:
            Instance of the requested executor
            
        Raises:
            ValueError: If the agent type is not registered
        """
        if agent_type not in cls._executors:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        executor_class = cls._executors[agent_type]
        return executor_class(**kwargs)

    @classmethod
    def list_types(cls) -> list[str]:
        """
        List all registered agent types.
        
        Returns:
            List of registered agent type identifiers
        """
        return list(cls._executors.keys())

    @classmethod
    def is_registered(cls, agent_type: str) -> bool:
        """
        Check if an agent type is registered.
        
        Args:
            agent_type: The type identifier to check
            
        Returns:
            True if the type is registered, False otherwise
        """
        return agent_type in cls._executors
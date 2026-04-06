"""Base agent executor abstract class."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgentExecutor(ABC):
    """Abstract base class for all agent executors."""

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
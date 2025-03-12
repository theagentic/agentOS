"""
Base class for all agents.

This provides common functionality that all agents can inherit from.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

class AgentBase:
    """Base class that all agents should inherit from."""
    
    def __init__(self, agent_name: str = "base", config: Optional[Dict[str, Any]] = None):
        """Initialize the agent with optional configuration."""
        self.agent_name = agent_name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # Load agent-specific .env file if it exists
        self._load_env_file()
        
    def _load_env_file(self):
        """Load agent-specific environment variables from .env file."""
        # Get the agent's directory path
        agent_file = os.path.abspath(self.__class__.__module__.replace('.', os.sep) + '.py')
        agent_dir = os.path.dirname(agent_file)
        
        # If we're in an agent directory
        if '/agents/' in agent_dir.replace('\\', '/') or '\\agents\\' in agent_dir:
            env_file = os.path.join(agent_dir, '.env')
            if os.path.exists(env_file):
                self.logger.info(f"Loading environment from {env_file}")
                load_dotenv(dotenv_path=env_file, override=True)
                return True
        
        return False
        
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and return results.
        
        Args:
            user_input: The command or query from the user
            
        Returns:
            A dictionary containing results and metadata
        """
        # Default implementation - should be overridden by subclasses
        return {
            "status": "error",
            "message": "This method should be implemented by subclasses",
            "spoke": "I'm not sure how to handle that request."
        }
    
    def get_capabilities(self) -> List[str]:
        """Return a list of this agent's capabilities."""
        return ["Base agent has no capabilities"]
    
    def summarize_result(self, result: Dict[str, Any]) -> str:
        """
        Generate a user-friendly summary of the results.
        
        Args:
            result: The result dictionary from process()
            
        Returns:
            A string summary of the results
        """
        if result.get("status") == "success":
            return result.get("message", "Operation completed successfully.")
        else:
            return result.get("message", "Operation failed.")
    
    def status_update(self, message: str) -> None:
        """Log a status update message."""
        self.logger.info(message)

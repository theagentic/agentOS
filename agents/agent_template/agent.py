"""
Agent Template

This is a template for creating new agents in the AgentOS system.
Copy this directory and customize it for your specific agent functionality.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from core.agent_base import AgentBase  # This import is now correct

class TemplateAgent(AgentBase):
    """Template for creating new agents."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the agent."""
        super().__init__("template", config)
        
        # Load environment variables specific to this agent
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path=env_path)
        
        # Initialize agent-specific variables
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        
        # Initialize any required services or connections
        # self._connect_to_service()
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and return results.
        
        Args:
            user_input: The command or query from the user
            
        Returns:
            A dictionary containing results and metadata
        """
        self.status_update(f"Processing command: {user_input}")
        
        # TODO: Implement your agent's logic here
        # This is where you parse the user's request and execute the appropriate action
        
        try:
            # Example implementation (replace with your own logic):
            if "help" in user_input.lower():
                return self._handle_help_command()
            elif "status" in user_input.lower():
                return self._handle_status_command()
            else:
                # Default handling for unknown commands
                return {
                    "status": "success",
                    "message": f"Processed: {user_input}",
                    "data": {},
                    "spoke": "I've processed your request."
                }
                
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "spoke": "Sorry, I encountered an error while processing your request."
            }
    
    def get_capabilities(self) -> List[str]:
        """Return a list of this agent's capabilities."""
        return [
            "Example capability 1",
            "Example capability 2",
            "Example capability 3"
        ]
    
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
    
    # Example helper methods (replace with your own):
    
    def _handle_help_command(self) -> Dict[str, Any]:
        """Handle the help command."""
        help_text = """
        Template Agent Help:
        
        - Command 1: Description of command 1
        - Command 2: Description of command 2
        - Command 3: Description of command 3
        """
        
        return {
            "status": "success",
            "message": help_text,
            "data": {"commands": ["Command 1", "Command 2", "Command 3"]},
            "spoke": "Here are the commands I understand."
        }
    
    def _handle_status_command(self) -> Dict[str, Any]:
        """Handle the status command."""
        return {
            "status": "success",
            "message": "The agent is running normally.",
            "data": {"status": "operational"},
            "spoke": "I'm up and running normally."
        }

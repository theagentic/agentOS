from core.agent_base import AgentBase
import os
import logging
from typing import Dict, Any, List, Optional
from .todoist_agent import TodoistAgent

class DatetimeAgent(AgentBase):
    """Agent that handles date, time, tasks, and calendar functions."""
    
    def __init__(self):
        """Initialize the datetime agent and its sub-agents."""
        super().__init__()
        self.agent_id = "datetime"
        self.logger = logging.getLogger("agent.datetime")
        
        # Initialize sub-agents
        try:
            self.todoist_agent = TodoistAgent()
            self.logger.info("Todoist agent initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Todoist agent: {e}")
            self.todoist_agent = None
    
    def process(self, command: str) -> Dict[str, Any]:
        """
        Process commands related to date, time, tasks, and calendar.
        
        Args:
            command: The command to process
            
        Returns:
            Response dictionary
        """
        command_lower = command.lower()
        
        # Task-related commands go to Todoist agent
        if any(kw in command_lower for kw in ["task", "todo", "reminder", "add", "list", "show"]):
            if self.todoist_agent:
                self.logger.info(f"Delegating to Todoist agent: {command}")
                return self.todoist_agent.process(command)
            else:
                return {
                    "status": "error",
                    "message": "Todoist agent is not available. Please check your API credentials.",
                    "spoke": "I couldn't process your task because the Todoist integration is not configured correctly."
                }
        
        # Time and date commands
        if command_lower.startswith("time"):
            return self._handle_time()
        
        if command_lower.startswith("date"):
            return self._handle_date()
            
        if command_lower.startswith("weather"):
            return self._handle_weather()
            
        # Help command
        if command_lower.startswith("help"):
            return self._handle_help()
            
        # Default response for unrecognized commands
        return {
            "status": "error",
            "message": "Unrecognized datetime command. Try 'datetime help' for available commands.",
            "spoke": "I'm not sure what you want me to do with that datetime command. Try asking for 'datetime help'."
        }
    
    def _handle_time(self) -> Dict[str, Any]:
        """Handle time-related commands."""
        import datetime
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        return {
            "status": "success",
            "message": f"Current time: {time_str}",
            "spoke": f"The current time is {time_str}.",
            "data": {
                "time": time_str,
                "hour": now.hour,
                "minute": now.minute
            }
        }
    
    def _handle_date(self) -> Dict[str, Any]:
        """Handle date-related commands."""
        import datetime
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        
        return {
            "status": "success",
            "message": f"Current date: {date_str}",
            "spoke": f"Today is {date_str}.",
            "data": {
                "date": date_str,
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "weekday": now.strftime("%A")
            }
        }
    
    def _handle_weather(self) -> Dict[str, Any]:
        """Handle weather-related commands."""
        return {
            "status": "info",
            "message": "Weather functionality is not yet implemented.",
            "spoke": "I don't have weather information available yet."
        }
    
    def _handle_help(self) -> Dict[str, Any]:
        """Handle help command."""
        help_text = """
Datetime Agent Commands:
- time: Show the current time
- date: Show the current date
- weather: Show weather information (not yet implemented)

Task Management:
- add task [description] [due time/date]: Add a new task
- list tasks: Show your current tasks
- show tasks [filter]: Show tasks with optional filter
"""
        
        return {
            "status": "success",
            "message": help_text,
            "spoke": "I can help with time, date, and task management. For tasks, try commands like 'add task' or 'list tasks'."
        }

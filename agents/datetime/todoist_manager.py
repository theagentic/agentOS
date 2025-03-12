import os
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

class TodoistManager:
    """Manages interactions with the Todoist API."""
    
    def __init__(self):
        """Initialize Todoist manager with API access."""
        # Load environment variables for API token (agent-specific .env)
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(dotenv_path=env_path)
        
        self.api_token = os.getenv("TODOIST_API_TOKEN")
        if not self.api_token:
            raise ValueError("Todoist API token not found. Set TODOIST_API_TOKEN in the datetime agent's .env file.")
            
        self.api = TodoistAPI(self.api_token)
        self.logger = logging.getLogger("agent.todoist.manager")
        self.projects = {}
        self._load_projects()
        
    def _load_projects(self):
        """Load and cache projects from Todoist."""
        try:
            projects = self.api.get_projects()
            self.projects = {project.name.lower(): project.id for project in projects}
        except Exception as e:
            self.logger.error(f"Failed to load projects: {e}")
            
    def add_task(self, content: str, due_string: Optional[str] = None, 
                priority: int = 1, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a task to Todoist.
        
        Args:
            content: Task description
            due_string: Due date/time in natural language format
            priority: Task priority (1-4, 4 being highest)
            project_name: Name of project to add task to
            
        Returns:
            The created task as a dictionary
        """
        # Convert priority to Todoist format (4=p1, 3=p2, 2=p3, 1=p4)
        todoist_priority = 5 - priority if 1 <= priority <= 4 else 1
        
        # Prepare task parameters
        task_params = {
            "content": content,
            "priority": todoist_priority,
        }
        
        # Add due string if provided
        if due_string:
            task_params["due_string"] = due_string
            
        # Add project if provided and exists
        if project_name and project_name.lower() in self.projects:
            task_params["project_id"] = self.projects[project_name.lower()]
        elif project_name:
            # Try to find similar project
            for proj in self.projects:
                if project_name.lower() in proj:
                    task_params["project_id"] = self.projects[proj]
                    break
        
        # Create the task
        try:
            task = self.api.add_task(**task_params)
            return {
                "id": task.id,
                "content": task.content,
                "priority": task.priority,
                "due": task.due,
                "url": f"https://todoist.com/app/task/{task.id}"
            }
        except Exception as e:
            self.logger.error(f"Failed to create task: {e}")
            raise RuntimeError(f"Failed to create task: {str(e)}")
    
    def list_tasks(self, filter_string: str = "") -> List[Dict[str, Any]]:
        """
        List tasks from Todoist matching the filter.
        
        Args:
            filter_string: Todoist filter string
            
        Returns:
            List of tasks as dictionaries
        """
        try:
            tasks = self.api.get_tasks(filter=filter_string if filter_string else None)
            return [{
                "id": task.id,
                "content": task.content,
                "priority": task.priority,
                "due": task.due,
                "url": f"https://todoist.com/app/task/{task.id}"
            } for task in tasks]
        except Exception as e:
            self.logger.error(f"Failed to list tasks: {e}")
            raise RuntimeError(f"Failed to list tasks: {str(e)}")
    
    def complete_task(self, task_id: str) -> bool:
        """
        Complete a task.
        
        Args:
            task_id: ID of the task to complete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.api.close_task(task_id=task_id)
            return True
        except Exception as e:
            self.logger.error(f"Failed to complete task: {e}")
            return False

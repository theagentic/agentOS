from todoist_api_python.api import TodoistAPI
import config

class TodoistClient:
    """Client for interacting with the Todoist API."""
    
    def __init__(self):
        """Initialize with API token from config."""
        self.api = TodoistAPI(config.TODOIST_API_TOKEN)
    
    def get_tasks(self):
        """Get all active tasks."""
        try:
            return self.api.get_tasks()
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def get_projects(self):
        """Get all projects."""
        try:
            return self.api.get_projects()
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
    
    def get_labels(self):
        """Get all labels."""
        try:
            return self.api.get_labels()
        except Exception as e:
            print(f"Error getting labels: {e}")
            return []
    
    def add_task(self, content, due_string=None, priority=None, 
                 project_id=None, labels=None, description=None):
        """Add a new task to Todoist.
        
        Args:
            content (str): Task title/content
            due_string (str, optional): Due date as a string (e.g., "tomorrow at 12pm")
            priority (int, optional): Priority from 1 (lowest) to 4 (highest)
            project_id (str, optional): Project ID to assign the task to
            labels (list, optional): List of label IDs to apply
            description (str, optional): Detailed task description
        
        Returns:
            Task object if successful, None otherwise
        """
        try:
            return self.api.add_task(
                content=content,
                due_string=due_string,
                priority=priority,
                project_id=project_id,
                label_ids=labels,
                description=description
            )
        except Exception as e:
            print(f"Error adding task: {e}")
            return None
    
    def extract_task_info(self, task):
        """Extract information from a task object."""
        due_date = None
        if hasattr(task, 'due') and task.due:
            if hasattr(task.due, 'date'):
                due_date = task.due.date
        
        return {
            'id': task.id,
            'content': task.content,
            'due_date': due_date,
            'priority': task.priority if hasattr(task, 'priority') else None,
            'project_id': task.project_id if hasattr(task, 'project_id') else None,
        }

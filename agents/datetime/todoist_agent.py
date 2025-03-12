import re
from typing import Dict, Any, List
from core.agent_base import AgentBase
from .todoist_manager import TodoistManager

class TodoistAgent(AgentBase):
    """AgentOS agent for managing Todoist tasks through natural language."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Todoist agent."""
        super().__init__("todoist", config)
        self.todoist = TodoistManager()
        self.commands = {
            "add": self._handle_add_task,
            "create": self._handle_add_task,
            "list": self._handle_list_tasks,
            "show": self._handle_list_tasks,
            "help": self._handle_help,
        }
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input related to Todoist tasks.
        
        Args:
            user_input: The command or query from the user
            
        Returns:
            A dictionary containing results and metadata
        """
        self.status_update(f"Processing Todoist command: {user_input}")
        
        # Try to match common command patterns
        command = self._extract_command(user_input)
        if command in self.commands:
            handler = self.commands[command]
            return handler(user_input)
        
        # If no specific command found, try to detect intent from the content
        if any(kw in user_input.lower() for kw in ["remind", "task", "todo", "reminder"]):
            return self._handle_add_task(user_input)
        
        return {
            "status": "error",
            "message": "I'm not sure what you want to do with your tasks. Try 'add a task' or 'list my tasks'.",
            "spoke": "I'm not sure what you want to do with your tasks. Try adding a task or listing your tasks."
        }
    
    def get_capabilities(self) -> List[str]:
        """Return capabilities for the router."""
        return [
            "Add new tasks to Todoist",
            "List existing Todoist tasks",
            "Manage task schedules and priorities",
            "Set recurring reminders"
        ]
    
    def _extract_command(self, user_input: str) -> str:
        """Extract the primary command from user input."""
        first_word = user_input.lower().split()[0] if user_input else ""
        
        # Check for command patterns
        if first_word in self.commands:
            return first_word
        
        # Check for "X my tasks" pattern
        match = re.search(r"(add|create|list|show) (?:my |the |all )?tasks", user_input.lower())
        if match:
            return match.group(1)
            
        return ""
    
    def _handle_add_task(self, user_input: str) -> Dict[str, Any]:
        """Handle adding a new task."""
        try:
            self.status_update("Adding new task...")
            
            # Parse task details from input
            task_content, due, priority, project = self._extract_task_details(user_input)
            
            # Add task through the manager
            task = self.todoist.add_task(task_content, due, priority, project)
            
            spoken_response = f"Added task: {task_content}"
            if due:
                spoken_response += f" due {due}"
            
            return {
                "status": "success",
                "action": "add_task",
                "task": task,
                "message": f"Added task: {task_content}",
                "spoke": spoken_response
            }
            
        except Exception as e:
            self.logger.error(f"Error adding task: {e}")
            return {
                "status": "error",
                "message": f"Failed to add task: {str(e)}",
                "spoke": "I couldn't add that task. Please check your Todoist connection."
            }
    
    def _handle_list_tasks(self, user_input: str) -> Dict[str, Any]:
        """Handle listing tasks."""
        try:
            self.status_update("Retrieving tasks...")
            
            # Extract filters from input
            filter_string = self._extract_list_filter(user_input)
            
            # Get tasks through the manager
            tasks = self.todoist.list_tasks(filter_string)
            
            if not tasks:
                return {
                    "status": "success",
                    "action": "list_tasks",
                    "tasks": [],
                    "message": "No tasks found matching your criteria.",
                    "spoke": "I didn't find any tasks matching your criteria."
                }
            
            # Format tasks for display
            task_list_text = "\n".join([
                f"• {task['content']} " +
                f"(Due: {task.get('due', {}).get('string', 'No date')}, " +
                f"Priority: {5 - task.get('priority', 1)})"
                for task in tasks
            ])
            
            # Shorter spoken version
            spoken_text = f"I found {len(tasks)} tasks. " 
            if len(tasks) <= 3:
                spoken_text += " ".join([f"{task['content']}." for task in tasks])
            
            return {
                "status": "success",
                "action": "list_tasks",
                "tasks": tasks,
                "message": f"Your tasks:\n{task_list_text}",
                "spoke": spoken_text
            }
            
        except Exception as e:
            self.logger.error(f"Error listing tasks: {e}")
            return {
                "status": "error",
                "message": f"Failed to list tasks: {str(e)}",
                "spoke": "I couldn't retrieve your tasks. Please check your Todoist connection."
            }
    
    def _handle_help(self, _: str) -> Dict[str, Any]:
        """Handle help request."""
        help_text = """
        Todoist Agent Commands:
        
        - Add a task: "Add a task to buy groceries tomorrow at 5pm"
        - List tasks: "List my tasks for today"
        - List specific tasks: "Show my high priority tasks"
        
        You can specify:
        - Due dates: "tomorrow", "next Monday", "every day at 9am"
        - Priorities: "high priority", "p1", "priority 1"
        - Projects: "in Work project", "for Personal"
        """
        
        return {
            "status": "success",
            "action": "help",
            "message": help_text,
            "spoke": "You can ask me to add tasks or list your existing tasks. You can specify due dates, priorities, and projects."
        }
    
    def _extract_task_details(self, user_input: str) -> tuple:
        """Extract task details from user input."""
        # Remove command words
        for cmd in ["add", "create", "new", "task", "reminder"]:
            user_input = re.sub(rf"^\s*{cmd}\s+", "", user_input, flags=re.IGNORECASE)
            
        # Default values
        task_content = user_input
        due = None
        priority = 1
        project = None
        
        # Extract due date
        due_patterns = [
            # tomorrow at 3pm, next monday
            r"(?:due |on |for )?(tomorrow|today|tonight|\w+ \d+(?:st|nd|rd|th)?|next \w+)(?:\s+at\s+(\d+(?::\d+)?(?:am|pm)?))?"
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, task_content, re.IGNORECASE)
            if match:
                due = match.group(0)
                # Remove the due date from the content
                task_content = re.sub(re.escape(match.group(0)), "", task_content).strip()
        
        # Extract priority
        priority_match = re.search(r"(?:with |at )?(?:priority|p)(\d)", task_content, re.IGNORECASE)
        if priority_match:
            priority = int(priority_match.group(1))
            task_content = re.sub(re.escape(priority_match.group(0)), "", task_content).strip()
        elif "high priority" in task_content.lower():
            priority = 4
            task_content = task_content.lower().replace("high priority", "").strip()
        elif "medium priority" in task_content.lower():
            priority = 3
            task_content = task_content.lower().replace("medium priority", "").strip()
        elif "low priority" in task_content.lower():
            priority = 2
            task_content = task_content.lower().replace("low priority", "").strip()
            
        # Extract project
        project_match = re.search(r"(?:in|to|for) (?:the )?(\w+)(?: project)?", task_content, re.IGNORECASE)
        if project_match:
            project = project_match.group(1)
            task_content = re.sub(re.escape(project_match.group(0)), "", task_content).strip()
            
        return task_content, due, priority, project
    
    def _extract_list_filter(self, user_input: str) -> str:
        """Extract filter criteria from user input for listing tasks."""
        filter_string = ""
        
        # Check for date filters
        if "today" in user_input.lower():
            filter_string += "today"
        elif "tomorrow" in user_input.lower():
            filter_string += "tomorrow"
        elif "week" in user_input.lower():
            filter_string += "next 7 days"
            
        # Check for priority filters
        if "high priority" in user_input.lower():
            filter_string += " & priority:1"
            
        # Add more filters as needed
            
        return filter_string
    
    def summarize_result(self, result: Dict[str, Any]) -> str:
        """Generate a user-friendly summary of the results."""
        if result["status"] == "error":
            return result["message"]
            
        if result.get("action") == "add_task":
            return f"Task added: {result.get('task', {}).get('content', '')}"
            
        if result.get("action") == "list_tasks":
            return f"Found {len(result.get('tasks', []))} tasks."
            
        return result.get("message", "Task operation complete.")

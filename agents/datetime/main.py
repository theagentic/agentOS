import asyncio
import config
import argparse
from todoist_client import TodoistClient

def add_new_task(todoist_client):
    """Interactive function to add a new task to Todoist."""
    print("\n=== Add New Todoist Task ===")
    
    # Get task details from user
    content = input("Task description: ")
    
    # Due date with optional recurring pattern
    due_string = input("Due date/time (e.g., 'tomorrow at 3pm', 'every day at 9am', press Enter to skip): ")
    if not due_string.strip():
        due_string = None
    
    # Description
    description = input("Additional description (press Enter to skip): ")
    if not description.strip():
        description = None
    
    # Priority
    priority_input = input("Priority (1-4, where 4 is highest, press Enter for default): ")
    priority = int(priority_input) if priority_input.strip() else None
    
    # Project selection
    show_projects = input("Do you want to assign this to a specific project? (y/n): ").lower()
    project_id = None
    
    if show_projects == 'y':
        projects = todoist_client.get_projects()
        if projects:
            print("\nAvailable Projects:")
            for i, project in enumerate(projects):
                print(f"{i+1}. {project.name}")
            
            project_choice = input("\nSelect project number (press Enter to skip): ")
            if project_choice.strip():
                try:
                    selected_project = projects[int(project_choice) - 1]
                    project_id = selected_project.id
                    print(f"Selected project: {selected_project.name}")
                except (ValueError, IndexError):
                    print("Invalid selection, using default project.")
    
    # Labels selection
    show_labels = input("Do you want to add labels to this task? (y/n): ").lower()
    labels = None
    
    if show_labels == 'y':
        all_labels = todoist_client.get_labels()
        if all_labels:
            print("\nAvailable Labels:")
            for i, label in enumerate(all_labels):
                print(f"{i+1}. {label.name}")
            
            label_choices = input("\nSelect label numbers (comma-separated, press Enter to skip): ")
            if label_choices.strip():
                try:
                    selected_indices = [int(x.strip()) - 1 for x in label_choices.split(',')]
                    labels = [all_labels[i].id for i in selected_indices if 0 <= i < len(all_labels)]
                    label_names = [all_labels[i].name for i in selected_indices if 0 <= i < len(all_labels)]
                    print(f"Selected labels: {', '.join(label_names)}")
                except (ValueError, IndexError):
                    print("Invalid selection, no labels will be applied.")
    
    # Add the task
    task = todoist_client.add_task(
        content=content,
        due_string=due_string,
        priority=priority,
        project_id=project_id,
        labels=labels,
        description=description
    )
    
    if task:
        print(f"Task added successfully!")
        print(f"ID: {task.id}")
        print(f"Content: {task.content}")
        if hasattr(task, 'due') and task.due:
            if hasattr(task.due, 'string'):
                print(f"Due: {task.due.string}")
    
    return task

def list_tasks(todoist_client):
    """List all tasks from Todoist."""
    tasks = todoist_client.get_tasks()
    
    if not tasks:
        print("No tasks found.")
        return
    
    print("\n=== Your Todoist Tasks ===")
    for i, task in enumerate(tasks):
        due_str = f"Due: {task.due.string}" if task.due and hasattr(task.due, 'string') else "No due date"
        print(f"{i+1}. {task.content} - {due_str}")

def main():
    """Simple task management entry point."""
    print("Todoist Task Manager")
    todoist_client = TodoistClient()
    
    while True:
        print("\n=== Menu ===")
        print("1. Add new task")
        print("2. List tasks")
        print("3. Exit")
        
        choice = input("Select an option: ")
        
        if choice == '1':
            add_new_task(todoist_client)
        elif choice == '2':
            list_tasks(todoist_client)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid option, please try again.")

def main_with_args():
    """Command line interface for Todoist task management."""
    parser = argparse.ArgumentParser(description='Todoist Task Manager')
    parser.add_argument('--add', action='store_true', help='Add a new task')
    parser.add_argument('--list', action='store_true', help='List all tasks')
    args = parser.parse_args()
    
    # Initialize client
    todoist_client = TodoistClient()
    
    if args.add:
        # Run in task adding mode
        add_new_task(todoist_client)
        return
        
    if args.list:
        # List all tasks
        list_tasks(todoist_client)
        return
    
    # If no specific argument provided, run the interactive menu
    main()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main_with_args()
    else:
        main()

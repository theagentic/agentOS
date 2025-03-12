#!/usr/bin/env python3
"""
AutoBlog Agent CLI Interface

This script provides a command-line interface for interacting with the AutoBlog agent.
"""

import sys
import time
import threading
from agents import create_agent_instance
from core.message_queue import MessageQueue

def print_usage():
    print("""
AutoBlog Agent Commands:
    help                    - Show this help message
    status                  - Show current agent status
    generate                - Generate blog posts from GitHub repositories
    setdate YYYY-MM-DD      - Set reference date for repository filtering
    blog-repo REPO_NAME     - Process a specific repository by name
    
Example usage:
    python run_autoblog.py help
    python run_autoblog.py generate
    python run_autoblog.py setdate 2024-01-01
    python run_autoblog.py blog-repo my-cool-repo
""")

def monitor_progress(agent_id: str):
    """Monitor and display progress messages from the agent."""
    print("\nMonitoring progress...")
    
    # Keep checking for messages until stopped
    last_check = 0
    message_count = 0
    
    try:
        while True:
            # Get all messages from all queues
            messages = MessageQueue.get_all_messages()
            
            # Filter for messages from our agent
            agent_messages = [m for m in messages if m.get('agent') == agent_id and m.get('status') == 'progress']
            
            # Display new messages
            for message in agent_messages:
                message_count += 1
                timestamp = message.get('timestamp', '').split('T')[1].split('.')[0] if 'T' in message.get('timestamp', '') else ''
                print(f"[{timestamp}] {message.get('message', '')}")
            
            # If we haven't received messages for a while and we've received some messages before, exit
            now = time.time()
            if message_count > 0 and now - last_check > 5:
                break
                
            # Update last check time if we received messages
            if agent_messages:
                last_check = now
                
            # Sleep to avoid hammering the system
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nProgress monitoring stopped.")

def main():
    # Create agent instance
    agent = create_agent_instance('autoblog')
    if not agent:
        print("Error: Could not initialize autoblog agent. Please check your configuration.")
        sys.exit(1)
    
    # Get command line arguments
    args = sys.argv[1:]
    if not args or args[0] == 'help':
        print_usage()
        sys.exit(0)
    
    # Process command
    command = ' '.join(args)
    
    # Support both the old and new command names
    if args[0] == 'process-repo' and len(args) > 1:
        command = f"blog-repo {' '.join(args[1:])}"
    
    # Start a thread to monitor progress if this is a long-running command
    is_long_running = args[0] in ['generate', 'process-repo', 'blog-repo']
    if is_long_running:
        progress_thread = threading.Thread(target=monitor_progress, args=('autoblog',))
        progress_thread.daemon = True
        progress_thread.start()
    
    # Process the command
    result = agent.process(command)
    
    # Print result
    print("\nResult:", result['status'])
    print("Message:", result['message'])
    if result.get('spoke'):
        print("Response:", result['spoke'])
    
    # If we're monitoring progress, wait a moment for final messages
    if is_long_running:
        time.sleep(2)

if __name__ == "__main__":
    main() 
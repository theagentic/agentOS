from core.agent_base import AgentBase
import os
import sys
import shlex
import time
from typing import Dict, Any, List
import logging
from datetime import datetime

# Import the existing autoblog components
from agents.autoblog.config import load_config
from agents.autoblog.github_handler import GitHubHandler
from agents.autoblog.blog_generator import BlogGenerator
from agents.autoblog.file_handler import FileHandler
from agents.autoblog.git_handler import GitHandler

# Import MessageQueue for frontend integration
from core.message_queue import MessageQueue

class Agent(AgentBase):
    """Autoblog agent that generates blog posts from GitHub repositories."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the autoblog agent."""
        super().__init__("autoblog", config)
        
        # Initialize configuration
        try:
            self.config = load_config()
            self._validate_config()
            
            # Initialize components
            self.github = GitHubHandler(self.config.github_token, self.config.github_username)
            self.blog_generator = BlogGenerator(self.config.blog_post_template)
            self.file_handler = FileHandler(self.config.obsidian_vault_path, self.config.blog_posts_folder)
            self.git_handler = GitHandler(self.config.blog_repo_path)
            
            # Initialize message queue for frontend updates
            self.message_queue = MessageQueue()
            
            self.is_initialized = True
        except Exception as e:
            self.logger.error(f"Error initializing autoblog agent: {e}")
            self.is_initialized = False
    
    def _validate_config(self):
        """Validate the configuration."""
        missing_configs = []
        if not self.config.github_token:
            missing_configs.append("GitHub token (GITHUB_TOKEN)")
        if not self.config.github_username:
            missing_configs.append("GitHub username (GITHUB_USERNAME)")
        if not self.config.obsidian_vault_path:
            missing_configs.append("Obsidian vault path (OBSIDIAN_VAULT_PATH)")
        if not self.config.blog_repo_path:
            missing_configs.append("Blog repo path (BLOG_REPO_PATH)")
        
        if missing_configs:
            error_msg = "Missing required configurations: " + ", ".join(missing_configs)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate paths
        if not os.path.exists(self.config.obsidian_vault_path):
            error_msg = f"Obsidian vault path does not exist: {self.config.obsidian_vault_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not os.path.exists(self.config.blog_repo_path):
            error_msg = f"Blog repository path does not exist: {self.config.blog_repo_path}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _send_progress_update(self, message: str):
        """Send a progress update to the frontend."""
        if hasattr(self, 'message_queue') and self.message_queue:
            self.logger.info(f"Progress update: {message}")
            self.message_queue.add_message({
                "agent": "autoblog",
                "status": "progress",
                "message": message,
                "spoke": message,
                "timestamp": datetime.now().isoformat()
            })
            # Small sleep to ensure updates are visible in UI
            time.sleep(0.2)
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input for the autoblog agent.
        
        Args:
            user_input: The command or query from the user
            
        Returns:
            A dictionary containing results and metadata
        """
        if not self.is_initialized:
            return {
                "status": "error",
                "message": "Autoblog agent is not properly initialized. Please check the logs.",
                "spoke": "I couldn't initialize the autoblog agent. Please check the configuration.",
                "agent_id": "autoblog"
            }
        
        try:
            original_input = user_input  # Save the original input for logging
            
            # Clean and parse the input
            # First, remove any potential "autoblog" prefix to handle both
            # "blog-repo X" and "autoblog blog-repo X" formats
            if user_input.lower().startswith("autoblog "):
                user_input = user_input[len("autoblog "):].strip()
                
            # Special case for backward compatibility - convert before parsing
            if user_input.lower().startswith("process-repo "):
                user_input = "blog-repo " + user_input[len("process-repo "):].strip()
                
            # Parse the command
            parts = shlex.split(user_input)
            command = parts[0].lower() if parts else "help"
            args = parts[1:] if len(parts) > 1 else []
            
            # Add an agent identifier to the response to help the frontend
            response_metadata = {
                "agent_id": "autoblog",
                "command_processed": command,
                "original_input": original_input
            }
            
            # Handle different commands
            if command == "help":
                result = self._handle_help()
            elif command == "generate":
                result = self._handle_generate()
            elif command == "status":
                result = self._handle_status()
            elif command == "setdate":
                date_str = args[0] if args else None
                result = self._handle_set_date(date_str)
            elif command == "blog-repo":
                repo_name = args[0] if args else None
                result = self._handle_process_repo(repo_name)
            else:
                result = {
                    "status": "error",
                    "message": f"Unknown command: {command}",
                    "spoke": f"Sorry, I don't understand the command '{command}'. Try 'help' for a list of commands."
                }
            
            # Add the metadata to the result
            result.update(response_metadata)
            return result
                
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "spoke": "Sorry, I encountered an error while processing your request.",
                "agent_id": "autoblog"  # Add agent identifier even in error case
            }
    
    def _handle_help(self) -> Dict[str, Any]:
        """Handle the help command."""
        help_text = """
Available commands:
- help: Show this help message
- generate: Generate blog posts from new GitHub repositories
- status: Show the current status of the autoblog agent
- setdate [YYYY-MM-DD]: Set the reference date for repository filtering
- blog-repo [REPO_NAME]: Process a specific repository even if it was processed before
"""
        return {
            "status": "success",
            "message": help_text,
            "spoke": "Here are the commands you can use with the autoblog agent."
        }
    
    def _handle_process_repo(self, repo_name: str = None) -> Dict[str, Any]:
        """
        Handle the process-repo command to process a specific repository.
        
        Args:
            repo_name: Name of the repository to process
            
        Returns:
            Result dictionary
        """
        if not repo_name:
            return {
                "status": "error",
                "message": "Please provide a repository name.",
                "spoke": "I need a repository name to process. Please specify a repository name."
            }
        
        self._send_progress_update(f"Processing specific repository: {repo_name}")
        
        try:
            # Get the repository from GitHub
            self._send_progress_update(f"Fetching repository information for {repo_name}...")
            repo = self.github.get_repository_by_name(repo_name)
            
            if not repo:
                self._send_progress_update(f"Repository '{repo_name}' not found.")
                return {
                    "status": "error",
                    "message": f"Repository '{repo_name}' not found. Make sure the repository exists and is accessible.",
                    "spoke": f"I couldn't find the repository '{repo_name}'. Please check the name and try again."
                }
            
            # Gather repository data
            self._send_progress_update(f"Gathering data for {repo_name}...")
            repo_data = self.github.gather_repo_data(repo)
            
            # Generate blog post
            self._send_progress_update(f"Generating blog post for {repo_name}...")
            blog_content = self.blog_generator.generate_blog_post(repo_data)
            
            # Save to Obsidian vault
            self._send_progress_update(f"Saving blog post to Obsidian vault...")
            file_path = self.file_handler.save_blog_post(repo_name, blog_content)
            self._send_progress_update(f"Blog post saved to: {file_path}")
            
            # Run the full workflow to publish the blog post
            self._send_progress_update(f"Publishing blog post to Git repository...")
            success, messages = self.git_handler.full_publish_workflow(
                source_path=self.config.obsidian_vault_path,
                commit_message=f"Add/Update blog post for {repo_name}"
            )
            
            if success:
                # Mark repository as processed with current date
                self.github.mark_repo_as_processed(repo_name, datetime.now().isoformat())
                self._send_progress_update(f"✅ Successfully processed and published blog post for {repo_name}")
                
                return {
                    "status": "success",
                    "message": f"✅ Successfully processed and published blog post for {repo_name}",
                    "spoke": f"I've generated and published a blog post for the repository {repo_name}."
                }
            else:
                error_msg = f"❌ Failed to publish blog post for {repo_name}: {' '.join(messages)}"
                self._send_progress_update(error_msg)
                
                return {
                    "status": "error",
                    "message": error_msg,
                    "spoke": f"I generated the blog post but couldn't publish it. Please check the logs for details."
                }
                
        except Exception as e:
            self.logger.error(f"Error processing repository {repo_name}: {e}")
            error_msg = f"❌ Error processing {repo_name}: {str(e)}"
            self._send_progress_update(error_msg)
            
            return {
                "status": "error",
                "message": error_msg,
                "spoke": f"I encountered an error while processing the repository {repo_name}."
            }
    
    def _handle_generate(self) -> Dict[str, Any]:
        """Handle the generate command."""
        self.logger.info("Starting blog post generation...")
        
        # Send initial progress update
        self._send_progress_update("Starting blog post generation process...")
        
        # Find new repositories
        self._send_progress_update("Scanning GitHub for new repositories...")
        new_repos = self.github.find_new_repos()
        
        if not new_repos:
            self._send_progress_update("No new repositories found with README.md files.")
            return {
                "status": "info",
                "message": "No new repositories found with README.md files.",
                "spoke": "I didn't find any new repositories to process."
            }
        
        # Send status update
        self._send_progress_update(f"Found {len(new_repos)} new repositories to process.")
        
        result_message = f"Found {len(new_repos)} new repositories.\n\n"
        processed_count = 0
        
        # Process each new repository
        for i, repo in enumerate(new_repos):
            repo_name = repo['name']
            created_date = repo['created_at']
            
            # Progress update
            self._send_progress_update(f"Processing repository {i+1}/{len(new_repos)}: {repo_name}")
            
            try:
                # Gather repository data
                self._send_progress_update(f"Gathering data for {repo_name}...")
                repo_data = self.github.gather_repo_data(repo)
                
                # Generate blog post
                self._send_progress_update(f"Generating blog post for {repo_name}...")
                blog_content = self.blog_generator.generate_blog_post(repo_data)
                
                # Save to Obsidian vault
                self._send_progress_update(f"Saving blog post to Obsidian vault...")
                file_path = self.file_handler.save_blog_post(repo_name, blog_content)
                self._send_progress_update(f"Blog post saved to: {file_path}")
                
                # Run the full workflow to publish the blog post
                self._send_progress_update(f"Publishing blog post to Git repository...")
                success, messages = self.git_handler.full_publish_workflow(
                    source_path=self.config.obsidian_vault_path,
                    commit_message=f"Add blog post for {repo_name}"
                )
                
                if success:
                    # Mark repository as processed with its creation date
                    self.github.mark_repo_as_processed(repo_name, created_date)
                    success_msg = f"✅ Successfully processed and published blog post for {repo_name}"
                    self._send_progress_update(success_msg)
                    result_message += success_msg + "\n"
                    processed_count += 1
                else:
                    error_msg = f"❌ Failed to publish blog post for {repo_name}: {' '.join(messages)}"
                    self._send_progress_update(error_msg)
                    result_message += error_msg + "\n"
            
            except Exception as e:
                self.logger.error(f"Error processing repository {repo_name}: {e}")
                error_msg = f"❌ Error processing {repo_name}: {str(e)}"
                self._send_progress_update(error_msg)
                result_message += error_msg + "\n"
        
        # Final summary
        summary = f"\nTotal: {len(new_repos)}, Successfully processed: {processed_count}"
        self._send_progress_update(f"Completed blog generation. {processed_count} of {len(new_repos)} repositories processed successfully.")
        result_message += summary
        
        return {
            "status": "success",
            "message": result_message,
            "spoke": f"I've generated blog posts for {processed_count} out of {len(new_repos)} repositories. Check the message for details."
        }
    
    def _handle_status(self) -> Dict[str, Any]:
        """Handle the status command."""
        self._send_progress_update("Checking autoblog agent status...")
        
        status_message = "Autoblog Agent Status:\n\n"
        status_message += f"GitHub Username: {self.config.github_username}\n"
        status_message += f"Obsidian Vault: {self.config.obsidian_vault_path}\n"
        status_message += f"Blog Repository: {self.config.blog_repo_path}\n"
        
        # Get information about processed repositories
        processed_repos = self.github.get_processed_repos()
        status_message += f"Processed Repositories: {len(processed_repos)}\n"
        
        # Send the final status
        self._send_progress_update("Status check complete.")
        
        return {
            "status": "success",
            "message": status_message,
            "spoke": "I've gathered the current status of the autoblog agent."
        }
    
    def _handle_set_date(self, date_str: str = None) -> Dict[str, Any]:
        """Handle the setdate command."""
        if not date_str:
            return {
                "status": "error",
                "message": "Please provide a date in YYYY-MM-DD format.",
                "spoke": "I need a date in YYYY-MM-DD format to set the reference date."
            }
        
        self._send_progress_update(f"Setting reference date to {date_str}...")
        
        if self.github.set_reference_date(date_str):
            self._send_progress_update(f"Reference date set successfully to {date_str}.")
            return {
                "status": "success",
                "message": f"Reference date set to: {date_str}\nRepositories created before this date will be ignored.",
                "spoke": f"I've set the reference date to {date_str}. Repositories created before this date will be ignored."
            }
        else:
            self._send_progress_update(f"Failed to set reference date. Invalid format: {date_str}")
            return {
                "status": "error",
                "message": f"'{date_str}' is not a valid date format. Use YYYY-MM-DD.",
                "spoke": f"Sorry, '{date_str}' is not a valid date format. Please use YYYY-MM-DD."
            }
    
    def get_capabilities(self) -> List[str]:
        """Return a list of this agent's capabilities."""
        return [
            "Generate blog posts from GitHub repositories",
            "Filter repositories by creation date",
            "Automatically publish blog posts to a Git repository",
            "Manage blog post generation workflow",
            "Process specific repositories on demand"
        ]

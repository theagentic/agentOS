import os
import sys
import argparse
from datetime import datetime

from config import load_config
from github_handler import GitHubHandler
from blog_generator import BlogGenerator
from file_handler import FileHandler
from git_handler import GitHandler

def setup():
    """Setup and validate the configuration"""
    config = load_config()
    
    # Check for required configuration
    missing_configs = []
    if not config.github_token:
        missing_configs.append("GitHub token (GITHUB_TOKEN)")
    if not config.github_username:
        missing_configs.append("GitHub username (GITHUB_USERNAME)")
    if not config.obsidian_vault_path:
        missing_configs.append("Obsidian vault path (OBSIDIAN_VAULT_PATH)")
    if not config.blog_repo_path:
        missing_configs.append("Blog repo path (BLOG_REPO_PATH)")
    
    if missing_configs:
        print("Error: Missing required configurations:")
        for missing in missing_configs:
            print(f"- {missing}")
        print("\nPlease set these environment variables or add them to a .env file.")
        sys.exit(1)
    
    # Validate paths
    if not os.path.exists(config.obsidian_vault_path):
        print(f"Error: Obsidian vault path does not exist: {config.obsidian_vault_path}")
        sys.exit(1)
    
    if not os.path.exists(config.blog_repo_path):
        print(f"Error: Blog repository path does not exist: {config.blog_repo_path}")
        sys.exit(1)
    
    return config

def set_reference_date(github_handler, date_str):
    """Set the reference date for repository filtering"""
    # Convert YYYY-MM-DD to ISO format
    try:
        if 'T' not in date_str:
            # If just a date is provided, add time component
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            date_str = date_obj.strftime('%Y-%m-%dT00:00:00Z')
        
        if github_handler.set_reference_date(date_str):
            print(f"Reference date set to: {date_str}")
            print("Repositories created before this date will be ignored.")
            return True
        else:
            return False
    except ValueError:
        print(f"Error: '{date_str}' is not a valid date format. Use YYYY-MM-DD.")
        return False

def main():
    """Main function to run the blog post generation pipeline"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate blog posts from GitHub repositories')
    parser.add_argument('--date', help='Set the reference date (YYYY-MM-DD). Repos created before this date will be ignored.')
    args = parser.parse_args()
    
    print("Starting automated blog post generation...")
    
    # Setup configuration
    config = setup()
    
    # Initialize GitHub handler
    github = GitHubHandler(config.github_token, config.github_username)
    
    # Set reference date if provided
    if args.date:
        if not set_reference_date(github, args.date):
            return
    
    # Initialize other components
    blog_generator = BlogGenerator(config.blog_post_template)
    file_handler = FileHandler(config.obsidian_vault_path, config.blog_posts_folder)
    git_handler = GitHandler(config.blog_repo_path)
    
    # Find new repositories
    print("Checking for new repositories with README.md files...")
    new_repos = github.find_new_repos()
    
    if not new_repos:
        print("No new repositories found with README.md files.")
        return
    
    print(f"Found {len(new_repos)} new repositories.")
    
    # Process each new repository
    for repo in new_repos:
        repo_name = repo['name']
        created_date = repo['created_at']
        print(f"\nProcessing repository: {repo_name} (created: {created_date})")
        
        # Gather repository data
        print("Gathering repository data...")
        repo_data = github.gather_repo_data(repo)
        
        # Generate blog post
        print("Generating blog post content...")
        blog_content = blog_generator.generate_blog_post(repo_data)
        
        # Save to Obsidian vault
        print("Saving blog post to Obsidian vault...")
        file_path = file_handler.save_blog_post(repo_name, blog_content)
        print(f"Blog post saved to: {file_path}")
        
        # Run the full workflow to publish the blog post
        print("\nRunning publishing workflow...")
        success, messages = git_handler.full_publish_workflow(
            source_path=config.obsidian_vault_path,  # Use the direct path
            commit_message=f"Add blog post for {repo_name}"
        )
        
        for message in messages:
            print(message)
            
        if success:
            print("Successfully published blog post.")
            # Mark repository as processed with its creation date
            github.mark_repo_as_processed(repo_name, created_date)
        else:
            print("Failed to publish blog post. See errors above.")
    
    print("\nBlog post generation complete!")

if __name__ == "__main__":
    main()

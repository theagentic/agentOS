import os
from dataclasses import dataclass

@dataclass
class Config:
    # GitHub settings
    github_token: str = os.environ.get("GITHUB_TOKEN", "")
    github_username: str = os.environ.get("GITHUB_USERNAME", "")
    
    # Path settings
    obsidian_vault_path: str = os.environ.get("OBSIDIAN_VAULT_PATH", "")
    blog_posts_folder: str = ""  # Empty since we're using direct paths
    
    # Blog repository settings
    blog_repo_path: str = os.environ.get("BLOG_REPO_PATH", "")
    
    # Blog post settings
    blog_post_template: str = """---
title: "{title}"
date: {date}
draft: false
tags: [{tags}]
---

# {title}

{content}

## Project Details

- GitHub Repository: [{repo_name}]({repo_url})
- Created: {created_date}
- Language: {main_language}

"""

def load_config():
    """Load configuration from environment variables or .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    return Config(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        github_username=os.environ.get("GITHUB_USERNAME", ""),
        obsidian_vault_path=os.environ.get("OBSIDIAN_VAULT_PATH", ""),
        blog_repo_path=os.environ.get("BLOG_REPO_PATH", "")
    )

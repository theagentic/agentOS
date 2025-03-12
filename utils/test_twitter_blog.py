"""
Test script for Twitter blog posting functionality.
Run this directly to test if the blog to Twitter feature works.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test the blog-to-Twitter functionality."""
    print("\n=== Testing Blog-to-Twitter Functionality ===\n")
    
    # Load environment variables
    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / "agents" / "twitter_bot" / ".env"
    
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)
        print(f"Loaded environment from {env_file}")
    else:
        print(f"Error: Could not find .env file at {env_file}")
        return False
    
    # Check blog path exists
    blog_path = os.getenv("BLOG_POSTS_PATH")
    if not blog_path:
        print("Error: BLOG_POSTS_PATH not set in .env file")
        return False
    
    print(f"Blog path: {blog_path}")
    
    if not os.path.exists(blog_path):
        print(f"Error: Blog path does not exist: {blog_path}")
        print("Check the path format - if using WSL path (/mnt/c/...), change to Windows format (C:/...)")
        return False
        
    print(f"Blog path exists: {os.path.exists(blog_path)}")
    
    # List files in blog directory
    blog_files = list(Path(blog_path).glob("*.md"))
    print(f"Found {len(blog_files)} Markdown files in blog directory:")
    for i, file in enumerate(sorted(blog_files, key=lambda x: x.stat().st_mtime, reverse=True)):
        if i < 5:  # Show only the 5 most recent
            modified_time = file.stat().st_mtime
            print(f" - {file.name} (Modified: {modified_time})")
    
    if not blog_files:
        print("No markdown files found in blog directory.")
        return False
    
    # Find the main.py script
    main_script = base_dir / "agents" / "twitter_bot" / "src" / "main.py"
    if not main_script.exists():
        print(f"Error: Could not find main.py script at {main_script}")
        return False
    
    print(f"\nScript path: {main_script}")
    
    # Run the script in dry-run mode
    try:
        print("\nRunning blog poster in dry-run mode (generate tweets without posting)...")
        result = subprocess.run(
            [sys.executable, str(main_script), "--dry-run"],
            cwd=main_script.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("\nDry run succeeded!")
            print("\nGenerated tweets:")
            print(result.stdout)
            return True
        else:
            print("\nDry run failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"\nError running script: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

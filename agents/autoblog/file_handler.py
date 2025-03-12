import os
import re
from datetime import datetime

class FileHandler:
    def __init__(self, obsidian_vault_path: str, blog_posts_folder: str = ""):
        self.obsidian_vault_path = obsidian_vault_path
        self.blog_posts_folder = blog_posts_folder
        self._ensure_blog_folder_exists()
    
    def _ensure_blog_folder_exists(self):
        """Ensure the blog posts folder exists in the Obsidian vault"""
        if self.blog_posts_folder:
            blog_dir = os.path.join(self.obsidian_vault_path, self.blog_posts_folder)
            os.makedirs(blog_dir, exist_ok=True)
        else:
            # If no subfolder specified, ensure the main path exists
            os.makedirs(self.obsidian_vault_path, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize the filename to be valid"""
        # Replace invalid characters
        sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
        # Replace spaces with hyphens
        sanitized = sanitized.replace(' ', '-')
        # Ensure the filename is not too long
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized
    
    def save_blog_post(self, repo_name: str, content: str) -> str:
        """Save the blog post to the Obsidian vault and return the file path"""
        # Create filename with date prefix for better organization
        date_prefix = datetime.now().strftime('%Y-%m-%d')
        sanitized_name = self._sanitize_filename(repo_name)
        filename = f"{date_prefix}-{sanitized_name}.md"
        
        # Complete path in Obsidian vault - handle both with and without subfolder
        if self.blog_posts_folder:
            file_path = os.path.join(self.obsidian_vault_path, self.blog_posts_folder, filename)
        else:
            file_path = os.path.join(self.obsidian_vault_path, filename)
        
        # Save the content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return file_path

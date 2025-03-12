import os
import yaml
from typing import List, Optional, Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class BlogPost:
    def __init__(self, filepath):
        self.filepath = filepath
        self.content = ""
        self.metadata = {}
        self.parse_file()
    
    def parse_file(self):
        try:
            with open(self.filepath, 'r') as file:
                content = file.read()
                # Split front matter and content
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        self.metadata = yaml.safe_load(parts[1]) or {}
                        if not isinstance(self.metadata, dict):
                            self.metadata = {}
                    except yaml.YAMLError:
                        self.metadata = {}
                    self.content = parts[2]
                else:
                    self.content = content
        except Exception as e:
            print(f"Error reading file {self.filepath}: {e}")
            self.content = ""
            self.metadata = {}

class BlogMonitor(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.last_processed_file = None

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.md'):
            return
        # Wait a brief moment to ensure file is fully written
        time.sleep(1)
        self.last_processed_file = event.src_path
        post = BlogPost(event.src_path)
        self.callback(post)

def get_latest_post(directory: str) -> Optional[BlogPost]:
    """Get the most recently created markdown file from the directory."""
    markdown_files = []
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            filepath = os.path.join(directory, filename)
            markdown_files.append((filepath, os.path.getctime(filepath)))
    
    if not markdown_files:
        return None
    
    # Get the most recently created file
    latest_file = max(markdown_files, key=lambda x: x[1])[0]
    return BlogPost(latest_file)

def monitor_blog_directory(directory: str, callback: Callable[[BlogPost], Any]) -> Any:
    """Start monitoring the blog directory for new markdown files."""
    observer = Observer()
    handler = BlogMonitor(callback)
    observer.schedule(handler, directory, recursive=False)
    observer.start()
    print(f"Started monitoring directory: {directory}")
    
    # Process the latest existing file on startup
    latest = get_latest_post(directory)
    if latest:
        print(f"Processing latest existing file: {os.path.basename(latest.filepath)}")
        callback(latest)
    
    return observer

# Keep the old function for compatibility
def get_blog_posts(directory: str) -> List[BlogPost]:
    """Get all markdown files from the specified directory."""
    blog_posts = []
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            filepath = os.path.join(directory, filename)
            blog_posts.append(BlogPost(filepath))
    return blog_posts

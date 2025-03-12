"""
Routes for the Twitter Bot agent.
Provides API endpoints for Twitter functionality.
"""

import os
import json
import logging
from flask import jsonify
import psutil
import time
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def get_status_file_path():
    """Get the path to the status file, ensuring the directory exists."""
    # Get the status directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    status_dir = os.path.join(current_dir, 'status')
    
    # Create the directory if it doesn't exist
    if not os.path.exists(status_dir):
        try:
            os.makedirs(status_dir)
            logger.info(f"Created status directory at {status_dir}")
        except Exception as e:
            logger.error(f"Error creating status directory: {e}")
            return None
    
    # Return the full path to the status file
    return os.path.join(status_dir, 'twitter_status.json')

def get_twitter_status():
    """
    Get the current status of Twitter operations.
    
    Returns:
        JSON response with the status information
    """
    logger.info("Twitter status endpoint called")
    
    status_file = get_status_file_path()
    logger.info(f"Checking status file at: {status_file}")
    
    # Check if the directory exists
    status_dir = os.path.dirname(status_file)
    status_dir_exists = os.path.isdir(status_dir)
    logger.info(f"Status directory exists: {status_dir_exists}")
    
    # Default status if file doesn't exist
    status_data = {
        "status": "unknown",  # Use unknown as default status, not idle
        "timestamp": datetime.now().isoformat(),
        "message": "No recent Twitter activity"
    }
    
    # Try to read the status file if it exists
    if os.path.exists(status_file):
        logger.info("Status file exists: True")
        try:
            with open(status_file, 'r') as f:
                file_data = json.load(f)
                logger.info(f"Status file content: {file_data}")
                
                # Update our status data with file contents
                status_data.update(file_data)
                
                # Ensure we have a valid status value
                if "status" not in status_data or not status_data["status"]:
                    status_data["status"] = "unknown"
                    
                # Log the final status being returned    
                logger.info(f"Returning Twitter status: {status_data['status']}")
                
        except Exception as e:
            logger.error(f"Error reading status file: {e}")
            status_data["status"] = "error"
            status_data["error"] = str(e)
    else:
        logger.info("Status file exists: False")
        # Don't create a file here, let the agent handle that
    
    logger.info("Twitter status request completed successfully")
    return jsonify(status_data)

def twitter_api_health():
    """
    Simple health check for Twitter API routes.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        "status": "ok",
        "message": "Twitter API routes are available",
        "timestamp": datetime.now().isoformat()
    })

def get_twitter_diagnostics():
    """
    Get diagnostic information about the Twitter API setup.
    
    Returns:
        JSON response with diagnostic information
    """
    # Check for Twitter API credentials
    credentials = {
        "api_key": bool(os.getenv('TWITTER_API_KEY')),
        "api_secret": bool(os.getenv('TWITTER_API_SECRET')),
        "access_token": bool(os.getenv('TWITTER_ACCESS_TOKEN')),
        "access_secret": bool(os.getenv('TWITTER_ACCESS_TOKEN_SECRET') or os.getenv('TWITTER_ACCESS_SECRET'))
    }
    
    # Check if Tweepy is installed
    tweepy_installed = False
    try:
        import tweepy
        tweepy_installed = True
        tweepy_version = getattr(tweepy, "__version__", "unknown")
    except ImportError:
        tweepy_version = None
    
    # Check for any Twitter processes
    twitter_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('twitter' in cmd.lower() for cmd in cmdline if cmd):
                twitter_processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "running_time": time.time() - proc.create_time() if hasattr(proc, 'create_time') else None
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    response = {
        "time": datetime.now().isoformat(),
        "credentials_available": all(credentials.values()),
        "credential_status": credentials,
        "tweepy_installed": tweepy_installed,
        "tweepy_version": tweepy_version,
        "twitter_processes": twitter_processes,
        "environment_variables": {
            "has_gemini_key": bool(os.getenv('GEMINI_API_KEY')),
            "blog_path_set": bool(os.getenv('BLOG_POSTS_PATH')),
            "blog_path_exists": os.path.exists(os.getenv('BLOG_POSTS_PATH', '')) if os.getenv('BLOG_POSTS_PATH') else False
        }
    }
    
    return jsonify(response)

def get_twitter_directory_diagnostics():
    """
    Diagnostic endpoint to check status directory health.
    
    Returns:
        JSON response with directory diagnostics
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    status_dir = os.path.join(current_dir, 'status')
    
    # Check if directory exists
    dir_exists = os.path.exists(status_dir)
    
    # Check if directory is writable
    dir_writable = os.access(status_dir, os.W_OK) if dir_exists else False
    
    # Get file listing if directory exists
    files = []
    if dir_exists:
        try:
            for filename in os.listdir(status_dir):
                file_path = os.path.join(status_dir, filename)
                if os.path.isfile(file_path):
                    files.append({
                        "name": filename,
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        except Exception as e:
            files = [{"error": str(e)}]
    
    # Create the directory if it doesn't exist
    if not dir_exists:
        try:
            os.makedirs(status_dir)
            dir_exists = True
            dir_writable = os.access(status_dir, os.W_OK)
        except Exception as _:
            pass
    
    return jsonify({
        "directory": status_dir,
        "exists": dir_exists,
        "writable": dir_writable,
        "files": files
    })

def twitter_debug():
    """
    Debug endpoint for Twitter status issues.
    
    Returns:
        JSON with detailed debugging information
    """
    status_file = get_status_file_path()
    status_data = {"debug_time": datetime.now().isoformat()}
    
    # Check file exists
    status_data["file_exists"] = os.path.exists(status_file)
    
    # Check file permissions
    if status_data["file_exists"]:
        status_data["readable"] = os.access(status_file, os.R_OK)
        status_data["writable"] = os.access(status_file, os.W_OK)
        
        # Check file size
        try:
            status_data["file_size"] = os.path.getsize(status_file)
            
            # Try to read content
            try:
                with open(status_file, 'r') as f:
                    content = f.read()
                    status_data["content_length"] = len(content)
                    
                    # Try to parse as JSON
                    try:
                        parsed = json.loads(content)
                        status_data["parsed"] = True
                        status_data["parsed_status"] = parsed.get("status", "missing")
                    except json.JSONDecodeError as e:
                        status_data["parsed"] = False
                        status_data["parse_error"] = str(e)
                        
            except Exception as e:
                status_data["read_error"] = str(e)
        except Exception as e:
            status_data["file_info_error"] = str(e)
    
    # Test creating a fresh status
    try:
        test_file = os.path.join(os.path.dirname(status_file), "twitter_test_status.json")
        test_data = {
            "status": "test", 
            "timestamp": datetime.now().isoformat(),
            "test": True
        }
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        status_data["test_file_created"] = True
        
        # Clean up the test file
        try:
            os.remove(test_file)
            status_data["test_file_deleted"] = True
        except Exception:
            status_data["test_file_deleted"] = False
    except Exception as e:
        status_data["test_file_error"] = str(e)
        
    return jsonify(status_data)

# Define the routes to be registered
routes = [
    ('/twitter/status', get_twitter_status, ['GET']),
    ('/twitter/health', twitter_api_health, ['GET']),
    ('/twitter/diagnostics', get_twitter_diagnostics, ['GET']),
    ('/twitter/directory', get_twitter_directory_diagnostics, ['GET']),
    ('/twitter/debug', twitter_debug, ['GET'])
]

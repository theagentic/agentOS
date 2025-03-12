"""
Path utilities for Twitter Bot agent.
Handles directory checks, creation, and file operations.
"""
import os
import shutil
import logging
import tempfile
import platform
import stat
from typing import Tuple

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path: str, create: bool = True) -> Tuple[bool, bool, str]:
    """
    Ensure a directory exists and is accessible.
    
    Args:
        directory_path: Path to the directory
        create: Whether to create the directory if it doesn't exist
        
    Returns:
        Tuple of (exists, accessible, message)
    """
    # Check if the directory exists
    if os.path.exists(directory_path):
        if os.path.isdir(directory_path):
            # Check if the directory is accessible (readable and writable)
            readable = os.access(directory_path, os.R_OK)
            writable = os.access(directory_path, os.W_OK)
            
            if readable and writable:
                logger.info(f"Directory exists and is writable: {directory_path}")
                return True, True, "Directory exists and is accessible"
            else:
                issues = []
                if not readable:
                    issues.append("not readable")
                if not writable:
                    issues.append("not writable")
                    
                message = f"Directory exists but is {' and '.join(issues)}"
                logger.warning(message)
                return True, False, message
        else:
            # Path exists but is not a directory
            return True, False, "Path exists but is not a directory"
    
    # Directory doesn't exist
    if not create:
        return False, False, "Directory does not exist"
    
    # Try to create the directory
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Created directory: {directory_path}")
        
        # Verify the directory was created and is accessible
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            readable = os.access(directory_path, os.R_OK)
            writable = os.access(directory_path, os.W_OK)
            
            if readable and writable:
                return True, True, "Directory created and is accessible"
            else:
                issues = []
                if not readable:
                    issues.append("not readable")
                if not writable:
                    issues.append("not writable")
                    
                message = f"Directory created but is {' and '.join(issues)}"
                return True, False, message
        else:
            return False, False, "Failed to create directory for unknown reason"
    except Exception as e:
        logger.error(f"Error creating directory: {e}")
        return False, False, f"Error creating directory: {str(e)}"

def fix_directory_permissions(directory_path: str) -> Tuple[bool, str]:
    """
    Try to fix permissions on a directory.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Tuple of (success, message)
    """
    if not os.path.exists(directory_path):
        return False, "Directory does not exist"
        
    if not os.path.isdir(directory_path):
        return False, "Path is not a directory"
    
    try:
        # Different approaches depending on the platform
        if platform.system() == 'Windows':
            # On Windows, try to change the file attributes
            import ctypes
            if not ctypes.windll.kernel32.SetFileAttributesW(directory_path, 128):  # 128 = FILE_ATTRIBUTE_NORMAL
                return False, "Failed to set directory attributes"
        else:
            # On Unix-like systems, try to change permissions
            current_mode = os.stat(directory_path).st_mode
            new_mode = current_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
            os.chmod(directory_path, new_mode)
        
        # Verify the fix worked
        readable = os.access(directory_path, os.R_OK)
        writable = os.access(directory_path, os.W_OK)
        
        if readable and writable:
            return True, "Successfully fixed directory permissions"
        else:
            issues = []
            if not readable:
                issues.append("not readable")
            if not writable:
                issues.append("not writable")
                
            message = f"Failed to fix permissions: directory is {' and '.join(issues)}"
            return False, message
            
    except Exception as e:
        logger.error(f"Error fixing directory permissions: {e}")
        return False, f"Error fixing permissions: {str(e)}"

def create_fallback_directory() -> Tuple[bool, str]:
    """
    Create a fallback directory for storing files when the regular directory is inaccessible.
    
    Returns:
        Tuple of (success, path_or_error_message)
    """
    try:
        # Create a directory in the system temp folder
        temp_dir = os.path.join(tempfile.gettempdir(), "twitter_bot_status")
        
        # Ensure the directory exists and is writable
        exists, accessible, message = ensure_directory_exists(temp_dir, create=True)
        
        if exists and accessible:
            return True, temp_dir
        else:
            # Try the user's home directory as a last resort
            home_dir = os.path.expanduser("~")
            fallback_dir = os.path.join(home_dir, ".twitter_bot_status")
            
            exists, accessible, message = ensure_directory_exists(fallback_dir, create=True)
            
            if exists and accessible:
                return True, fallback_dir
            else:
                return False, f"Failed to create fallback directory: {message}"
    
    except Exception as e:
        logger.error(f"Error creating fallback directory: {e}")
        return False, f"Error creating fallback directory: {str(e)}"

def migrate_files(source_dir: str, target_dir: str) -> Tuple[bool, str, int]:
    """
    Migrate files from one directory to another.
    
    Args:
        source_dir: Source directory path
        target_dir: Target directory path
        
    Returns:
        Tuple of (success, message, count_of_migrated_files)
    """
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        return False, "Source directory does not exist or is not a directory", 0
        
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        return False, "Target directory does not exist or is not a directory", 0
    
    try:
        migrated_count = 0
        
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            target_file = os.path.join(target_dir, filename)
            
            # Only migrate regular files
            if os.path.isfile(source_file):
                try:
                    shutil.copy2(source_file, target_file)
                    migrated_count += 1
                except Exception as e:
                    logger.warning(f"Failed to copy {filename}: {e}")
        
        return True, f"Successfully migrated {migrated_count} files", migrated_count
    
    except Exception as e:
        logger.error(f"Error migrating files: {e}")
        return False, f"Error migrating files: {str(e)}", 0

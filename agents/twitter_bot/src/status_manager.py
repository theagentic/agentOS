"""
Status Manager module for the Twitter Bot agent.
Handles status file management, cleanup, and utilities.
"""
import os
import glob
import json
import logging
from datetime import datetime, timedelta
from .path_utils import ensure_directory_exists, fix_directory_permissions, create_fallback_directory, migrate_files

logger = logging.getLogger(__name__)

class StatusManager:
    """Manages status files for the Twitter Bot agent."""
    
    def __init__(self, status_dir=None):
        """
        Initialize the status manager.
        
        Args:
            status_dir: Directory where status files are stored
        """
        self.default_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "status"
        )
        self.fallback_dir = None
        self.using_fallback = False
        
        # Use provided directory or default
        self.status_dir = status_dir if status_dir else self.default_dir
        
        # Ensure the status directory exists and is accessible
        self._ensure_status_directory()
            
        logger.debug(f"Status manager initialized with directory: {self.status_dir}")
    
    def _ensure_status_directory(self):
        """
        Ensure the status directory exists and is accessible.
        If not, try to fix permissions or use a fallback directory.
        """
        exists, accessible, message = ensure_directory_exists(self.status_dir, create=True)
        
        if exists and accessible:
            # Directory exists and is accessible, all good
            logger.info(f"Using status directory: {self.status_dir}")
            return
        
        # Try to fix permissions if directory exists but isn't accessible
        if exists and not accessible:
            logger.warning(f"Status directory exists but is not accessible: {self.status_dir}")
            logger.warning(f"Reason: {message}")
            
            # Try to fix permissions
            success, fix_message = fix_directory_permissions(self.status_dir)
            if success:
                # Check again if it's accessible now
                exists, accessible, _ = ensure_directory_exists(self.status_dir, create=False)
                if accessible:
                    logger.info(f"Fixed permissions for status directory: {self.status_dir}")
                    return
            
            logger.warning(f"Could not fix permissions: {fix_message}")
        
        # If we get here, we need to use a fallback directory
        logger.warning("Using fallback directory for status files")
        success, result = create_fallback_directory()
        
        if success:
            # Set fallback directory and mark as using fallback
            self.fallback_dir = result
            self.using_fallback = True
            
            # Update the status directory to use the fallback
            self.status_dir = self.fallback_dir
            
            # Try to migrate existing files if the original directory exists
            if os.path.exists(self.default_dir) and os.path.isdir(self.default_dir):
                migrated, message, count = migrate_files(self.default_dir, self.fallback_dir)
                if migrated and count > 0:
                    logger.info(f"Migrated {count} files from {self.default_dir} to {self.fallback_dir}")
            
            logger.info(f"Using fallback status directory: {self.fallback_dir}")
        else:
            # Cannot create fallback directory, this is a critical error
            logger.critical(f"Cannot create or access any status directory: {result}")
            # Continue with the default directory, but operations may fail
    
    def clean_old_files(self, max_age_days=7, keep_latest=5, exclude_patterns=None):
        """
        Clean up old status files.
        
        Args:
            max_age_days: Maximum age of files to keep (in days)
            keep_latest: Minimum number of latest files to keep regardless of age
            exclude_patterns: List of filename patterns to exclude from cleanup
            
        Returns:
            Tuple of (number of files deleted, number of files kept)
        """
        if exclude_patterns is None:
            exclude_patterns = ["README.md", ".gitkeep", "README.txt"]
            
        try:
            # Check if the directory exists and is accessible
            exists, accessible, message = ensure_directory_exists(self.status_dir, create=False)
            if not exists or not accessible:
                logger.warning(f"Cannot clean status directory: {message}")
                return 0, 0
            
            # Get all JSON files in the status directory
            json_files = glob.glob(os.path.join(self.status_dir, "*.json"))
            
            # Skip if no files found
            if not json_files:
                logger.debug("No status files found for cleanup")
                return 0, 0
                
            # Filter out excluded files
            for pattern in exclude_patterns:
                json_files = [f for f in json_files if pattern not in f]
                
            # Get file info with timestamps
            file_info = []
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            for file_path in json_files:
                try:
                    # Get the file's modified time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Try to parse timestamp from the file content
                    timestamp = None
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if 'timestamp' in data:
                                # Parse ISO format timestamp
                                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    except Exception:
                        # If we can't read the file or parse timestamp, use file modified time
                        pass
                        
                    # Use the timestamp from file content if available, otherwise use modified time
                    file_time = timestamp if timestamp else mod_time
                    
                    file_info.append({
                        'path': file_path,
                        'time': file_time,
                        'name': os.path.basename(file_path)
                    })
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {e}")
            
            # Sort files by time (newest first)
            file_info.sort(key=lambda x: x['time'], reverse=True)
            
            # Keep the most recent files up to keep_latest
            files_to_keep = file_info[:keep_latest]
            
            # For the rest, keep only those that are newer than the cutoff date
            for file in file_info[keep_latest:]:
                if file['time'] > cutoff_date:
                    files_to_keep.append(file)
            
            # Determine which files to delete
            files_to_delete = [f for f in file_info if f not in files_to_keep]
            
            # Delete the old files
            deleted_count = 0
            for file in files_to_delete:
                try:
                    os.remove(file['path'])
                    deleted_count += 1
                    logger.debug(f"Deleted old status file: {file['name']} (from {file['time']})")
                except Exception as e:
                    logger.warning(f"Error deleting file {file['path']}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Status cleanup: deleted {deleted_count} old files, kept {len(files_to_keep)} files")
            
            return deleted_count, len(files_to_keep)
            
        except Exception as e:
            logger.error(f"Error in status file cleanup: {e}")
            return 0, 0
    
    def clean_by_status(self, status_values=None):
        """
        Clean status files by their status value.
        
        Args:
            status_values: List of status values to remove (e.g., ["complete", "error"])
            
        Returns:
            Number of files deleted
        """
        if status_values is None:
            status_values = ["complete", "error"]
        
        deleted_count = 0
        
        try:
            # Check if the directory exists and is accessible
            exists, accessible, message = ensure_directory_exists(self.status_dir, create=False)
            if not exists or not accessible:
                logger.warning(f"Cannot clean status files: {message}")
                return 0
                
            # Get all JSON files
            json_files = glob.glob(os.path.join(self.status_dir, "*.json"))
            
            for file_path in json_files:
                try:
                    # Read file and check status
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if 'status' in data and data['status'] in status_values:
                        # This file has a status that should be cleaned
                        os.remove(file_path)
                        deleted_count += 1
                        logger.debug(f"Deleted status file with status '{data['status']}': {os.path.basename(file_path)}")
                except Exception:
                    # Skip files that can't be read or don't match
                    continue
                    
            if deleted_count > 0:
                logger.info(f"Status cleanup by status: deleted {deleted_count} files with status in {status_values}")
                
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error in status cleanup by status: {e}")
            return 0
    
    def get_status_file_path(self, filename):
        """
        Get the full path for a status file.
        
        Args:
            filename: The name of the status file
            
        Returns:
            Full path to the status file
        """
        # Make sure the directory exists before returning the path
        exists, accessible, message = ensure_directory_exists(self.status_dir, create=True)
        if not exists or not accessible:
            logger.warning(f"Status directory issue: {message}")
            
            # If we have a fallback directory but aren't using it yet, switch to it
            if not self.using_fallback:
                success, result = create_fallback_directory()
                if success:
                    self.fallback_dir = result
                    self.status_dir = result
                    self.using_fallback = True
                    logger.info(f"Switched to fallback directory: {self.status_dir}")
                    
                    # Ensure the fallback directory exists
                    ensure_directory_exists(self.status_dir, create=True)
                    
        return os.path.join(self.status_dir, filename)

    def get_status_directory_info(self):
        """
        Get information about the status directory.
        
        Returns:
            Dictionary with status directory information
        """
        exists, accessible, message = ensure_directory_exists(self.status_dir, create=False)
        
        info = {
            "directory": self.status_dir,
            "exists": exists,
            "accessible": accessible,
            "using_fallback": self.using_fallback,
            "fallback_directory": self.fallback_dir,
            "message": message
        }
        
        if exists:
            try:
                # Count files
                json_files = glob.glob(os.path.join(self.status_dir, "*.json"))
                info["file_count"] = len(json_files)
                
                # Check for specific files
                info["has_status_file"] = os.path.exists(os.path.join(self.status_dir, "twitter_status.json"))
                info["has_rate_limit_file"] = os.path.exists(os.path.join(self.status_dir, "rate_limit.json"))
                
                # Get space info
                try:
                    if os.name == 'nt':  # Windows
                        import ctypes
                        free_bytes = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            ctypes.c_wchar_p(self.status_dir), None, None, ctypes.pointer(free_bytes))
                        info["free_space"] = free_bytes.value
                    else:
                        stats = os.statvfs(self.status_dir)
                        info["free_space"] = stats.f_bavail * stats.f_frsize
                except Exception as e:
                    info["free_space"] = f"Error: {str(e)}"
            except Exception as e:
                info["error"] = str(e)
        
        return info

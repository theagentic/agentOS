import os
import logging
import time
from datetime import datetime
from pathlib import Path

def setup_logging(log_file, log_level=logging.INFO):
    """Set up logging with the specified file and level."""
    log_file_path = os.path.expanduser(log_file)
    log_dir = os.path.dirname(log_file_path)
    
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        filename=log_file_path,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger('file_manager')

def ensure_dir_exists(directory):
    """Ensure the specified directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        return True
    return False

def get_file_size_mb(file_path):
    """Get file size in megabytes."""
    return os.path.getsize(file_path) / (1024 * 1024)

def get_file_access_time_days(file_path):
    """Get file access time in days from now."""
    access_time = os.path.getatime(file_path)
    current_time = time.time()
    return (current_time - access_time) / (60 * 60 * 24)  # Convert seconds to days

def format_timestamp(format_string):
    """Format current timestamp according to the provided format string."""
    timestamp = datetime.now()
    return timestamp.strftime(format_string.replace('YYYY', '%Y')
                              .replace('MM', '%m')
                              .replace('DD', '%d')
                              .replace('HH', '%H')
                              .replace('MM', '%M')
                              .replace('SS', '%S'))

def parse_schedule(schedule_str):
    """Parse schedule string to seconds."""
    if schedule_str == "hourly":
        return 60 * 60
    elif schedule_str == "daily":
        return 24 * 60 * 60
    elif schedule_str == "weekly":
        return 7 * 24 * 60 * 60
    elif schedule_str == "monthly":
        return 30 * 24 * 60 * 60
    elif schedule_str == "continuous":
        return 10  # Check every 10 seconds
    else:
        try:
            # Assume schedule_str is in seconds
            return int(schedule_str)
        except ValueError:
            return 3600  # Default to hourly if unrecognized format

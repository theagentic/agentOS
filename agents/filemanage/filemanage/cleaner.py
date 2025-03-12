import os
import shutil
import logging
from datetime import datetime, timedelta
from . import utils

class FileCleaner:
    def __init__(self, config):
        self.logger = logging.getLogger('file_manager.cleaner')
        self.clean_directories = config.get('clean_directories', [os.path.expanduser('~/Downloads')])
        self.access_threshold_days = config.get('access_time_threshold_days', 90)
        self.size_threshold_mb = config.get('size_threshold_mb', 50)
        self.file_type_exclusions = config.get('file_type_exclusions', ['.exe', '.dll'])
        self.safe_delete = config.get('safe_delete', True)
        self.trash_folder_name = config.get('trash_folder_name', '.file_trash')
        
    def clean(self):
        """Clean unused files from specified directories."""
        self.logger.info(f"Starting file cleaning process with {len(self.clean_directories)} directories")
        
        for directory in self.clean_directories:
            if os.path.exists(directory):
                self._clean_directory(directory)
            else:
                self.logger.warning(f"Directory does not exist: {directory}")
                
        self.logger.info("File cleaning process completed")
                
    def _clean_directory(self, directory):
        """Clean unused files from a single directory."""
        self.logger.info(f"Scanning directory: {directory}")
        
        # Create trash folder if safe_delete is enabled
        trash_path = None
        if self.safe_delete:
            trash_path = os.path.join(directory, self.trash_folder_name)
            utils.ensure_dir_exists(trash_path)
            
        # Track files that were cleaned for logging
        cleaned_files = []
        total_size_cleaned = 0
        
        # Walk through directory recursively
        for root, dirs, files in os.walk(directory):
            # Skip the trash folder itself
            if os.path.basename(root) == self.trash_folder_name:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file should be cleaned
                if self._should_clean_file(file_path):
                    try:
                        # Get file size before cleaning
                        file_size = utils.get_file_size_mb(file_path)
                        
                        if self.safe_delete:
                            # Move to trash folder
                            trash_subpath = os.path.relpath(root, directory)
                            trash_destination = os.path.join(trash_path, trash_subpath)
                            
                            # Create subdirectories in trash if needed
                            if not os.path.exists(trash_destination):
                                os.makedirs(trash_destination, exist_ok=True)
                                
                            shutil.move(file_path, os.path.join(trash_destination, file))
                            self.logger.info(f"Moved to trash: {file_path}")
                        else:
                            # Permanently delete
                            os.remove(file_path)
                            self.logger.info(f"Permanently deleted: {file_path}")
                            
                        cleaned_files.append(file_path)
                        total_size_cleaned += file_size
                    except (PermissionError, OSError) as e:
                        self.logger.error(f"Error cleaning {file_path}: {e}")
                        
        # Log summary
        self.logger.info(f"Cleaned {len(cleaned_files)} files, freeing {total_size_cleaned:.2f} MB in {directory}")
        
    def _should_clean_file(self, file_path):
        """Determine if a file should be cleaned based on criteria."""
        try:
            # Check file extension exclusions
            _, extension = os.path.splitext(file_path.lower())
            if extension in self.file_type_exclusions:
                return False
                
            # Check file size
            file_size = utils.get_file_size_mb(file_path)
            if file_size < self.size_threshold_mb:
                return False
                
            # Check access time
            access_days = utils.get_file_access_time_days(file_path)
            return access_days > self.access_threshold_days
            
        except (OSError, PermissionError) as e:
            self.logger.warning(f"Cannot check file {file_path}: {e}")
            return False

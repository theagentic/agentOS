import os
import shutil
import logging
from pathlib import Path
from . import utils

class FileOrganizer:
    def __init__(self, config):
        self.logger = logging.getLogger('file_manager.organizer')
        self.target_directory = config.get('target_directory', os.path.expanduser('~/Downloads'))
        self.file_type_folders = config.get('file_type_folders', {})
        
    def organize(self):
        """Organize files in the target directory based on file extensions."""
        self.logger.info(f"Starting file organization in {self.target_directory}")
        
        if not os.path.exists(self.target_directory):
            self.logger.error(f"Target directory does not exist: {self.target_directory}")
            return

        # Get all files in the target directory
        try:
            files = [f for f in os.listdir(self.target_directory) 
                     if os.path.isfile(os.path.join(self.target_directory, f))]
        except PermissionError:
            self.logger.error(f"Permission denied accessing {self.target_directory}")
            return
            
        for file_name in files:
            self._organize_file(file_name)
        
        self.logger.info(f"File organization completed for {self.target_directory}")
    
    def _organize_file(self, file_name):
        """Organize a single file based on its extension."""
        file_path = os.path.join(self.target_directory, file_name)
        
        # Skip hidden files
        if file_name.startswith('.'):
            return
            
        # Get file extension
        _, extension = os.path.splitext(file_name.lower())
        
        # Skip if no extension
        if not extension:
            return
            
        # Check if we have a mapping for this extension
        if extension in self.file_type_folders:
            folder_name = self.file_type_folders[extension]
            destination_folder = os.path.join(self.target_directory, folder_name)
            
            # Create destination folder if it doesn't exist
            if '/' in folder_name:  # Handle subdirectories
                utils.ensure_dir_exists(destination_folder)
            else:
                os.makedirs(destination_folder, exist_ok=True)
            
            # Move the file
            destination_path = os.path.join(destination_folder, file_name)
            
            # If file already exists in destination, don't overwrite
            if os.path.exists(destination_path):
                base_name, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(destination_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    destination_path = os.path.join(destination_folder, new_name)
                    counter += 1
                
            try:
                shutil.move(file_path, destination_path)
                self.logger.info(f"Moved {file_name} to {os.path.relpath(destination_path, self.target_directory)}")
            except (shutil.Error, PermissionError) as e:
                self.logger.error(f"Error moving {file_name}: {e}")

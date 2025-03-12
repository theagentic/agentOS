import os
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from . import utils

class BackupSystem:
    def __init__(self, config):
        self.logger = logging.getLogger('file_manager.backup')
        self.backup_sources = config.get('backup_sources', [os.path.expanduser('~/Downloads')])
        self.backup_destination = config.get('backup_destination', os.path.expanduser('~/Backups'))
        self.naming_convention = config.get('backup_naming_convention', 'AutomatedBackup_YYYY-MM-DD_HH-MM-SS.zip')
        self.encrypt_backups = config.get('encrypt_backups', False)
        
    def create_backup(self):
        """Create backup of specified sources."""
        self.logger.info(f"Starting backup process for {len(self.backup_sources)} sources")
        
        # Create backup destination if it doesn't exist
        utils.ensure_dir_exists(self.backup_destination)
        
        # Generate backup filename based on naming convention
        backup_filename = utils.format_timestamp(self.naming_convention)
        backup_path = os.path.join(self.backup_destination, backup_filename)
        
        try:
            self._create_zip_backup(backup_path)
            self.logger.info(f"Backup successfully created at {backup_path}")
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            
    def _create_zip_backup(self, backup_path):
        """Create a zip archive of the source directories."""
        # Use ZIP_DEFLATED for better compression
        compression = zipfile.ZIP_DEFLATED
        
        with zipfile.ZipFile(backup_path, 'w', compression=compression) as backup_zip:
            # Process each source directory/file
            for source in self.backup_sources:
                if not os.path.exists(source):
                    self.logger.warning(f"Backup source does not exist: {source}")
                    continue
                    
                self.logger.info(f"Adding {source} to backup")
                
                if os.path.isdir(source):
                    self._add_directory_to_zip(backup_zip, source)
                else:
                    # For single files, add them directly with their basename as arcname
                    backup_zip.write(source, os.path.basename(source))
    
    def _add_directory_to_zip(self, zip_file, directory):
        """Add a directory and its contents to the zip file."""
        source_base = os.path.basename(directory)
        
        for root, dirs, files in os.walk(directory):
            # Skip the trash folder if it exists
            if ".file_trash" in dirs:
                dirs.remove(".file_trash")
                
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Create arcname (path within the zip file)
            arcroot = os.path.join(source_base, os.path.relpath(root, directory))
            
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.join(arcroot, file)
                
                try:
                    zip_file.write(file_path, arcname)
                except (PermissionError, OSError) as e:
                    self.logger.warning(f"Error adding file {file_path} to backup: {e}")

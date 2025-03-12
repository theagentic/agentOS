import os
import json
from pathlib import Path

class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            # Default to config.json in the same directory as this script
            self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        else:
            self.config_path = config_path
        
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as config_file:
                config = json.load(config_file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {self.config_path}")
    
    def get_organizer_config(self):
        """Get configuration for file organizer module."""
        return self._expand_paths(self.config.get('organize', {}))
    
    def get_backup_config(self):
        """Get configuration for backup module."""
        backup_config = self.config.get('backup', {})
        if 'backup_sources' in backup_config:
            backup_config['backup_sources'] = [self._expand_path(path) for path in backup_config['backup_sources']]
        if 'backup_destination' in backup_config:
            backup_config['backup_destination'] = self._expand_path(backup_config['backup_destination'])
        return backup_config
    
    def get_cleaner_config(self):
        """Get configuration for file cleaner module."""
        cleaner_config = self.config.get('clean', {})
        if 'clean_directories' in cleaner_config:
            cleaner_config['clean_directories'] = [self._expand_path(path) for path in cleaner_config['clean_directories']]
        return cleaner_config
    
    def get_logging_config(self):
        """Get configuration for logging."""
        return self.config.get('logging', {'log_file': 'file_manager.log', 'log_level': 'INFO'})
    
    def _expand_paths(self, config_section):
        """Expand paths in a configuration section."""
        if 'target_directory' in config_section:
            config_section['target_directory'] = self._expand_path(config_section['target_directory'])
        return config_section
    
    def _expand_path(self, path):
        """Expand user home directory in a path."""
        return os.path.expanduser(path) if isinstance(path, str) else path

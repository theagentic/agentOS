import os
import time
import logging
import threading
import signal
import sys
from pathlib import Path

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filemanage import utils
from filemanage.config import Config
from filemanage.organizer import FileOrganizer
from filemanage.backup import BackupSystem
from filemanage.cleaner import FileCleaner

class FileManager:
    def __init__(self, config_path=None):
        # Load configuration
        self.config = Config(config_path)
        
        # Set up logging
        log_config = self.config.get_logging_config()
        self.logger = utils.setup_logging(log_config.get('log_file', 'file_manager.log'),
                                         getattr(logging, log_config.get('log_level', 'INFO')))
        
        # Initialize modules
        self.organizer = FileOrganizer(self.config.get_organizer_config())
        self.backup_system = BackupSystem(self.config.get_backup_config())
        self.cleaner = FileCleaner(self.config.get_cleaner_config())
        
        # Threads for background processes
        self.threads = []
        self.stop_event = threading.Event()
        
    def start(self):
        """Start the file manager background processes."""
        self.logger.info("Starting File Manager background processes")
        
        # Schedule the organizer
        organizer_config = self.config.get_organizer_config()
        schedule_str = organizer_config.get('organize_schedule', 'hourly')
        self._start_background_task(self.organizer.organize, utils.parse_schedule(schedule_str), "organizer")
        
        # Schedule the backup system
        backup_config = self.config.get_backup_config()
        schedule_str = backup_config.get('backup_schedule', 'daily')
        self._start_background_task(self.backup_system.create_backup, utils.parse_schedule(schedule_str), "backup")
        
        # Schedule the cleaner
        cleaner_config = self.config.get_cleaner_config()
        schedule_str = cleaner_config.get('clean_schedule', 'weekly')
        self._start_background_task(self.cleaner.clean, utils.parse_schedule(schedule_str), "cleaner")
        
        self.logger.info("All background processes started")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Keep main thread alive
            while not self.stop_event.is_set():
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
            
    def stop(self):
        """Stop all background processes."""
        self.logger.info("Stopping File Manager background processes")
        self.stop_event.set()
        
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
                
        self.logger.info("All background processes stopped")
        
    def _start_background_task(self, task_func, interval, task_name):
        """Start a task in a background thread with the specified interval."""
        def run_task():
            self.logger.info(f"Starting {task_name} task thread with interval {interval} seconds")
            while not self.stop_event.is_set():
                try:
                    task_func()
                except Exception as e:
                    self.logger.error(f"Error in {task_name} task: {e}")
                
                # Sleep for the interval or until stop_event is set
                self.stop_event.wait(interval)
                
        # Create and start the thread
        thread = threading.Thread(target=run_task, name=f"{task_name}_thread")
        thread.daemon = True  # Thread will exit when main program exits
        thread.start()
        self.threads.append(thread)
        
    def _signal_handler(self, sig, frame):
        """Handle termination signals."""
        self.logger.info(f"Received signal {sig}")
        self.stop()
        sys.exit(0)

def main():
    """Main entry point for the file manager."""
    manager = FileManager()
    manager.start()

if __name__ == "__main__":
    main()

"""
Process Logger

Provides detailed logging of each process step and AI responses.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

class ProcessLogger:
    """
    Logs detailed information about agent processes and AI responses.
    Acts as a central hub for system-wide logging with UI callbacks.
    """
    
    def __init__(self, log_to_file: bool = True, log_to_console: bool = True):
        """
        Initialize the process logger.
        
        Args:
            log_to_file: Whether to write logs to file
            log_to_console: Whether to output logs to console
        """
        self.logger = logging.getLogger("process")
        self.execution_callback = None
        self.conversation_callback = None
        
        # Configure logging
        if log_to_file or log_to_console:
            handlers = []
            
            if log_to_console:
                handlers.append(logging.StreamHandler())
                
            if log_to_file:
                log_dir = Path(__file__).parent.parent / "logs"
                log_dir.mkdir(exist_ok=True)
                log_file = log_dir / "process_log.txt"
                handlers.append(logging.FileHandler(log_file))
            
            for handler in handlers:
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                
            self.logger.setLevel(logging.INFO)
    
    def register_execution_callback(self, callback: Callable[[str], None]):
        """
        Register a callback to receive execution log messages.
        
        Args:
            callback: Function that takes a log message string
        """
        self.execution_callback = callback
    
    def register_conversation_callback(self, callback: Callable[[str, str], None]):
        """
        Register a callback to receive conversation messages.
        
        Args:
            callback: Function that takes (message, message_type)
        """
        self.conversation_callback = callback
    
    def log_execution(self, message: str, level: str = "info"):
        """
        Log an execution step.
        
        Args:
            message: The log message
            level: Log level (info, warning, error)
        """
        # Log to file/console
        if level == "info":
            self.logger.info(f"EXEC: {message}")
        elif level == "warning":
            self.logger.warning(f"EXEC: {message}")
        elif level == "error":
            self.logger.error(f"EXEC: {message}")
            
        # Call execution display callback if registered
        if self.execution_callback:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.execution_callback(f"[{timestamp}] {message}")
    
    def log_conversation(self, message: str, message_type: str):
        """
        Log a conversation message.
        
        Args:
            message: The conversation message
            message_type: Type of message (user, assistant, system)
        """
        self.logger.info(f"CONV {message_type.upper()}: {message}")
        
        # Call conversation callback if registered
        if self.conversation_callback:
            self.conversation_callback(message, message_type)
    
    def log_ai_response(self, response: Dict[str, Any], agent_name: str):
        """
        Log an AI-generated response with details.
        
        Args:
            response: The response dictionary from the agent
            agent_name: Name of the agent that generated the response
        """
        self.log_execution(f"AI Response from {agent_name}:")
        
        # Log the full structure for debugging
        for key, value in response.items():
            if key != 'data':  # Skip large data structures
                self.log_execution(f"  {key}: {value}")
        
        # Extract the spoken response if available
        if 'spoke' in response:
            self.log_conversation(f"Assistant: {response['spoke']}", "assistant")

    def log_process_start(self, process_name: str, details: Optional[Dict[str, Any]] = None):
        """Log the start of a process with timestamp and details."""
        start_time = time.time()
        self.log_execution(f"Starting process: {process_name}")
        
        if details:
            for key, value in details.items():
                self.log_execution(f"  {key}: {value}")
                
        return start_time
    
    def log_process_end(self, process_name: str, start_time: float):
        """Log the end of a process with elapsed time."""
        elapsed = time.time() - start_time
        self.log_execution(f"Completed process: {process_name} (took {elapsed:.2f}s)")

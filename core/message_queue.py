"""
Message Queue for streaming updates to UI.
"""
import time
import logging
import threading
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageQueue:
    """
    Queue for streaming messages to the UI.
    Allows agents to provide ongoing updates during long-running processes.
    """
    
    # Class-level dictionary of all active queues
    _queues = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_queue(cls, queue_id):
        """Get a queue by its ID."""
        with cls._lock:
            return cls._queues.get(queue_id)
    
    @classmethod
    def get_all_messages(cls):
        """Get all pending messages from all queues."""
        messages = []
        with cls._lock:
            for queue in cls._queues.values():
                messages.extend(queue.get_messages())
        return messages
    
    @classmethod
    def cleanup_old_queues(cls, max_age_seconds=300):
        """Remove queues that haven't been updated in a while."""
        now = time.time()
        with cls._lock:
            to_remove = []
            for queue_id, queue in cls._queues.items():
                if now - queue.last_update > max_age_seconds:
                    to_remove.append(queue_id)
            
            for queue_id in to_remove:
                del cls._queues[queue_id]
                logger.debug(f"Removed inactive queue {queue_id}")
    
    def __init__(self, queue_id=None, max_size=100):
        """
        Initialize a message queue.
        
        Args:
            queue_id: Optional queue ID (generated if not provided)
            max_size: Maximum number of messages to store
        """
        self.queue_id = queue_id or str(uuid.uuid4())
        self.max_size = max_size
        self.messages = []
        self.last_update = time.time()
        self.creation_time = self.last_update
        
        # Register this queue
        with self.__class__._lock:
            self.__class__._queues[self.queue_id] = self
        
        logger.debug(f"Created message queue {self.queue_id}")
    
    def add_message(self, message):
        """
        Add a message to the queue.
        
        Args:
            message: The message to add (dictionary)
        """
        with self.__class__._lock:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
                
            # Add queue ID
            message["queue_id"] = self.queue_id
            
            # Add the message
            self.messages.append(message)
            
            # Trim if necessary
            if len(self.messages) > self.max_size:
                self.messages = self.messages[-self.max_size:]
            
            # Update last activity time
            self.last_update = time.time()
    
    def get_messages(self, clear=True):
        """
        Get messages from the queue.
        
        Args:
            clear: Whether to clear the queue after retrieval
            
        Returns:
            List of messages
        """
        with self.__class__._lock:
            messages = list(self.messages)
            if clear:
                self.messages = []
            self.last_update = time.time()
            return messages
    
    def __del__(self):
        """Clean up when the object is garbage collected."""
        try:
            with self.__class__._lock:
                if self.queue_id in self.__class__._queues:
                    del self.__class__._queues[self.queue_id]
        except Exception:
            # Ignore errors during cleanup
            pass

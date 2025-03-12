import logging
import importlib
import os
import re
import traceback
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class AgentRouter:
    """Routes commands to the appropriate agent."""
    
    def __init__(self, process_logger=None):
        """Initialize the agent router."""
        self.agents = {}
        self.process_logger = process_logger
        self.last_agent = None
        self.load_agent_modules()
        self.use_natural_language = True  # Enable natural language processing by default
    
    def load_agent_modules(self):
        """Load all agent modules from the agents directory."""
        # Get the parent directory of core
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agents_dir = os.path.join(parent_dir, "agents")
        
        # Get all agent directories
        agent_dirs = [d for d in os.listdir(agents_dir) 
                    if os.path.isdir(os.path.join(agents_dir, d)) 
                    and not d.startswith("__")]
        
        for agent_dir in agent_dirs:
            try:
                # Try to load the agent module
                module_name = f"agents.{agent_dir}.agent"
                module = importlib.import_module(module_name)
                
                # Find all classes that end with 'Agent'
                agent_classes = [cls for name, cls in module.__dict__.items() 
                               if name.endswith("Agent") and callable(cls)]
                
                if agent_classes:
                    # Use the first agent class
                    agent_class = agent_classes[0]
                    # Initialize the agent
                    agent = agent_class()
                    # Register the agent
                    self.agents[agent_dir] = agent
                    logger.info(f"Loaded agent: {agent_dir}")
            except Exception as e:
                logger.error(f"Failed to load agent {agent_dir}: {e}")
                traceback.print_exc()
        
        logger.info(f"Loaded {len(self.agents)} agents")

    def get_agent_names(self) -> List[str]:
        """Return a list of loaded agent names."""
        return list(self.agents.keys())

    def route_command(self, command: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Alias for process_command to ensure backward compatibility.
        
        Args:
            command: The command to process
            verbose: Whether to include verbose output
            
        Returns:
            The response from the agent
        """
        return self.process_command(command, verbose)

    def process_command(self, command: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Process a command and route to the appropriate agent.
        
        Args:
            command: The command to process
            verbose: Whether to include verbose output
            
        Returns:
            The response from the agent
        """
        if not command:
            return {
                "status": "error",
                "message": "Empty command",
                "spoke": "I didn't receive any command to process."
            }
        
        try:
            # Log the command if we have a process logger
            if self.process_logger:
                self.process_logger.log_execution(f"Routing command: {command}")
            
            # Try to handle as direct command first (format: "<agent> <command>")
            direct_result = self._try_direct_command(command, verbose)
            if direct_result:
                return direct_result
            
            # Try natural language processing if enabled and direct command fails
            if self.use_natural_language and "natural_language" in self.agents:
                # This doesn't look like a direct agent command, try natural language processing
                logger.info("Using natural language processing for command")
                if self.process_logger:
                    self.process_logger.log_execution("Using natural language processing")
                
                # Use the natural language agent to translate the command
                nlp_result = self._process_with_agent(self.agents["natural_language"], command, verbose)
                
                # Check if the translation was successful and contains a command
                if (nlp_result.get("status") == "success" and 
                    "command" in nlp_result and 
                    isinstance(nlp_result["command"], str)):
                    
                    # Log the translation
                    if self.process_logger:
                        self.process_logger.log_execution(
                            f"NLP translated '{command}' to '{nlp_result['command']}'"
                        )
                    
                    # Use the translated command
                    translated_command = nlp_result["command"]
                    logger.info(f"NLP translation: '{command}' -> '{translated_command}'")
                    
                    # Process the translated command directly
                    result = self._route_command_direct(translated_command, verbose)
                    
                    # Add NLP metadata to the result if successful
                    if isinstance(result, dict):
                        result["nlp_processed"] = True
                        result["original_query"] = command
                        if "agent" not in result and "agent" in nlp_result:
                            result["agent"] = nlp_result["agent"]
                    
                    return result
            
            # If all else fails, try the content-based routing
            return self._route_command(command, verbose)
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "spoke": "Sorry, there was an error processing your command."
            }

    def _try_direct_command(self, command: str, verbose: bool) -> Optional[Dict[str, Any]]:
        """Try to process a command directly if it starts with an agent name."""
        # Make command handling case-insensitive by normalizing to lowercase
        command_lower = command.lower()
        
        # Special handling for voice commands that might be misheard
        # This helps with common voice recognition errors
        if "Twitter" in command or "tweet" in command_lower:
            if "twitter_bot" in self.agents:
                # Log the routing decision for debugging
                logger.info(f"Routing Twitter-related command to twitter_bot agent: {command}")
                self.last_agent = "twitter_bot"
                return self._process_with_agent(self.agents["twitter_bot"], command, verbose)
        
        # Try direct agent command (format: "<agent> <command>")
        agent_match = re.match(r"^(\w+)(?:\s+(.+))?$", command, re.IGNORECASE)
        
        if agent_match:
            agent_name = agent_match.group(1).lower()
            agent_command = agent_match.group(2) or ""
            
            if agent_name in self.agents:
                # Process with the specific agent
                self.last_agent = agent_name
                result = self._process_with_agent(self.agents[agent_name], agent_command, verbose)
                
                # Ensure agent field is set properly in the response
                if isinstance(result, dict) and "agent" not in result:
                    result["agent"] = agent_name
                    
                return result
        
        # Not a direct command
        return None
    
    def _route_command_direct(self, command: str, verbose: bool) -> Dict[str, Any]:
        """Route a command directly without additional natural language processing."""
        # Check if this is a direct command with agent prefix
        direct_result = self._try_direct_command(command, verbose)
        if direct_result:
            return direct_result
        
        # If not a direct command, try content-based routing with NLP disabled
        old_nlp_setting = self.use_natural_language
        self.use_natural_language = False
        try:
            return self._route_command(command, verbose)
        finally:
            # Restore the natural language setting
            self.use_natural_language = old_nlp_setting

    def _process_with_agent(self, agent, command: str, verbose: bool) -> Dict[str, Any]:
        """Process a command with a specific agent."""
        try:
            result = agent.process(command)
            
            # Make sure result is a dictionary with required fields
            if not isinstance(result, dict):
                result = {"message": str(result), "status": "success"}
            
            # Add spoke field if missing
            if "spoke" not in result and "message" in result:
                result["spoke"] = result["message"]
                
            # Ensure agent field is set correctly
            if "agent" not in result:
                # Try to get the agent name from the agent's class
                agent_class = agent.__class__.__name__
                agent_id = None
                
                # Check if the agent has a specific ID attribute first
                if hasattr(agent, 'agent_id'):
                    agent_id = agent.agent_id
                else:
                    # Otherwise derive it from the class name
                    if agent_class.endswith("Agent"):
                        agent_id = agent_class[:-5].lower()
                
                result["agent"] = agent_id
            
            # Add verbose data if requested
            if verbose:
                # Add any additional data that might be helpful
                result["verbose"] = {
                    "agent_class": agent.__class__.__name__,
                    "timestamp": self._get_timestamp()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in agent process: {e}")
            return {
                "status": "error",
                "message": f"Agent error: {str(e)}",
                "spoke": "Sorry, there was an error processing your request."
            }

    def _route_command(self, command: str, verbose: bool) -> Dict[str, Any]:
        """Route a command to the appropriate agent based on content."""
        # Check for specific Twitter-related keywords first with more flexibility for voice recognition
        twitter_keywords = [
            # Standard keywords
            "tweet", "twitter", "post thread", "post blog", "create thread", 
            "blog thread", "timeline", "notifications", "blog to twitter", 
            
            # Voice recognition variations - common misheard words
            "tweeter", "twit", "twitters", "tweeting", "treat", "sweet",
            "treated", "post blood", "post threat", "post blog thread", 
            "post block", "blogger", "blogging", "create treat",
            "treat started", "thread started",
            
            # Phonetic variations
            "twittr", "twitr", "tuitter", "twiter"
        ]
        
        command_lower = command.lower()
        
        # Special case for Twitter - check both exact and approximate matches
        if any(keyword in command_lower for keyword in twitter_keywords) and "twitter_bot" in self.agents:
            logger.info(f"Routing Twitter-related command to twitter_bot agent: {command}")
            self.last_agent = "twitter_bot"
            return self._process_with_agent(self.agents["twitter_bot"], command, verbose)
        
        # First check if we have a last agent that might handle follow-ups
        if self.last_agent and self.last_agent in self.agents:
            result = self._process_with_agent(self.agents[self.last_agent], command, verbose)
            # If the agent understood the command, return its result
            if result.get("status") != "error":
                return result
        
        # Special handling for voice command variations
        if "twitter_bot" in self.agents:
            # Check for command variations that might be misheard
            if any(x in command_lower for x in ["tweet", "twit", "threat", "treat", "sweet"]):
                logger.info(f"Routing possible Twitter command to twitter_bot agent: {command}")
                self.last_agent = "twitter_bot"
                return self._process_with_agent(self.agents["twitter_bot"], command, verbose)
        
        # Other command routing logic
        for agent_name, agent in self.agents.items():
            try:
                result = self._process_with_agent(agent, command, verbose)
                if result.get("status") != "error":
                    self.last_agent = agent_name
                    
                    # Ensure agent field is set properly
                    if "agent" not in result:
                        result["agent"] = agent_name
                        
                    return result
            except Exception:
                pass
        
        # No agent could handle the command
        return {
            "status": "error",
            "message": "I'm not sure how to help with that. Please try a different command.",
            "spoke": "I'm not sure how to help with that. Please try a different command."
        }

    def _get_timestamp(self) -> str:
        """Get a timestamp string for logging purposes."""
        from datetime import datetime
        return datetime.now().isoformat()

"""
Natural Language Processing Agent

This agent translates natural language queries to specific commands that can be
routed to the appropriate agent in the AgentOS system.

Features:
- Translates natural language to specific commands for other agents
- Supports multiple LLM backends:
  - Google's Gemini models (requires API key)
  - Local Ollama models (requires Ollama running)
- Handles voice input with conversational responses
- Runtime configuration of model providers and specific models
- Fallback translation for when LLM services are unavailable

Configuration:
- Environment variables (see .env.example)
  - NLP_MODEL_PROVIDER: "gemini" or "ollama"
  - GEMINI_API_KEY: API key for Google's Gemini models
  - GEMINI_MODEL: Specific Gemini model to use
  - OLLAMA_API_URL: URL for local Ollama API
  - OLLAMA_MODEL: Specific Ollama model to use
  - NLP_DEBUG: Enable debug logging

API Endpoints:
- /get_model_info: Get current model configuration
- /set_model_provider: Change the model provider
- /set_model: Change the specific model for the current provider
- /health_check: Get the health status of the agent

Usage:
1. Configure the .env file with appropriate model settings
2. The agent will automatically translate natural language to commands
3. Voice input is automatically processed for more conversational responses
"""

import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
from core.agent_base import AgentBase

# Conditional import of Google's generative AI library
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    GENAI_AVAILABLE = False

class NaturalLanguageAgent(AgentBase):
    """Agent that uses LLMs to translate natural language to specific commands."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the agent."""
        super().__init__("natural_language", config)
        
        # Load environment variables
        self.model_provider = os.getenv("NLP_MODEL_PROVIDER", "gemini").lower()
        
        # Gemini configuration
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        
        # Ollama configuration
        self.ollama_api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        # Debug setting
        self.debug = os.getenv("NLP_DEBUG", "false").lower() == "true"
        
        # Get all available agents from the router
        self.available_agents = []
        self._init_router()
        
        # Load saved preferences if they exist
        self._load_saved_preferences()
        
        # Configure Gemini if it's the selected provider
        if self.model_provider == "gemini" and GENAI_AVAILABLE:
            if not self.gemini_api_key:
                self.logger.warning("Gemini API key not configured. Falling back to Ollama.")
                self.model_provider = "ollama"
            else:
                try:
                    genai.configure(api_key=self.gemini_api_key)
                    self.logger.info("Gemini API configured successfully")
                except Exception as e:
                    self.logger.error(f"Error configuring Gemini API: {e}")
                    self.model_provider = "ollama"
        elif self.model_provider == "gemini" and not GENAI_AVAILABLE:
            self.logger.warning("Google generativeai package not available. Falling back to Ollama.")
            self.model_provider = "ollama"
        
        self.logger.info(f"NaturalLanguageAgent initialized with provider: {self.model_provider}")
        if self.model_provider == "gemini":
            self.logger.info(f"Using Gemini model: {self.gemini_model}")
        else:
            self.logger.info(f"Using Ollama model: {self.ollama_model}")
            
        if self.debug and self.available_agents:
            self.logger.info(f"Available agents: {', '.join(self.available_agents)}")
    
    def _init_router(self):
        """Initialize the agent router to get available agents."""
        try:
            # Try to get directory list directly to avoid import issues
            self._get_agent_directories()
            
            # If that failed or returned an empty list, try the import method
            if not self.available_agents:
                try:
                    # Import in local scope to avoid circular imports
                    from agents import get_agent_names
                    self.available_agents = get_agent_names()
                except (ImportError, AttributeError) as e:
                    self.logger.warning(f"Failed to import get_agent_names: {e}")
            
            # Remove ourselves from the available agents list to avoid confusion
            if "natural_language" in self.available_agents:
                self.available_agents.remove("natural_language")
                
        except Exception as e:
            self.logger.error(f"Error initializing agent list: {e}")
            # Fallback to some default agents
            self.available_agents = ["datetime", "filemanage", "twitter_bot", "spotiauto"]
            
    def _get_agent_directories(self):
        """Get agent names by looking at directories."""
        try:
            # Get the parent directory of the agent
            current_dir = os.path.dirname(os.path.abspath(__file__))
            agents_dir = os.path.dirname(current_dir)
            
            # Get all agent directories
            self.available_agents = [
                d for d in os.listdir(agents_dir) 
                if os.path.isdir(os.path.join(agents_dir, d)) 
                and not d.startswith("__")
                and d != "agent_template"
            ]
        except Exception as e:
            self.logger.error(f"Error scanning agent directories: {e}")
            self.available_agents = []
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process natural language input and translate to a specific command.
        
        Args:
            user_input: Natural language query from the user
            
        Returns:
            Result dictionary with the translated command and routing info
        """
        self.status_update(f"Processing natural language query: {user_input}")
        
        # Skip processing if the query is empty
        if not user_input or user_input.strip() == "":
            return {
                "status": "error",
                "message": "Empty query",
                "spoke": "I didn't receive any query to process."
            }
        
        try:
            # Try to translate the query to a specific command
            translated_command, agent_name = self._translate_query(user_input)
            
            if self.debug:
                self.logger.info(f"Translated '{user_input}' to '{translated_command}' for agent '{agent_name}'")
            
            # If we couldn't translate the query, return an error
            if not translated_command or not agent_name:
                return {
                    "status": "error",
                    "message": "Unsupported query",
                    "spoke": "I'm not sure how to handle that query. Please try a different one."
                }
            
            # If the agent doesn't exist, return an error
            if agent_name not in self.available_agents:
                return {
                    "status": "error",
                    "message": f"Unknown agent: {agent_name}",
                    "spoke": f"I couldn't find an agent named {agent_name}. Please try a different query."
                }
            
            # Return the translated command without trying to route it directly
            return {
                "status": "success",
                "message": f"Query translated to: {agent_name} {translated_command}",
                "command": f"{agent_name} {translated_command}",
                "agent": agent_name,
                "translated": True,
                "original_query": user_input,
                "spoke": f"Processing your request with the {agent_name} agent."
            }
                
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}",
                "spoke": "Sorry, I encountered an error while processing your query."
            }
    
    def _translate_query(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Translate a natural language query to a specific command using an LLM.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Tuple of (translated_command, agent_name) or (None, None) if unsupported
        """
        # Choose the appropriate translation method based on the provider
        if self.model_provider == "gemini" and GENAI_AVAILABLE:
            return self._translate_with_gemini(query)
        else:
            return self._translate_with_ollama(query)
    
    def _translate_with_gemini(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Translate natural language using Google's Gemini API.
        
        Args:
            query: The natural language query from the user
        
        Returns:
            Tuple of (translated_command, agent_name) or (None, None) if unsupported
        """
        # Construct the prompt for Gemini
        agent_list = ", ".join(self.available_agents)
        
        prompt = f"""You are a command translator for AgentOS.
Available agents: {agent_list}

Translate the following natural language query to a specific agent command. 
Return only a JSON response with the following structure:
{{
  "agent": "<agent_name>",
  "command": "<command>"
}}

If the query can't be mapped to any agent, respond with:
{{
  "agent": null,
  "command": null
}}

For task-related queries, such as adding tasks or reminders, always use the "datetime" agent.

Query: {query}
"""
        
        try:
            # Call the Gemini API with corrected configuration
            generation_config = {
                "temperature": 0.1,
                "max_output_tokens": 256,
            }
            
            model = genai.GenerativeModel(
                model_name=self.gemini_model,
                generation_config=generation_config
            )
            
            response = model.generate_content(prompt)
            
            if self.debug:
                self.logger.info(f"Gemini raw response: {response.text}")
            
            # Parse the JSON response
            try:
                # Look for JSON in the response text
                text = response.text
                # Find JSON-like content in the response
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = text[json_start:json_end]
                    result = json.loads(json_str)
                    agent = result.get("agent")
                    command = result.get("command")
                    
                    # If either agent or command is null or missing, return None for both
                    if not agent or not command or agent == "null" or command == "null":
                        return self._fallback_translation(query)
                    
                    # Ensure task-related commands go to datetime agent
                    if agent == "todoist":
                        agent = "datetime"
                    
                    # Process special commands for specific agents
                    if agent == "twitter_bot":
                        return self._process_twitter_command(query, agent, command)
                    elif agent == "autoblog":
                        return self._process_autoblog_command(query, agent, command)
                    elif agent == "datetime":
                        return self._process_todoist_command(query, agent, command)
                    
                    return command, agent
                else:
                    self.logger.error("No JSON found in Gemini response")
                    return self._fallback_translation(query)
                    
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse JSON from Gemini response: {response.text}")
                return self._fallback_translation(query)
                
        except Exception as e:
            self.logger.error(f"Error translating with Gemini: {e}")
            return self._fallback_translation(query)
    
    def _translate_with_ollama(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Translate a natural language query to a specific command using Ollama.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Tuple of (translated_command, agent_name) or (None, None) if unsupported
        """
        # Construct the prompt for the LLM
        agent_list = ", ".join(self.available_agents)
        
        prompt = f"""You are a command translator for AgentOS.
Available agents: {agent_list}

Translate the following natural language query to a specific agent command. 
Format your response as JSON with the following structure:
{{
  "agent": "<agent_name>",
  "command": "<command>"
}}

If the query can't be mapped to any agent, respond with:
{{
  "agent": null,
  "command": null
}}

For task-related queries, such as adding tasks or reminders, always use the "datetime" agent.

Query: {query}

Output (JSON):"""
        
        try:
            # Call the Ollama API to get the translation
            try:
                response = requests.post(
                    f"{self.ollama_api_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for more deterministic results
                            "num_predict": 256   # Limit output length
                        }
                    },
                    timeout=3  # Shorter timeout to avoid hanging
                )
                
                # Check if the request was successful
                if response.status_code != 200:
                    self.logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return self._fallback_translation(query)
                
                # Extract the response text from the JSON response
                response_json = response.json()
                response_text = response_json.get("response", "")
                
                if self.debug:
                    self.logger.info(f"Ollama raw response: {response_text}")
                
                # Parse the JSON response
                # First try to find JSON in the response (the model might add explanatory text)
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    try:
                        result = json.loads(json_str)
                        agent = result.get("agent")
                        command = result.get("command")
                        
                        # If either agent or command is null or missing, return None for both
                        if not agent or not command or agent == "null" or command == "null":
                            return self._fallback_translation(query)
                        
                        # Ensure task-related commands go to datetime agent
                        if agent == "todoist":
                            agent = "datetime"
                        
                        # Process special commands for specific agents
                        if agent == "twitter_bot":
                            return self._process_twitter_command(query, agent, command)
                        elif agent == "autoblog":
                            return self._process_autoblog_command(query, agent, command)
                        elif agent == "datetime":
                            return self._process_todoist_command(query, agent, command)
                        
                        return command, agent
                        
                    except json.JSONDecodeError:
                        self.logger.error(f"Failed to parse JSON from Ollama response: {json_str}")
                
                # If we couldn't parse JSON, try to extract agent and command directly
                self.logger.warning("Couldn't parse JSON from Ollama response, falling back to basic extraction")
                lines = response_text.split("\n")
                for line in lines:
                    if "agent" in line.lower() and ":" in line:
                        agent = line.split(":", 1)[1].strip().strip('"\'{}').strip()
                        
                        # Ensure task-related commands go to datetime agent
                        if agent == "todoist":
                            agent = "datetime"
                            
                        if agent and agent != "null" and agent in self.available_agents:
                            for cmd_line in lines:
                                if "command" in cmd_line.lower() and ":" in cmd_line:
                                    command = cmd_line.split(":", 1)[1].strip().strip('"\'{}').strip()
                                    if command and command != "null":
                                        # Process special commands for specific agents
                                        if agent == "twitter_bot":
                                            return self._process_twitter_command(query, agent, command)
                                        elif agent == "autoblog":
                                            return self._process_autoblog_command(query, agent, command)
                                        elif agent == "datetime":
                                            return self._process_todoist_command(query, agent, command)
                                        
                                        return command, agent
                
                # If we couldn't extract the agent and command, use fallback
                return self._fallback_translation(query)
                
            except requests.RequestException as e:
                # If we can't connect to Ollama, log and use fallback
                self.logger.error(f"Ollama API request error: {e}")
                if isinstance(e, requests.ConnectionError):
                    self.logger.error(f"Ollama connection error - is Ollama running at {self.ollama_api_url}?")
                return self._fallback_translation(query)
            
        except Exception as e:
            self.logger.error(f"Error translating query: {e}")
            return self._fallback_translation(query)
    
    def _fallback_translation(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fallback to a simple keyword-based translation when model APIs are not available.
        
        Args:
            query: The natural language query
            
        Returns:
            A tuple of (command, agent) or (None, None) if no keywords match
        """
        query_lower = query.lower()
        
        # Special handling for Twitter-related commands
        if "twitter" in query_lower and "twitter_bot" in self.available_agents:
            # Tweet creation
            if any(word in query_lower for word in ["tweet"]):
                # Extract the message, removing "tweet" keyword
                message = query
                if "tweet" in query_lower:
                    # Try to extract the content after "tweet"
                    split_query = query_lower.split("tweet", 1)
                    if len(split_query) > 1 and split_query[1].strip():
                        message = split_query[1].strip()
                return f"tweet {message}", "twitter_bot"
            
            # Thread creation from blog
            if any(word in query_lower for word in ["post", "create", "thread", "publish"]) and any(word in query_lower for word in ["blog", "thread"]):
                return "post blog thread", "twitter_bot"
            
            # Timeline request
            if "timeline" in query_lower:
                return "timeline", "twitter_bot"
            
            # Monitor blog
            if "monitor" in query_lower and "blog" in query_lower:
                return "monitor blog", "twitter_bot"
            
            # Stop monitoring
            if "stop" in query_lower and "monitor" in query_lower:
                return "stop monitor", "twitter_bot"
            
            # Status check (default fallback for other Twitter queries)
            if any(word in query_lower for word in ["status", "check"]):
                return "status", "twitter_bot"
            
            # Default to status for any Twitter mention that doesn't match other patterns
            return "status", "twitter_bot"
        
        # Special handling for Autoblog commands
        if (any(word in query_lower for word in ["blog", "post"]) or "autoblog" in query_lower) and "autoblog" in self.available_agents:
            # Generate blog posts
            if any(word in query_lower for word in ["generate", "create", "new", "make"]):
                return "generate", "autoblog"
            
            # Process specific repository
            if any(word in query_lower for word in ["repo", "repository"]):
                # Try to extract repo name if present
                parts = query_lower.split("repo", 1)
                if len(parts) > 1 and parts[1].strip():
                    repo_name = parts[1].strip()
                    return f"blog-repo {repo_name}", "autoblog"
                return "help", "autoblog"  # If no repo specified, show help
            
            # Set date
            if "date" in query_lower:
                # Try to extract date if present
                import re
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', query)
                if date_match:
                    return f"setdate {date_match.group(0)}", "autoblog"
                return "help", "autoblog"
            
            # Status check
            if any(word in query_lower for word in ["status", "check"]):
                return "status", "autoblog"
            
            # Default to help for any autoblog mention
            return "help", "autoblog"
        
        # Special handling for task-related commands
        if any(word in query_lower for word in ["task", "todo", "reminder"]) and "datetime" in self.available_agents:
            # Adding a task
            if any(word in query_lower for word in ["add", "create", "new", "make"]):
                # Avoid redundant add prefix
                if query_lower.startswith("add "):
                    return query, "datetime"
                else:
                    return f"add {query}", "datetime"
            
            # Listing tasks
            if any(word in query_lower for word in ["list", "show", "get", "what"]):
                return f"list {query}", "datetime"
            
            # Help for tasks
            if "help" in query_lower:
                return "help", "datetime"
            
            # Default to adding a task if no specific command is detected
            if query_lower.startswith("add "):
                return query, "datetime"
            else:
                return f"add {query}", "datetime"
        
        # Simple keyword to agent mapping for other agents
        keyword_map = {
            "weather": ("datetime", "weather"),
            "time": ("datetime", "time"),
            "date": ("datetime", "date"),
            
            "file": ("filemanage", "list"),
            "folder": ("filemanage", "list"),
            "open": ("filemanage", "open"),
            
            "play": ("spotiauto", "play"),
            "music": ("spotiauto", "play"),
            "spotify": ("spotiauto", "status"),
        }
        
        # Check for keywords in the query
        for keyword, (agent, command) in keyword_map.items():
            if keyword in query_lower and agent in self.available_agents:
                # For some agents, include additional context from the query
                if agent == "filemanage" and "open" in command:
                    # Try to extract a filename
                    words = query_lower.split()
                    if "open" in words and words.index("open") + 1 < len(words):
                        filename = words[words.index("open") + 1:]
                        return f"{command} {' '.join(filename)}", agent
                elif agent == "spotiauto" and "play" in command:
                    # Include the whole query for music requests
                    return f"{command} {query}", agent
                else:
                    return command, agent
        
        # Nothing matched
        return None, None
    
    def get_capabilities(self) -> List[str]:
        """Return a list of this agent's capabilities."""
        capabilities = [
            "Translate natural language queries to specific commands",
            "Route queries to the appropriate agent",
            "Handle queries that don't match any known agent"
        ]
        
        # Add provider-specific capabilities
        if self.model_provider == "gemini":
            capabilities.append("Use Google's Gemini AI for language understanding")
        else:
            capabilities.append("Use local Ollama models for language understanding")
            
        return capabilities
        
    def _load_saved_preferences(self):
        """Load saved model preferences from disk."""
        try:
            # Determine the path for the preferences file
            prefs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preferences.json")
            
            # Check if the file exists
            if os.path.exists(prefs_path):
                with open(prefs_path, 'r') as f:
                    prefs = json.load(f)
                    
                # Apply the saved preferences
                if "model_provider" in prefs:
                    saved_provider = prefs["model_provider"].lower()
                    # Only use if it's a valid provider
                    if saved_provider in ["gemini", "ollama"]:
                        self.model_provider = saved_provider
                
                # Apply the saved model for the current provider
                if self.model_provider == "gemini" and "gemini_model" in prefs:
                    self.gemini_model = prefs["gemini_model"]
                elif self.model_provider == "ollama" and "ollama_model" in prefs:
                    self.ollama_model = prefs["ollama_model"]
                    
                self.logger.info(f"Loaded saved model preferences: {self.model_provider} - {self.gemini_model if self.model_provider == 'gemini' else self.ollama_model}")
        except Exception as e:
            self.logger.warning(f"Could not load saved preferences: {e}")
            
    def _save_preferences(self):
        """Save current model preferences to disk."""
        try:
            # Create a preferences object
            prefs = {
                "model_provider": self.model_provider,
                "gemini_model": self.gemini_model,
                "ollama_model": self.ollama_model
            }
            
            # Determine the path for the preferences file
            prefs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preferences.json")
            
            # Write to disk
            with open(prefs_path, 'w') as f:
                json.dump(prefs, f, indent=2)
                
            self.logger.info("Saved model preferences")
        except Exception as e:
            self.logger.error(f"Error saving preferences: {e}")
            
    def set_model_provider(self, provider: str) -> bool:
        """
        Change the model provider at runtime.
        
        Args:
            provider: The provider to use ('gemini' or 'ollama')
            
        Returns:
            True if successful, False otherwise
        """
        provider = provider.lower()
        if provider not in ["gemini", "ollama"]:
            self.logger.error(f"Invalid model provider: {provider}")
            return False
            
        # If switching to Gemini, verify it's available
        if provider == "gemini":
            if not GENAI_AVAILABLE:
                self.logger.error("Gemini API not available. Install google-generativeai package.")
                return False
            if not self.gemini_api_key:
                self.logger.error("Gemini API key not configured")
                return False
                
        # Update the provider
        self.model_provider = provider
        self.logger.info(f"Switched model provider to {provider}")
        
        # Save the updated preferences
        self._save_preferences()
        
        return True
        
    def process_voice_command(self, voice_text: str) -> Dict[str, Any]:
        """
        Process a command received from voice input.
        
        Args:
            voice_text: The transcribed voice command text
            
        Returns:
            Result dictionary with the processed command
        """
        self.status_update(f"Processing voice command: {voice_text}")
        
        # Voice commands often need special handling
        # First, check if it's a direct command to an agent
        try:
            result = self.process(voice_text)
            
            # Add a flag indicating this came from voice input
            result['voice_input'] = True
            
            # Make responses more conversational for voice
            if 'spoke' in result and result['spoke']:
                # Already has spoken text, no need to modify
                pass
            elif 'message' in result:
                # Create a more conversational response
                result['spoke'] = f"I understood: {voice_text}. {result['message']}"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing voice command: {e}")
            return {
                "status": "error",
                "message": f"Error processing voice command: {str(e)}",
                "spoke": "I had trouble processing your voice command. Could you try again?",
                "voice_input": True
            }
            
    def handle_api_request(self, request_type: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle special API requests for this agent.
        
        Args:
            request_type: Type of API request
            data: Additional data for the request
            
        Returns:
            Response dictionary
        """
        data = data or {}
        
        try:
            if request_type == "get_model_info":
                return {
                    "status": "success",
                    "data": self.get_model_info()
                }
                
            elif request_type == "set_model_provider":
                provider = data.get("provider")
                if not provider:
                    return {
                        "status": "error",
                        "message": "No provider specified"
                    }
                
                success = self.set_model_provider(provider)
                return {
                    "status": "success" if success else "error",
                    "message": f"Model provider {'updated' if success else 'update failed'}"
                }
                
            elif request_type == "set_model":
                model_name = data.get("model_name")
                if not model_name:
                    return {
                        "status": "error",
                        "message": "No model specified"
                    }
                
                success = self.set_model(model_name)
                return {
                    "status": "success" if success else "error",
                    "message": f"Model {'updated' if success else 'update failed'}"
                }
                
            elif request_type == "health_check":
                return {
                    "status": "success",
                    "data": self.health_check()
                }
                
            else:
                return {
                    "status": "error",
                    "message": f"Unknown API request type: {request_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling API request {request_type}: {e}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current language model configuration.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "provider": self.model_provider,
            "available_providers": ["gemini", "ollama"],
            "current_model": None,
            "available_models": []
        }
        
        # Add provider-specific details
        if self.model_provider == "gemini":
            info["current_model"] = self.gemini_model
            info["api_key_configured"] = bool(self.gemini_api_key)
            info["available_models"] = ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-1.0-pro"]
        else:  # ollama
            info["current_model"] = self.ollama_model
            info["api_url"] = self.ollama_api_url
            
            # Try to get available models from Ollama
            try:
                response = requests.get(f"{self.ollama_api_url}/api/tags", timeout=1)
                if response.ok:
                    models_data = response.json()
                    if "models" in models_data:
                        info["available_models"] = [model["name"] for model in models_data["models"]]
            except:
                # Don't fail if we can't get model list
                info["available_models"] = ["Unable to retrieve models"]
        
        return info
        
    def set_model(self, model_name: str) -> bool:
        """
        Change the model for the current provider.
        
        Args:
            model_name: The name of the model to use
            
        Returns:
            True if successful, False otherwise
        """
        if not model_name:
            self.logger.error("Invalid model name")
            return False
            
        if self.model_provider == "gemini":
            # Update Gemini model
            self.gemini_model = model_name
            self.logger.info(f"Switched Gemini model to {model_name}")
        else:
            # Update Ollama model
            self.ollama_model = model_name
            self.logger.info(f"Switched Ollama model to {model_name}")
            
        # Save the updated preferences
        self._save_preferences()
        
        return True
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the agent and its dependencies.
        
        Returns:
            Dictionary with health status information
        """
        health_info = {
            "status": "healthy",
            "model_provider": self.model_provider,
            "issues": []
        }
        
        # Check model provider availability
        if self.model_provider == "gemini":
            if not GENAI_AVAILABLE:
                health_info["status"] = "degraded"
                health_info["issues"].append("Google GenerativeAI package not installed")
            
            if not self.gemini_api_key:
                health_info["status"] = "degraded"
                health_info["issues"].append("Gemini API key not configured")
                
            # Try a simple API call to test connectivity
            if GENAI_AVAILABLE and self.gemini_api_key:
                try:
                    genai.configure(api_key=self.gemini_api_key)
                    model = genai.GenerativeModel(model_name=self.gemini_model)
                    # Just a tiny prompt to test connectivity
                    response = model.generate_content("Hi")
                    if not response or not hasattr(response, 'text'):
                        health_info["status"] = "degraded"
                        health_info["issues"].append("Gemini API returned invalid response")
                except Exception as e:
                    health_info["status"] = "degraded"
                    health_info["issues"].append(f"Gemini API error: {str(e)}")
        else:
            # Ollama health check
            try:
                response = requests.get(f"{self.ollama_api_url}/api/tags", timeout=2)
                if not response.ok:
                    health_info["status"] = "degraded"
                    health_info["issues"].append(f"Ollama API returned status {response.status_code}")
            except Exception as e:
                health_info["status"] = "degraded"
                health_info["issues"].append(f"Ollama API error: {str(e)}")
        
        # Check if we have available agents
        if not self.available_agents:
            health_info["status"] = "degraded"
            health_info["issues"].append("No available agents found")
        
        return health_info
        
    def self_test(self) -> Dict[str, Any]:
        """
        Run a self-test to verify the agent's functionality.
        
        Returns:
            Dictionary with test results
        """
        test_results = {
            "agent": "natural_language",
            "success": True,
            "tests": []
        }
        
        # Test 1: Check health status
        try:
            health = self.health_check()
            test_pass = health["status"] == "healthy"
            test_results["tests"].append({
                "name": "health_check",
                "success": test_pass,
                "message": "Health check passed" if test_pass else f"Health check failed: {', '.join(health['issues'])}"
            })
            
            # Update overall success
            test_results["success"] = test_results["success"] and test_pass
        except Exception as e:
            test_results["tests"].append({
                "name": "health_check",
                "success": False,
                "message": f"Health check error: {str(e)}"
            })
            test_results["success"] = False
        
        # Test 2: Simple translation test with direct query
        test_queries = [
            "what time is it",  # should map to datetime agent
            "open my document.txt"  # should map to filemanage agent
        ]
        
        for query in test_queries:
            try:
                # Skip actual API calls but test the translation logic
                translated_command, agent_name = self._translate_query(query)
                
                test_pass = translated_command is not None and agent_name is not None
                test_results["tests"].append({
                    "name": f"translation_test_{query}",
                    "success": test_pass,
                    "message": f"Translated '{query}' to '{translated_command}' for agent '{agent_name}'" if test_pass else f"Failed to translate '{query}'",
                    "details": {
                        "query": query,
                        "command": translated_command,
                        "agent": agent_name
                    }
                })
                
                # Update overall success
                test_results["success"] = test_results["success"] and test_pass
                
            except Exception as e:
                test_results["tests"].append({
                    "name": f"translation_test_{query}",
                    "success": False,
                    "message": f"Translation error for '{query}': {str(e)}"
                })
                test_results["success"] = False
        
        # Test 3: Test model info
        try:
            model_info = self.get_model_info()
            test_pass = model_info["provider"] in ["gemini", "ollama"] and model_info["current_model"] is not None
            
            test_results["tests"].append({
                "name": "model_info",
                "success": test_pass,
                "message": f"Model info returned: {model_info['provider']} - {model_info['current_model']}" if test_pass else "Invalid model info returned"
            })
            
            # Update overall success
            test_results["success"] = test_results["success"] and test_pass
            
        except Exception as e:
            test_results["tests"].append({
                "name": "model_info",
                "success": False,
                "message": f"Model info error: {str(e)}"
            })
            test_results["success"] = False
                
        return test_results

    def _process_twitter_command(self, query: str, agent: str, command: str) -> Tuple[str, str]:
        """
        Process Twitter-specific commands to ensure they're properly formatted.
        
        Args:
            query: The original query
            agent: The detected agent
            command: The detected command
            
        Returns:
            Properly formatted (command, agent) tuple
        """
        query_lower = query.lower()
        
        if agent != "twitter_bot":
            return command, agent
            
        # Check for tweet creation intent
        if any(keyword in command.lower() for keyword in ["tweet", "post tweet"]):
            # Extract the message content after "tweet" in the command, or use the query
            message = command.lower().replace("tweet", "", 1).strip()
            if not message:
                message = query
            return f"tweet {message}", agent
            
        # Check for thread/post creation intent
        if any(keyword in command.lower() for keyword in ["post", "create", "thread", "publish"]):
            # Match the exact command pattern expected by the TwitterBotAgent
            if "blog" in query_lower or "thread" in query_lower:
                return "post blog thread", agent
            return "post blog thread", agent
            
        # Check for status check intent
        if any(keyword in command.lower() for keyword in ["status", "check"]):
            return "status", agent
            
        # Check for timeline request
        if "timeline" in command.lower():
            return "timeline", agent
            
        # Check for monitoring commands
        if "monitor" in command.lower() and "blog" in command.lower():
            return "monitor blog", agent
            
        if "stop" in command.lower() and "monitor" in command.lower():
            return "stop monitor", agent
            
        # Default to help if command not recognized
        if "help" in command.lower():
            return "help", agent
            
        # Return original command if no patterns match
        return command, agent

    def _process_autoblog_command(self, query: str, agent: str, command: str) -> Tuple[str, str]:
        """
        Process Autoblog-specific commands to ensure they're properly formatted.
        
        Args:
            query: The original query
            agent: The detected agent
            command: The detected command
            
        Returns:
            Properly formatted (command, agent) tuple
        """
        query_lower = query.lower()
        
        if agent != "autoblog":
            return command, agent
        
        # Check for generate blog post intent
        if any(keyword in command.lower() for keyword in ["generate", "create", "new", "make", "post"]):
            return "generate", agent
        
        # Check for repository processing
        if any(keyword in command.lower() for keyword in ["repo", "repository"]):
            # Extract repo name if possible
            parts = command.lower().split("repo", 1)
            if len(parts) > 1 and parts[1].strip():
                repo_name = parts[1].strip()
                return f"blog-repo {repo_name}", agent
            return "help", agent  # Default to help if no repo specified
        
        # Check for date setting
        if "date" in command.lower() or "setdate" in command.lower():
            import re
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', command)
            if date_match:
                return f"setdate {date_match.group(0)}", agent
            return "help", agent
        
        # Check for status
        if "status" in command.lower():
            return "status", agent
        
        # Default to help
        return "help", agent

    def _process_todoist_command(self, query: str, agent: str, command: str) -> Tuple[str, str]:
        """
        Process task-specific commands to ensure they're properly formatted.
        
        Args:
            query: The original query
            agent: The detected agent
            command: The detected command
            
        Returns:
            Properly formatted (command, agent) tuple
        """
        query_lower = query.lower()
        
        # Always route task-related commands to datetime agent
        # The datetime agent will handle delegation to todolist internally
        agent = "datetime"
        
        # Check for task creation intent
        if any(keyword in query_lower for keyword in ["add", "create", "new", "remind", "task", "todo"]):
            # Avoid redundant "add add" prefix
            if query_lower.startswith("add "):
                return query, agent
            else:
                return f"add {query}", agent
        
        # Check for task listing intent
        if any(keyword in query_lower for keyword in ["list", "show", "get", "what"]):
            return f"list {query}", agent
        
        # Default to help if command is unclear
        if "help" in query_lower:
            return "help", agent
        
        # Default to adding a task for any other task-related query
        if query_lower.startswith("add "):
            return query, agent
        else:
            return f"add {query}", agent 
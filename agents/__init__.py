"""
AgentOS Agents Package

This package contains all the specialized agents for AgentOS.
Each agent is a separate subpackage with its own functionality.
"""

import os
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

logger = logging.getLogger(__name__)

def discover_agents() -> Dict[str, Optional[Type]]:
    """
    Dynamically discover all available agents in the agents directory.
    
    Returns:
        Dict mapping agent names to their Agent classes
    """
    agents = {}
    
    # Get the current directory (agents package)
    package_dir = Path(__file__).parent
    
    # Loop through all subdirectories that don't start with underscore
    for item in os.listdir(package_dir):
        agent_dir = package_dir / item
        
        # Skip files and special directories
        if not agent_dir.is_dir() or item.startswith('__'):
            continue
        
        # Check if it has an __init__.py file (making it a proper package)
        if not (agent_dir / "__init__.py").exists():
            continue
        
        try:
            # Import the agent module
            module_name = f"agents.{item}"
            agent_module = importlib.import_module(module_name)
            
            # Check if the module has an Agent class
            if hasattr(agent_module, 'Agent'):
                agents[item] = agent_module.Agent
                logger.debug(f"Discovered agent: {item}")
            else:
                logger.warning(f"Module {module_name} does not have an Agent class")
                agents[item] = None
                
        except Exception as e:
            logger.error(f"Error loading agent {item}: {e}")
            agents[item] = None
    
    return agents

def get_agent_names() -> List[str]:
    """
    Get a list of all available agent names.
    
    Returns:
        List of agent names
    """
    return list(discover_agents().keys())

def get_agent_class(agent_name: str) -> Optional[Type]:
    """
    Get the Agent class for a specific agent by name.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        The Agent class or None if not found
    """
    agents = discover_agents()
    return agents.get(agent_name)

def create_agent_instance(agent_name: str, config=None):
    """
    Create an instance of an agent by name.
    
    Args:
        agent_name: Name of the agent to create
        config: Optional configuration to pass to the agent
        
    Returns:
        An instance of the agent or None if not found
    """
    agent_class = get_agent_class(agent_name)
    if agent_class:
        try:
            return agent_class(config)
        except Exception as e:
            logger.error(f"Error creating agent instance {agent_name}: {e}")
            return None
    return None

# Dictionary of all available agents (lazy-loaded on first access)
_agents = None

def get_all_agents() -> Dict[str, Optional[Type]]:
    """Get a dictionary of all available agents (cached)."""
    global _agents
    if _agents is None:
        _agents = discover_agents()
    return _agents

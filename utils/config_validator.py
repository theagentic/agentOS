"""
Configuration Validation Utility

This module provides functions to validate environment variables and configurations
for both the core system and individual agents.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Set up better console output
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

# Ensure we load the main .env file first when running as standalone script
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    main_env = base_dir / ".env"
    if main_env.exists():
        load_dotenv(dotenv_path=main_env)
        print(f"Loaded environment from {main_env}")

def validate_system_env() -> bool:
    """
    Validate system-level environment variables.
    
    Returns:
        bool: True if all required variables are present with valid values
    """
    # Add debug output to check what's actually in the environment
    debug_value = os.getenv("AGENTOS_DEBUG")
    log_level = os.getenv("AGENTOS_LOG_LEVEL")
    print(f"DEBUG: Found AGENTOS_DEBUG={debug_value}, AGENTOS_LOG_LEVEL={log_level}")
    
    # System doesn't have strictly required env vars, but we can check for recommended ones
    recommended_vars = [
        "AGENTOS_DEBUG",
        "AGENTOS_LOG_LEVEL"
    ]
    
    missing = []
    for var in recommended_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.warning(f"Recommended environment variables not set: {', '.join(missing)}")
    
    return True  # System can still run with defaults

def validate_agent_env(agent_name: str) -> Tuple[bool, List[str]]:
    """
    Validate agent-specific environment variables.
    
    Args:
        agent_name: Name of the agent to validate
        
    Returns:
        Tuple of (is_valid, missing_vars)
    """
    base_dir = Path(__file__).resolve().parent.parent
    agent_dir = base_dir / "agents" / agent_name
    
    if not agent_dir.exists() or not agent_dir.is_dir():
        logger.error(f"Agent directory not found: {agent_dir}")
        return False, [f"Agent '{agent_name}' not found"]
    
    env_file = agent_dir / ".env"
    env_example = agent_dir / ".env.example"
    
    print(f"\nChecking {agent_name} agent...")
    print(f"* Agent directory: {agent_dir}")
    print(f"* .env file exists: {env_file.exists()}")
    print(f"* .env.example file exists: {env_example.exists()}")
    
    if not env_file.exists():
        if env_example.exists():
            logger.warning(f"Agent {agent_name} missing .env file. Please copy from .env.example")
            return False, ["Missing .env file. Copy from .env.example"]
        else:
            logger.warning(f"Agent {agent_name} has no .env or .env.example file")
            return True, []  # Assume no env vars needed
    
    # Load the agent-specific .env file
    load_dotenv(dotenv_path=env_file)
    print(f"* Loaded environment from {env_file}")
    
    # Agent-specific validation
    if agent_name == "datetime":
        token = os.getenv("TODOIST_API_TOKEN")
        print(f"* Found TODOIST_API_TOKEN: {'Yes' if token else 'No'}")
        if not token:
            return False, ["TODOIST_API_TOKEN"]
    elif agent_name == "spotiauto":
        missing = []
        for var in ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI"]:
            val = os.getenv(var)
            print(f"* Found {var}: {'Yes' if val else 'No'}")
            if not val:
                missing.append(var)
        if missing:
            return False, missing
    elif agent_name == "twitter_bot":
        missing = []
        # Check for Twitter API credentials
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        
        # Check for both access secret naming conventions
        access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        # Use either one if available
        access_secret = access_secret or access_token_secret
        
        # Check for Gemini API key (optional but recommended)
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Check for blog posts path (optional but needed for blog features)
        blog_path = os.getenv("BLOG_POSTS_PATH")
        
        # Print status of all keys
        print(f"* Found TWITTER_API_KEY: {'Yes' if api_key else 'No'}")
        print(f"* Found TWITTER_API_SECRET: {'Yes' if api_secret else 'No'}")
        print(f"* Found TWITTER_ACCESS_TOKEN: {'Yes' if access_token else 'No'}")
        print(f"* Found Access Secret (either name): {'Yes' if access_secret else 'No'}")
        print(f"* Found GEMINI_API_KEY: {'Yes' if gemini_key else 'No'}")
        print(f"* Found BLOG_POSTS_PATH: {'Yes' if blog_path else 'No'}")
        
        # Check which variables are missing
        if not api_key:
            missing.append("TWITTER_API_KEY")
        if not api_secret:
            missing.append("TWITTER_API_SECRET")
        if not access_token:
            missing.append("TWITTER_ACCESS_TOKEN")
        if not access_secret:
            missing.append("TWITTER_ACCESS_SECRET or TWITTER_ACCESS_TOKEN_SECRET")
        
        # Optional variables warnings
        if not gemini_key:
            logger.warning("GEMINI_API_KEY not found - blog to tweet features will be limited")
        if not blog_path:
            logger.warning("BLOG_POSTS_PATH not found - blog monitoring features will not work")
            
        # If we have all Twitter API credentials, try a live validation
        if all([api_key, api_secret, access_token, access_secret]):
            print("* All Twitter credentials found. Attempting to validate...")
            try:
                import tweepy
                auth = tweepy.OAuth1UserHandler(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret
                )
                api = tweepy.API(auth)
                user = api.verify_credentials()
                print(f"✅ Twitter credentials validated! Connected as @{user.screen_name}")
                
            except ImportError:
                print("* Could not import tweepy library. Install it with: pip install tweepy")
            except Exception as e:
                print(f"❌ Twitter API validation failed: {str(e)}")
                # We found all credentials, but they don't work
                return False, [f"Twitter API Error: {str(e)}"]
            
        if missing:
            return False, missing
    
    return True, []

def validate_all_agents() -> Dict[str, Tuple[bool, List[str]]]:
    """
    Validate all available agents.
    
    Returns:
        Dict mapping agent names to (is_valid, missing_vars) tuples
    """
    base_dir = Path(__file__).resolve().parent.parent
    agents_dir = base_dir / "agents"
    
    results = {}
    
    for agent_dir in [d for d in agents_dir.iterdir() 
                      if d.is_dir() and not d.name.startswith('__')]:
        agent_name = agent_dir.name
        results[agent_name] = validate_agent_env(agent_name)
    
    return results

def validate_specific_agent(agent_name: str) -> Tuple[bool, List[str]]:
    """
    Validate a specific agent by name.
    
    Args:
        agent_name: The name of the agent to validate
        
    Returns:
        Tuple of (is_valid, missing_vars)
    """
    base_dir = Path(__file__).resolve().parent.parent
    agent_dir = base_dir / "agents" / agent_name
    
    if not agent_dir.exists() or not agent_dir.is_dir():
        logger.error(f"Agent directory not found: {agent_dir}")
        return False, [f"Agent '{agent_name}' not found"]
    
    return validate_agent_env(agent_name)

def print_validation_report(specific_agent: Optional[str] = None):
    """
    Print a validation report for all configurations.
    
    Args:
        specific_agent: If provided, only validate this specific agent
    """
    print("\n" + "=" * 50)
    print("AgentOS Configuration Validation Report")
    print("=" * 50)
    
    # System validation
    system_valid = validate_system_env()
    print(f"\n✅ System Environment: {'Valid' if system_valid else 'Issues Found'}")
    
    # Agent validation
    if specific_agent:
        valid, missing = validate_specific_agent(specific_agent)
        status = "✅ Valid" if valid else "❌ Issues Found"
        print(f"\nAgent '{specific_agent}': {status}")
        if missing:
            print(f"  Missing or invalid: {', '.join(missing)}")
    else:
        agent_results = validate_all_agents()
        print("\nAgent Environments:")
        
        for agent, (valid, missing) in agent_results.items():
            status = "✅ Valid" if valid else "❌ Issues Found"
            print(f"  {agent}: {status}")
            if missing:
                print(f"    Missing or invalid: {', '.join(missing)}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Validate AgentOS configurations")
    parser.add_argument('--agent', help='Validate a specific agent')
    args = parser.parse_args()
    
    # Run validation when script is executed directly
    print_validation_report(specific_agent=args.agent)

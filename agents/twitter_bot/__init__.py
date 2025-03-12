"""
Twitter Bot Agent Package

Handles Twitter automation for creating and managing tweets.
"""

# Import the actual TwitterBotAgent implementation, not the template
from .agent import TwitterBotAgent
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load the Twitter agent's .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)

# Export the agent class for the agent router to discover
Agent = TwitterBotAgent

"""
AgentOS Configuration System

This module provides a centralized configuration for all AgentOS components.
Settings can be overridden through environment variables or a .env file.
"""

import os
import platform
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file - only system-level settings
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
AGENTS_DIR = BASE_DIR / "agents"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True)

# Load all agent-specific .env files
def load_agent_env_files():
    """Load all agent-specific .env files."""
    for agent_dir in AGENTS_DIR.iterdir():
        if (agent_dir.is_dir() and not agent_dir.name.startswith('__')):
            env_file = agent_dir / '.env'
            if env_file.exists():
                logging.info(f"Loading environment from {env_file}")
                load_dotenv(dotenv_path=env_file, override=True)

# Load agent-specific environment variables
load_agent_env_files()

# General settings
APP_NAME = "AgentOS"
APP_VERSION = "0.1.0"
DEBUG_MODE = os.getenv("AGENTOS_DEBUG", "False").lower() == "true"

# UI settings
UI_CONFIG = {
    "window_title": os.getenv("AGENTOS_WINDOW_TITLE", "AgentOS Voice Assistant"),
    "window_width": int(os.getenv("AGENTOS_WINDOW_WIDTH", "1200")),
    "window_height": int(os.getenv("AGENTOS_WINDOW_HEIGHT", "800")),
    "splitter_ratio": float(os.getenv("AGENTOS_SPLITTER_RATIO", "0.33")),  # Left:Right ratio
    "theme": os.getenv("AGENTOS_THEME", "system"),  # system, light, dark
    "font_size": int(os.getenv("AGENTOS_FONT_SIZE", "12")),
}

# Voice settings
VOICE_CONFIG = {
    "wake_word": os.getenv("AGENTOS_WAKE_WORD", "agent"),
    "tts_engine": os.getenv("AGENTOS_TTS_ENGINE", "system"),  # system, google, azure
    "tts_rate": int(os.getenv("AGENTOS_TTS_RATE", "150")),
    "voice_id": os.getenv("AGENTOS_VOICE_ID", None),  # None uses system default
    "speech_recognition_engine": os.getenv("AGENTOS_SPEECH_ENGINE", "google"),
    "energy_threshold": int(os.getenv("AGENTOS_ENERGY_THRESHOLD", "4000")),
    "enable_wake_word": os.getenv("AGENTOS_ENABLE_WAKE_WORD", "True").lower() == "true",
}

# Logging settings
LOG_CONFIG = {
    "level": os.getenv("AGENTOS_LOG_LEVEL", "INFO").upper(),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOG_DIR / "agentos.log",
    "max_file_size": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5,
}

# Agent-specific settings (defaults)
AGENT_CONFIGS = {
    # DateTime/Todoist agent
    "datetime": {
        "enabled": os.getenv("AGENTOS_TODOIST_ENABLED", "True").lower() == "true",
    },
    
    # FileManage agent
    "filemanage": {
        "enabled": os.getenv("AGENTOS_FILEMANAGE_ENABLED", "True").lower() == "true",
        "allowed_directories": os.getenv("AGENTOS_FILEMANAGE_ALLOWED_DIRS", 
                                         str(Path.home() / "Documents")).split(";"),
        "backup_directory": os.getenv("AGENTOS_FILEMANAGE_BACKUP_DIR", 
                                      str(DATA_DIR / "backups")),
    },
    
    # SpotiAuto agent
    "spotiauto": {
        "enabled": os.getenv("AGENTOS_SPOTIAUTO_ENABLED", "True").lower() == "true",
        "auto_play": os.getenv("AGENTOS_SPOTIAUTO_AUTOPLAY", "False").lower() == "true",
    },
    
    # Twitter Bot agent
    "twitter_bot": {
        "enabled": os.getenv("AGENTOS_TWITTER_ENABLED", "True").lower() == "true",
        "auto_reply": os.getenv("AGENTOS_TWITTER_AUTOREPLY", "False").lower() == "true",
    },
    
    # AutoBlog agent
    "autoblog": {
        "enabled": os.getenv("AGENTOS_AUTOBLOG_ENABLED", "True").lower() == "true",
    },
}

def setup_logging():
    """Configure logging based on the settings."""
    log_level = getattr(logging, LOG_CONFIG["level"], logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format=LOG_CONFIG["format"],
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(  # Now this will work
                LOG_CONFIG["file"],
                maxBytes=LOG_CONFIG["max_file_size"],
                backupCount=LOG_CONFIG["backup_count"]
            )
        ]
    )
    
    # If debug mode is enabled, set all loggers to DEBUG level
    if DEBUG_MODE:
        for logger in logging.root.manager.loggerDict:
            logging.getLogger(logger).setLevel(logging.DEBUG)

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for a specific agent."""
    return AGENT_CONFIGS.get(agent_name, {})

def is_agent_enabled(agent_name: str) -> bool:
    """Check if an agent is enabled in configuration."""
    agent_config = get_agent_config(agent_name)
    return agent_config.get("enabled", True)

def get_platform_info() -> Dict[str, str]:
    """Get information about the platform."""
    return {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

#!/usr/bin/env python
"""
AgentOS Setup Script
This script helps with initial setup of the AgentOS system.
"""

import shutil
from pathlib import Path
import logging
import argparse
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentOS-Setup")

def setup_env_files(force=False):
    """
    Copy example .env files to .env files if they don't exist.
    
    Args:
        force: If True, overwrite existing files
    """
    base_dir = Path(__file__).resolve().parent
    
    # Create main .env file
    main_env_example = base_dir / ".env.example"
    main_env = base_dir / ".env"
    
    if main_env_example.exists() and (not main_env.exists() or force):
        logger.info("Creating main .env file from example")
        shutil.copy(main_env_example, main_env)
        logger.info(f"Created {main_env}")
    
    # Create agent .env files
    agents_dir = base_dir / "agents"
    if agents_dir.exists():
        for agent_dir in [d for d in agents_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]:
            env_example = agent_dir / ".env.example"
            env_file = agent_dir / ".env"
            
            if env_example.exists() and (not env_file.exists() or force):
                logger.info(f"Creating .env file for {agent_dir.name} agent")
                shutil.copy(env_example, env_file)
                logger.info(f"Created {env_file}")

def create_directories():
    """Create necessary directories if they don't exist."""
    base_dir = Path(__file__).resolve().parent
    
    # Directories to create
    directories = [
        base_dir / "data",
        base_dir / "logs",
        base_dir / "data" / "backups"
    ]
    
    for directory in directories:
        if not directory.exists():
            logger.info(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)

def check_requirements():
    """Check if requirements are installed."""
    required_packages = ["PyQt5", "pyttsx3", "speech_recognition"]
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing dependencies: {', '.join(missing_packages)}")
        logger.error("Please install requirements first: pip install -r requirements.txt")
        return False
    else:
        logger.info("Core dependencies found")
        return True

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="AgentOS Setup Script")
    parser.add_argument('--force', '-f', action='store_true', help="Force overwrite of existing files")
    args = parser.parse_args()
    
    logger.info("Starting AgentOS Setup")
    
    create_directories()
    
    if check_requirements():
        setup_env_files(force=args.force)
        
    logger.info("Setup complete. Edit the .env files with your credentials before running the application.")
    logger.info("Run 'python main.py' to start AgentOS")

if __name__ == "__main__":
    main()

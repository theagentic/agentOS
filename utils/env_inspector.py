"""
Environment Variable Inspector

Checks what environment variables are available to different parts of the system.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_env_var(name):
    """Print a censored version of an environment variable."""
    value = os.getenv(name)
    if value:
        censored = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
        return f"{name}: {censored}"
    else:
        return f"{name}: Not set"

def inspect_environment():
    """Inspect the current environment variables."""
    print("\n===== Environment Variable Inspector =====\n")
    
    # Print script location and Python version
    print(f"Script location: {__file__}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}\n")
    
    # Print relevant paths
    base_dir = Path(__file__).resolve().parent.parent
    print(f"Base directory: {base_dir}")
    
    # Check .env files
    main_env = base_dir / ".env"
    twitter_env = base_dir / "agents" / "twitter_bot" / ".env"
    
    print(f"\n.env file exists: {main_env.exists()}")
    print(f".env.twitter file exists: {twitter_env.exists()}")
    
    # Print original environment variables
    print("\nOriginal Environment Variables:")
    for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", 
               "TWITTER_ACCESS_SECRET", "TWITTER_ACCESS_TOKEN_SECRET"]:
        print(print_env_var(var))
    
    # Load main .env
    if main_env.exists():
        load_dotenv(dotenv_path=main_env)
        print("\nAfter loading main .env:")
        for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", 
                   "TWITTER_ACCESS_SECRET", "TWITTER_ACCESS_TOKEN_SECRET"]:
            print(print_env_var(var))
    
    # Load twitter .env (with precedence)
    if twitter_env.exists():
        load_dotenv(dotenv_path=twitter_env, override=True)
        print("\nAfter loading twitter_bot .env:")
        for var in ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", 
                   "TWITTER_ACCESS_SECRET", "TWITTER_ACCESS_TOKEN_SECRET"]:
            print(print_env_var(var))
    
    print("\n===== End of Environment Inspection =====\n")

if __name__ == "__main__":
    inspect_environment()

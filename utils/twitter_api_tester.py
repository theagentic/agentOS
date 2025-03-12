"""
Twitter API Tester

This script tests the connection to the Twitter API using the configured credentials.
Run this script directly to verify that your Twitter API credentials work correctly.
"""

import os
import sys
import tweepy
from pathlib import Path
from dotenv import load_dotenv
import traceback

# Ensure we load the right .env file
def load_credentials():
    """Load Twitter credentials from .env files."""
    # Load from main .env file
    base_dir = Path(__file__).resolve().parent.parent
    main_env = base_dir / ".env"
    if main_env.exists():
        load_dotenv(dotenv_path=main_env)
        print(f"Loaded environment from {main_env}")
    
    # Load from agent-specific .env file (which takes precedence)
    twitter_env = base_dir / "agents" / "twitter_bot" / ".env"
    if twitter_env.exists():
        load_dotenv(dotenv_path=twitter_env, override=True)
        print(f"Loaded environment from {twitter_env}")

def get_twitter_credentials():
    """Get Twitter API credentials from environment."""
    credentials = {
        'TWITTER_API_KEY': os.getenv('TWITTER_API_KEY'),
        'TWITTER_API_SECRET': os.getenv('TWITTER_API_SECRET'),
        'TWITTER_ACCESS_TOKEN': os.getenv('TWITTER_ACCESS_TOKEN'),
        'TWITTER_ACCESS_SECRET': os.getenv('TWITTER_ACCESS_SECRET', 
                                          os.getenv('TWITTER_ACCESS_TOKEN_SECRET'))  # Check both names
    }
    
    # Print the credentials (with masking for security)
    for key, value in credentials.items():
        masked = value[:4] + '****' if value else None
        print(f"{key}: {masked}")
    
    return credentials

def test_twitter_api():
    """Test if Twitter API credentials work properly."""
    print("\n=== Twitter API Test ===\n")
    
    # Load credentials
    load_credentials()
    creds = get_twitter_credentials()
    
    # Check if all credentials are present
    missing = [k for k, v in creds.items() if not v]
    if missing:
        print(f"❌ Error: Missing credentials: {', '.join(missing)}")
        print("Please check your .env file in the twitter_bot agent directory.")
        return False
    
    # Attempt to connect to Twitter API
    try:
        print("\nAttempting to connect to Twitter API...")
        
        auth = tweepy.OAuth1UserHandler(
            consumer_key=creds['TWITTER_API_KEY'],
            consumer_secret=creds['TWITTER_API_SECRET'],
            access_token=creds['TWITTER_ACCESS_TOKEN'],
            access_token_secret=creds['TWITTER_ACCESS_SECRET']
        )
        
        api = tweepy.API(auth)
        
        # Verify credentials
        user = api.verify_credentials()
        print(f"✅ Authentication successful for @{user.screen_name}")
        
        # Get rate limit status
        rate_limit = api.rate_limit_status()
        resources = rate_limit.get('resources', {})
        
        # Show some API limits
        if 'statuses' in resources:
            timeline_limit = resources['statuses'].get('/statuses/home_timeline', {})
            print(f"Home timeline API calls remaining: {timeline_limit.get('remaining', 'unknown')}/{timeline_limit.get('limit', 'unknown')}")
        
        if 'users' in resources:
            user_limit = resources['users'].get('/users/show/:id', {})
            print(f"User info API calls remaining: {user_limit.get('remaining', 'unknown')}/{user_limit.get('limit', 'unknown')}")
        
        print("\nTwitter API connection is working correctly!")
        return True
        
    except tweepy.TweepyException as e:
        print(f"❌ Twitter API Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_twitter_api()
    sys.exit(0 if success else 1)

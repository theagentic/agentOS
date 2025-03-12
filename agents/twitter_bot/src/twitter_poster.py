import tweepy
import os
import time
from typing import List
import random
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitterPoster:
    def __init__(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Missing Twitter API credentials in .env file")

        auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        
        self.client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )

        # Add v1 API for rate limit checking
        self.api = tweepy.API(auth)

        # Verify credentials
        try:
            self.client.get_me()
            print("Successfully authenticated with Twitter API")
        except tweepy.Forbidden:
            print("""
ERROR: Twitter API authentication failed due to permissions issue.
Please check your Twitter Developer Portal settings:
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Select your app
3. Go to "User authentication settings"
4. Enable OAuth 1.0a
5. Set App permissions to "Read and write"
6. Set Type of App to "Web App, Automated App or Bot"
7. Save changes and regenerate tokens if needed
            """)
            raise
        except Exception as e:
            print(f"Twitter API authentication failed: {str(e)}")
            raise

        # Get user info during initialization
        try:
            self.user_info = self.client.get_me().data
            self.username = self.user_info.username
            print(f"Authenticated as @{self.username}")
        except Exception as e:
            print(f"Error getting user info: {str(e)}")
            raise

    def check_rate_limits(self):
        """Check current rate limits and wait if needed."""
        try:
            limits = self.api.rate_limit_status()
            tweets_remaining = limits['resources']['tweets']['/tweets']['remaining']
            reset_time = limits['resources']['tweets']['/tweets']['reset']
            
            if tweets_remaining == 0:
                reset_datetime = datetime.fromtimestamp(reset_time, timezone.utc)
                now = datetime.now(timezone.utc)
                wait_seconds = (reset_datetime - now).total_seconds() + 10  # Add buffer
                
                print(f"Rate limit reached. Waiting {wait_seconds:.0f} seconds until {reset_datetime} UTC")
                time.sleep(wait_seconds)
                return False
            
            print(f"Rate limits: {tweets_remaining} tweets remaining")
            return True
            
        except Exception as e:
            print(f"Error checking rate limits: {e}")
            return True  # Continue if we can't check

    def post_with_retry(self, tweet_func, max_retries=5, initial_delay=15):
        """Post with exponential backoff retry logic and jitter."""
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return tweet_func()
            except tweepy.TooManyRequests:
                if attempt == max_retries - 1:
                    raise
                # Add jitter to avoid thundering herd
                jitter = random.uniform(0, 5)
                wait_time = delay + jitter
                print(f"Rate limit hit, waiting {wait_time:.1f} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
                delay *= 2  # Exponential backoff
            except Exception as e:
                print(f"Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)

    def post_tweets(self, tweets: List[str], blog_title: str = "Unknown", blog_file: str = "unknown.md") -> bool:
        """Post a thread of tweets."""
        if not tweets:
            self._print_progress("No tweets to post")
            return False
            
        successful_tweets = 0
        thread_url = None
        
        try:
            # Print initial status
            self._print_progress(f"Starting to post {len(tweets)} tweets for blog: {blog_title}")
            
            # Post the first tweet
            self._print_progress("🚀 Posting main tweet...")
            
            # Create first tweet with specific handling for response
            try:
                response = self.client.create_tweet(text=tweets[0])
                if not response or not response.data:
                    raise Exception("Empty response when posting main tweet")
                    
                # Capture the tweet id from first tweet's response
                first_tweet_id = response.data['id']
                previous_tweet_id = first_tweet_id
                successful_tweets = 1
                
                # Generate the thread URL
                thread_url = f"https://twitter.com/{self.username}/status/{first_tweet_id}"
                self._print_progress(f"✅ Posted main tweet! ({successful_tweets}/{len(tweets)})")
                self._print_progress(f"Thread started at: {thread_url}")
                
            except Exception as e:
                # Special handling for rate limit errors
                error_str = str(e)
                if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                    self._print_progress("❌ Error posting main tweet: 429 Too Many Requests")
                    self._print_progress("Failed to complete tweet thread")
                    return False
                else:
                    self._print_progress(f"❌ Error posting main tweet: {str(e)}")
                    return False
            
            # Post the rest of the tweets as replies with better error handling
            for i, tweet in enumerate(tweets[1:], 1):
                try:
                    # Check rate limits between tweets
                    self.check_rate_limits()
                    
                    # Add delay between tweets
                    delay = random.uniform(3, 8)
                    self._print_progress(f"Waiting {delay:.1f}s before posting next reply...")
                    time.sleep(delay)
                    
                    self._print_progress(f"🔄 Posting tweet {i+1}/{len(tweets)}...")
                    
                    # Create reply tweet with fixed reference to previous tweet
                    reply_response = self.client.create_tweet(
                        text=tweet,
                        in_reply_to_tweet_id=previous_tweet_id
                    )
                    
                    if not reply_response or not reply_response.data or 'id' not in reply_response.data:
                        raise Exception(f"Failed to post reply {i+1}")
                        
                    # Update previous_tweet_id for the next reply
                    previous_tweet_id = reply_response.data['id']
                    successful_tweets += 1
                    self._print_progress(f"✅ Posted reply {i+1}/{len(tweets)}")
                    
                except Exception as e:
                    self._print_progress(f"❌ Error posting reply {i+1}: {str(e)}")
                    # Continue with next tweet even if one fails
                
            # Report final status
            if successful_tweets == len(tweets):
                self._print_progress(f"🎉 Successfully posted all {successful_tweets} tweets!")
            else:
                self._print_progress(f"⚠️ Posted {successful_tweets}/{len(tweets)} tweets")
                
            self._print_progress(f"📱 View the thread at: {thread_url}")
            return successful_tweets > 0
            
        except Exception as e:
            # Check for rate limit errors in the exception
            error_str = str(e)
            if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                self._print_progress("❌ Error: Twitter rate limit reached (429 Too Many Requests)")
            else:
                self._print_progress(f"❌ Error in post_tweets: {str(e)}")
            return False

    def _print_progress(self, message: str):
        """Print progress message with clear formatting for both human readers and parent process."""
        # Format timestamp for human readability
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        # Print the human-readable format
        print(formatted_msg, flush=True)
        
        # Print the machine-readable format for the parent process
        # Make sure this is a separate print statement
        print(f"PROGRESS: {message}", flush=True)
        
        # Log the message
        logger.info(message)

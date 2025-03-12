"""
Main script for the Twitter Bot agent.
Handles blog post monitoring and tweet generation.
"""
import os
import sys
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    # Import components - Fix the import for monitor_blog_directory
    from src.blog_reader import BlogPost, get_latest_post, monitor_blog_directory
    from src.tweet_generator import TweetGenerator
    from src.twitter_poster import TwitterPoster
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)

def load_environment():
    """Load environment variables from both system and agent .env files."""
    load_dotenv()

def get_blog_post() -> Optional[BlogPost]:
    """Get the latest blog post if available."""
    posts_path = os.getenv('BLOG_POSTS_PATH')
    if not posts_path:
        raise ValueError("BLOG_POSTS_PATH not set in .env file")
    
    if not os.path.exists(posts_path):
        raise ValueError(f"Directory does not exist: {posts_path}")

    return get_latest_post(posts_path)

def generate_and_post_tweets(dry_run: bool = False):
    """Generate and optionally post tweets from the latest blog post."""
    try:
        # Get latest blog post
        blog_post = get_blog_post()
        if not blog_post:
            return False
        
        # Get blog title from metadata if available
        title = "Unknown"
        if hasattr(blog_post, 'metadata') and blog_post.metadata:
            if isinstance(blog_post.metadata, dict) and 'title' in blog_post.metadata:
                title = blog_post.metadata['title']
        
        # Check if progress updates are enabled
        notify_progress = os.getenv('TWITTER_NOTIFY_PROGRESS') == '1'
        if notify_progress:
            print(f"PROGRESS: Processing blog post: {title}")
            # Make sure output is flushed
            sys.stdout.flush()
        else:
            print(f"Processing blog post: {title}")
            sys.stdout.flush()
        
        # Generate tweets with retry logic
        tweet_generator = TweetGenerator()
        
        try:
            # Generate tweets
            tweets = tweet_generator.generate_tweets_with_retry(blog_post)
            
            if notify_progress:
                print(f"PROGRESS: Generated {len(tweets)} tweets successfully")
                sys.stdout.flush()
        except Exception as e:
            # Check for specific errors
            error_str = str(e).lower()
            if "quota" in error_str or "rate limit" in error_str or "limit exceeded" in error_str:
                logger.error(f"Gemini API quota error: {e}")
                if notify_progress:
                    print(f"PROGRESS: Gemini API quota error: {str(e)}")
                    sys.stdout.flush()
            else:
                logger.error(f"Failed to generate tweets: {e}")
                if notify_progress:
                    print(f"PROGRESS: Error generating tweets: {str(e)}")
                    sys.stdout.flush()
            return False
        
        if not tweets:
            logger.error("No tweets generated")
            if notify_progress:
                print("PROGRESS: No tweets could be generated from the blog post")
                sys.stdout.flush()
            return False
            
        # If not dry run, post the tweets
        if not dry_run:
            if notify_progress:
                print("PROGRESS: Starting to post tweets to Twitter")
                sys.stdout.flush()
            try:
                poster = TwitterPoster()
                blog_filename = os.path.basename(blog_post.filepath) if blog_post.filepath else "unknown.md"
                success = poster.post_tweets(tweets, title, blog_filename)
                
                if success:
                    if notify_progress:
                        print("PROGRESS: Successfully completed tweet thread")
                        sys.stdout.flush()
                    return True
                else:
                    if notify_progress:
                        print("PROGRESS: Failed to complete tweet thread")
                        sys.stdout.flush()
                    return False
            except Exception as e:
                logger.error(f"Error posting tweets: {e}")
                if notify_progress:
                    print(f"PROGRESS: Error posting tweets: {str(e)}")
                    sys.stdout.flush()
                return False
        else:
            if notify_progress:
                print("PROGRESS: Dry run complete - tweets generated but not posted")
                sys.stdout.flush()
            return True
            
    except Exception as e:
        # Check for specific error types
        error_str = str(e).lower()
        if "rate" in error_str and "limit" in error_str:
            logger.error(f"Rate limit error in generate_and_post_tweets: {e}")
            if os.getenv('TWITTER_NOTIFY_PROGRESS') == '1':
                print(f"PROGRESS: Twitter rate limit error: {str(e)}")
                sys.stdout.flush()
        elif "quota" in error_str or "gemini" in error_str:
            logger.error(f"Gemini API error in generate_and_post_tweets: {e}")
            if os.getenv('TWITTER_NOTIFY_PROGRESS') == '1':
                print(f"PROGRESS: Gemini API error: {str(e)}")
                sys.stdout.flush()
        else:
            logger.error(f"Error in generate_and_post_tweets: {e}")
            if os.getenv('TWITTER_NOTIFY_PROGRESS') == '1':
                print(f"PROGRESS: Error: {str(e)}")
                sys.stdout.flush()
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', 
                       help='Generate tweets without posting')
    parser.add_argument('--run-once', action='store_true',
                       help='Run once and exit (do not monitor for changes)')
    parser.add_argument('--progress-updates', action='store_true',
                       help='Enable verbose progress updates')
    parser.add_argument('--timeout', type=int, default=600,
                       help='Maximum time to run in monitor mode (seconds), default 10 minutes')
    args = parser.parse_args()
    
    load_environment()
    
    # Enable progress updates in environment if flag is set
    if args.progress_updates:
        os.environ['TWITTER_NOTIFY_PROGRESS'] = '1'
        print("Progress updates enabled")
    
    # Decide whether to run once or monitor
    if args.run_once:
        return generate_and_post_tweets(args.dry_run)
    
    # Otherwise run in monitor mode
    print(f"Starting blog monitor on {os.getenv('BLOG_POSTS_PATH')}")
    observer = monitor_blog_directory(
        os.getenv('BLOG_POSTS_PATH'),
        lambda post: generate_and_post_tweets(args.dry_run)
    )
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping blog monitor...")
    observer.join()

if __name__ == "__main__":
    main()

import os
import re
import time
import logging
import google.generativeai as genai
from typing import List
import random
from src.blog_reader import BlogPost  # Direct import

# Configure logging
logger = logging.getLogger(__name__)

class TweetGenerator:
    """Generates tweets from blog posts using Google's Gemini API."""
    
    def __init__(self):
        """Initialize the tweet generator with API key from environment."""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Get available models
        self.models = genai.list_models()
        # Look for text generation capable models
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Track generation progress
        self.generation_progress = {
            "status": "not_started",
            "progress": 0,  # 0-100%
            "step": "",
            "message": "",
            "started_at": None,
            "completed_at": None
        }
        
        logger.info(f"Initialized TweetGenerator using {self.model.model_name}")
    
    def _update_progress(self, status: str, progress: int, step: str, message: str = ""):
        """Update the generation progress and print it to console."""
        self.generation_progress = {
            "status": status,
            "progress": progress,
            "step": step,
            "message": message,
            "started_at": self.generation_progress["started_at"],
            "completed_at": None if status != "complete" else time.time()
        }
        
        # Print progress to console
        progress_bar = self._get_progress_bar(progress)
        print(f"\r{progress_bar} {progress}% | {step}: {message}", end="")
        
        # Add a newline if complete
        if status == "complete":
            print()
    
    def _get_progress_bar(self, percentage: int, width: int = 20) -> str:
        """Generate a text-based progress bar."""
        filled_width = int(width * percentage / 100)
        bar = '█' * filled_width + '░' * (width - filled_width)
        return f"[{bar}]"
    
    def _extract_tweets(self, ai_response: str) -> List[str]:
        """Extract tweets from the AI response."""
        # Update progress
        self._update_progress("processing", 75, "Extracting tweets", "Parsing AI response")
        
        # Remove any "Tweet X: " prefixes as we'll handle numbering ourselves
        cleaned_response = re.sub(r'Tweet \d+:\s*', '', ai_response)
        
        # Try to find tweets in the response first by looking for numbered lists
        tweet_pattern = re.compile(r'(?:^|\n)(\d+\.\s*.*?)(?=\n\d+\.|$)', re.DOTALL)
        tweets = tweet_pattern.findall(cleaned_response)
        
        # If that didn't work, try splitting by double newlines
        if not tweets:
            # Update progress with the change in strategy
            self._update_progress("processing", 80, "Extracting tweets", "Using alternate parsing method")
            tweets = [t.strip() for t in cleaned_response.split('\n\n') if t.strip()]
        
        # Clean up each tweet
        tweets = [t.strip().replace('\n\n', '\n') for t in tweets]
        tweets = [t[2:].strip() if t.startswith('- ') else t for t in tweets]  # Remove leading bullet if present
        tweets = [t[2:].strip() if re.match(r'^\d+\.', t) else t for t in tweets]  # Remove leading numbers
        
        # Update progress
        self._update_progress("processing", 85, "Finalizing tweets", f"Found {len(tweets)} tweets")
        
        return tweets
        
    # Replace the backoff-decorated function with our own retry implementation
    # @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def generate_tweets(self, blog_post: BlogPost) -> List[str]:
        """
        Generate tweets from a blog post using the Gemini API.
        
        Args:
            blog_post: The blog post to create tweets from
            
        Returns:
            A list of tweets suitable for posting
        """
        # Reset and start progress tracking
        self.generation_progress = {
            "status": "starting",
            "progress": 0,
            "step": "Initializing",
            "message": "Preparing blog post for AI analysis",
            "started_at": time.time(),
            "completed_at": None
        }
        
        # Print initial progress status
        print("\n🔄 Starting tweet generation...")
        self._update_progress("starting", 5, "Initializing", "Preparing blog post")
        
        # Get the content and metadata
        content = blog_post.content
        metadata = getattr(blog_post, 'metadata', {}) or {}
        
        # Extract title and other metadata
        title = metadata.get('title', 'Untitled')
        author = metadata.get('author', 'Unknown')
        tags = metadata.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Prepare a prompt based on the blog post
        self._update_progress("processing", 15, "Processing blog", f"Analyzing '{title}'")
        
        max_content_length = 6000  # Limit content length to avoid token limits
        if len(content) > max_content_length:
            # Truncate content but keep beginning and end
            begin_portion = content[:max_content_length//2]
            end_portion = content[-max_content_length//2:]
            content = begin_portion + "\n...[content truncated]...\n" + end_portion
            self._update_progress("processing", 20, "Processing blog", "Truncated long content")
        
        # Construct the prompt
        self._update_progress("processing", 25, "Crafting prompt", "Building AI instruction")
        
        # Add some variety to the prompting for better results
        variation = random.choice(["informative", "engaging", "professional", "conversational"])
        
        prompt = f"""
        You are a professional social media content creator specializing in Twitter threads.
        
        Create a Twitter thread based on this blog post, using a {variation} style. 
        
        Blog post title: {title}
        Author: {author}
        Tags: {', '.join(tags) if tags else 'None'}
        
        Blog post content:
        {content}
        
        Guidelines:
        1. Create 4-6 tweets that capture the key points of the blog post
        2. Make the first tweet attention-grabbing, mentioning what the thread is about
        3. Each tweet should be under 280 characters
        4. Include relevant hashtags in some of the tweets (but not too many)
        5. The last tweet should include a clear call to action
        6. Focus on delivering value to the reader
        
        Format each tweet as a numbered list (1., 2., etc.) with one tweet per item.
        Don't include "Tweet X:" prefixes.
        
        Create a thread that makes people want to read the full blog post!
        """
        
        self._update_progress("processing", 30, "Sending to AI", "Connecting to Gemini API")
        
        # Make API call to generate tweets
        try:
            # Show a wait message
            self._update_progress("processing", 40, "Awaiting response", "AI is generating tweets...")
            
            # Add small random delays to show progress animation
            for progress in range(40, 71, 5):
                time.sleep(random.uniform(0.5, 1.5))  # Random delay to simulate work
                activity_messages = [
                    "AI analyzing content...",
                    "Identifying key points...",
                    "Crafting compelling tweets...",
                    "Optimizing messaging...",
                    "Checking character limits...",
                    "Adding hashtags...",
                ]
                message = random.choice(activity_messages)
                self._update_progress("processing", progress, "Generating tweets", message)
            
            # Make the actual API call
            ai_response = self.model.generate_content(prompt).text
            
            # Update progress now that we have the response
            self._update_progress("processing", 70, "Received response", "Got AI-generated content")
            
            # Extract tweets
            tweets = self._extract_tweets(ai_response)
            
            # Validate tweet lengths and adjust if needed
            self._update_progress("processing", 90, "Validating tweets", "Checking character limits")
            valid_tweets = []
            for i, tweet in enumerate(tweets):
                if len(tweet) > 280:
                    # Truncate and add ellipsis if too long
                    valid_tweets.append(tweet[:276] + "...")
                    logger.warning(f"Tweet {i+1} was too long ({len(tweet)} chars) and was truncated")
                else:
                    valid_tweets.append(tweet)
            
            # Complete progress
            self._update_progress("complete", 100, "Complete", f"Generated {len(valid_tweets)} tweets")
            
            return valid_tweets
            
        except Exception as e:
            self._update_progress("error", 0, "Error", f"Failed: {str(e)}")
            logger.error(f"Tweet generation error: {e}")
            raise
    
    def generate_tweets_with_retry(self, blog_post: BlogPost, max_retries: int = 3) -> List[str]:
        """
        Generate tweets with automatic retry.
        
        Args:
            blog_post: The blog post to create tweets from
            max_retries: Maximum number of retry attempts
            
        Returns:
            A list of tweets suitable for posting
        """
        attempt = 0
        
        while attempt < max_retries:
            try:
                return self.generate_tweets(blog_post)
            except Exception as e:
                attempt += 1
                
                # Check for specific API errors
                error_str = str(e).lower()
                if "quota" in error_str or "rate limit" in error_str or "limit exceeded" in error_str:
                    print("\n🚫 Gemini API quota reached or exceeded.")
                    print("PROGRESS: Error: Gemini API quota limit reached. Please try again later.")
                    if attempt >= max_retries:
                        logger.error(f"Gemini API quota error after {max_retries} attempts: {str(e)}")
                        raise Exception(f"Gemini API quota error: {str(e)}")
                # Print retry message
                elif attempt < max_retries:
                    remaining = max_retries - attempt
                    retry_msg = f"⚠️ Tweet generation failed. Retrying ({remaining} attempts remaining)..."
                    print(f"\n{retry_msg}")
                    logger.warning(f"Retry {attempt}/{max_retries}: {str(e)}")
                    time.sleep(2)  # Wait before retrying
                else:
                    logger.error(f"All {max_retries} generation attempts failed: {str(e)}")
                    raise

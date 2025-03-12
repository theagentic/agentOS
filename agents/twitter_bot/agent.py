import os
import tweepy
import subprocess
import threading
import logging
import traceback
from pathlib import Path
from datetime import datetime
from core.agent_base import AgentBase

logger = logging.getLogger(__name__)

class TwitterBotAgent(AgentBase):
    def __init__(self):
        super().__init__()
        
        # Add debug logging
        logger.info("Initializing TwitterBotAgent")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', os.getenv('TWITTER_ACCESS_SECRET'))
        
        # Debug logging for credential detection (with minimal disclosure)
        logger.info(f"API key detected: {'Yes' if self.api_key else 'No'}")
        logger.info(f"API secret detected: {'Yes' if self.api_secret else 'No'}")
        logger.info(f"Access token detected: {'Yes' if self.access_token else 'No'}")
        logger.info(f"Access secret detected: {'Yes' if self.access_secret else 'No'}")
        
        self.blog_monitor = None
        self.blog_monitor_thread = None
        
        try:
            if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                logger.info("All Twitter credentials found, initializing API")
                auth = tweepy.OAuth1UserHandler(self.api_key, self.api_secret, self.access_token, self.access_secret)
                self.api = tweepy.API(auth)
                self.api_initialized = True
                
                # Try a quick verification
                try:
                    user = self.api.verify_credentials()
                    logger.info(f"Successfully authenticated as @{user.screen_name}")
                except Exception as e:
                    logger.error(f"Failed to verify credentials: {e}")
                    self.api_initialized = False
            else:
                logger.error("Missing Twitter credentials")
                self.api_initialized = False
        except Exception as e:
            logger.error(f"Error initializing Twitter API: {e}")
            self.api_initialized = False
    
    def process(self, command: str):
        # Check API initialization
        if not self.api_initialized and not ("help" in command.lower() or "status" in command.lower()):
            return {
                "status": "error",
                "message": "Twitter API not initialized. Please check your credentials in .env file.",
                "spoke": "Twitter API not initialized. Please check your API credentials."
            }
            
        command_lower = command.lower()
        
        # Standard Twitter commands
        if "tweet " in command_lower and len(command_lower) > 6:
            return self.tweet(command)
        elif "timeline" in command_lower:
            return self.get_timeline()
        elif "notifications" in command_lower:
            return self.get_notifications()
        elif "messages" in command_lower:
            return self.get_messages()
            
        # Blog to Twitter functionality
        elif "monitor blog" in command_lower:
            return self.start_blog_monitor()
        elif "stop monitor" in command_lower:
            return self.stop_blog_monitor()
        elif "generate tweets" in command_lower and "blog" in command_lower:
            return self.generate_tweets_from_blog(dry_run=True)
        # Fix the command pattern matching to be more flexible
        elif any(phrase in command_lower for phrase in ["post blog thread", "post thread", "create thread", "post blog"]):
            return self.generate_tweets_from_blog(dry_run=False)
        elif "status" in command_lower:
            return self.get_status()
        elif "help" in command_lower:
            return self.get_help()
        else:
            return {"status": "error", "message": "Unknown command for TwitterBotAgent. Try 'twitter help' for available commands."}
    
    def tweet(self, command: str):
        try:
            message = command.replace("tweet", "", 1).strip()
            self.api.update_status(message)
            return {
                "status": "success", 
                "message": f"Tweeted: {message}",
                "spoke": "Your tweet has been posted successfully."
            }
        except Exception as e:
            return {"status": "error", "message": f"Error posting tweet: {str(e)}"}
    
    def get_timeline(self):
        try:
            timeline = self.api.home_timeline(count=5)
            tweets = [tweet.text for tweet in timeline]
            
            message = "Recent tweets from your timeline:\n\n" + "\n\n".join([f"- {tweet}" for tweet in tweets])
            return {
                "status": "success", 
                "tweets": tweets,
                "message": message,
                "spoke": f"Here are your {len(tweets)} most recent tweets from your timeline."
            }
        except Exception as e:
            return {"status": "error", "message": f"Error fetching timeline: {str(e)}"}
    
    def start_blog_monitor(self):
        blog_path = os.getenv('BLOG_POSTS_PATH')
        if not blog_path:
            return {
                "status": "error",
                "message": "BLOG_POSTS_PATH not set in .env file",
                "spoke": "Blog posts path is not configured. Please set BLOG_POSTS_PATH in your environment variables."
            }
            
        if not os.path.exists(blog_path):
            return {
                "status": "error",
                "message": f"Blog path does not exist: {blog_path}",
                "spoke": "The specified blog posts directory does not exist."
            }
            
        if self.blog_monitor_thread and self.blog_monitor_thread.is_alive():
            return {
                "status": "info",
                "message": "Blog monitor is already running",
                "spoke": "Blog monitor is already running."
            }
            
        # Run the monitor in a separate process
        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "main.py")
            
            def run_monitor():
                subprocess.run(["python", script_path], cwd=os.path.dirname(script_path))
                
            self.blog_monitor_thread = threading.Thread(target=run_monitor, daemon=True)
            self.blog_monitor_thread.start()
            
            return {
                "status": "success",
                "message": f"Started monitoring blog directory: {blog_path}",
                "spoke": "Blog directory monitoring has been started. I'll create tweets for new posts."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error starting blog monitor: {str(e)}",
                "spoke": "There was an error starting the blog monitor."
            }
    
    def stop_blog_monitor(self):
        if self.blog_monitor_thread and self.blog_monitor_thread.is_alive():
            # We can't easily kill the thread, but we can inform the user
            return {
                "status": "info",
                "message": "Blog monitor process will continue in the background. You can restart the application to stop it completely.",
                "spoke": "Blog monitor will continue running in the background until the application is restarted."
            }
        else:
            return {
                "status": "info",
                "message": "Blog monitor is not currently running",
                "spoke": "Blog monitor is not currently running."
            }
    
    def generate_tweets_from_blog(self, dry_run=True):
        thread_url = None
        rate_limit_error = False
        gemini_api_error = False
        error_message = None
        blog_path = os.getenv('BLOG_POSTS_PATH')
        if not blog_path:
            return {
                "status": "error",
                "message": "BLOG_POSTS_PATH not set in .env file",
                "spoke": "Blog posts path is not configured. Please set BLOG_POSTS_PATH in your environment variables."
            }
            
        # First check if the blog path exists
        if not os.path.exists(blog_path):
            return {
                "status": "error", 
                "message": f"Blog path does not exist: {blog_path}",
                "spoke": "The blog directory doesn't exist. Please check your BLOG_POSTS_PATH setting."
            }
            
        # Check if there are any markdown files
        blog_files = list(Path(blog_path).glob("*.md"))
        if not blog_files:
            return {
                "status": "error",
                "message": "No markdown files found in blog directory",
                "spoke": "I couldn't find any blog posts in your blog directory."
            }
        
        # Since we can't return an early status update in a synchronous call,
        # we'll just log it for visibility
        logger.info(f"Processing blog post. Found {len(blog_files)} markdown files. This may take up to 30 seconds...")
            
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "main.py")
        
        try:
            # Provide immediate feedback
            logger.info(f"Starting blog processing script at {script_path}")
            logger.info(f"Using blog path: {blog_path}")
            logger.info(f"Dry run: {dry_run}")
            
            cmd = ["python", script_path]
            if dry_run:
                cmd.append("--dry-run")
                
            # Add progress updates flag
            cmd.append("--progress-updates")
            cmd.append("--run-once")  # Make sure it runs once and exits
            
            # Create process with explicit UTF-8 encoding
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(script_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # This enables text mode with default UTF-8 encoding
                encoding='utf-8',  # Explicitly set UTF-8 encoding
                errors='replace',  # Replace invalid characters instead of failing
                bufsize=1  # Line buffered
            )

            # Create a message queue for streaming updates to the UI
            from core.message_queue import MessageQueue
            self.message_queue = MessageQueue()
            
            # Send initial status update to UI
            self.message_queue.add_message({
                "agent": "twitter_bot",
                "status": "progress",
                "message": f"Starting to process blog post for {'generating' if dry_run else 'posting'} tweets...",
                "spoke": f"Starting to process blog post for {'generating' if dry_run else 'posting'} tweets...",
                "timestamp": datetime.now().isoformat()
            })

            # Improved output reader with better error handling
            def read_output():
                try:
                    nonlocal rate_limit_error, gemini_api_error, error_message
                    for line in process.stdout:
                        if not line:  # Skip empty lines
                            continue
                            
                        line = line.strip()
                        if not line:  # Skip lines that are just whitespace
                            continue
                        
                        # Detect rate limit errors in progress messages
                        if "429 Too Many Requests" in line or "rate limit" in line.lower():
                            rate_limit_error = True
                            error_message = line.split("Error posting")[1].strip() if "Error posting" in line else "Twitter rate limit exceeded"
                            logger.warning(f"Detected rate limit error: {error_message}")
                            
                        # Detect Gemini API errors
                        elif any(x in line.lower() for x in ["gemini", "google ai"]) and any(x in line.lower() for x in ["api error", "quota", "limit"]):
                            gemini_api_error = True
                            error_message = line
                            logger.warning(f"Detected Gemini API error: {error_message}")
                            
                        # Detect general errors in progress messages
                        elif "Error" in line and any(x in line.lower() for x in ["posting", "tweet", "failed"]):
                            if not error_message:  # Don't overwrite rate limit or Gemini error
                                error_message = line.split("Error")[1].strip() if "Error" in line else "Error posting tweets"
                                logger.warning(f"Detected error in tweets: {error_message}")
                        
                        # Process progress messages
                        if line.startswith("PROGRESS:"):
                            message = line[9:].strip()
                            logger.info(f"Progress update: {message}")
                            
                            # Send progress message to UI
                            if hasattr(self, 'message_queue') and self.message_queue:
                                self.message_queue.add_message({
                                    "agent": "twitter_bot",
                                    "status": "progress",
                                    "message": message,
                                    "spoke": message,
                                    "timestamp": datetime.now().isoformat()
                                })
                        # Fix: Check if the line contains the thread URL text before splitting
                        elif "Thread started at:" in line:
                            try:
                                nonlocal thread_url
                                thread_url = line.split("Thread started at:")[1].strip()
                                # Send thread URL to UI
                                if hasattr(self, 'message_queue') and self.message_queue:
                                    self.message_queue.add_message({
                                        "agent": "twitter_bot",
                                        "status": "progress",
                                        "message": f"Thread posted at: {thread_url}",
                                        "thread_url": thread_url,
                                        "timestamp": datetime.now().isoformat()
                                    })
                            except Exception as url_error:
                                logger.error(f"Error extracting thread URL: {url_error}")
                except Exception as e:
                    logger.error(f"Error reading subprocess output: {e}")
                    logger.error(traceback.format_exc())
                    
                    # Send error message to UI
                    if hasattr(self, 'message_queue') and self.message_queue:
                        self.message_queue.add_message({
                            "agent": "twitter_bot",
                            "status": "error",
                            "message": f"Error processing output: {str(e)}",
                            "spoke": "There was an error processing the Twitter bot output.",
                            "timestamp": datetime.now().isoformat()
                        })

            # Start output reading thread
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            try:
                exit_code = process.wait(timeout=300)  # 5 minute timeout
                
                # Check for rate limit error that we detected in the output
                if rate_limit_error:
                    return {
                        "status": "error",
                        "message": f"Twitter API rate limit reached: {error_message}",
                        "spoke": "Twitter's rate limit has been reached. Please wait a few minutes before trying again.",
                        "error_type": "rate_limit"
                    }
                    
                # Check for other errors we detected in the output
                if gemini_api_error:
                    return {
                        "status": "error",
                        "message": f"Gemini API error: {error_message}",
                        "spoke": "I've hit my Gemini API quota. Please try again later or check your API key.",
                        "error_type": "gemini_api_error"
                    }
                    
                if error_message and exit_code != 0:
                    return {
                        "status": "error",
                        "message": f"Error posting tweets: {error_message}",
                        "spoke": "There was an error posting your tweets to Twitter.",
                        "error_type": "posting_error"
                    }
                    
                if exit_code != 0:
                    error_text = process.stderr.read() if process.stderr else "Unknown error occurred"
                    raise Exception(f"Process failed with exit code {exit_code}: {error_text}")
            except subprocess.TimeoutExpired:
                process.kill()
                raise Exception("Process timed out after 5 minutes")
            
            # After process completes, check again for rate limit or error flags
            if rate_limit_error:
                return {
                    "status": "error",
                    "message": f"Twitter API rate limit reached: {error_message}",
                    "spoke": "Twitter's rate limit has been reached. Please wait a few minutes before trying again.",
                    "error_type": "rate_limit"
                }
                
            if gemini_api_error:
                return {
                    "status": "error",
                    "message": f"Gemini API error: {error_message}",
                    "spoke": "I've hit my Gemini API quota. Please try again later or check your API key.",
                    "error_type": "gemini_api_error"
                }
                
            if error_message:
                return {
                    "status": "error",
                    "message": f"Error posting tweets: {error_message}",
                    "spoke": "There was an error posting your tweets to Twitter.",
                    "error_type": "posting_error"
                }
            
            if process.returncode == 0:
                # Fix: Read the content from stdout before trying to use it
                stdout_content = ""
                if process.stdout:
                    stdout_content = process.stdout.read() if hasattr(process.stdout, 'read') else str(process.stdout)
                message = stdout_content or "Processing complete."
                
                # Extract the actual tweets from the output if possible
                tweets = []
                lines = message.split('\n')
                capturing = False
                current_tweet = []
                
                for line in lines:
                    if line.startswith("Tweet ") and ":" in line:
                        if capturing and current_tweet:
                            tweets.append("\n".join(current_tweet).strip())
                            current_tweet = []
                        capturing = True
                        continue
                    elif capturing and line.startswith("---"):
                        continue
                    elif capturing and line.startswith("Generated") and "tweets" in line:
                        capturing = False
                        if current_tweet:
                            tweets.append("\n".join(current_tweet).strip())
                    elif capturing:
                        current_tweet.append(line)
                
                # If we captured any tweets, format them nicely for display
                if tweets:
                    formatted_output = ["✅ Successfully processed your blog post!"]
                    
                    # Add status message based on dry run
                    if dry_run:
                        formatted_output.append("\n📝 Generated tweets (not posted to Twitter):")
                    else:
                        formatted_output.append("\n🚀 Posted the following tweets to Twitter:")
                    
                    # Add each tweet with formatting
                    for i, tweet in enumerate(tweets):
                        formatted_output.append(f"\n📌 Tweet {i+1}:\n{tweet}")
                    
                    # Add instructions for next steps
                    if dry_run:
                        formatted_output.append("\n\nTo post these tweets, use the 'post blog thread' command.")
                    
                    # Add final success message to queue
                    if self.message_queue:
                        self.message_queue.add_message({
                            "agent": "twitter_bot",
                            "status": "complete",
                            "message": "Successfully completed Twitter operation!",
                            "thread_url": thread_url if 'thread_url' in locals() else None,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    return {
                        "status": "success",
                        "message": "\n".join(formatted_output),
                        "spoke": f"Successfully {'generated' if dry_run else 'posted'} {len(tweets)} tweets from your blog post.",
                        "tweet_count": len(tweets),
                        "tweets": tweets
                    }
                # No tweets found in output, use default success message
                return {
                    "status": "success",
                    "message": message,
                    "spoke": "Blog post processed successfully." + (" Tweets were generated but not posted." if dry_run else " Tweets were posted to Twitter.")
                }
            else:
                # Fix the error handling for stderr - read the content first
                error_text = process.stderr.read() if process.stderr else "Unknown error occurred"
                
                # Check for rate limit errors
                if "rate limit" in error_text.lower() or "too many requests" in error_text.lower() or "429" in error_text:
                    return {
                        "status": "error",
                        "message": "Twitter API rate limit reached. Please try again later.",
                        "spoke": "Twitter's API rate limit has been reached. Please wait a few minutes before trying again.",
                        "error_type": "rate_limit"
                    }
                # Enhanced check for Gemini API errors
                elif any(x in error_text.lower() for x in ["gemini", "google ai"]) and any(x in error_text.lower() for x in ["api", "quota", "limit", "error"]):
                    return {
                        "status": "error",
                        "message": f"Gemini API error: {error_text}",
                        "spoke": "I've reached my Gemini AI quota limit. Please try again later or check your API key settings.",
                        "error_type": "gemini_api_error"
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Error processing blog post: {error_text}",
                        "spoke": "There was an error processing the blog post."
                    }
                
        except subprocess.TimeoutExpired:  # Keep this just in case there's a system timeout
            return {
                "status": "error", 
                "message": "Blog processing is taking longer than expected. Consider checking logs for more information.",
                "spoke": "Blog processing is taking longer than expected. You can check the logs for details."
            }
        except Exception as e:
            # Also check the exception for API errors
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                return {
                    "status": "error",
                    "message": f"Twitter API rate limit error: {str(e)}",
                    "spoke": "Twitter's rate limit has been reached. Please wait a few minutes before trying again.",
                    "error_type": "rate_limit"
                }
            elif "gemini" in error_str or "google ai" in error_str:
                return {
                    "status": "error",
                    "message": f"Gemini API error: {str(e)}",
                    "spoke": "There was an error with the Gemini AI service. This might be due to quota limitations.",
                    "error_type": "gemini_api_error"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Error running blog processor: {str(e)}",
                    "spoke": "There was an error running the blog processor."
                }
        finally:
            # Clean up message queue reference after completion
            self.message_queue = None
    
    def get_notifications(self):
        # Placeholder for notifications functionality
        return {"status": "info", "message": "Notifications feature not fully implemented yet.", "spoke": "The notifications feature is not fully implemented yet."}
    
    def get_messages(self):
        # Placeholder for messages functionality
        return {"status": "info", "message": "Messages feature not fully implemented yet.", "spoke": "The messages feature is not fully implemented yet."}
        
    def get_status(self):
        status_info = {
            "api_initialized": self.api_initialized,
            "blog_monitor_running": bool(self.blog_monitor_thread and self.blog_monitor_thread.is_alive()),
            "blog_path": os.getenv('BLOG_POSTS_PATH') or "Not set"
        }
        
        message = f"""Twitter Bot Status:
- API Initialized: {'Yes' if status_info['api_initialized'] else 'No - Check credentials'}
- Blog Monitor Running: {'Yes' if status_info['blog_monitor_running'] else 'No'}
- Blog Path: {status_info['blog_path']}
"""

        return {
            "status": "success",
            "message": message,
            "data": status_info,
            "spoke": f"Twitter bot status: API {'initialized' if status_info['api_initialized'] else 'not initialized'}. Blog monitor {'running' if status_info['blog_monitor_running'] else 'not running'}."
        }
        
    def get_help(self):
        help_text = """
Twitter Bot Commands:

Basic Twitter:
- Tweet [your message] - Post a tweet with the given message
- Twitter timeline - Show your recent timeline
- Twitter notifications - Check your notifications
- Twitter messages - Check your direct messages

Blog to Twitter:
- Monitor blog - Start monitoring your blog directory for new posts
- Stop monitoring - Stop the blog monitor
- Generate tweets from blog - Create tweets from latest post (dry run)
- Post blog thread - Create and post tweets from latest blog post

Status:
- Twitter status - Check the status of the Twitter bot
- Twitter help - Show this help message
"""

        return {
            "status": "success",
            "message": help_text,
            "spoke": "I can help you post tweets, monitor your timeline, and automatically create Twitter threads from your blog posts. Try 'Twitter help' to see all commands."
        }

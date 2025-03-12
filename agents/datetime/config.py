from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get Todoist API token from environment variable
TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')

# Verify token exists
if not TODOIST_API_TOKEN:
    raise ValueError("TODOIST_API_TOKEN not found in environment variables")

"""
Command line utility to check Twitter status without the GUI
"""
import requests
import json
import sys
from datetime import datetime

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'

def get_twitter_status():
    """Get Twitter status from backend"""
    try:
        print(f"{Colors.BLUE}Checking Twitter status...{Colors.RESET}")
        
        response = requests.get('http://127.0.0.1:5000/twitter/status', timeout=5)
        
        if not response.ok:
            print(f"{Colors.RED}Error: HTTP {response.status_code}{Colors.RESET}")
            print(f"{Colors.RED}Unable to fetch Twitter status. Make sure the backend server is running.{Colors.RESET}")
            return
        
        data = response.json()
        print(f"\n{Colors.BOLD}Twitter Status Report{Colors.RESET}\n")
        
        # Print API status
        status_color = Colors.YELLOW
        status_symbol = "⚠"
        
        if data.get('api_status') == "operational":
            status_color = Colors.GREEN
            status_symbol = "✓"
        elif data.get('api_status') == "error":
            status_color = Colors.RED
            status_symbol = "✗"
        
        print(f"API Status:     {status_color}{status_symbol} {data.get('api_status', 'unknown')}{Colors.RESET}")
        
        # Print rate limit info
        rate_limit = data.get('rate_limit', {})
        rate_limit_text = "Unknown"
        
        if rate_limit and rate_limit.get('remaining') != "unknown":
            rate_limit_text = f"{rate_limit.get('remaining')} calls remaining"
            
            if rate_limit.get('reset_time'):
                reset_time = datetime.fromisoformat(rate_limit['reset_time'].replace('Z', '+00:00'))
                formatted_time = reset_time.strftime('%H:%M:%S')
                rate_limit_text += f" (resets at {formatted_time})"
        
        print(f"Rate Limit:     {rate_limit_text}")
        
        # Print last thread info
        last_thread = data.get('last_thread')
        if last_thread:
            print(f"Latest Thread:  {Colors.CYAN}{last_thread}{Colors.RESET}")
        else:
            print(f"Latest Thread:  None")
        
        # Print last operation info
        operation = data.get('last_operation', {})
        if operation and operation.get('status') != "none":
            op_color = Colors.WHITE
            
            if operation.get('status') == "complete":
                op_color = Colors.GREEN
            elif operation.get('status') == "error":
                op_color = Colors.RED
            elif operation.get('status') in ["partial", "rate_limited"]:
                op_color = Colors.YELLOW
            
            print(f"Last Operation: {op_color}{operation.get('message', operation.get('status', 'unknown'))}{Colors.RESET}")
            
            if operation.get('timestamp'):
                op_time = datetime.fromisoformat(operation['timestamp'].replace('Z', '+00:00'))
                now = datetime.now()
                diff_mins = int((now - op_time).total_seconds() / 60)
                
                if diff_mins < 1:
                    time_ago = "just now"
                elif diff_mins < 60:
                    time_ago = f"{diff_mins} minute{'s' if diff_mins != 1 else ''} ago"
                else:
                    hours = diff_mins // 60
                    time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
                
                print(f"                ({time_ago})")
        else:
            print(f"Last Operation: None")
        
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}Error checking Twitter status: {e}{Colors.RESET}")
        print(f"{Colors.RED}Make sure the backend server is running at http://127.0.0.1:5000{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")

if __name__ == "__main__":
    get_twitter_status()

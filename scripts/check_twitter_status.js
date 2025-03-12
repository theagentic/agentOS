/**
 * Command line utility to check Twitter status without the GUI
 */
const fetch = require('node-fetch');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bold: '\x1b[1m'
};

/**
 * Get Twitter status from backend
 */
async function getTwitterStatus() {
  try {
    console.log(`${colors.blue}Checking Twitter status...${colors.reset}`);
    
    const response = await fetch('http://127.0.0.1:5000/twitter/status');
    
    if (!response.ok) {
      console.error(`${colors.red}Error: HTTP ${response.status}${colors.reset}`);
      console.error(`${colors.red}Unable to fetch Twitter status. Make sure the backend server is running.${colors.reset}`);
      return;
    }
    
    const data = await response.json();
    console.log(`\n${colors.bold}Twitter Status Report${colors.reset}\n`);
    
    // Print API status
    let statusColor = colors.yellow;
    let statusSymbol = "⚠";
    
    if (data.api_status === "operational") {
      statusColor = colors.green;
      statusSymbol = "✓";
    } else if (data.api_status === "error") {
      statusColor = colors.red;
      statusSymbol = "✗";
    }
    
    console.log(`API Status:     ${statusColor}${statusSymbol} ${data.api_status}${colors.reset}`);
    
    // Print rate limit info
    if (data.rate_limit) {
      const rateLimit = data.rate_limit;
      let rateLimitText = "Unknown";
      
      if (rateLimit.remaining !== "unknown") {
        rateLimitText = `${rateLimit.remaining} calls remaining`;
        
        if (rateLimit.reset_time) {
          const resetTime = new Date(rateLimit.reset_time);
          const formattedTime = resetTime.toLocaleTimeString();
          rateLimitText += ` (resets at ${formattedTime})`;
        }
      }
      
      console.log(`Rate Limit:     ${rateLimitText}`);
    }
    
    // Print last thread info
    if (data.last_thread) {
      console.log(`Latest Thread:  ${colors.cyan}${data.last_thread}${colors.reset}`);
    } else {
      console.log(`Latest Thread:  None`);
    }
    
    // Print last operation info
    if (data.last_operation && data.last_operation.status !== "none") {
      const operation = data.last_operation;
      let opColor = colors.white;
      
      if (operation.status === "complete") {
        opColor = colors.green;
      } else if (operation.status === "error") {
        opColor = colors.red;
      } else if (operation.status === "partial" || operation.status === "rate_limited") {
        opColor = colors.yellow;
      }
      
      console.log(`Last Operation: ${opColor}${operation.message || operation.status}${colors.reset}`);
      
      if (operation.timestamp) {
        const opTime = new Date(operation.timestamp);
        const now = new Date();
        const diffMs = now - opTime;
        const diffMins = Math.floor(diffMs / 60000);
        
        let timeAgo;
        if (diffMins < 1) {
          timeAgo = "just now";
        } else if (diffMins < 60) {
          timeAgo = `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        } else {
          const hours = Math.floor(diffMins / 60);
          timeAgo = `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        }
        
        console.log(`                (${timeAgo})`);
      }
    } else {
      console.log(`Last Operation: None`);
    }
    
  } catch (error) {
    console.error(`${colors.red}Error checking Twitter status: ${error.message}${colors.reset}`);
    console.error(`${colors.red}Make sure the backend server is running at http://127.0.0.1:5000${colors.reset}`);
  }
}

// Execute the function
getTwitterStatus();

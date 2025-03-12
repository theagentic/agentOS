/**
 * Twitter Panel Module
 * Handles Twitter status display and interactions
 */

const TwitterPanel = (function() {
    // Cache DOM elements
    let panelElement = null;
    let statusDisplay = null;
    let rateLimitDisplay = null;
    let lastOperationDisplay = null;
    let threadLinkDisplay = null;
    let refreshButton = null;
    
    // Track state
    let lastFetchTime = 0;
    let fetchInterval = null;
    const MIN_FETCH_INTERVAL = 3000; // 3 seconds between fetches
    let isFirstFetch = true;
    let errorCount = 0;
    const MAX_ERROR_COUNT = 5;
    
    // Initialize the panel
    function init() {
        console.log('Initializing Twitter Panel');
        
        // Find panel element
        panelElement = document.getElementById('twitter-panel');
        if (!panelElement) {
            console.error('Twitter panel element not found');
            return false;
        }
        
        // Find panel elements
        statusDisplay = document.getElementById('twitter-status');
        rateLimitDisplay = document.getElementById('twitter-rate-limit');
        lastOperationDisplay = document.getElementById('twitter-last-operation');
        threadLinkDisplay = document.getElementById('twitter-thread-link');
        refreshButton = document.getElementById('twitter-refresh');
        
        // Add event listeners
        if (refreshButton) {
            refreshButton.addEventListener('click', fetchStatus);
        }
        
        // Initial fetch after a small delay
        setTimeout(() => {
            fetchStatus();
            
            // Start periodic updates
            fetchInterval = setInterval(fetchStatus, 30000); // 30 seconds
        }, 2000);
        
        return true;
    }
    
    // Fetch Twitter status from backend
    async function fetchStatus(forceRefresh = false) {
        // Throttle requests
        const now = Date.now();
        if (!forceRefresh && now - lastFetchTime < MIN_FETCH_INTERVAL) {
            return;
        }
        
        lastFetchTime = now;
        
        try {
            // Show loading state
            updateLoadingState(true);
            
            // Make the request
            console.log('Fetching Twitter status...');
            const response = await fetch('/twitter/status');
            
            // Handle different response statuses
            if (response.ok) {
                // Reset error count on success
                errorCount = 0;
                
                // Parse response
                const data = await response.json();
                console.log('Twitter status:', data);
                
                // Update UI with the data
                updateStatusUI(data);
                
                // Not first fetch anymore
                isFirstFetch = false;
            } 
            else if (response.status === 404) {
                // Handle 404 errors (route not found)
                console.warn('Twitter status endpoint not found (404)');
                errorCount++;
                
                // Check if this is the first attempt
                if (isFirstFetch) {
                    // Display helpful message for initial setup
                    updateErrorState("Twitter integration is not properly configured", 
                        "The Twitter status endpoint was not found. This could be because:\n" +
                        "1. The Twitter routes haven't been registered correctly\n" +
                        "2. The backend server hasn't fully initialized yet\n\n" +
                        "Try refreshing in a few moments or check server logs for more information."
                    );
                    
                    // Try diagnostics endpoint
                    tryDiagnostics();
                } else if (errorCount >= MAX_ERROR_COUNT) {
                    // After multiple failures, show persistent error
                    updateErrorState("Twitter Status Unavailable", 
                        "The Twitter status endpoint is not responding after multiple attempts."
                    );
                } else {
                    // Generic 404 error
                    updateErrorState("Twitter Status Not Found", 
                        "The Twitter status endpoint could not be found. Will retry shortly."
                    );
                }
            }
            else {
                // Handle other error codes
                errorCount++;
                console.error(`Twitter status fetch failed with status: ${response.status}`);
                
                // After multiple failures, show a different message
                if (errorCount >= MAX_ERROR_COUNT) {
                    updateErrorState("Connection Issues", 
                        `Unable to fetch Twitter status after multiple attempts. (HTTP ${response.status})`
                    );
                } else {
                    updateErrorState("Fetch Error", 
                        `Failed to get Twitter status: HTTP ${response.status}`
                    );
                }
            }
        } catch (error) {
            // Handle network errors
            errorCount++;
            console.error('Error fetching Twitter status:', error);
            
            if (errorCount >= MAX_ERROR_COUNT) {
                updateErrorState("Network Error", 
                    "Connection to the server was lost. Please check that the backend is running."
                );
            } else {
                updateErrorState("Connection Error", 
                    "Failed to connect to the server. Will retry shortly."
                );
            }
        } finally {
            // Always remove loading state
            updateLoadingState(false);
        }
    }
    
    // Try to fetch diagnostics when status fails
    async function tryDiagnostics() {
        try {
            // First try the health check endpoint
            const healthResponse = await fetch('/twitter/health');
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                console.log('Twitter health check passed:', healthData);
                
                // If health check passes but status doesn't, suggest a different issue
                updateDiagnosticsInfo("✅ Twitter routes are mounted correctly, but status data is unavailable.");
                
                // Try diagnostics endpoint
                const diagResponse = await fetch('/twitter/diagnostics');
                if (diagResponse.ok) {
                    const diagData = await diagResponse.json();
                    console.log('Twitter diagnostics:', diagData);
                    
                    // Check configuration
                    const configOK = diagData.config && 
                        diagData.config.api_key_configured &&
                        diagData.config.api_secret_configured &&
                        diagData.config.access_token_configured;
                        
                    if (configOK) {
                        updateDiagnosticsInfo("✅ Twitter API credentials are configured correctly.");
                    } else {
                        updateDiagnosticsInfo("❌ Twitter API credentials are incomplete or missing.");
                    }
                    
                    // Check directory status
                    if (diagData.status && diagData.status.status_directory_exists) {
                        updateDiagnosticsInfo("✅ Twitter status directory exists.");
                    } else {
                        updateDiagnosticsInfo("❌ Twitter status directory is missing.");
                        
                        // Try directory diagnostics endpoint
                        tryDirectoryDiagnostics();
                    }
                } else {
                    updateDiagnosticsInfo("❌ Diagnostics endpoint is not available.");
                }
            } else {
                // Health check failed
                updateDiagnosticsInfo("❌ Twitter health check failed, routes may not be mounted correctly.");
            }
        } catch (error) {
            console.error('Error fetching diagnostics:', error);
        }
    }
    
    // Try to check directory issues
    async function tryDirectoryDiagnostics() {
        try {
            const dirResponse = await fetch('/twitter/directory');
            if (dirResponse.ok) {
                const dirData = await dirResponse.json();
                console.log('Directory diagnostics:', dirData);
                
                // Display useful directory info
                if (dirData.directory) {
                    const dir = dirData.directory;
                    
                    if (!dir.exists) {
                        updateDiagnosticsInfo(`❌ Status directory doesn't exist: ${dir.path}`);
                    }
                    else if (!dir.accessible) {
                        updateDiagnosticsInfo(`❌ Status directory exists but is not accessible: ${dir.message}`);
                    }
                    
                    if (dir.permissions && dir.permissions.error) {
                        updateDiagnosticsInfo(`ℹ️ Permission info: ${dir.permissions.error}`);
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching directory diagnostics:', error);
        }
    }
    
    // Update the status UI with data
    function updateStatusUI(data) {
        // Clear any error states
        clearErrorState();
        
        if (!statusDisplay || !rateLimitDisplay || !lastOperationDisplay) {
            console.error('Twitter panel elements not found');
            return;
        }
        
        // Update API status
        if (statusDisplay) {
            let statusText = "Unknown";
            let statusClass = "status-unknown";
            
            switch (data.api_status) {
                case "operational":
                    statusText = "Operational ✓";
                    statusClass = "status-ok";
                    break;
                case "rate_limited":
                    statusText = "Rate Limited ⚠";
                    statusClass = "status-warning";
                    break;
                case "error":
                    statusText = "Error ✗";
                    statusClass = "status-error";
                    break;
            }
            
            statusDisplay.textContent = statusText;
            statusDisplay.className = statusClass;
        }
        
        // Update rate limit
        if (rateLimitDisplay) {
            const rateLimit = data.rate_limit;
            let rateText = "Unknown";
            
            if (rateLimit && rateLimit.remaining !== "unknown") {
                rateText = `${rateLimit.remaining} calls remaining`;
                
                // Add reset time if available
                if (rateLimit.reset_time) {
                    const resetTime = new Date(rateLimit.reset_time);
                    const formattedTime = resetTime.toLocaleTimeString();
                    rateText += ` (resets at ${formattedTime})`;
                }
            }
            
            rateLimitDisplay.textContent = rateText;
        }
        
        // Update last operation
        if (lastOperationDisplay && data.last_operation) {
            const operation = data.last_operation;
            let opText = "No recent operations";
            
            if (operation.status !== "none") {
                opText = operation.message || operation.status;
                
                // Add timestamp if available
                if (operation.timestamp) {
                    const opTime = new Date(operation.timestamp);
                    const timeAgo = getTimeAgo(opTime);
                    opText += ` (${timeAgo})`;
                }
            }
            
            lastOperationDisplay.textContent = opText;
        }
        
        // Update thread link if available
        if (threadLinkDisplay) {
            if (data.last_thread) {
                threadLinkDisplay.innerHTML = `<a href="${data.last_thread}" target="_blank">View Last Thread</a>`;
                threadLinkDisplay.style.display = 'block';
            } else {
                threadLinkDisplay.innerHTML = '';
                threadLinkDisplay.style.display = 'none';
            }
        }
    }
    
    // Update loading state
    function updateLoadingState(isLoading) {
        if (panelElement) {
            if (isLoading) {
                panelElement.classList.add('loading');
                if (refreshButton) refreshButton.disabled = true;
            } else {
                panelElement.classList.remove('loading');
                if (refreshButton) refreshButton.disabled = false;
            }
        }
    }
    
    // Update the error state
    function updateErrorState(title, message) {
        if (!panelElement) return;
        
        // Clear existing error
        clearErrorState();
        
        // Create error element
        const errorEl = document.createElement('div');
        errorEl.className = 'twitter-error';
        errorEl.innerHTML = `
            <h4>${title}</h4>
            <p>${message}</p>
        `;
        
        // Add error to panel
        panelElement.querySelector('.twitter-content').appendChild(errorEl);
        
        // Show error state
        panelElement.classList.add('error');
    }
    
    // Add diagnostics info to the panel
    function updateDiagnosticsInfo(message) {
        if (!panelElement) return;
        
        // Get or create diagnostics section
        let diagSection = panelElement.querySelector('.twitter-diagnostics');
        if (!diagSection) {
            diagSection = document.createElement('div');
            diagSection.className = 'twitter-diagnostics';
            diagSection.innerHTML = '<h4>Diagnostics:</h4>';
            panelElement.querySelector('.twitter-content').appendChild(diagSection);
        }
        
        // Add diagnostic message
        const diagLine = document.createElement('p');
        diagLine.innerHTML = message;
        diagSection.appendChild(diagLine);
    }
    
    // Clear the error state
    function clearErrorState() {
        if (!panelElement) return;
        
        // Remove error class
        panelElement.classList.remove('error');
        
        // Remove error and diagnostics elements
        const errorEl = panelElement.querySelector('.twitter-error');
        if (errorEl) errorEl.remove();
        
        const diagEl = panelElement.querySelector('.twitter-diagnostics');
        if (diagEl) diagEl.remove();
    }
    
    // Get relative time string
    function getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        
        if (diffSecs < 60) {
            return 'just now';
        } else if (diffSecs < 3600) {
            const mins = Math.floor(diffSecs / 60);
            return `${mins} minute${mins > 1 ? 's' : ''} ago`;
        } else if (diffSecs < 86400) {
            const hours = Math.floor(diffSecs / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diffSecs / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }
    
    // Stop fetching status
    function destroy() {
        if (fetchInterval) {
            clearInterval(fetchInterval);
            fetchInterval = null;
        }
    }
    
    // Public API
    return {
        init,
        fetchStatus,
        destroy
    };
})();

// Initialize the panel when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    TwitterPanel.init();
});

// Export the module for potential use by other modules
if (typeof module !== 'undefined') {
    module.exports = TwitterPanel;
}

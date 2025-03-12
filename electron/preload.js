const { contextBridge, ipcRenderer } = require('electron');

// Global state
let clientId = null;
let isPolling = false;
let pollInterval = null;
const POLL_FREQUENCY = 500; // Poll every 500ms
let isConnecting = false;
let connectionAttempts = 0;
const MAX_CONNECTION_ATTEMPTS = 20;

// Test if the backend is reachable
async function testBackend() {
    try {
        const response = await fetch('http://127.0.0.1:5000/health');
        if (response.ok) {
            const data = await response.json();
            console.log('Backend health check passed:', data);
            return true;
        }
        console.error('Health check failed:', response.status);
        return false;
    } catch (error) {
        console.error('Backend health check error:', error);
        return false;
    }
}

// Register as a new client
async function registerClient() {
    try {
        const response = await fetch('http://127.0.0.1:5000/register', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            clientId = data.client_id;
            console.log(`Registered with client ID: ${clientId}`);
            return true;
        }
        
        console.error('Failed to register client:', response.status);
        return false;
    } catch (error) {
        console.error('Client registration error:', error);
        return false;
    }
}

// Poll for new messages
async function pollMessages() {
    if (!clientId || isPolling) return;
    
    isPolling = true;
    
    try {
        const response = await fetch('http://127.0.0.1:5000/poll', {
            headers: {
                'X-Client-ID': clientId
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.messages && data.messages.length > 0) {
                // Process each message
                data.messages.forEach(message => {
                    window.postMessage({
                        type: message.type,
                        data: message.data
                    }, '*');
                });
            }
        } else {
            // If client ID becomes invalid, try to register again
            if (response.status === 401) {
                console.warn('Client ID no longer valid. Attempting to reconnect...');
                await connect();
            }
        }
    } catch (error) {
        console.error('Error polling for messages:', error);
        window.postMessage({
            type: 'ws_status',
            data: { 
                status: 'error', 
                message: `Polling error: ${error.message}`
            }
        }, '*');
        
        // Try to reconnect after error
        stopPolling();
        setTimeout(connect, 5000);
    } finally {
        isPolling = false;
    }
}

// Start polling for messages
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollMessages, POLL_FREQUENCY);
    
    console.log('Started polling for messages');
}

// Stop polling for messages
function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    console.log('Stopped polling for messages');
}

// Connect to the backend
async function connect() {
    if (isConnecting) return;
    
    isConnecting = true;
    connectionAttempts++;
    
    try {
        window.postMessage({
            type: 'ws_status',
            data: { status: 'connecting' }
        }, '*');
        
        // Test backend health first
        const isHealthy = await testBackend();
        if (!isHealthy) {
            throw new Error('Backend is not responsive');
        }
        
        // Register as a client
        const registered = await registerClient();
        if (!registered) {
            throw new Error('Failed to register as client');
        }
        
        // Start polling for messages
        startPolling();
        
        console.log('Successfully connected to backend');
        window.postMessage({
            type: 'ws_status',
            data: { status: 'connected' }
        }, '*');
        
        // Reset connection attempts on success
        connectionAttempts = 0;
        return true;
    } catch (error) {
        console.error('Connection failed:', error);
        window.postMessage({
            type: 'ws_status',
            data: { 
                status: 'error', 
                message: `Connection error: ${error.message}`
            }
        }, '*');
        
        // If we've tried too many times, give up
        if (connectionAttempts >= MAX_CONNECTION_ATTEMPTS) {
            console.error('Maximum connection attempts reached. Giving up.');
            return false;
        }
        
        // Otherwise try again after a delay
        setTimeout(connect, 2000);
        return false;
    } finally {
        isConnecting = false;
    }
}

// Disconnect from the backend
function disconnect() {
    stopPolling();
    clientId = null;
    
    window.postMessage({
        type: 'ws_status',
        data: { status: 'disconnected' }
    }, '*');
    
    console.log('Disconnected from backend');
}

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('api', {
    connect: connect,
    disconnect: disconnect,
    
    sendCommand: async (command) => {
        try {
            // Error check for malformed command
            if (!command) {
                console.error('Invalid command object:', command);
                throw new Error('Invalid command object');
            }
            
            // Add default for verbose mode if not provided
            if (command.verbose === undefined || command.verbose === null) {
                command.verbose = false;
            }
            
            // Handle special toggle voice command
            if (command.command === '__toggle_voice__') {
                console.log('Sending voice toggle command with enabled=', command.enabled);
                const response = await fetch('http://127.0.0.1:5000/voice/toggle', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-Client-ID': clientId || 'anonymous'
                    },
                    body: JSON.stringify({ enabled: command.enabled })
                });
                
                if (!response.ok) {
                    throw new Error(`Voice toggle failed with status: ${response.status}`);
                }
                
                return await response.json();
            }
            
            // Regular command handling
            const response = await fetch('http://127.0.0.1:5000/command', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Client-ID': clientId
                },
                body: JSON.stringify(command)
            });
            return await response.json();
        } catch (error) {
            console.error('Error sending command:', error);
            throw error;
        }
    },
    
    checkBackend: testBackend,
    
    reconnect: async () => {
        disconnect();
        return await connect();
    },
    
    testConnection: async () => {
        try {
            const isHealthy = await testBackend();
            if (!isHealthy) {
                return { success: false, error: 'Backend health check failed' };
            }
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },
    
    // NLP Model Management Functions
    getModelInfo: async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/natural_language/model_info', {
                headers: { 'X-Client-ID': clientId || 'anonymous' }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to get model info: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error getting model info:', error);
            throw error;
        }
    },
    
    setModelProvider: async (provider) => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/natural_language/set_provider', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Client-ID': clientId || 'anonymous'
                },
                body: JSON.stringify({ provider: provider })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to set model provider: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error setting model provider:', error);
            throw error;
        }
    },
    
    setModel: async (modelName) => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/natural_language/set_model', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Client-ID': clientId || 'anonymous'
                },
                body: JSON.stringify({ model_name: modelName })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to set model: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error setting model:', error);
            throw error;
        }
    },
    
    nlpHealthCheck: async () => {
        try {
            const response = await fetch('http://127.0.0.1:5000/api/natural_language/health_check', {
                headers: { 'X-Client-ID': clientId || 'anonymous' }
            });
            
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error checking NLP health:', error);
            throw error;
        }
    },
    
    cleanup: disconnect
});

// No need for automatic connection - the renderer will call connect()

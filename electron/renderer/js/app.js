document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const conversationContainer = document.getElementById('conversation');
    const executionLog = document.getElementById('execution-log');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const voiceButton = document.getElementById('voice-button');
    const clearLogButton = document.getElementById('clear-log');
    const verboseModeCheckbox = document.getElementById('verbose-mode');
    const statusMessage = document.getElementById('status-message');
    const connectionStatus = document.getElementById('connection-status');
    const splitter = document.getElementById('splitter');
    const themeToggle = document.getElementById('theme-toggle');
    const developerModeToggle = document.getElementById('developer-mode');
    const toggleSidebarButton = document.getElementById('toggle-sidebar');
    const settingsButton = document.getElementById('settings-button');
    const settingsMenu = document.getElementById('settings-menu');
    const nlpModelProvider = document.getElementById('nlp-model-provider');
    const nlpModelSelector = document.getElementById('nlp-model-selector');
    const modelStatus = document.getElementById('model-status');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

    // Add error handlers for missing elements
    function addToExecutionLog(message, level = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        
        // Create the log entry element
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level}`;
        logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;
        
        // Try to append to executionLog if it exists
        if (executionLog) {
            executionLog.appendChild(logEntry);
            executionLog.scrollTop = executionLog.scrollHeight;
        } else {
            // Fallback to console if element not found
            console.log(`${timestamp} - ${level}: ${message}`);
        }
    }

    // Auto-resize textarea input
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            // Reset height to auto to properly calculate new height
            this.style.height = 'auto';
            // Set new height based on content (with max-height handled by CSS)
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // NLP Model Management
    // Function to update model status display
    function updateModelStatus(message, type = 'info') {
        if (!modelStatus) return;
        
        modelStatus.textContent = message;
        modelStatus.className = `model-status ${type}`;
    }
    
    // Function to populate the model selector based on the selected provider
    async function populateModelSelector(provider) {
        if (!nlpModelSelector) return;
        
        // Clear existing options
        nlpModelSelector.innerHTML = '';
        updateModelStatus('Loading models...', 'loading');
        
        try {
            // Get model info from the backend
            const response = await window.api.getModelInfo();
            
            if (response.status === 'success' && response.data) {
                const modelInfo = response.data;
                
                // Make sure we're showing the correct provider
                if (modelInfo.provider !== provider) {
                    // Update provider if it's different in the backend
                    if (nlpModelProvider) {
                        nlpModelProvider.value = modelInfo.provider;
                    }
                }
                
                // Populate the model selector with available models
                if (modelInfo.available_models && modelInfo.available_models.length > 0) {
                    modelInfo.available_models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        
                        // Select the current model
                        if (model === modelInfo.current_model) {
                            option.selected = true;
                        }
                        
                        nlpModelSelector.appendChild(option);
                    });
                    
                    updateModelStatus(`Using ${modelInfo.current_model}`, 'success');
                    // Log to execution log
                    addToExecutionLog(`NLP model info retrieved: ${modelInfo.provider} - ${modelInfo.current_model}`, 'info');
                } else {
                    // No models available
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = 'No models available';
                    nlpModelSelector.appendChild(option);
                    
                    updateModelStatus('No models available', 'error');
                }
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error fetching model info:', error);
            updateModelStatus(`Error: ${error.message}`, 'error');
            
            // Add a fallback option
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Failed to load models';
            nlpModelSelector.appendChild(option);
            
            // Log to execution log
            addToExecutionLog(`Error fetching NLP model info: ${error.message}`, 'error');
        }
    }
    
    // Initialize model selector on page load
    if (nlpModelProvider) {
        // Load saved provider preference from localStorage or use default from the UI
        const savedProvider = localStorage.getItem('nlpModelProvider') || nlpModelProvider.value;
        
        // Update the provider dropdown
        nlpModelProvider.value = savedProvider;
        
        // Initial population of the model selector
        populateModelSelector(savedProvider);
        
        // Set up event listener for provider changes
        nlpModelProvider.addEventListener('change', async function() {
            const selectedProvider = this.value;
            localStorage.setItem('nlpModelProvider', selectedProvider);
            
            // Show loading state
            updateModelStatus('Switching provider...', 'loading');
            
            try {
                // Send the model provider selection to the backend
                const result = await window.api.setModelProvider(selectedProvider);
                
                if (result.status === 'success') {
                    // Refresh the model selector with models for the new provider
                    populateModelSelector(selectedProvider);
                    addToExecutionLog(`NLP provider changed to: ${selectedProvider}`, 'info');
                } else {
                    throw new Error(result.message || 'Failed to change provider');
                }
            } catch (error) {
                console.error('Error changing model provider:', error);
                updateModelStatus(`Error: ${error.message}`, 'error');
                addToExecutionLog(`Error changing NLP provider: ${error.message}`, 'error');
                
                // Revert the UI selection
                const currentProvider = await getCurrentProvider();
                if (currentProvider) {
                    nlpModelProvider.value = currentProvider;
                }
            }
        });
    }
    
    // Set up event listener for specific model changes
    if (nlpModelSelector) {
        nlpModelSelector.addEventListener('change', async function() {
            const selectedModel = this.value;
            if (!selectedModel) return; // Skip empty selections
            
            updateModelStatus('Switching model...', 'loading');
            
            try {
                // Send the model selection to the backend
                const result = await window.api.setModel(selectedModel);
                
                if (result.status === 'success') {
                    updateModelStatus(`Using ${selectedModel}`, 'success');
                    addToExecutionLog(`NLP model changed to: ${selectedModel}`, 'info');
                    
                    // Store in localStorage
                    localStorage.setItem('nlpModel', selectedModel);
                } else {
                    throw new Error(result.message || 'Failed to change model');
                }
            } catch (error) {
                console.error('Error changing model:', error);
                updateModelStatus(`Error: ${error.message}`, 'error');
                addToExecutionLog(`Error changing NLP model: ${error.message}`, 'error');
                
                // Refresh the selector to show the actual current model
                const provider = nlpModelProvider ? nlpModelProvider.value : await getCurrentProvider();
                if (provider) {
                    populateModelSelector(provider);
                }
            }
        });
    }
    
    // Helper function to get the current provider from backend
    async function getCurrentProvider() {
        try {
            const response = await window.api.getModelInfo();
            if (response.status === 'success' && response.data) {
                return response.data.provider;
            }
        } catch (error) {
            console.error('Error getting current provider:', error);
        }
        return null;
    }

    // Settings dropdown toggle
    if (settingsButton && settingsMenu) {
        settingsButton.addEventListener('click', (e) => {
            e.stopPropagation();
            settingsMenu.classList.toggle('active');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!settingsMenu.contains(e.target) && e.target !== settingsButton) {
                settingsMenu.classList.remove('active');
            }
        });
    }

    // Developer mode toggle
    if (developerModeToggle) {
        // Load developer mode state from localStorage or default to false
        const isDeveloperMode = localStorage.getItem('developerMode') === 'true';
        developerModeToggle.checked = isDeveloperMode;
        
        // Apply saved state on load
        if (isDeveloperMode) {
            document.body.classList.add('developer-mode');
        } else {
            document.body.classList.remove('developer-mode');
        }
        
        developerModeToggle.addEventListener('change', () => {
            if (developerModeToggle.checked) {
                document.body.classList.add('developer-mode');
                localStorage.setItem('developerMode', 'true');
            } else {
                document.body.classList.remove('developer-mode');
                localStorage.setItem('developerMode', 'false');
            }
        });
    }

    // Toggle sidebar button
    if (toggleSidebarButton) {
        toggleSidebarButton.addEventListener('click', () => {
            document.body.classList.toggle('developer-mode');
            
            // Update the checkbox state to match the body class
            if (developerModeToggle) {
                developerModeToggle.checked = document.body.classList.contains('developer-mode');
                // Save state to localStorage
                localStorage.setItem('developerMode', developerModeToggle.checked);
            }
        });
    }

    // Check for any missing critical elements and create safe fallbacks
    if (!splitter) {
        console.warn("Splitter element not found, creating one dynamically");
        
        // Create and insert a splitter element
        const newSplitter = document.createElement('div');
        newSplitter.id = 'splitter';
        newSplitter.className = 'splitter';
        
        const container = document.querySelector('.app-container');
        const rightPane = document.querySelector('.right-pane');
        
        if (container && rightPane) {
            container.insertBefore(newSplitter, rightPane);
            // Re-assign the splitter variable
            splitter = newSplitter;
        }
    }
    
    // Initialize splitter functionality with safety checks
    if (splitter) {
        let isResizing = false;
        let lastDownX = 0;
        
        splitter.addEventListener('mousedown', (e) => {
            isResizing = true;
            lastDownX = e.clientX;
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const leftPane = document.querySelector('.left-pane');
            const container = document.querySelector('.app-container');
            
            if (leftPane && container) {
                const containerWidth = container.offsetWidth;
                const newLeftWidth = (e.clientX * 100) / containerWidth;
                
                // Constrain within reasonable limits (20% to 80%)
                const constrainedWidth = Math.max(20, Math.min(80, newLeftWidth));
                leftPane.style.flex = `0 0 ${constrainedWidth}%`;
            }
        });
        
        document.addEventListener('mouseup', () => {
            isResizing = false;
            document.body.style.userSelect = '';
        });
    } else {
        console.error("Could not initialize splitter functionality");
    }

    const requiredElements = {
        'conversation': conversationContainer,
        'message-input': messageInput,
        'send-button': sendButton,
        'voice-button': voiceButton,
        'clear-log': clearLogButton,
        'status-message': statusMessage,
        'connection-status': connectionStatus,
        'splitter': splitter,
        'theme-toggle': themeToggle
    };

    for (const [id, element] of Object.entries(requiredElements)) {
        if (!element) {
            console.error(`Required element #${id} not found in the DOM`);
        }
    }

    // Theme toggle functionality
    if (themeToggle) {
        // Load theme from localStorage or default to system preference
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const isDark = savedTheme ? savedTheme === 'dark' : prefersDark;
        
        // Update toggle state
        themeToggle.checked = isDark;
        
        // Apply theme immediately
        setTheme(isDark);
        
        // Listen for changes
        themeToggle.addEventListener('change', function() {
            const isDark = this.checked;
            setTheme(isDark);
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }

    let connectionRetries = 0;
    const MAX_CONNECTION_RETRIES = 5;

    // Track microphone state
    let micActive = false;

    // Initialize connection to backend
    async function initializeConnection() {
        console.log('Initializing connection to backend...');
        addToExecutionLog('Connecting to backend...', 'info');
        
        try {
            // First check if backend is healthy
            updateConnectionStatus('connecting');
            
            const connected = await window.api.connect();
            
            if (connected) {
                updateConnectionStatus('connected');
                addToExecutionLog('Connected to backend successfully', 'info');
                connectionRetries = 0; // Reset retry count on success
            } else {
                throw new Error('Connection failed');
            }
        } catch (error) {
            console.error('Connection error:', error);
            updateConnectionStatus('disconnected');
            addToExecutionLog(`Failed to connect: ${error.message}`, 'error');
            
            // Auto-retry logic with increasing delays
            if (connectionRetries < MAX_CONNECTION_RETRIES) {
                connectionRetries++;
                const delay = connectionRetries * 2000; // Increasing delay
                
                addToExecutionLog(`Retrying in ${delay/1000} seconds...`, 'info');
                setTimeout(initializeConnection, delay);
            } else {
                // Show manual retry button after max auto retries
                showRetryButton();
            }
        }
    }
    
    // Show retry button for manual reconnection
    function showRetryButton() {
        // Remove any existing retry buttons
        const existingButton = document.querySelector('.retry-button');
        if (existingButton) {
            existingButton.remove();
        }
        
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry Connection';
        retryButton.className = 'retry-button';
        retryButton.style = 'padding: 10px; background: var(--primary); color: white; border: none; border-radius: 8px; margin: 20px auto; display: block; cursor: pointer;';
        
        retryButton.onclick = () => {
            retryButton.textContent = 'Connecting...';
            retryButton.disabled = true;
            connectionRetries = 0; // Reset retry count
            initializeConnection().finally(() => {
                // If still present, remove
                if (retryButton.parentNode) {
                    retryButton.remove();
                }
            });
        };
        
        conversationContainer.appendChild(retryButton);
    }

    // Enhanced connection status update
    function updateConnectionStatus(status) {
        connectionStatus.className = `status-indicator ${status}`;
        
        let statusText;
        switch (status) {
            case 'connecting':
                statusText = 'Connecting to backend...';
                break;
            case 'connected':
                statusText = 'Connected to AgentOS backend';
                break;
            case 'disconnected':
                statusText = 'Disconnected from backend';
                break;
            case 'error':
                statusText = 'Connection error';
                break;
            default:
                statusText = 'Unknown status';
        }
        
        statusMessage.textContent = statusText;
        document.body.classList.toggle('disconnected', status !== 'connected');
    }
    
    // Remove the debug button event handler
    // document.getElementById('debug-connection').addEventListener('click', async function() {
    //     try {
    //         addToExecutionLog('Testing connection...', 'info');
    //         const result = await window.api.testConnection();
    //         
    //         if (result.success) {
    //             addToExecutionLog('Connection test successful!', 'info');
    //         } else {
    //             addToExecutionLog(`Connection test failed: ${result.error}`, 'error');
    //         }
    //     } catch (error) {
    //         addToExecutionLog(`Connection test error: ${error.message}`, 'error');
    //     }
    // });

    // Start initial connection
    initializeConnection();

    // Enhanced WebSocket message handling
    window.addEventListener('message', (event) => {
        if (event.source === window) {
            const { type, data } = event.data;
            
            switch (type) {
                case 'ws_status':
                    updateConnectionStatus(data.status);
                    if (data.message) {
                        addToExecutionLog(data.message, data.status === 'error' ? 'error' : 'info');
                    }
                    break;
                    
                case 'execution_log':
                    addToExecutionLog(data.message, data.level || 'info');
                    break;
                    
                case 'conversation_message':
                    addToConversation(data.message, data.message_type);
                    break;
            }
        }
    });

    // Add a function to handle streaming updates from agents
    async function fetchStreamingUpdates() {
        try {
            const response = await fetch('http://127.0.0.1:5000/stream_updates');
            if (response.ok) {
                const data = await response.json();
                
                // Process any messages
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(message => {
                        // Handle progress messages from Twitter agent
                        if (message.agent === "twitter_bot" && message.status === "progress") {
                            // Update any existing processing message with the progress update
                            const processingMsg = document.querySelector('.processing-message');
                            if (processingMsg) {
                                processingMsg.innerHTML = `<div class="message-content">${message.message}</div>`;
                            } else {
                                // Or add as a new system message if no processing message exists
                                addToConversation(message.message, 'system');
                            }
                            
                            // Log to execution log as well
                            addToExecutionLog(`Twitter progress: ${message.message}`, 'info');
                            
                            // If there's a thread URL, display it prominently
                            if (message.thread_url) {
                                const threadMsg = document.createElement('div');
                                threadMsg.className = 'message system-message twitter-thread-message';
                                threadMsg.innerHTML = `
                                    <div class="message-content">
                                        <strong>Twitter Thread Posted!</strong><br>
                                        <a href="${message.thread_url}" target="_blank" rel="noopener noreferrer">
                                            ${message.thread_url}
                                        </a>
                                    </div>
                                `;
                                conversationContainer.appendChild(threadMsg);
                                conversationContainer.scrollTop = conversationContainer.scrollHeight;
                            }
                        }
                        
                        // Handle progress messages from Autoblog agent
                        if (message.agent === "autoblog" && message.status === "progress") {
                            // Update any existing processing message with the progress update
                            const processingMsg = document.querySelector('.processing-message');
                            if (processingMsg) {
                                processingMsg.innerHTML = `<div class="message-content">${message.message}</div>`;
                            } else {
                                // Or add as a new system message if no processing message exists
                                addToConversation(message.message, 'system');
                            }
                            
                            // Log to execution log as well
                            addToExecutionLog(`Autoblog progress: ${message.message}`, 'info');
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error fetching streaming updates:', error);
        }
        
        // Schedule next update
        setTimeout(fetchStreamingUpdates, 1000);
    }

    // Initialize streaming updates when the app starts
    setTimeout(() => {
        fetchStreamingUpdates();
    }, 2000);

    // Send message function
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Disable input while processing
        messageInput.value = '';
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Display the message in the conversation
        addToConversation(message, 'user');
        
        // Add a "processing" message that we'll replace later
        const processingMsgEl = document.createElement('div');
        processingMsgEl.className = 'message system-message processing-message';
        processingMsgEl.innerHTML = '<div class="typing-indicator">Processing...</div>';
        conversationContainer.appendChild(processingMsgEl);
        conversationContainer.scrollTop = conversationContainer.scrollHeight;
        
        // Safety check for the verboseMode
        const verboseMode = verboseModeCheckbox ? verboseModeCheckbox.checked : false;
        
        // Send to backend without any timeout to allow long-running operations
        window.api.sendCommand({
            command: message,
            verbose: verboseMode
        })
        .then(response => {
            // Replace processing message with the response
            if (processingMsgEl.parentNode) {
                processingMsgEl.remove();
            }
            
            // Special handling for Twitter responses with thread URLs
            if (response.agent === 'twitter_bot' && response.thread_url) {
                addToConversation(`<strong>Success!</strong> ${response.spoke || response.message}`, 'assistant');
                
                // Add a special message for the thread URL
                const threadMsg = document.createElement('div');
                threadMsg.className = 'message system-message twitter-thread-message';
                threadMsg.innerHTML = `
                    <div class="message-content">
                        <strong>Twitter Thread Posted!</strong><br>
                        <a href="${response.thread_url}" target="_blank" rel="noopener noreferrer">
                            ${response.thread_url}
                        </a>
                    </div>
                `;
                conversationContainer.appendChild(threadMsg);
            } 
            // Special handling for Autoblog responses
            else if (response.agent === 'autoblog') {
                const resultMsg = response.spoke || response.message;
                
                // Show success message with appropriate styling
                if (response.status === 'success') {
                    addToConversation(`<strong>Success!</strong> ${resultMsg}`, 'assistant');
                } else {
                    addToConversation(resultMsg, 'assistant');
                }
                
                // If there's additional information to display, add it
                if (response.blog_post_url) {
                    const blogPostMsg = document.createElement('div');
                    blogPostMsg.className = 'message system-message blog-post-message';
                    blogPostMsg.innerHTML = `
                        <div class="message-content">
                            <strong>Blog Post Created!</strong><br>
                            <a href="${response.blog_post_url}" target="_blank" rel="noopener noreferrer">
                                ${response.blog_post_url}
                            </a>
                        </div>
                    `;
                    conversationContainer.appendChild(blogPostMsg);
                }
            }
            else {
                // Default response handling
                addToConversation(response.spoke || response.message, 'assistant');
            }
        })
        .catch(error => {
            // Remove processing message
            if (processingMsgEl.parentNode) {
                processingMsgEl.remove();
            }
            
            // Display error
            addToConversation(`Error: ${error.message || 'Unknown error occurred'}`, 'system');
            addToExecutionLog(`Error processing command: ${error.message || 'Unknown error'}`, 'error');
        })
        .finally(() => {
            // Re-enable input
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        });
    }

    // Update voice button to show toggle state
    function updateVoiceButtonState() {
        if (!voiceButton) return;
        
        if (micActive) {
            voiceButton.classList.add('active');
            voiceButton.setAttribute('title', 'Turn off microphone');
            voiceButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>`;
            
            messageInput.disabled = true;
            messageInput.placeholder = "Microphone active - listening...";
        } else {
            voiceButton.classList.remove('active', 'pulsing');
            voiceButton.setAttribute('title', 'Turn on microphone');
            voiceButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>`;
            
            messageInput.disabled = false;
            messageInput.placeholder = "Type a command...";
        }
    }

    // Toggle microphone function with improved state handling
    async function toggleMicrophone() {
        if (micActive) {
            // Turn off microphone
            micActive = false;
            updateVoiceButtonState();
            
            try {
                // First update UI state
                voiceButton.classList.remove('pulsing');
                messageInput.disabled = false;
                messageInput.placeholder = "Type a command...";
                messageInput.focus();
                
                // Then tell backend
                await window.api.sendCommand({
                    command: '__toggle_voice__',
                    enabled: false
                });
                addToExecutionLog('Voice input deactivated');
            } catch (error) {
                addToExecutionLog(`Error deactivating voice: ${error.message}`, 'error');
            }
        } else {
            // Turn on microphone
            micActive = true;
            updateVoiceButtonState();
            
            try {
                // Update UI first
                messageInput.disabled = true;
                messageInput.placeholder = "Listening for voice commands...";
                voiceButton.classList.add('pulsing');
                
                // Add listening message to conversation
                addToConversation('Listening for commands...', 'system');
                addToExecutionLog('Voice input activated');
                
                // Send command to backend to start listening
                await window.api.sendCommand({
                    command: '__toggle_voice__',
                    enabled: true
                });
            } catch (error) {
                // Revert UI changes if there's an error
                micActive = false;
                updateVoiceButtonState();
                messageInput.disabled = false;
                messageInput.placeholder = "Type a command...";
                voiceButton.classList.remove('pulsing');
                
                addToExecutionLog(`Error activating voice: ${error.message}`, 'error');
                addToConversation(`Sorry, I couldn't activate the microphone: ${error.message}`, 'system');
            }
        }
    }

    // Update the voice button click handler
    voiceButton.addEventListener('click', toggleMicrophone);

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Remove this duplicate handler
    // voiceButton.addEventListener('click', () => {
    //     addToConversation('Listening...', 'system');
    //     addToExecutionLog('Voice input activated');
    //     
    //     window.api.sendCommand({
    //         command: '__voice_input__',
    //         verbose: verboseModeCheckbox.checked
    //     });
    // });
    
    // Enhance clear log button with confirmation
    clearLogButton.addEventListener('click', () => {
        // Add a small animation effect
        clearLogButton.classList.add('clicked');
        setTimeout(() => clearLogButton.classList.remove('clicked'), 300);
        
        executionLog.innerHTML = '';
        addToExecutionLog('Log cleared', 'info');
    });

    // Helper functions for adding messages
    function addToConversation(message, messageType) {
        // Remove any existing processing messages when adding new assistant messages
        if (messageType === 'assistant') {
            const processingMsgs = document.querySelectorAll('.processing-message');
            processingMsgs.forEach(el => el.remove());
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${messageType}-message`;
        
        // Add typing animation for assistant messages
        if (messageType === 'assistant') {
            messageElement.innerHTML = `<div class="typing-indicator">●●●</div>`;
            
            // Format tweet output with nicer styling 
            if (message.includes('Tweet') && message.includes('Successfully')) {
                setTimeout(() => {
                    // Format tweets with nice styling
                    const formattedMessage = message.replace(
                        /📌 Tweet (\d+):([\s\S]*?)(?=\n📌 Tweet \d+:|\n\nTo post these tweets|$)/g, 
                        '<div class="tweet-preview"><div class="tweet-header">📌 Tweet $1:</div><div class="tweet-content">$2</div></div>'
                    );
                    
                    messageElement.innerHTML = formattedMessage;
                }, 500);
            } 
            // Format error messages with styling (looking for emoji indicators and bold markdown)
            else if (message.includes('❌') || message.includes('⚠️') || message.includes('🕒') || message.includes('**')) {
                setTimeout(() => {
                    // Format bold text with markdown-like syntax
                    let formattedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    
                    // Highlight suggested actions
                    if (formattedMessage.includes('suggestion:') || formattedMessage.includes('Suggestion:')) {
                        formattedMessage = formattedMessage.replace(
                            /(Suggestion:|suggestion:)(.*?)($|\n)/g, 
                            '<div class="suggestion-box"><span class="suggestion-label">💡 Suggestion:</span>$2</div>'
                        );
                    }
                    
                    messageElement.innerHTML = formattedMessage;
                    messageElement.classList.add('error-message');
                }, 500);
            }
            else {
                setTimeout(() => {
                    messageElement.textContent = message;
                }, 500);
            }
        } else {
            messageElement.textContent = message;
        }
        
        conversationContainer.appendChild(messageElement);
        conversationContainer.scrollTop = conversationContainer.scrollHeight;
        
        // Call this at the end
        setTimeout(autoResizeTextarea, 0);
    }

    // Initialize splitter functionality
    let isResizing = false;
    let lastDownX = 0;
    
    splitter.addEventListener('mousedown', (e) => {
        isResizing = true;
        lastDownX = e.clientX;
        document.body.style.userSelect = 'none';
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const leftPane = document.querySelector('.left-pane');
        const container = document.querySelector('.app-container');
        const containerWidth = container.offsetWidth;
        
        const newLeftWidth = (e.clientX * 100) / containerWidth;
        leftPane.style.flex = `0 0 ${newLeftWidth}%`;
    });
    
    document.addEventListener('mouseup', () => {
        isResizing = false;
        document.body.style.userSelect = '';
    });

    function addToExecutionLog(message, level = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${level}`;
        logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;
        executionLog.appendChild(logEntry);
        executionLog.scrollTop = executionLog.scrollHeight;
    }

    // Theme handling - Fixed implementation
    function setTheme(isDark) {
        // Set body class
        document.body.classList.toggle('light-theme', !isDark);
        
        // Store preference
        localStorage.setItem('darkMode', isDark.toString());
        
        // Update button state
        themeToggle.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
        
        // Log theme change for debugging
        console.log('Theme changed:', isDark ? 'dark' : 'light');
    }

    // Initialize theme with proper boolean conversion
    const savedTheme = localStorage.getItem('darkMode');
    const initialTheme = savedTheme !== null ? savedTheme === 'true' : prefersDark.matches;
    setTheme(initialTheme);

    // Theme toggle with proper event handling
    themeToggle.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent any default button behavior
        const isDark = !document.body.classList.contains('light-theme');
        setTheme(!isDark);
        
        // Add rotation animation
        themeToggle.style.transition = 'transform 0.3s ease';
        themeToggle.style.transform = 'rotate(360deg)';
        
        // Reset transform after animation
        setTimeout(() => {
            themeToggle.style.transition = '';
            themeToggle.style.transform = '';
        }, 300);
    });

    // System theme changes
    prefersDark.addEventListener('change', (e) => {
        if (localStorage.getItem('darkMode') === null) {
            // Only follow system if user hasn't set a preference
            setTheme(e.matches);
        }
    });

    // Initial message
    addToConversation('Welcome to AgentOS! How can I help you today?', 'assistant');
    addToExecutionLog('AgentOS initialized and ready');

    // Cleanup on window unload
    window.addEventListener('beforeunload', () => {
        window.api.disconnect();
    });

    // Add CSS for the active mic button
    const style = document.createElement('style');
    style.textContent = `
        #voice-button.active {
            background-color: var(--primary);
            color: white;
            animation: pulse 2s infinite;
        }
        #voice-button.processing {
            opacity: 0.7;
            pointer-events: none;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        #message-input:disabled {
            background-color: rgba(var(--card-rgb), 0.5);
            color: var(--light-text);
        }
        /* Add animation for clicked state */
        .action-button.clicked {
            animation: buttonClick 0.3s ease;
        }
        @keyframes buttonClick {
            0% { transform: scale(1); }
            50% { transform: scale(0.95); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);

    // Add CSS for tweet styling
    const tweetStyle = document.createElement('style');
    tweetStyle.textContent = `
        .tweet-preview {
            background: rgba(29, 161, 242, 0.1);
            border-left: 3px solid #1da1f2;
            padding: 8px 12px;
            margin: 8px 0;
            border-radius: 4px;
        }
        .tweet-header {
            font-weight: bold;
            margin-bottom: 4px;
            color: var(--primary);
        }
        .tweet-content {
            white-space: pre-wrap;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
    `;
    document.head.appendChild(tweetStyle);

    // Initialize with mic off
    updateVoiceButtonState();

    // Also add a diagnostics function
    async function runSystemDiagnostics() {
        addToExecutionLog('Running system diagnostics...', 'info');
        
        try {
            // Check backend connectivity
            const healthCheck = await fetch('http://127.0.0.1:5000/health')
                .then(res => res.json())
                .catch(() => ({ status: 'error' }));
                
            addToExecutionLog(`Health check: ${healthCheck.status === 'ok' ? 'OK' : 'Failed'}`, 
                healthCheck.status === 'ok' ? 'info' : 'error');
                
            // Check component status
            const componentStatus = await fetch('http://127.0.0.1:5000/debug/status')
                .then(res => res.json())
                .catch(() => ({ status: 'error' }));
                
            addToExecutionLog(`Component status:`, 'info');
            for (const [component, status] of Object.entries(componentStatus)) {
                if (typeof status === 'boolean') {
                    addToExecutionLog(`- ${component}: ${status ? 'OK' : 'Failed'}`, 
                        status ? 'info' : 'warning');
                } else if (component === 'agents_loaded') {
                    addToExecutionLog(`- Agents loaded: ${status.join(', ') || 'None'}`, 
                        status.length > 0 ? 'info' : 'warning');
                }
            }
            
            return componentStatus;
        } catch (error) {
            addToExecutionLog(`Diagnostics error: ${error}`, 'error');
            return null;
        }
    }

    // Call diagnostics on startup
    setTimeout(() => {
        runSystemDiagnostics().then(status => {
            if (status && (!status.agent_router || status.agents_loaded.length === 0)) {
                addToConversation('System initialization incomplete. Some features may not work properly.', 'system');
            }
        });
    }, 2000);

    // Auto-expand textarea when needed
    function autoResizeTextarea() {
        if (messageInput) {
            messageInput.style.height = 'auto';
            messageInput.style.height = (messageInput.scrollHeight) + 'px';
        }
    }

    // Clear the input field and reset its height
    function clearInput() {
        if (messageInput) {
            messageInput.value = '';
            messageInput.style.height = 'auto';
        }
    }

    // Enhanced send message function to handle Enter key properly
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            // Allow Shift+Enter for new line
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }

            // Escape key to clear input
            if (e.key === 'Escape') {
                clearInput();
            }
        });
    }
});

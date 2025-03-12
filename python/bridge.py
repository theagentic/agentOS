"""
Bridge module for Electron-Python communication.
Exposes AgentOS functionality through a Flask API and WebSockets.
"""

import sys
import os
import argparse
import logging
import threading
import time
import traceback
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from datetime import datetime
import uuid
from typing import Dict, List, Any
import inspect

# Configure basic logging first thing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("bridge")

# Add project root to path to make imports work first
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
logger.info(f"Added {project_root} to sys.path")

# Now we can import our module
from core.message_queue import MessageQueue

# Add more verbose error logging for initial startup
logger.info("Starting AgentOS bridge...")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Python path: {sys.path}")

# Try to import Twitter routes if available
try:
    from agents.twitter_bot.routes import get_twitter_routes
    twitter_routes = get_twitter_routes()
    HAS_TWITTER_ROUTES = True
    logger.info(f"Loaded {len(twitter_routes)} Twitter routes")
except ImportError:
    logger.warning("Twitter routes not available")
    twitter_routes = []
    HAS_TWITTER_ROUTES = False

# Try to import NLP routes if available
try:
    from api.routes.nlp_routes import nlp_routes
    HAS_NLP_ROUTES = True
    logger.info("Loaded NLP routes blueprint")
except ImportError:
    logger.warning("NLP routes not available")
    HAS_NLP_ROUTES = False

# ...rest of the imports...

def initialize_server():
    """Initialize Flask server with proper production settings."""
    app = Flask(__name__)
    app.config.update(
        ENV='production',
        DEBUG=False,
        PROPAGATE_EXCEPTIONS=True,
        # Add these lines:
        SERVER_NAME=None,  # Don't set a specific server name
        APPLICATION_ROOT='/',
    )
    
    # Initialize CORS with explicit options
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "allow_headers": ["Content-Type"],
            "methods": ["GET", "POST", "OPTIONS"]
        }
    })
    
    # Configure Socket.IO
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=False,
        engineio_logger=False,
        ping_timeout=60
    )
    
    return app, socketio

# Create Flask app and Socket.IO instance
app, socketio = initialize_server()
server_ready = False

# Mount Twitter routes immediately after creating the Flask app
# This ensures they're registered before any requests come in
if HAS_TWITTER_ROUTES:
    logger.info("Mounting Twitter routes early in initialization...")
    try:
        for route_path, view_func, methods in twitter_routes:
            app.add_url_rule(route_path, view_func.__name__, view_func, methods=methods)
            logger.info(f"Added Twitter route: {route_path} -> {view_func.__name__}")
        
        # Debug log available routes
        logger.info(f"Available routes after early mounting: {[rule.rule for rule in app.url_map.iter_rules()]}")
    except Exception as e:
        logger.error(f"Error mounting Twitter routes early: {e}")
        HAS_TWITTER_ROUTES = False

# Replace before_first_request with a startup handler
@app.before_request
def check_server_ready():
    global server_ready
    if not server_ready:
        logger.info("First request received - server is ready")
        server_ready = True

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Add WebSocket connection handlers
@socketio.on('connect')
def handle_connect():
    print("WEBSOCKET CONNECTION ESTABLISHED")
    logger.warning("WEBSOCKET CONNECTION ESTABLISHED")
    logger.info("Client connected")
    socketio.emit('execution_log', {
        'message': 'Connected to AgentOS backend',
        'level': 'info'
    })

@socketio.on('disconnect')
def handle_disconnect():
    print("WEBSOCKET CONNECTION CLOSED")
    logger.warning("WEBSOCKET CONNECTION CLOSED")
    logger.info("Client disconnected")

@socketio.on('ping_test')
def handle_ping(data):
    print(f"PING received with data: {data}")
    logger.warning(f"PING received with data: {data}")
    return {'response': 'pong', 'received': data}

@socketio.on('process_command')
def handle_command(data):
    """Process commands from frontend."""
    print(f"COMMAND received: {data}")
    logger.warning(f"COMMAND received: {data}")
    
    try:
        if data.get('command') == '__voice_input__':
            # Handle voice command activation properly
            if process_logger:
                process_logger.log_execution("Voice command activated")
                process_logger.log_conversation("Listening...", "system")
            
            # Initialize a temporary voice processor for this one-time command
            try:
                from core.voice_processor import VoiceProcessor
                
                def voice_command_callback(text):
                    try:
                        if not text:
                            return

                        # Log that we received voice input
                        if process_logger:
                            process_logger.log_execution(f"Voice command received: {text}")
                            # User message already logged by listen_once

                        # Process command through the agent router
                        if agent_router:
                            result = agent_router.process_command(text, verbose=data.get('verbose', False))
                            
                            # Handle the response to display in UI
                            if process_logger and result:
                                # Convert result to string if needed
                                response_text = result.get('spoke', result.get('message', str(result)))
                                process_logger.log_conversation(response_text, "assistant")
                                
                                # Speak response if TTS is available
                                if tts_engine and 'spoke' in result:
                                    tts_engine.speak(result['spoke'])
                        else:
                            if process_logger:
                                process_logger.log_execution("Agent router not available for voice command", level="error")
                                process_logger.log_conversation("Sorry, I'm not fully initialized yet.", "system")
                    except Exception as e:
                        logger.error(f"Error processing voice command: {e}")
                        if process_logger:
                            process_logger.log_execution(f"Error processing voice command: {e}", level="error")
                            process_logger.log_conversation("Sorry, there was an error processing your command.", "system")

                # Set the callback for this voice session
                temp_voice_processor = VoiceProcessor(
                    wake_word=None, 
                    callback=voice_command_callback,
                    process_logger=process_logger
                )
                
                # Try to initialize the voice processor first
                if not temp_voice_processor.initialize():
                    if process_logger:
                        process_logger.log_execution("Failed to initialize voice processor", level="error")
                        process_logger.log_conversation("Sorry, I couldn't access the microphone. Please check your microphone settings.", "system")
                    return {'status': 'error', 'message': 'Failed to initialize voice processor'}
                
                # Start listening in a dedicated thread
                threading.Thread(target=temp_voice_processor.listen_once, daemon=True).start()
                
                return {'status': 'ok', 'message': 'Voice command activated'}
            
            except Exception as e:
                logger.error(f"Error setting up voice processor: {e}")
                if process_logger:
                    process_logger.log_execution(f"Error setting up voice processor: {e}", level="error")
                    process_logger.log_conversation("Sorry, there was an error activating voice recognition.", "system")
                return {'status': 'error', 'message': f'Error activating voice: {str(e)}'}
        else:
            # Normal text command
            command = data.get('command', '')
            verbose = data.get('verbose', False)
            
            # Log the command
            if process_logger:
                process_logger.log_execution(f"Processing command: {command}")
                process_logger.log_conversation(command, "user")
            
            # Process the command with the agent router
            if agent_router:
                result = agent_router.process_command(command, verbose=verbose)
                
                # Log and return the result
                if process_logger and result:
                    spoke_text = result.get('spoke', result.get('message', str(result)))
                    process_logger.log_conversation(spoke_text, "assistant")
                    
                    # Speak response if TTS is available
                    if tts_engine and 'spoke' in result:
                        tts_engine.speak(result['spoke'])
                
                return {'status': 'ok', 'message': 'Command processed', 'result': result}
            else:
                return {
                    'status': 'error', 
                    'message': 'Agent router not initialized',
                    'spoke': "I'm still initializing. Please try again in a moment."
                }
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}")
        return {'status': 'error', 'message': str(e)}

# Simple health check endpoint that doesn't require other imports
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Add these lines for better debugging
    print("HEALTH CHECK RECEIVED - Responding with OK")  # Direct console output
    logger.warning("HEALTH CHECK RECEIVED - Responding with OK")
    
    return jsonify({
        "status": "ok",
        "message": "Bridge is running",
        "time": str(datetime.now())
    }), 200  # Explicitly return 200 status code

# Attempt to import AgentOS modules
logger.info("Importing AgentOS modules...")
try:
    # Try to import each module separately to identify which one fails
    logger.info("Importing config...")
    import config
    
    logger.info("Importing core modules...")
    from core.agent_router import AgentRouter
    from core.tts_engine import TTSEngine
    from core.voice_processor import VoiceProcessor
    
    logger.info("Importing process logger...")
    from utils.process_logger import ProcessLogger
    
    logger.info("All modules imported successfully")
    module_import_success = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    module_import_success = False

# Global instances
agent_router = None
tts_engine = None
voice_processor = None
process_logger = None
clients = {}  # Store client IDs and their message queues
client_messages: Dict[str, List[Dict[str, Any]]] = {}  # Maps client IDs to message queues

# Add global variable to track voice activation state
voice_listening_active = False

class ElectronProcessLogger(ProcessLogger):
    """Specialized process logger that sends updates to Electron via Socket.IO."""
    
    def log_execution(self, message: str, level: str = "info"):
        """Log execution step and emit to Socket.IO."""
        super().log_execution(message, level)
        socketio.emit('execution_log', {
            'message': message,
            'level': level
        })
    
    def log_conversation(self, message: str, message_type: str):
        """Log conversation message and emit to Socket.IO."""
        super().log_conversation(message, message_type)
        socketio.emit('conversation_message', {
            'message': message,
            'message_type': message_type
        })

def initialize_components():
    """Initialize all core AgentOS components."""
    global agent_router, tts_engine, voice_processor, process_logger
    
    if not module_import_success:
        logger.error("Cannot initialize components due to import errors")
        return False
        
    try:
        # Set up the specialized process logger
        process_logger = ElectronProcessLogger(log_to_file=True, log_to_console=True)
        process_logger.log_execution("Initializing AgentOS components...")
        
        # Initialize core components
        config.setup_logging()
        tts_engine = TTSEngine()
        agent_router = AgentRouter(process_logger=process_logger)
        
        # Initialize voice processor with callback
        def voice_input_callback(text):
            process_logger.log_conversation(f"You: {text}", "user")
            result = agent_router.process_command(text)
            if result and 'message' in result:
                process_logger.log_conversation(result.get('spoke', result.get('message', str(result))), "assistant")
                if 'spoke' in result:
                    tts_engine.speak(result['spoke'])
        
        voice_processor = VoiceProcessor(
            wake_word=config.VOICE_CONFIG["wake_word"],
            callback=voice_input_callback,
            process_logger=process_logger
        )
        
        process_logger.log_execution("AgentOS components initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing components: {e}", exc_info=True)
        return False

@app.route('/command', methods=['POST'])
def process_command():
    """
    Process a command from the frontend.
    This function handles the command processing and response formatting.
    """
    data = request.json
    command = data.get('command', '')
    verbose = data.get('verbose', False)
    client_id = request.headers.get('X-Client-ID')
    
    try:
        logger.info(f"Processing command: {command}")
        
        # Process the command
        if not agent_router:
            logger.error("Agent router not initialized")
            return jsonify({
                "status": "error",
                "message": "Agent router not initialized",
                "spoke": "Sorry, the system is not fully initialized yet."
            })
        
        # Log the command before processing
        if process_logger:
            process_logger.log_execution("Starting process: Command Routing")
            process_logger.log_execution(f"input: {command}")
            process_logger.log_execution(f"Routing command: {command}")
            process_logger.log_conversation(command, "user")
        
        # Track start time for performance monitoring
        start_time = time.time()
        
        # Process the command
        response = agent_router.process_command(command, verbose=verbose)
        
        # Track end time and calculate duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Log completion and response
        if process_logger:
            process_logger.log_execution(f"Completed process: Command Routing (took {duration:.2f}s)")
            
            # Log the response in the conversation
            if response:
                # Get the text to display (prefer 'spoke' over 'message')
                response_text = response.get('spoke', response.get('message', str(response)))
                process_logger.log_conversation(response_text, "assistant")
                
                # Speak the response if TTS is available and there's spoken content
                if tts_engine and 'spoke' in response:
                    tts_engine.speak(response['spoke'])
            
            # For Twitter agents in particular, provide more detailed response logging
            if response and isinstance(response, dict):
                agent_type = response.get('agent', '')
                
                if agent_type == 'twitter_bot':
                    process_logger.log_execution("AI Response from twitter_bot:")
                    
                    # Add special handling for Twitter completion messages
                    for key in ['status', 'message', 'spoke', 'thread_url']:
                        if key in response:
                            process_logger.log_execution(f"{key}: {response[key]}")
        
        # If there's a client ID, add any spoken response to their message queue
        if client_id and response and 'spoke' in response:
            # Add both a conversation message and detailed execution info
            add_message_to_client(client_id, {
                'type': 'conversation_message',
                'data': {
                    'message': response.get('message', response.get('spoke', '')),
                    'message_type': 'assistant'
                }
            })
            
            # For Twitter specifically, add formatted message for better display
            if response.get('agent') == 'twitter_bot' and 'message' in response:
                # First add standard message (ensures audio works)
                add_message_to_client(client_id, {
                    'type': 'execution_log',
                    'data': {
                        'message': f"Twitter agent response: {response.get('status', 'unknown')}",
                        'level': 'info'
                    }
                })
                
                # If there's a thread URL, add that specifically
                if 'thread_url' in response:
                    add_message_to_client(client_id, {
                        'type': 'execution_log',
                        'data': {
                            'message': f"Twitter thread available at: {response['thread_url']}",
                            'level': 'info'
                        }
                    })
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing command: {str(e)}", exc_info=True)
        
        # Log the error
        if process_logger:
            process_logger.log_execution(f"Error executing command: {str(e)}", level="error")
        
        return jsonify({
            "status": "error",
            "message": f"Error processing command: {str(e)}",
            "spoke": "Sorry, an error occurred while processing your request."
        })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the Python backend."""
    logger.info("Shutdown requested by Electron")
    # Clean up and stop any running processes
    if voice_processor and voice_processor.listening:
        voice_processor.stop_listening()
    
    # Allow some time for cleanup operations
    def shutdown_server():
        os._exit(0)
    
    threading.Timer(1.0, shutdown_server).start()
    return jsonify({"status": "success", "message": "Shutting down"})

@app.route('/voice/activate', methods=['POST'])
def activate_voice():
    """Activate voice detection for a single command."""
    logger.info("Voice activation requested")
    if process_logger:
        process_logger.log_execution("Voice activation requested")
        process_logger.log_conversation("Listening...", "system")
    
    # In a real implementation, you would activate a single voice capture
    if voice_processor:
        threading.Thread(target=voice_processor.listen_once, daemon=True).start()
        return jsonify({"status": "success", "message": "Voice activation started"})
    else:
        return jsonify({"status": "error", "message": "Voice processor not initialized"})

@app.route('/status', methods=['GET'])
def status():
    """Get the current status of the system."""
    agents = [name for name in agent_router.agents.keys()] if agent_router else []
    status_info = {
        "status": "running",
        "modules_loaded": module_import_success,
        "components_initialized": agent_router is not None,
        "agents_loaded": agents,
        "voice_processor_active": voice_processor.listening if voice_processor else False,
    }
    
    # Add system info if config was successfully imported
    try:
        status_info["system_info"] = config.get_platform_info()
    except Exception:
        status_info["system_info"] = {"error": "Config not available"}
        
    return jsonify(status_info)

@app.route('/debug/status', methods=['GET'])
def get_debug_status():
    """Get detailed system status for diagnostics."""
    agents = [name for name in agent_router.agents.keys()] if agent_router else []
    
    # Collect detailed status information
    status_info = {
        "agent_router": agent_router is not None,
        "process_logger": process_logger is not None,
        "tts_engine": tts_engine is not None,
        "voice_processor": voice_processor is not None,
        "voice_listening_active": voice_listening_active,
        "agents_loaded": agents
    }
    
    return jsonify(status_info)

@app.route('/voice/toggle', methods=['POST'])
def toggle_voice():
    """Toggle voice listening on/off with improved state management."""
    global voice_listening_active, voice_processor
    
    try:
        data = request.json
        enabled = data.get('enabled', False)
        
        logger.info(f"Voice toggle requested: {'ON' if enabled else 'OFF'}")
        
        # Initialize voice processor if needed
        if enabled and (not voice_processor or not voice_processor.initialized):
            logger.info("Creating voice processor for voice toggle")
            try:
                from core.voice_processor import VoiceProcessor
                
                def voice_input_callback(text):
                    """Callback to process recognized voice commands"""
                    if not text:
                        return
                    
                    logger.info(f"Voice command received: {text}")
                    if process_logger:
                        process_logger.log_execution(f"Voice command received: {text}")
                        # Note: Voice processor already logs the user message
                    
                    # Process the command through the agent router
                    if agent_router:
                        logger.info(f"Routing voice command to agent_router: {text}")
                        process_logger.log_execution(f"Routing voice command to agent_router: {text}")
                        
                        # Use the same command processing flow as text commands
                        result = agent_router.process_command(text, verbose=False)
                        
                        if process_logger and result:
                            response_text = result.get('spoke', result.get('message', str(result)))
                            process_logger.log_conversation(response_text, "assistant")
                            
                            # Speak response if TTS is available
                            if tts_engine and 'spoke' in result:
                                tts_engine.speak(result['spoke'])
                    else:
                        logger.error("Agent router not available for processing voice command")
                        if process_logger:
                            process_logger.log_execution("Agent router not available for voice command", level="error")
                            process_logger.log_conversation("Sorry, I'm not fully initialized yet.", "system")
                
                # Create a new voice processor with the callback
                voice_processor = VoiceProcessor(
                    wake_word=None,
                    callback=voice_input_callback,
                    process_logger=process_logger
                )
                
                # Initialize but don't start listening yet
                if not voice_processor.initialize():
                    logger.error("Failed to initialize voice processor")
                    if process_logger:
                        process_logger.log_execution("Failed to initialize voice processor", level="error")
                        process_logger.log_conversation("Sorry, I couldn't initialize voice recognition. Please check your microphone settings.", "system")
                    return jsonify({
                        "status": "error",
                        "message": "Failed to initialize voice processor", 
                        "voice_active": False
                    })
            except Exception as init_error:
                logger.error(f"Error creating voice processor: {init_error}")
                if process_logger:
                    process_logger.log_execution(f"Error creating voice processor: {init_error}", level="error")
                return jsonify({
                    "status": "error",
                    "message": f"Error initializing voice processor: {str(init_error)}", 
                    "voice_active": False
                })
        
        if process_logger:
            process_logger.log_execution(f"Voice {'activated' if enabled else 'deactivated'}")
            
            # Add user-facing message
            if enabled:
                process_logger.log_conversation("Voice input activated. You can speak now.", "system")
            else:
                process_logger.log_conversation("Voice input deactivated. Using text input.", "system")
        
        voice_listening_active = enabled
        
        # Actually control the voice processor state
        if voice_processor:
            try:
                if enabled:
                    # Only start listening if it's not already listening
                    if not voice_processor.listening:
                        # Make sure the callback is set correctly
                        if not voice_processor.callback and 'voice_input_callback' in locals():
                            voice_processor.callback = locals()['voice_input_callback']
                            logger.info("Reset voice processor callback")
                            
                        voice_processor.start_listening()
                        logger.info("Voice listening started")
                else:
                    # Only stop if it's currently listening
                    if voice_processor.listening:
                        voice_processor.stop_listening()
                        logger.info("Voice listening stopped")
            except Exception as voice_error:
                logger.error(f"Error controlling voice processor: {voice_error}")
                if process_logger:
                    process_logger.log_execution(f"Error controlling voice processor: {voice_error}", level="error")
                
                # Try to reset the state if there was an error
                try:
                    if voice_processor.listening:
                        voice_processor.stop_listening()
                except:
                    pass
                
                return jsonify({
                    "status": "error",
                    "message": f"Error controlling voice processor: {str(voice_error)}",
                    "voice_active": False
                })
        
        return jsonify({
            "status": "success",
            "voice_active": voice_listening_active
        })
    except Exception as e:
        logger.error(f"Error toggling voice: {e}")
        # Always set voice inactive on error
        voice_listening_active = False
        if process_logger:
            process_logger.log_execution(f"Error toggling voice: {e}", level="error")
            process_logger.log_conversation("Sorry, there was an error with voice input. Please try again.", "system")
        
        return jsonify({
            "status": "error", 
            "message": f"Error toggling voice: {str(e)}",
            "voice_active": False
        }), 500

@app.route('/register', methods=['POST'])
def register_client():
    """Register a new client and return a client ID."""
    client_id = str(uuid.uuid4())
    clients[client_id] = {
        "registered_at": datetime.now().isoformat(),
        "last_poll": datetime.now().isoformat(),
    }
    client_messages[client_id] = []  # Initialize empty message queue
    
    logger.info(f"Registered new client: {client_id}")
    return jsonify({
        "status": "success",
        "client_id": client_id,
        "message": "Client registered successfully"
    })

@app.route('/poll', methods=['GET'])
def poll_messages():
    """Poll for new messages for a specific client."""
    client_id = request.headers.get('X-Client-ID')
    
    if not client_id or client_id not in clients:
        return jsonify({"status": "error", "message": "Invalid or missing client ID"}), 401
    
    # Update last poll time
    clients[client_id]["last_poll"] = datetime.now().isoformat()
    
    # Get messages for this client
    messages = client_messages.get(client_id, [])
    
    # Clear the message queue after sending
    client_messages[client_id] = []
    
    return jsonify({
        "status": "success",
        "messages": messages
    })

@app.route("/stream_updates", methods=["GET"])
def stream_updates():
    """
    Get ongoing updates from agents with message queues.
    
    Returns:
        JSON with any pending messages
    """
    # Clean up old queues first
    MessageQueue.cleanup_old_queues()
    
    # Get all pending messages
    messages = MessageQueue.get_all_messages()
    
    # Log message count for debugging
    if messages:
        logger.debug(f"Streaming {len(messages)} messages to frontend")
    
    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": messages
    })

def add_message_to_client(client_id: str, message: Dict[str, Any]) -> bool:
    """Add a message to a client's queue."""
    if client_id in client_messages:
        client_messages[client_id].append(message)
        return True
    return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AgentOS Python Bridge')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the bridge server on')
    return parser.parse_args()

def print_route_tree(app):
    """Print a detailed tree of all routes registered in the Flask app."""
    route_count = 0
    
    print("\n==== REGISTERED ROUTES ====")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        route_count += 1
        methods = ','.join(rule.methods)
        endpoint = rule.endpoint
        
        # Get function docstring if available
        view_func = app.view_functions.get(endpoint)
        doc = inspect.getdoc(view_func) if view_func else None
        doc_preview = f"- {doc.split('.')[0]}" if doc else ""
        
        print(f"Route {route_count}: {rule.rule} [{methods}] => {endpoint} {doc_preview}")
        
        # Show arguments if any
        if rule.arguments:
            print(f"  Arguments: {', '.join(rule.arguments)}")
    
    print(f"\nTotal routes: {route_count}\n")
    logger.info(f"Total routes registered in app: {route_count}")

def mount_routes(app, routes_list, source_name):
    """Mount a list of routes to the Flask app with better error handling and logging."""
    if not routes_list:
        logger.warning(f"No {source_name} routes provided to mount")
        return 0
        
    mounted_count = 0
    
    for route_info in routes_list:
        try:
            if len(route_info) >= 3:
                route_path, view_func, methods = route_info
                
                # Check if route already exists
                existing_routes = [r.rule for r in app.url_map.iter_rules()]
                if route_path in existing_routes:
                    logger.warning(f"Route {route_path} already exists, skipping")
                    continue
                
                # Add the route
                app.add_url_rule(route_path, view_func.__name__, view_func, methods=methods)
                mounted_count += 1
                
                # Log success with route info
                doc = inspect.getdoc(view_func)
                doc_str = f" - {doc}" if doc else ""
                logger.info(f"Mounted {source_name} route: {route_path} [{','.join(methods)}] => {view_func.__name__}{doc_str}")
            else:
                logger.error(f"Invalid route format for {route_info}, expected (path, view_func, methods)")
        except Exception as e:
            logger.error(f"Failed to mount route {route_info}: {str(e)}")
    
    return mounted_count

def main():
    """Main entry point for the bridge server."""
    args = parse_arguments()
    
    try:
        # Initialize components first
        success = initialize_components()
        if not success:
            logger.warning("Running with limited functionality")
        
        # Configure voice processor but don't start it
        if voice_processor:
            voice_processor.initialize()
            logger.info("Voice processor initialized but not actively listening")
        
        logger.info(f"Starting bridge server on port {args.port}")
        
        # Double check and mount Twitter routes again if they weren't mounted earlier
        # This ensures they're definitely available even if the early import failed
        total_custom_routes = 0
        if HAS_TWITTER_ROUTES:
            logger.info("Verifying Twitter routes are mounted...")
            twitter_endpoints = [rule.endpoint for rule in app.url_map.iter_rules() 
                                if rule.rule.startswith('/twitter')]
            
            if not twitter_endpoints:
                logger.warning("Twitter routes were not mounted earlier, mounting now...")
                mounted = mount_routes(app, twitter_routes, "Twitter")
                total_custom_routes += mounted
                logger.info(f"Mounted {mounted} Twitter routes")
            else:
                logger.info(f"Twitter routes already mounted: {len(twitter_endpoints)} endpoints")
                total_custom_routes += len(twitter_endpoints)
        
        # Register NLP routes blueprint if available
        if HAS_NLP_ROUTES:
            logger.info("Registering NLP routes blueprint...")
            try:
                app.register_blueprint(nlp_routes)
                nlp_endpoints = [rule.endpoint for rule in app.url_map.iter_rules() 
                                if rule.rule.startswith('/api/natural_language')]
                total_custom_routes += len(nlp_endpoints)
                logger.info(f"Registered NLP routes blueprint with {len(nlp_endpoints)} endpoints")
            except Exception as e:
                logger.error(f"Failed to register NLP routes blueprint: {e}")
        
        # Log all registered routes for debugging
        print_route_tree(app)
        
        # Log all endpoints available in the API
        endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]
        logger.info(f"Available endpoints before starting: {', '.join(sorted(endpoints))}")
        
        print("FLASK STARTING ON PORT 5000")
        logger.warning("FLASK STARTING ON PORT 5000 - LOOK FOR ERRORS BELOW")
        
        # Start the server
        socketio.run(
            app, 
            host='127.0.0.1',
            port=args.port,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"CRITICAL ERROR STARTING SERVER: {str(e)}")
        logger.error(f"Server failed to start: {str(e)}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
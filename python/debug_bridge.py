"""
Minimal debug bridge to troubleshoot startup issues.
"""

import sys
import os
import logging
import time

# Configure extensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bridge_debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("debug_bridge")

# Log system information
logger.info("="*40)
logger.info("DIAGNOSTIC BRIDGE STARTING")
logger.info("="*40)
logger.info(f"Python version: {sys.version}")
logger.info(f"Python executable: {sys.executable}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")

# Try to determine the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
logger.info(f"Project root: {project_root}")

# Add project root to path
sys.path.insert(0, project_root)
logger.info(f"Python path: {sys.path}")

# Try importing each key component separately to pinpoint the issue
try:
    logger.info("Attempting to import Flask...")
    from flask import Flask
    logger.info("Flask imported successfully")
    
    logger.info("Attempting to import flask_socketio...")
    from flask_socketio import SocketIO
    logger.info("flask_socketio imported successfully")
    
    logger.info("Attempting to import flask_cors...")
    from flask_cors import CORS
    logger.info("flask_cors imported successfully")
    
    logger.info("Attempting to import config...")
    import config
    logger.info("config imported successfully")
    
    logger.info("Attempting to import agent_router...")
    from core.agent_router import AgentRouter
    logger.info("agent_router imported successfully")
    
    logger.info("Attempting to import tts_engine...")
    from core.tts_engine import TTSEngine
    logger.info("tts_engine imported successfully")
    
    logger.info("Attempting to import voice_processor...")
    from core.voice_processor import VoiceProcessor
    logger.info("voice_processor imported successfully")

    logger.info("Attempting to import process_logger...")
    from utils.process_logger import ProcessLogger
    logger.info("process_logger imported successfully")
    
    logger.info("All imports successful!")
except Exception as e:
    logger.error(f"Import error: {e}", exc_info=True)

# Start a basic Flask app to test
try:
    logger.info("Creating minimal Flask app...")
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return {"status": "ok", "message": "Debug bridge is running"}
    
    # Keep the script running
    logger.info("Starting minimal Flask app on port 5000...")
    app.run(host='0.0.0.0', port=5000)
    
except Exception as e:
    logger.error(f"Flask error: {e}", exc_info=True)

# This keeps the script open
logger.info("Debug bridge is now running indefinitely...")
while True:
    time.sleep(10)

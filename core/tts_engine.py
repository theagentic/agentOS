"""
Text-to-Speech Engine

Provides speech synthesis capabilities to the AgentOS system.
"""

import pyttsx3
import logging
import threading
from threading import Thread

class TTSEngine:
    """Handles text-to-speech conversion with configurable voices."""
    
    def __init__(self, voice_id=None, rate=150):
        """
        Initialize the TTS engine.
        
        Args:
            voice_id: ID of the voice to use (None for default)
            rate: Speech rate (words per minute)
        """
        self.logger = logging.getLogger("core.tts")
        self.initialized = False
        self.engine = None
        self.voice_id = voice_id
        self.rate = rate
        self.lock = threading.Lock()
        
        # Try to initialize the engine
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the TTS engine with error handling."""
        try:
            self.logger.info("Initializing TTS engine")
            self.engine = pyttsx3.init()
            
            # Set properties
            self.engine.setProperty('rate', self.rate)
            
            # Set voice if specified
            if self.voice_id:
                try:
                    self.engine.setProperty('voice', self.voice_id)
                    self.logger.info(f"Set voice to {self.voice_id}")
                except Exception as e:
                    self.logger.error(f"Failed to set voice: {e}")
            
            # Log available voices
            voices = self.engine.getProperty('voices')
            self.logger.info(f"Available voices: {len(voices)}")
            for voice in voices:
                self.logger.debug(f"Voice ID: {voice.id}, Name: {voice.name}, Languages: {voice.languages}")
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.initialized = False
            return False
    
    def speak(self, text):
        """
        Speak the given text asynchronously.
        
        Args:
            text: The text to convert to speech
        """
        if not text:
            return
            
        # If not initialized, try to initialize again
        if not self.initialized or not self.engine:
            self.logger.warning("TTS engine not initialized, attempting to reinitialize")
            if not self._initialize_engine():
                self.logger.error("Failed to reinitialize TTS engine, cannot speak")
                return
            
        # Use a thread to avoid blocking the UI
        def _speak():
            # Use a lock to prevent multiple speak operations from interfering with each other
            with self.lock:
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    self.logger.error(f"TTS error: {e}")
                    # Try to reinitialize the engine for next time
                    try:
                        self.engine = pyttsx3.init()
                        self.engine.setProperty('rate', self.rate)
                        if self.voice_id:
                            self.engine.setProperty('voice', self.voice_id)
                    except Exception as reinit_error:
                        self.logger.error(f"Failed to reinitialize TTS engine: {reinit_error}")
                        self.initialized = False
                
        Thread(target=_speak, daemon=True).start()
        
    def list_voices(self):
        """Return a list of available voices."""
        if not self.initialized or not self.engine:
            if not self._initialize_engine():
                return []
                
        try:
            return [{"id": voice.id, "name": voice.name} for voice in self.engine.getProperty('voices')]
        except Exception as e:
            self.logger.error(f"Error listing voices: {e}")
            return []

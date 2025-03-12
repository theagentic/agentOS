"""
Voice Processor Module

Handles voice input, wake word detection, and speech recognition.
"""

import speech_recognition as sr
import threading
import time
from utils.process_logger import ProcessLogger
import logging

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Handles voice input, wake word detection, and speech recognition."""
    
    def __init__(self, wake_word=None, callback=None, process_logger=None):
        """
        Initialize the voice processor.
        
        Args:
            wake_word (str, optional): Wake word to trigger voice commands
            callback (callable): Function to call with recognized speech
            process_logger (ProcessLogger): Logger for debug output
        """
        self.wake_word = wake_word.lower() if wake_word else None
        self.callback = callback
        self.process_logger = process_logger or ProcessLogger()
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.listening_thread = None
        self.should_stop = threading.Event()
        self.initialized = False
        self._configure_recognizer()
        
    def _configure_recognizer(self):
        """Configure the speech recognizer."""
        try:
            self.process_logger.log_execution("Configuring speech recognizer")
            
            # Set up microphone with better error handling
            try:
                # First check if microphone is available
                microphones = sr.Microphone.list_microphone_names()
                if not microphones:
                    raise Exception("No microphone devices found")
                
                self.process_logger.log_execution(f"Found {len(microphones)} microphone devices")
                
                # Try to use default microphone
                with sr.Microphone() as source:
                    self.process_logger.log_execution("Adjusting for ambient noise")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as mic_error:
                self.process_logger.log_execution(f"Microphone error: {mic_error}", level="error")
                logger.error(f"Microphone initialization error: {mic_error}")
                raise Exception(f"Microphone setup failed: {mic_error}")
            
            # Tweak recognition parameters
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            self.process_logger.log_execution(f"Recognizer configured with energy threshold {self.recognizer.energy_threshold}")
        except Exception as e:
            self.process_logger.log_execution(f"Error configuring recognizer: {e}", level="error")
            logger.error(f"Failed to configure recognizer: {e}")
            self.initialized = False
            raise
    
    def start_continuous_listening(self, callback=None, no_wake_word=False):
        """
        Start continuous listening without waiting for wake word.
        
        Args:
            callback (callable, optional): Function to call with recognized speech
            no_wake_word (bool): Skip wake word detection if True
        """
        # Update the callback if provided
        if callback:
            self.callback = callback
        
        # Don't start if we're already listening or have no callback
        if self.listening:
            self.process_logger.log_execution("Already listening, ignoring request", level="warning")
            return
        
        if not self.callback:
            self.process_logger.log_execution("No callback provided, cannot start listening", level="error")
            return
            
        self.listening = True
        
        self.process_logger.log_execution("Starting continuous voice listening")
        self.process_logger.log_execution("Ready to capture voice commands")
        
        with sr.Microphone() as source:
            # First, adjust for ambient noise once before starting
            try:
                self.process_logger.log_execution("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.process_logger.log_execution(f"Energy threshold set to {self.recognizer.energy_threshold}")
            except Exception as e:
                self.process_logger.log_execution(f"Error adjusting for noise: {e}", level="error")
            
            # Start the listening loop
            while self.listening:
                try:
                    self.process_logger.log_execution("Listening for command...", level="debug")
                    audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                    
                    try:
                        self.process_logger.log_execution("Processing audio...")
                        recognized_text = self.recognizer.recognize_google(audio).lower()
                        self.process_logger.log_execution(f"Recognized: '{recognized_text}'")
                        
                        # Call the callback with the recognized text
                        if self.callback:
                            self.callback(recognized_text)
                        else:
                            self.process_logger.log_execution("Warning: No callback available for processing text", level="warning")
                            
                    except sr.UnknownValueError:
                        self.process_logger.log_execution("Speech unintelligible", level="warning")
                    except sr.RequestError as e:
                        self.process_logger.log_execution(f"Recognition error: {e}", level="error")
                
                except sr.WaitTimeoutError:
                    # This is normal, continue listening
                    pass
                except Exception as e:
                    self.process_logger.log_execution(f"Error in listening loop: {e}", level="error")
                    # Add a small delay to avoid tight error loops
                    time.sleep(0.5)
        
        self.process_logger.log_execution("Continuous listening stopped")
    
    def start_listening(self):
        """Start the voice listening thread with no wake word detection."""
        if self.listening:
            return
        
        self.listening = True
        self.listening_thread = threading.Thread(
            target=self._direct_listening_loop, 
            daemon=True
        )
        self.listening_thread.start()
        self.process_logger.log_execution("Voice listening started - processing all commands directly")
    
    def _direct_listening_loop(self):
        """Background thread that directly listens for commands without wake word."""
        self.process_logger.log_execution("Voice direct listening loop started")
        
        with sr.Microphone() as source:
            while self.listening:
                try:
                    self.process_logger.log_execution("Listening for command...")
                    audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                    
                    try:
                        start_time = time.time()
                        text = self.recognizer.recognize_google(audio).lower()
                        elapsed = time.time() - start_time
                        
                        self.process_logger.log_execution(f"Command recognized: '{text}' (took {elapsed:.2f}s)")
                        self.process_logger.log_conversation(f"You: {text}", "user")
                        
                        # Process all heard speech immediately
                        if self.callback:
                            try:
                                # Log that we're executing the callback
                                self.process_logger.log_execution(f"Executing callback for recognized text: '{text}'")
                                self.callback(text)
                            except Exception as callback_error:
                                self.process_logger.log_execution(f"Error in callback execution: {callback_error}", level="error")
                                self.process_logger.log_conversation("Sorry, there was an error processing your command.", "system")
                        else:
                            self.process_logger.log_execution("No callback set for voice processor", level="error")
                        
                    except sr.UnknownValueError:
                        self.process_logger.log_execution("Speech unintelligible", level="warning")
                    except sr.RequestError as e:
                        self.process_logger.log_execution(f"Recognition error: {e}", level="error")
                
                except sr.WaitTimeoutError:
                    # This is normal, continue listening
                    pass
                except Exception as e:
                    self.process_logger.log_execution(f"Error in listening loop: {e}", level="error")
                    # Add a small delay to avoid tight error loops
                    time.sleep(0.5)
    
    # Replace existing _listening_loop with our direct version that doesn't wait for wake word
    _listening_loop = _direct_listening_loop
    
    def _process_command(self, text=None):
        """Process a single command."""
        if not text:
            self.process_logger.log_execution("Processing command...")
            self.process_logger.log_conversation("Listening for command...", "system")
            
            with sr.Microphone() as source:
                try:
                    # Only record a new command if we don't already have text
                    self.process_logger.log_execution("Recording command...")
                    audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                    
                    try:
                        start_time = time.time()
                        text = self.recognizer.recognize_google(audio).lower()
                        elapsed = time.time() - start_time
                        
                        self.process_logger.log_execution(f"Command recognized: '{text}' (took {elapsed:.2f}s)")
                    except sr.UnknownValueError:
                        self.process_logger.log_execution("Could not understand audio", level="warning")
                        return
                    except sr.RequestError as e:
                        self.process_logger.log_execution(f"Recognition error: {e}", level="error")
                        return
                except Exception as e:
                    self.process_logger.log_execution(f"Error processing command: {e}", level="error")
                    return
        
        # Process the recognized text
        if text and self.callback:
            self.callback(text)
    
    def listen_once(self):
        """Listen for a single command with improved error handling."""
        self.process_logger.log_execution("Recording command...")
        self.process_logger.log_conversation("Listening...", "system")
        
        # Verify the recognizer is initialized
        if not self.initialized:
            try:
                # Try to initialize first
                self.initialize()
                if not self.initialized:
                    self.process_logger.log_execution("Failed to initialize recognizer before listen_once", level="error")
                    self.process_logger.log_conversation("Sorry, I couldn't access the microphone. Please check your microphone settings.", "system")
                    return
            except Exception as e:
                self.process_logger.log_execution(f"Error initializing recognizer: {e}", level="error")
                self.process_logger.log_conversation("Sorry, I couldn't access the microphone. Please check your microphone settings.", "system")
                return
        
        try:
            with sr.Microphone() as source:
                # Update energy threshold for the current environment
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self.process_logger.log_execution(f"Adjusted energy threshold to {self.recognizer.energy_threshold}")
                except Exception as e:
                    self.process_logger.log_execution(f"Error adjusting for ambient noise: {e}", level="warning")
                
                # Listen for command with timeout handling
                try:
                    audio = None
                    try:
                        self.process_logger.log_execution("Waiting for voice input...")
                        audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                    except sr.WaitTimeoutError:
                        self.process_logger.log_execution("No speech detected within timeout", level="warning")
                        self.process_logger.log_conversation("I didn't hear anything. Please try again.", "system")
                        return
                    except Exception as e:
                        self.process_logger.log_execution(f"Error listening: {e}", level="error")
                        self.process_logger.log_conversation("I couldn't hear you properly. Please try again.", "system")
                        return
                    
                    if not audio:
                        self.process_logger.log_execution("No audio captured", level="warning")
                        self.process_logger.log_conversation("I couldn't hear anything. Please try again.", "system")
                        return
                    
                    try:
                        start_time = time.time()
                        # Try a couple of recognition services in case one fails
                        text = None
                        try:
                            text = self.recognizer.recognize_google(audio).lower()
                        except (sr.UnknownValueError, sr.RequestError) as e:
                            self.process_logger.log_execution(f"Google recognition failed, trying alternative: {e}", level="warning")
                            try:
                                # Fall back to Sphinx for offline recognition
                                text = self.recognizer.recognize_sphinx(audio).lower()
                            except Exception as sphinx_error:
                                self.process_logger.log_execution(f"Sphinx recognition also failed: {sphinx_error}", level="error")
                                raise e  # Re-raise the original error
                        
                        elapsed = time.time() - start_time
                        
                        if text:
                            self.process_logger.log_execution(f"Command recognized: '{text}' (took {elapsed:.2f}s)")
                            self.process_logger.log_conversation(f"You: {text}", "user")
                            
                            if self.callback:
                                self.callback(text)
                        else:
                            self.process_logger.log_execution("Recognition returned empty text", level="warning")
                            self.process_logger.log_conversation("I couldn't understand what you said. Please try again.", "system")
                        
                    except sr.UnknownValueError:
                        self.process_logger.log_execution("Could not understand audio", level="warning")
                        self.process_logger.log_conversation("I couldn't understand what you said. Please try again.", "system")
                    except sr.RequestError as e:
                        self.process_logger.log_execution(f"Recognition error: {e}", level="error")
                        self.process_logger.log_conversation("There was a problem connecting to the speech recognition service.", "system")
                
                except Exception as e:
                    self.process_logger.log_execution(f"Error in audio processing: {e}", level="error")
                    self.process_logger.log_conversation("Sorry, there was a problem processing your voice command.", "system")
                
        except Exception as e:
            self.process_logger.log_execution(f"Error processing command: {e}", level="error")
            self.process_logger.log_conversation("Sorry, there was an error processing your voice command.", "system")
    
    def stop_listening(self):
        """Stop the voice listening thread."""
        self.listening = False
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=1.0)
            self.listening_thread = None

    def initialize(self):
        """Initialize the recognizer but don't start listening yet."""
        try:
            if self.initialized:
                logger.info("Voice processor already initialized")
                return True
                
            # Set up the recognizer without activating the microphone
            if self.process_logger:
                self.process_logger.log_execution("Configuring speech recognizer")
            
            # Check if microphones are available
            try:
                microphones = sr.Microphone.list_microphone_names()
                if not microphones:
                    if self.process_logger:
                        self.process_logger.log_execution("No microphone devices found", level="error")
                    logger.error("No microphone devices found")
                    return False
                
                if self.process_logger:
                    self.process_logger.log_execution(f"Found {len(microphones)} microphone devices")
            except Exception as e:
                if self.process_logger:
                    self.process_logger.log_execution(f"Error listing microphones: {e}", level="error")
                logger.error(f"Error listing microphones: {e}")
                return False
                
            # Adjust energy threshold for ambient noise
            try:
                with sr.Microphone() as source:
                    if self.process_logger:
                        self.process_logger.log_execution("Adjusting for ambient noise")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                if self.process_logger:
                    self.process_logger.log_execution(f"Error adjusting for ambient noise: {e}", level="error")
                logger.error(f"Error adjusting for ambient noise: {e}")
                return False
                
            logger.info(f"Recognizer configured with energy threshold {self.recognizer.energy_threshold}")
            if self.process_logger:
                self.process_logger.log_execution(f"Recognizer configured with energy threshold {self.recognizer.energy_threshold}")
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing speech recognition: {e}")
            if self.process_logger:
                self.process_logger.log_execution(f"Error initializing speech recognition: {e}", level="error")
            self.initialized = False
            return False

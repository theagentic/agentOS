"""
Voice diagnostics utility for troubleshooting microphone issues.
"""
import speech_recognition as sr
import pyaudio
import os
import logging
import json
import platform
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_audio_devices():
    """Get a list of available audio devices."""
    try:
        p = pyaudio.PyAudio()
        info = []
        
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            
            # Add useful device properties
            device = {
                "index": i,
                "name": device_info.get("name", "Unknown"),
                "channels": device_info.get("maxInputChannels", 0),
                "sample_rate": int(device_info.get("defaultSampleRate", 0)),
                "is_input": device_info.get("maxInputChannels", 0) > 0
            }
            info.append(device)
        
        p.terminate()
        return info
    except Exception as e:
        logger.error(f"Error getting audio devices: {e}")
        return []

def detect_default_microphone():
    """Detect the default microphone."""
    try:
        with sr.Microphone() as source:
            return {
                "name": source.device_index or "Default",
                "sample_rate": source.SAMPLE_RATE,
                "chunk_size": source.CHUNK
            }
    except Exception as e:
        logger.error(f"Error detecting default microphone: {e}")
        return {"error": str(e)}

def test_microphone():
    """Test the microphone by recording a short sample."""
    results = {}
    
    try:
        r = sr.Recognizer()
        
        # Try with default microphone
        with sr.Microphone() as source:
            results["microphone_type"] = "default"
            results["device_index"] = source.device_index
            
            logger.info("Adjusting for ambient noise")
            r.adjust_for_ambient_noise(source)
            results["energy_threshold"] = r.energy_threshold
            
            logger.info("Recording test audio (3 seconds)")
            print("Please speak something for 3 seconds...")
            audio = r.listen(source, timeout=3.0, phrase_time_limit=3.0)
            results["audio_recorded_bytes"] = len(audio.get_raw_data())
            results["audio_recorded"] = True
            
            try:
                text = r.recognize_google(audio)
                results["recognition_successful"] = True
                results["recognized_text"] = text
                logger.info(f"Recognized: {text}")
            except sr.UnknownValueError:
                results["recognition_successful"] = False
                results["recognition_error"] = "UnknownValueError"
                logger.info("Speech unrecognizable")
            except Exception as e:
                results["recognition_successful"] = False
                results["recognition_error"] = str(e)
                logger.error(f"Recognition error: {e}")
    
    except Exception as e:
        logger.error(f"Error testing microphone: {e}")
        results["error"] = str(e)
    
    return results

def get_system_audio_info():
    """Get system audio information."""
    info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": sys.version,
        "pyaudio_version": pyaudio.__version__,
        "speechrecognition_version": sr.__version__
    }
    
    # Add OS-specific audio info
    if platform.system() == 'Windows':
        try:
            import winreg
            
            # Check Windows audio services
            audio_services = [
                "Audiosrv",  # Windows Audio
                "AudioEndpointBuilder"  # Windows Audio Endpoint Builder
            ]
            
            info["windows_audio_services"] = {}
            for service in audio_services:
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        f"SYSTEM\\CurrentControlSet\\Services\\{service}"
                    )
                    start_type = winreg.QueryValueEx(key, "Start")[0]
                    info["windows_audio_services"][service] = {
                        "exists": True,
                        "start_type": start_type
                    }
                    winreg.CloseKey(key)
                except Exception as e:
                    info["windows_audio_services"][service] = {
                        "exists": False,
                        "error": str(e)
                    }
        except Exception as e:
            info["windows_registry_error"] = str(e)
    
    return info

def run_diagnostics():
    """Run comprehensive voice diagnostics."""
    diagnostics = {
        "timestamp": str(sr.datetime.datetime.now()),
        "system_info": get_system_audio_info(),
        "audio_devices": get_audio_devices(),
        "default_microphone": detect_default_microphone()
    }
    
    # Ask for permission before testing microphone
    print("\nWould you like to test your microphone? (y/n)")
    response = input().strip().lower()
    
    if response == 'y' or response == 'yes':
        print("\nTesting microphone...")
        diagnostics["microphone_test"] = test_microphone()
    
    # Save results to file
    try:
        os.makedirs("diagnostics", exist_ok=True)
        filename = os.path.join("diagnostics", f"voice_diagnostics_{sr.datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(filename, "w") as f:
            json.dump(diagnostics, f, indent=2)
            
        print(f"\nDiagnostics saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving diagnostics: {e}")
        print(f"Error saving diagnostics: {e}")
    
    return diagnostics

if __name__ == "__main__":
    print("Running Voice Diagnostics Tool")
    print("=============================")
    print("This tool will help diagnose issues with your microphone setup.")
    
    results = run_diagnostics()
    
    # Print summary
    print("\nDiagnostics Summary:")
    print("------------------")
    
    device_count = len(results["audio_devices"])
    input_devices = sum(1 for device in results["audio_devices"] if device["is_input"])
    
    print(f"Total audio devices detected: {device_count}")
    print(f"Input devices detected: {input_devices}")
    
    if "microphone_test" in results:
        test = results["microphone_test"]
        if "error" in test:
            print(f"Microphone test failed: {test['error']}")
        else:
            print(f"Microphone test successful: {test.get('recognition_successful', False)}")
            if test.get("recognized_text"):
                print(f"Recognized text: {test['recognized_text']}")
    
    print("\nFor detailed results, check the saved JSON file.")

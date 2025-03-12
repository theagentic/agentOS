"""
Setup script for the Python-Electron bridge.
Validates the environment and dependencies.
"""
import sys
import importlib
from pathlib import Path

def check_dependency(package_name):
    """
    Check if a Python package is installed.
    
    Handles the package name vs. import name discrepancy
    (e.g., flask-socketio vs flask_socketio)
    """
    try:
        # Convert package names with hyphens to underscores for import
        import_name = package_name.replace('-', '_')
        importlib.import_module(import_name)
        return True
    except ImportError:
        # Also try the reverse (underscore to hyphen) for completeness
        try:
            alt_name = package_name.replace('_', '-')
            importlib.import_module(alt_name)
            return True
        except ImportError:
            # If both attempts fail, the package is not installed
            return False

def main():
    """Main entry point for the setup script."""
    print("Checking Python-Electron bridge environment...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("Error: Python 3.8 or higher is required.")
        sys.exit(1)
    
    # Check required packages - use the PyPI package names
    required_packages = [
        "flask", 
        "flask-socketio",  # Note: hyphenated package name 
        "flask-cors", 
        "pyttsx3", 
        "speech_recognition", 
        "pyaudio"
    ]
    
    missing_packages = []
    for package in required_packages:
        if not check_dependency(package):
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Error: The following required packages are missing: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements-electron.txt")
        sys.exit(1)
    
    # Check bridge configuration
    bridge_path = Path(__file__).parent / "bridge.py"
    if not bridge_path.exists():
        print(f"Error: Bridge script not found at {bridge_path}")
        sys.exit(1)
    
    # Validate core system modules
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    try:
        for module in ['config', 'core.agent_router', 'core.tts_engine']:
            if importlib.util.find_spec(module) is None:
                raise ImportError(f"Module {module} not found")
        print("Core modules loaded successfully.")
    except ImportError as e:
        print(f"Error importing core modules: {e}")
        sys.exit(1)
    
    print("Python-Electron bridge environment is ready.")
    
    # Return the port the bridge will run on
    return 5000

if __name__ == "__main__":
    port = main()
    print(f"Bridge will run on port {port}")

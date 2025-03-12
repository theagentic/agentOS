"""Script to detect and output virtual environment information."""
import sys
import json

venv_info = {
    "executable": sys.executable,
    "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "prefix": sys.prefix
}

print(json.dumps(venv_info))

import os
import platform
import sys
import urllib.request
import socket
import shutil
from pathlib import Path
from .const import PyWestConstants


class ProjectValidator:
    """Validate project directory and structure"""
    
    def __init__(self):
        pass
    
    def validate_project_directory(self, project_path):
        """Validate project directory exists and is accessible"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' not found")
        
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_path}' is not a directory")
        
        # Check read permissions
        if not os.access(project_path, os.R_OK):
            raise PermissionError(f"No read permission for project directory: {project_path}")
        
        return project_path


class SystemValidator:
    """Validate system requirements and environment"""
    
    def __init__(self):
        pass
    
    def validate_windows_environment(self):
        """Validate running on Windows (required for this tool)"""
        if platform.system() != 'Windows':
            return False, "PyWest is designed for Windows only"
        
        return True, None
    
    def validate_python_version(self):
        """Validate current Python version meets requirements"""
        major, minor = sys.version_info[:2]
        
        if major < 3 or (major == 3 and minor < 8):
            return False, f"Python 3.8+ required, currently running Python {major}.{minor}"
        
        return True, None
    
    def validate_internet_connection(self):
        """Validate internet connection for downloading Python"""
        try:
            # Try to reach Python.org with a short timeout
            urllib.request.urlopen('https://www.python.org', timeout=5)
            return True, None
        except (urllib.error.URLError, socket.timeout):
            return False, "Internet connection required to download Python embeddable"
        except Exception as e:
            return False, f"Network error: {str(e)}"
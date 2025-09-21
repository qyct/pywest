import os
import platform
import sys
import urllib.request
import socket
from pathlib import Path
from .const import PyWestConstants


class ProjectValidator:
    """Validate project directory and structure"""
    
    def validate_project_directory(self, project_path):
        """Validate project directory exists and is accessible"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' not found")
        
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_path}' is not a directory")
        
        if not os.access(project_path, os.R_OK):
            raise PermissionError(f"No read permission for project directory: {project_path}")
        
        return project_path


class BundleValidator:
    """Validate bundle configuration and requirements"""
    
    def validate_bundle_requirements(self, bundle_config):
        """Validate bundle creation requirements"""
        errors = []
        
        if bundle_config.python_version not in PyWestConstants.SUPPORTED_PYTHON_VERSIONS:
            errors.append(f"Unsupported Python version: {bundle_config.python_version}")
        
        if not (0 <= bundle_config.compression_level <= 9):
            errors.append(f"Compression level must be between 0-9, got: {bundle_config.compression_level}")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return True
    
    def validate_output_directory(self, output_path):
        """Validate output directory is writable"""
        output_path = Path(output_path)
        
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True)
            except Exception as e:
                raise PermissionError(f"Cannot create output directory: {str(e)}")
        
        if not os.access(output_path, os.W_OK):
            raise PermissionError(f"No write permission for output directory: {output_path}")
        
        return True
    
    def validate_bundle_name(self, bundle_name):
        """Validate bundle name is valid for filesystem"""
        if not bundle_name or not bundle_name.strip():
            raise ValueError("Bundle name cannot be empty")
        
        invalid_chars = '<>:"/\\|?*'
        if any(char in bundle_name for char in invalid_chars):
            raise ValueError(f"Bundle name contains invalid characters: {invalid_chars}")
        
        return True


class SystemValidator:
    """Validate system requirements and environment"""
    
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
            urllib.request.urlretrieve('https://www.python.org', timeout=5)
            return True, None
        except (urllib.error.URLError, socket.timeout):
            return False, "Internet connection required to download Python embeddable"
        except Exception as e:
            return False, f"Network error: {str(e)}"
import os
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
    
    def validate_project_structure(self, project_path):
        """Validate project has minimum required structure"""
        project_path = Path(project_path)
        warnings = []
        
        # Check for Python files
        python_files = list(project_path.rglob('*.py'))
        if not python_files:
            warnings.append("No Python files found in project directory")
        
        # Check for main entry points
        main_candidates = ['main.py', '__main__.py', f'{project_path.name}.py']
        has_main = any((project_path / candidate).exists() for candidate in main_candidates)
        
        # Check for pyproject.toml
        has_pyproject = (project_path / 'pyproject.toml').exists()
        
        if not has_main and not has_pyproject:
            warnings.append("No main entry point found and no pyproject.toml with entry points")
        
        return warnings
    
    def check_project_dependencies(self, project_path):
        """Check if project has dependency management files"""
        project_path = Path(project_path)
        dependency_files = []
        
        # Check for various dependency management files
        dep_candidates = [
            'pyproject.toml',
            'requirements.txt',
            'setup.py',
            'setup.cfg',
            'Pipfile',
            'poetry.lock'
        ]
        
        for candidate in dep_candidates:
            if (project_path / candidate).exists():
                dependency_files.append(candidate)
        
        return dependency_files


class BundleValidator:
    """Validate bundle creation parameters and environment"""
    
    def __init__(self):
        pass
    
    def validate_bundle_name(self, bundle_name):
        """Validate bundle name is valid for filesystem"""
        if not bundle_name:
            return False, "Bundle name cannot be empty"
        
        if len(bundle_name.strip()) == 0:
            return False, "Bundle name cannot be whitespace only"
        
        # Check for invalid Windows filename characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in bundle_name for char in invalid_chars):
            return False, f"Bundle name contains invalid characters: {invalid_chars}"
        
        # Check for reserved Windows names
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        if bundle_name.upper() in reserved_names:
            return False, f"Bundle name '{bundle_name}' is a reserved Windows name"
        
        # Check length (Windows MAX_PATH is 260, leave room for path)
        if len(bundle_name) > 100:
            return False, "Bundle name is too long (max 100 characters)"
        
        return True, None
    
    def validate_output_directory(self, output_path):
        """Validate output directory is writable"""
        output_path = Path(output_path)
        
        # Check if directory exists
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create output directory: {str(e)}"
        
        # Check write permissions
        if not os.access(output_path, os.W_OK):
            return False, f"No write permission for output directory: {output_path}"
        
        # Test write access
        test_file = output_path / "test_write_access.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            return False, f"Cannot write to output directory: {str(e)}"
        
        return True, None
    
    def validate_python_version(self, python_version):
        """Validate Python version is supported"""
        if python_version not in PyWestConstants.SUPPORTED_PYTHON_VERSIONS:
            return False, f"Unsupported Python version: {python_version}. Supported: {PyWestConstants.SUPPORTED_PYTHON_VERSIONS}"
        
        return True, None
    
    def validate_compression_level(self, compression_level):
        """Validate compression level is in valid range"""
        if not isinstance(compression_level, int):
            return False, "Compression level must be an integer"
        
        if not (0 <= compression_level <= 9):
            return False, "Compression level must be between 0 and 9"
        
        return True, None


class SystemValidator:
    """Validate system requirements and environment"""
    
    def __init__(self):
        pass
    
    def validate_windows_environment(self):
        """Validate running on Windows (required for this tool)"""
        import platform
        
        if platform.system() != 'Windows':
            return False, "PyWest is designed for Windows only"
        
        return True, None
    
    def validate_python_version(self):
        """Validate current Python version meets requirements"""
        import sys
        
        major, minor = sys.version_info[:2]
        
        if major < 3 or (major == 3 and minor < 8):
            return False, f"Python 3.8+ required, currently running Python {major}.{minor}"
        
        return True, None
    
    def check_available_disk_space(self, required_mb=500):
        """Check available disk space"""
        import shutil
        
        try:
            total, used, free = shutil.disk_usage(".")
            free_mb = free // (1024 * 1024)
            
            if free_mb < required_mb:
                return False, f"Insufficient disk space. Required: {required_mb}MB, Available: {free_mb}MB"
            
            return True, None
        except Exception as e:
            return False, f"Cannot check disk space: {str(e)}"
    
    def validate_internet_connection(self):
        """Validate internet connection for downloading Python"""
        import urllib.request
        import socket
        
        try:
            # Try to reach Python.org with a short timeout
            urllib.request.urlopen('https://www.python.org', timeout=5)
            return True, None
        except (urllib.error.URLError, socket.timeout):
            return False, "Internet connection required to download Python embeddable"
        except Exception as e:
            return False, f"Network error: {str(e)}"


class DependencyValidator:
    """Validate dependencies and requirements"""
    
    def __init__(self):
        pass
    
    def validate_required_packages(self):
        """Validate required packages are available"""
        missing_packages = []
        
        # Check for tomllib (Python 3.11+ builtin)
        try:
            import tomllib
        except ImportError:
            missing_packages.append("tomllib")
        
        if missing_packages:
            return False, f"Missing required packages: {', '.join(missing_packages)}"
        
        return True, None
    
    def validate_optional_packages(self):
        """Check optional packages availability"""
        optional_status = {}
        
        # Check py7zr for 7-zip support
        try:
            import py7zr
            optional_status['py7zr'] = True
        except ImportError:
            optional_status['py7zr'] = False
        
        return optional_status
    
    def get_missing_optional_info(self):
        """Get information about missing optional packages"""
        status = self.validate_optional_packages()
        info = []
        
        if not status.get('py7zr', True):
            info.append("Install py7zr for 7-Zip archive support: pip install py7zr")
        
        return info
"""
config.py - Configuration handling and pyproject.toml parsing
"""

import tomllib
from pathlib import Path
from printer import StylePrinter


class ProjectConfig:
    """Handle project configuration from pyproject.toml"""
    
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.printer = StylePrinter()
        self.config_data = None
        self.load_config()
    
    def load_config(self):
        """Load and parse pyproject.toml if it exists"""
        pyproject_path = self.project_path / "pyproject.toml"
        if not pyproject_path.exists():
            self.config_data = None
            return
        
        try:
            with open(pyproject_path, 'rb') as f:
                self.config_data = tomllib.load(f)
        except Exception as e:
            self.printer.warning(f"Could not parse pyproject.toml: {str(e)}")
            self.config_data = None
    
    def has_config(self):
        """Check if configuration was loaded successfully"""
        return self.config_data is not None
    
    def get_entry_point(self):
        """Extract entry point from pyproject.toml"""
        if not self.config_data:
            return None, None
            
        try:
            scripts = self.config_data['project']['scripts']
            if len(scripts) != 1:
                self.printer.warning("Multiple entry points found, using first one")
            
            entry_name, entry_point = next(iter(scripts.items()))
            return entry_name, entry_point
        except KeyError:
            return None, None
    
    def get_dependencies(self):
        """Extract dependencies from pyproject.toml"""
        dependencies = []
        
        if not self.config_data:
            return dependencies
        
        try:
            if 'project' in self.config_data and 'dependencies' in self.config_data['project']:
                dependencies.extend(self.config_data['project']['dependencies'])
        except (KeyError, TypeError):
            pass
        
        return dependencies
    
    def get_project_name(self):
        """Get project name from config or fallback to directory name"""
        if self.config_data:
            try:
                return self.config_data['project']['name']
            except KeyError:
                pass
        
        return self.project_path.name
    
    def get_project_version(self):
        """Get project version from config"""
        if self.config_data:
            try:
                return self.config_data['project']['version']
            except KeyError:
                pass
        
        return "1.0.0"


class BundleConfig:
    """Configuration for bundle creation"""
    
    def __init__(self, python_version=None, compression_level=None):
        from constants import PyWestConstants
        
        self.python_version = python_version or PyWestConstants.DEFAULT_PYTHON_VERSION
        self.compression_level = compression_level or PyWestConstants.DEFAULT_COMPRESSION_LEVEL
        self.python_embed_url = f"{PyWestConstants.PYTHON_BASE_URL}/{self.python_version}/python-{self.python_version}-embed-amd64.zip"
    
    def validate(self):
        """Validate configuration settings"""
        from constants import PyWestConstants
        
        if self.python_version not in PyWestConstants.SUPPORTED_PYTHON_VERSIONS:
            raise ValueError(f"Unsupported Python version: {self.python_version}")
        
        if not (0 <= self.compression_level <= 9):
            raise ValueError(f"Compression level must be between 0-9, got: {self.compression_level}")
        
        return True
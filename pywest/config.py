import tomllib
from pathlib import Path
from .utils import StylePrinter
from .const import PyWestConstants


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
        """Extract entry point from [tool.pywest] in pyproject.toml"""
        if not self.config_data:
            raise ValueError("pyproject.toml not loaded")

        tool_section = self.config_data.get("tool", {})
        pywest_section = tool_section.get("pywest", {})
        entry = pywest_section.get("entry")

        if not entry:
            raise ValueError(
                "Entry point not found in [tool.pywest] section of pyproject.toml. "
                "Define it like:\n\n"
                "[tool.pywest]\nentry = \"src.main:cli\""
            )

        return "pywest-cli", entry
    
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


class BundleConfig:
    """Configuration for bundle creation"""
    
    def __init__(self, python_version=None, compression_level=None):
        self.python_version = python_version or PyWestConstants.DEFAULT_PYTHON_VERSION
        self.compression_level = compression_level or PyWestConstants.DEFAULT_COMPRESSION_LEVEL
        self.python_embed_url = f"{PyWestConstants.PYTHON_BASE_URL}/{self.python_version}/python-{self.python_version}-embed-amd64.zip"
    
    def validate(self):
        """Validate configuration settings"""
        if self.python_version not in PyWestConstants.SUPPORTED_PYTHON_VERSIONS:
            raise ValueError(f"Unsupported Python version: {self.python_version}")
        
        if not (0 <= self.compression_level <= 9):
            raise ValueError(f"Compression level must be between 0-9, got: {self.compression_level}")
        
        return True
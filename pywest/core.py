import shutil
from pathlib import Path
from .config import ProjectConfig, BundleConfig
from .pyth import PythonDownloader
from .env import PythonEnvironment
from .files import ProjectFileManager, BundleDirectoryManager, ProjectValidator
from .genb import RunScriptGenerator, SetupScriptGenerator
from .pack import ArchiveManager
from .utils import StylePrinter, HeaderPrinter

import os
import shutil
from pathlib import Path

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

class ProjectFileManager:
    """Manage project file operations"""
    
    def __init__(self):
        self.exclude_patterns = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    
    def copy_project_files(self, source_path, target_path):
        """Copy project files to target directory, excluding pyproject.toml"""
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        exclude_items = set(self.exclude_patterns)
        exclude_items.add('pyproject.toml')
        
        file_count = 0
        
        try:
            for item in source_path.iterdir():
                if item.name in exclude_items:
                    continue
                
                dest = target_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                    file_count += len(list(item.rglob('*')))
                else:
                    shutil.copy2(item, dest)
                    file_count += 1
            
            return file_count
            
        except Exception as e:
            raise Exception(f"Failed to copy project files: {str(e)}")



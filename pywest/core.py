import shutil
from pathlib import Path
from .config import ProjectConfig, BundleConfig
from .get import PythonDownloader
from .env import PythonEnvironment
from .files import ProjectFileManager, BundleDirectoryManager, ProjectValidator
from .gen import RunScriptGenerator, SetupScriptGenerator
from .pack import ArchiveManager
from .utils import StylePrinter, HeaderPrinter

import os
import shutil
from pathlib import Path

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


class BundleDirectoryManager:
    """Manage bundle directory creation and cleanup"""
    
    def create_bundle_directory(self, output_path, bundle_name):
        """Create bundle directory, handling existing directories"""
        bundle_dir = Path(output_path) / bundle_name
        
        if bundle_dir.exists():
            if not self._confirm_overwrite(bundle_dir):
                return None
            
            self._remove_existing_directory(bundle_dir)
        
        try:
            bundle_dir.mkdir(parents=True)
            return bundle_dir
        except PermissionError as e:
            raise PermissionError(f"Cannot create bundle directory. Check permissions: {str(e)}")
    
    def _confirm_overwrite(self, bundle_dir):
        """Ask user confirmation to overwrite existing directory"""
        print(f"Bundle directory already exists: {bundle_dir}")
        response = input("Overwrite existing bundle? [y/N]: ").strip().lower()
        
        if response not in ('y', 'yes'):
            print("Bundle creation cancelled")
            return False
        
        return True
    
    def _remove_existing_directory(self, bundle_dir):
        """Remove existing bundle directory"""
        try:
            shutil.rmtree(bundle_dir)
        except PermissionError as e:
            raise PermissionError(f"Cannot remove existing bundle directory. Files may be in use: {str(e)}")
    
    def cleanup_on_error(self, bundle_dir):
        """Clean up partial bundle on error"""
        if bundle_dir and Path(bundle_dir).exists():
            try:
                shutil.rmtree(bundle_dir)
            except Exception:
                pass

class ProjectBundler:
    """Main project bundler class"""
    
    def __init__(self, python_version=None, compression_level=None):
        self.bundle_config = BundleConfig(python_version, compression_level)
        self.bundle_config.validate()
        
        # Initialize components
        self.printer = StylePrinter()
        self.header_printer = HeaderPrinter()
        self.python_downloader = PythonDownloader()
        self.file_manager = ProjectFileManager()
        self.bundle_dir_manager = BundleDirectoryManager()
        self.run_script_generator = RunScriptGenerator()
        self.setup_script_generator = SetupScriptGenerator()
        
    def bundle_project(self, project_name, bundle_type='folder', bundle_name=None):
        """Main entry point for project bundling"""
        try:
            # Validate project
            project_path = self._validate_and_prepare_project(project_name)
            
            # Load project configuration
            project_config = ProjectConfig(project_path)
            
            # Create bundle folder first
            bundle_path = self._create_bundle_folder(
                project_path, project_config, bundle_name or f"{project_path.name}_bundle"
            )
            
            if bundle_path is None:
                return None
            
            # Create archive if requested
            if bundle_type == 'zip':
                return self._create_zip_archive(bundle_path, bundle_name)
            
            return bundle_path
            
        except Exception as e:
            self.printer.error(f"Bundle creation failed: {str(e)}")
            raise
    
    def _validate_and_prepare_project(self, project_name):
        """Validate project and return resolved path"""
        validator = ProjectValidator()
        return validator.validate_project_directory(project_name)
    
    def _create_bundle_folder(self, project_path, project_config, bundle_name):
        """Create complete bundle folder"""
        # Print header information
        self.header_printer.print_banner()
        
        dependencies = project_config.get_dependencies()
        self.header_printer.print_project_info(
            project_path.name, 
            project_path.parent / bundle_name,
            len(dependencies)
        )
        
        # Create bundle directory
        bundle_dir = self.bundle_dir_manager.create_bundle_directory(
            project_path.parent, bundle_name
        )
        
        if bundle_dir is None:
            return None
        
        try:
            # Setup Python environment
            self._setup_python_environment(bundle_dir, dependencies)
            
            # Copy project files and pyproject.toml
            self._copy_project_and_config_files(project_path, project_config, bundle_dir)
            
            # Create scripts
            self._create_bundle_scripts(bundle_dir, project_config, project_path.name)
            
            # Print completion info
            self.header_printer.print_completion_info(bundle_dir, "folder")
            
            return bundle_dir
            
        except Exception as e:
            self.bundle_dir_manager.cleanup_on_error(bundle_dir)
            raise Exception(f"Bundle creation failed: {str(e)}")
    
    def _setup_python_environment(self, bundle_dir, dependencies):
        """Setup Python environment with project dependencies"""
        # Download and extract Python
        bin_dir = bundle_dir / "bin"
        self.python_downloader.download_and_extract(
            self.bundle_config.python_version,
            self.bundle_config.python_embed_url,
            bin_dir
        )
        
        # Setup Python environment
        python_env = PythonEnvironment(bin_dir)
        python_env.setup_pip()
        
        # Install project dependencies
        if dependencies:
            python_env.install_dependencies(dependencies)
        
        self.printer.progress("Setting up Python environment...")
        self.printer.progress_done("Python environment ready")
    
    def _copy_project_and_config_files(self, project_path, project_config, bundle_dir):
        """Copy project files and pyproject.toml to bundle"""
        # Copy project files
        self.file_manager.copy_project_files(project_path, bundle_dir)
        
        # Copy pyproject.toml to bin folder if it exists
        pyproject_source = project_path / "pyproject.toml"
        if pyproject_source.exists():
            bin_dir = bundle_dir / "bin"
            bin_dir.mkdir(exist_ok=True)
            pyproject_dest = bin_dir / "pyproject.toml"
            shutil.copy2(pyproject_source, pyproject_dest)
            self.printer.dim("Copied pyproject.toml to bin folder")
    
    def _create_bundle_scripts(self, bundle_dir, project_config, project_name):
        """Create all bundle scripts"""
        # Create run script
        self.printer.progress("Generating launcher...")
        entry_name, entry_point = project_config.get_entry_point()
        self.run_script_generator.create_run_script(bundle_dir, entry_name, entry_point, project_name)
        self.printer.progress_done("Launcher created")
        
        # Create setup script
        self.printer.progress("Creating setup script...")
        self.setup_script_generator.create_simple_setup_script(bundle_dir, project_name)
        self.printer.progress_done("Setup script created")
    
    def _create_zip_archive(self, bundle_path, bundle_name):
        """Create ZIP archive from bundle folder"""
        # Determine archive name
        if bundle_name is None:
            archive_name = f"{bundle_path.name}.zip"
        else:
            archive_name = f"{bundle_name}.zip"
        
        # Create archive
        archive_manager = ArchiveManager(self.bundle_config.compression_level)
        
        try:
            print()  # Add spacing before archive creation
            archive_path = archive_manager.create_zip_archive(
                bundle_path, bundle_path.parent, archive_name
            )
            
            # Print completion info
            archive_size = archive_path.stat().st_size
            self.header_printer.print_completion_info(
                archive_path, "zip", archive_size, self.bundle_config.compression_level
            )
            
            return archive_path
            
        except Exception as e:
            raise Exception(f"ZIP creation failed: {str(e)}")


class BundlerWorkflow:
    """Manage different bundler workflows"""
    
    def __init__(self, bundler):
        self.bundler = bundler
        self.printer = StylePrinter()
    
    def create_folder_bundle(self, project_name, bundle_name=None):
        """Create folder bundle workflow"""
        return self.bundler.bundle_project(project_name, 'folder', bundle_name)
    
    def create_zip_bundle(self, project_name, bundle_name=None):
        """Create ZIP bundle workflow"""
        return self.bundler.bundle_project(project_name, 'zip', bundle_name)
import shutil
from pathlib import Path
from .config import ProjectConfig, BundleConfig
from .dl import PythonDownloader
from .env import PythonEnvironment
from .files import ProjectFileManager, BundleDirectoryManager, ProjectValidator
from .gen import RunScriptGenerator, SetupScriptGenerator
from .pack import ArchiveManager
from .ui import StylePrinter, HeaderPrinter


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
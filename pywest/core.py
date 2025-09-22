import py7zr
from pathlib import Path
from .config import ProjectConfig, BundleConfig
from .dl import PythonDownloader
from .env import PythonEnvironment, DependencyInstaller
from .files import ProjectFileManager, BundleDirectoryManager
from .run import RunScriptGenerator, SetupScriptGenerator
from .inst import InstallerGUIGenerator
from .pack import ArchiveManager, ArchiveInfoProvider
from .ui import StylePrinter, HeaderPrinter
from .valid import ProjectValidator, BundleValidator


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
        self.installer_generator = InstallerGUIGenerator()
        
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
            if bundle_type in ['zip', '7zip']:
                return self._create_archive_from_bundle(bundle_path, bundle_type, bundle_name)
            
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
            
            # Copy project files (excluding icon since it's handled separately)
            icon_path = project_config.get_icon_path()
            self.file_manager.copy_project_files(
                project_path, bundle_dir, exclude_pyproject=True, icon_path=icon_path
            )
            
            # Create scripts and handle icon conversion
            self._create_bundle_scripts(bundle_dir, project_config, project_path.name)
            
            # Print completion info
            self.header_printer.print_completion_info(bundle_dir, "folder")
            
            return bundle_dir
            
        except Exception as e:
            self.bundle_dir_manager.cleanup_on_error(bundle_dir)
            raise Exception(f"Bundle creation failed: {str(e)}")
    
    def _setup_python_environment(self, bundle_dir, dependencies):
        """Setup Python environment with dependencies"""
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
        
        # Install dependencies
        dependency_installer = DependencyInstaller(python_env)
        dependency_installer.install_all_dependencies(dependencies)
        
        self.printer.progress("Setting up Python environment...")
        self.printer.progress_done("Python environment ready")
    
    def _create_bundle_scripts(self, bundle_dir, project_config, project_name):
        """Create all bundle scripts"""
        # Convert and copy icon to bin folder
        project_config.convert_and_copy_icon(bundle_dir)
        
        # Create run script
        self.printer.progress("Generating launcher...")
        entry_name, entry_point = project_config.get_entry_point()
        self.run_script_generator.create_run_script(bundle_dir, entry_name, entry_point, project_name)
        self.printer.progress_done("Launcher created")
        
        # Create setup script
        self.printer.progress("Creating installer...")
        self.setup_script_generator.create_setup_script(bundle_dir, project_name)
        self.installer_generator.create_installer_script(bundle_dir, project_name)
        self.printer.progress_done("Installer created")
    
    def _create_archive_from_bundle(self, bundle_path, bundle_type, bundle_name):
        """Create archive from bundle folder"""
        # Determine archive name
        if bundle_name is None:
            archive_name = f"{bundle_path.name}"
        else:
            archive_name = bundle_name
        
        # Create archive
        archive_manager = ArchiveManager(self.bundle_config.compression_level)
        
        try:
            print()  # Add spacing before archive creation
            archive_path = archive_manager.create_archive(
                bundle_path, bundle_path.parent, archive_name, bundle_type
            )
            
            # Print completion info
            ArchiveInfoProvider.print_archive_completion(archive_path, self.bundle_config.compression_level)
            
            return archive_path
            
        except Exception as e:
            raise Exception(f"Archive creation failed: {str(e)}")


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
    
    def create_7zip_bundle(self, project_name, bundle_name=None):
        """Create 7-Zip bundle workflow"""
        return self.bundler.bundle_project(project_name, '7zip', bundle_name)
    
    def get_supported_formats(self):
        """Get list of supported bundle formats"""
        return ['folder', 'zip', '7zip']


class BundlerStatus:
    """Track bundler operation status"""
    
    def __init__(self):
        self.current_operation = None
        self.progress_percentage = 0
        self.errors = []
        self.warnings = []
    
    def set_operation(self, operation_name):
        """Set current operation"""
        self.current_operation = operation_name
        self.progress_percentage = 0
    
    def update_progress(self, percentage):
        """Update progress percentage"""
        self.progress_percentage = max(0, min(100, percentage))
    
    def add_error(self, error_message):
        """Add error message"""
        self.errors.append(error_message)
    
    def add_warning(self, warning_message):
        """Add warning message"""
        self.warnings.append(warning_message)
    
    def has_errors(self):
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self):
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def get_summary(self):
        """Get operation summary"""
        return {
            'operation': self.current_operation,
            'progress': self.progress_percentage,
            'errors': self.errors,
            'warnings': self.warnings,
            'success': not self.has_errors()
        }
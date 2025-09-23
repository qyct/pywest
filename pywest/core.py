import os
import re
import shutil
import zipfile
import tomllib
from pathlib import Path
from .utils import StylePrinter, PythonManager
from .genb import ScriptGenerator

class ProjectBundler:
    """Main project bundler class"""
    
    DEFAULT_COMPRESSION = 6
    EXCLUDE_PATTERNS = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    
    def __init__(self, python_version=None, compression_level=None):
        self.python_version = python_version or PythonManager.DEFAULT_VERSION
        self.compression_level = compression_level or self.DEFAULT_COMPRESSION
        
        # Validate settings
        if self.python_version not in PythonManager.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported Python version: {self.python_version}")
        if not (0 <= self.compression_level <= 9):
            raise ValueError(f"Compression level must be between 0-9, got: {self.compression_level}")
        
        # Initialize components
        self.printer = StylePrinter()
        self.python_manager = PythonManager()
        self.script_generator = ScriptGenerator()

    def _sanitize_bundle_name(self, name: str) -> str:
        # Lowercase
        name = name.lower()
        # Replace any non-alphanumeric with underscore
        name = re.sub(r'[^a-z0-9]', '_', name)
        # Collapse multiple underscores
        name = re.sub(r'_+', '_', name)
        # Strip leading/trailing underscores
        name = name.strip('_')
        return name
    
    def bundle_project(self, project_name, bundle_type='folder', bundle_name=None):
        """Main entry point for project bundling"""
        try:
            # Validate project
            project_path = self._validate_project(project_name)
            
            # Load project configuration
            config = self._load_project_config(project_path)

            # Sanitize bundle name
            bundle_name = self._sanitize_bundle_name(bundle_name or f"{project_path.name}_bundle")
            
            # Create bundle
            bundle_path = self._create_bundle(project_path, config, bundle_name)
            
            if bundle_path is None:
                return None
            
            # Create archive if requested
            if bundle_type == 'zip':
                return self._create_zip_archive(bundle_path, bundle_name)
            
            return bundle_path
            
        except Exception as e:
            self.printer.error(f"Bundle creation failed: {str(e)}")
            raise
    
    def _validate_project(self, project_path):
        """Validate project directory exists and is accessible"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' not found")
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_path}' is not a directory")
        if not os.access(project_path, os.R_OK):
            raise PermissionError(f"No read permission for project directory: {project_path}")
        
        return project_path
    
    def _load_project_config(self, project_path):
        """Load and parse pyproject.toml if it exists"""
        pyproject_path = project_path / "pyproject.toml"
        config = {'dependencies': [], 'entry_point': None, 'name': project_path.name}
        
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found '{project_path}'")
        
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        
        # Get dependencies
        if 'project' in data and 'dependencies' in data['project']:
            config['dependencies'] = data['project']['dependencies']
        
        # Get entry point
        if 'tool' in data and 'pywest' in data['tool'] and 'entry' in data['tool']['pywest']:
            config['entry_point'] = data['tool']['pywest']['entry']
        else:
            raise ValueError("Missing required 'entry' field in [tool.pywest] section of pyproject.toml")
        
        # Get optional icon
        if 'tool' in data and 'pywest' in data['tool'] and 'icon' in data['tool']['pywest']:
            config['icon'] = data['tool']['pywest']['icon']
        
        # Get project name
        if 'project' in data and 'name' in data['project']:
            config['name'] = data['project']['name']
        
        return config
    
    def _create_bundle(self, project_path, config, bundle_name):
        """Create complete bundle folder"""
        # Print header
        self.printer.print_banner()
        self.printer.print_project_info(
            config['name'], 
            project_path.parent / bundle_name,
            len(config['dependencies'])
        )
        
        # Create bundle directory
        bundle_dir = self._create_bundle_directory(project_path.parent, bundle_name)
        if bundle_dir is None:
            return None
        
        try:
            # Setup Python environment
            bin_dir = bundle_dir / "bin"
            self.python_manager.setup_environment(
                self.python_version, bin_dir, config['dependencies']
            )
            
            # Copy project files
            self._copy_project_files(project_path, bundle_dir)
            
            # Copy pyproject.toml to bin folder
            pyproject_source = project_path / "pyproject.toml"
            pyproject_dest = bin_dir / "pyproject.toml"
            shutil.copy2(pyproject_source, pyproject_dest)

            # Copy icon to bin folder if it exists
            if "icon" in config and config["icon"]:
                icon_source = project_path / config["icon"]
                icon_dest = bin_dir / Path(config["icon"]).name
                
                if icon_source.exists():
                    shutil.copy2(icon_source, icon_dest)
                else:
                    raise FileNotFoundError(f"Icon file '{icon_source}' not found")
            
            # Create scripts
            self.script_generator.create_run_script(bundle_dir, config['entry_point'], config['name'])
            self.script_generator.create_setup_script(bundle_dir, config['name'])
            
            # Print completion info
            self.printer.print_completion_info(bundle_dir, "folder")
            
            return bundle_dir
            
        except Exception as e:
            self._cleanup_bundle(bundle_dir)
            raise Exception(f"Bundle creation failed: {str(e)}")
    
    def _create_bundle_directory(self, output_path, bundle_name):
        """Create bundle directory, handling existing directories"""
        bundle_dir = Path(output_path) / bundle_name
        
        if bundle_dir.exists():
            print(f"Bundle directory already exists: {bundle_dir}")
            response = input("Overwrite existing bundle? [y/N]: ").strip().lower()
            
            if response not in ('y', 'yes'):
                print("Bundle creation cancelled")
                return None
            
            try:
                shutil.rmtree(bundle_dir)
            except PermissionError as e:
                raise PermissionError(f"Cannot remove existing bundle directory. Files may be in use: {str(e)}")
        
        try:
            bundle_dir.mkdir(parents=True)
            return bundle_dir
        except PermissionError as e:
            raise PermissionError(f"Cannot create bundle directory. Check permissions: {str(e)}")
    
    def _copy_project_files(self, source_path, target_path):
        """Copy project files to target directory, excluding certain patterns"""
        exclude_items = set(self.EXCLUDE_PATTERNS)
        exclude_items.add('pyproject.toml')
        
        try:
            for item in source_path.iterdir():
                if item.name in exclude_items:
                    continue
                
                dest = target_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                else:
                    shutil.copy2(item, dest)
                    
        except Exception as e:
            raise Exception(f"Failed to copy project files: {str(e)}")
    
    def _create_zip_archive(self, bundle_path, bundle_name):
        """Create ZIP archive from bundle folder"""
        if bundle_name is None:
            archive_name = f"{bundle_path.name}.zip"
        else:
            archive_name = f"{bundle_name}.zip"
        
        archive_path = bundle_path.parent / archive_name
        
        if archive_path.exists():
            raise ValueError(f"ZIP file already exists: {archive_path}")
        
        try:
            compression_method, compress_level = self._get_zip_compression()
            
            with zipfile.ZipFile(archive_path, 'w', compression_method, compresslevel=compress_level) as zipf:
                for file_path in bundle_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(bundle_path.parent)
                        zipf.write(file_path, arcname)
            
            # Remove bundle directory after successful archive creation
            shutil.rmtree(bundle_path)
            
            # Print completion info
            archive_size = archive_path.stat().st_size
            self.printer.print_completion_info(
                archive_path, "zip", archive_size, self.compression_level
            )
            
            return archive_path
            
        except Exception as e:
            if archive_path.exists():
                archive_path.unlink()
            raise Exception(f"ZIP creation failed: {str(e)}")
    
    def _get_zip_compression(self):
        """Convert compression level to zipfile settings"""
        if self.compression_level == 0:
            return zipfile.ZIP_STORED, None
        elif self.compression_level <= 3:
            return zipfile.ZIP_DEFLATED, self.compression_level + 3
        elif self.compression_level <= 6:
            return zipfile.ZIP_DEFLATED, 6
        else:
            return zipfile.ZIP_DEFLATED, 9
    
    def _cleanup_bundle(self, bundle_dir):
        """Clean up partial bundle on error"""
        if bundle_dir and Path(bundle_dir).exists():
            try:
                shutil.rmtree(bundle_dir)
            except Exception:
                pass
import os
import re
import shutil
import zipfile
import tomllib
from pathlib import Path
from .utils import StylePrinter, PythonManager
from .gens import ScriptGenerator
from .icon import DEFAULT_ICON_BASE64

# Import Pillow for image conversion (required dependency)
from PIL import Image
import base64
import io

class ProjectBundler:
    """Main project bundler class"""
    
    DEFAULT_COMPRESSION = 6
    EXCLUDE_PATTERNS = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}
    ICON_SIZE = (256, 256)  # Standard icon size
    
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
    
    def _resize_image_to_icon(self, image_path, output_path):
        """Resize and convert image to 256x256 ICO format using Pillow"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGBA if necessary (ICO format supports transparency)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize to exactly 256x256
                resized_img = img.resize(self.ICON_SIZE, Image.Resampling.LANCZOS)
                
                # Save as ICO with 256x256 size
                resized_img.save(output_path, format='ICO', sizes=[self.ICON_SIZE])
                
        except Exception as e:
            raise Exception(f"Failed to convert image to 256x256 ICO format: {str(e)}")
    
    def _generate_default_icon_256x256(self, output_path):
        """Generate 256x256 default icon from base64 constant"""
        try:
            # Decode base64 icon data
            icon_data = base64.b64decode(DEFAULT_ICON_BASE64)
            
            # Load the base64 icon as an image and resize to 256x256
            with Image.open(io.BytesIO(icon_data)) as img:
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize to 256x256
                resized_img = img.resize(self.ICON_SIZE, Image.Resampling.LANCZOS)
                
                # Save as ICO
                resized_img.save(output_path, format='ICO', sizes=[self.ICON_SIZE])
                
        except Exception as e:
            # Fallback: create a simple colored 256x256 icon
            try:
                # Create a simple default icon (blue square with white border)
                img = Image.new('RGBA', self.ICON_SIZE, (70, 130, 180, 255))  # Steel blue
                # Add white border
                for i in range(8):  # 8-pixel border
                    # Top and bottom borders
                    for x in range(self.ICON_SIZE[0]):
                        img.putpixel((x, i), (255, 255, 255, 255))
                        img.putpixel((x, self.ICON_SIZE[1] - 1 - i), (255, 255, 255, 255))
                    # Left and right borders
                    for y in range(self.ICON_SIZE[1]):
                        img.putpixel((i, y), (255, 255, 255, 255))
                        img.putpixel((self.ICON_SIZE[0] - 1 - i, y), (255, 255, 255, 255))
                
                img.save(output_path, format='ICO', sizes=[self.ICON_SIZE])
                
            except Exception as fallback_e:
                raise Exception(f"Failed to generate default 256x256 icon: {str(e)}, fallback error: {str(fallback_e)}")
    
    def _validate_project_config(self, project_path):
        """Validate project configuration early - check for entry point, project name, and icon"""
        pyproject_path = project_path / "pyproject.toml"
        
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found in '{project_path}'")
        
        # Load and validate configuration
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        
        # Check for required entry point
        if not ('tool' in data and 'pywest' in data['tool'] and 'entry' in data['tool']['pywest']):
            raise ValueError(
                "Missing required 'entry' field in [tool.pywest] section of pyproject.toml.\n"
                "Please add: [tool.pywest]\nentry = \"module.name:function_name\""
            )
        
        entry_point = data['tool']['pywest']['entry']
        if ':' not in entry_point:
            raise ValueError(
                f"Invalid entry point format: '{entry_point}'. "
                "Expected format: 'module.name:function_name'"
            )
        
        # Check for required project name
        if not ('project' in data and 'name' in data['project']):
            raise ValueError(
                "Missing required 'name' field in [project] section of pyproject.toml.\n"
                "Please add: [project]\nname = \"your-project-name\""
            )
        
        project_name = data['project']['name']
        if not project_name or not project_name.strip():
            raise ValueError(
                "Project name cannot be empty. Please provide a valid project name in pyproject.toml"
            )
        
        # Validate icon if specified
        icon_path = None
        if 'tool' in data and 'pywest' in data['tool'] and 'icon' in data['tool']['pywest']:
            icon_path = data['tool']['pywest']['icon']
            if icon_path:  # Only validate if not empty
                icon_source = project_path / icon_path
                
                if not icon_source.exists():
                    raise FileNotFoundError(f"Icon file '{icon_source}' not found")
                
                # Check if it's a supported format
                source_ext = icon_source.suffix.lower()
                if source_ext not in self.SUPPORTED_IMAGE_FORMATS and source_ext != '.ico':
                    raise ValueError(
                        f"Unsupported icon format '{source_ext}'. "
                        f"Supported formats: {', '.join(self.SUPPORTED_IMAGE_FORMATS)} and .ico"
                    )
        
        return {
            'entry_point': entry_point,
            'project_name': project_name.strip(),
            'icon_path': icon_path,
            'data': data  # Return full data for later use
        }
    
    def bundle_project(self, project_name, bundle_type='folder', bundle_name=None):
        """Main entry point for project bundling"""
        try:
            # Validate project directory first
            project_path = self._validate_project(project_name)
            
            # Validate configuration early (entry point and icon)
            config_validation = self._validate_project_config(project_path)
            
            # Load full project configuration
            config = self._load_project_config(project_path, config_validation['data'])

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
    
    def _load_project_config(self, project_path, toml_data):
        """Load project configuration from already validated toml data"""
        
        
        config = {
            'dependencies': [], 
            'entry_point': toml_data['tool']['pywest']['entry'],
            'name': project_path.name
        }
        
        # Get dependencies
        if 'project' in toml_data and 'dependencies' in toml_data['project']:
            config['dependencies'] = toml_data['project']['dependencies']
        
        # Get optional icon
        if 'tool' in toml_data and 'pywest' in toml_data['tool'] and 'icon' in toml_data['tool']['pywest']:
            config['icon'] = toml_data['tool']['pywest']['icon']
        
        # Get project name
        if 'project' in toml_data and 'name' in toml_data['project']:
            config['name'] = toml_data['project']['name']
        
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
        
        config['dependencies'].append("pyweste")

        try:
            # Setup Python environment
            bin_dir = bundle_dir / "bin"
            self.python_manager.setup_environment(
                self.python_version, bin_dir, config['dependencies']
            )
            
            # Copy project files (excluding icon to prevent duplication)
            self._copy_project_files(project_path, bundle_dir, config.get('icon'))
            
            # Copy pyproject.toml to bin folder
            pyproject_source = project_path / "pyproject.toml"
            pyproject_dest = bin_dir / "pyproject.toml"
            shutil.copy2(pyproject_source, pyproject_dest)

            # Handle icon - always create 256x256 icon.ico in bin folder
            icon_dest = bin_dir / "icon.ico"
            self._process_icon(project_path, config, icon_dest)
            
            # Create scripts
            self.script_generator.create_run_script(bundle_dir, config['entry_point'], config['name'])
            self.script_generator.create_setup_script(bundle_dir, config['name'])
            
            # Print completion info
            self.printer.print_completion_info(bundle_dir, "folder")
            
            return bundle_dir
            
        except Exception as e:
            self._cleanup_bundle(bundle_dir)
            raise Exception(f"Bundle creation failed: {str(e)}")
    
    def _process_icon(self, project_path, config, icon_dest):
        """Process icon - either from config or generate default, always 256x256"""
        if "icon" in config and config["icon"]:
            # User specified an icon
            icon_source = project_path / config["icon"]
            source_ext = icon_source.suffix.lower()
            
            if source_ext == '.ico':
                # Already ICO format, resize to 256x256
                self.printer.step(f"Resizing ICO file {icon_source.name} to 256x256...")
                self._resize_image_to_icon(icon_source, icon_dest)
                self.printer.success(f"Icon resized and saved as 256x256 icon.ico")
                
            elif source_ext in self.SUPPORTED_IMAGE_FORMATS:
                # Convert to 256x256 ICO format
                try:
                    self.printer.step(f"Converting {icon_source.name} to 256x256 ICO format...")
                    self._resize_image_to_icon(icon_source, icon_dest)
                    self.printer.success(f"Icon converted and saved as 256x256 icon.ico")
                    
                except Exception as e:
                    self.printer.warning(f"Failed to convert icon: {str(e)}")
                    # Generate default icon as fallback
                    self.printer.step("Generating default 256x256 icon...")
                    self._generate_default_icon_256x256(icon_dest)
                    self.printer.info("Default 256x256 icon generated")
            else:
                # This shouldn't happen due to early validation, but keep as safety
                self.printer.warning(f"Unsupported icon format '{source_ext}'")
                self.printer.step("Generating default 256x256 icon...")
                self._generate_default_icon_256x256(icon_dest)
                self.printer.info("Default 256x256 icon generated")
        else:
            # No icon specified, generate default 256x256
            self.printer.step("No icon specified, generating default 256x256 icon...")
            self._generate_default_icon_256x256(icon_dest)
            self.printer.success("Default 256x256 icon generated")
    
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
    
    def _copy_project_files(self, source_path, target_path, icon_path=None):
        """Copy project files to target directory, excluding certain patterns and icon file"""
        exclude_items = set(self.EXCLUDE_PATTERNS)
        exclude_items.add('pyproject.toml')
        
        # Add icon file to exclude list if it exists to prevent duplication
        if icon_path:
            exclude_items.add(icon_path)
            # Also exclude just the filename in case it's in the root
            exclude_items.add(Path(icon_path).name)
        
        try:
            for item in source_path.iterdir():
                if item.name in exclude_items:
                    continue
                
                # Check if this item matches the icon path (for relative paths)
                if icon_path and str(item.relative_to(source_path)) == icon_path:
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
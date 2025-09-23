import tomllib
from pathlib import Path
from PIL import Image, ImageDraw
from .ui import StylePrinter
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
    
    def get_icon_path(self):
        """Get icon path from pyproject.toml, supporting common image formats"""
        if not self.config_data:
            return None
            
        try:
            icon_filename = self.config_data['project'].get('icon')
            if icon_filename:
                # Support common image formats
                supported_formats = {'.png', '.ico', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
                icon_ext = Path(icon_filename).suffix.lower()
                
                if icon_ext in supported_formats:
                    icon_path = self.project_path / icon_filename
                    if icon_path.exists():
                        return icon_path
                    else:
                        self.printer.warning(f"Icon file specified in pyproject.toml not found: {icon_filename}")
                else:
                    self.printer.warning(f"Unsupported icon format: {icon_ext}. Supported formats: {', '.join(supported_formats)}")
        except (KeyError, TypeError):
            pass
        
        return None
    
    def _create_default_icon(self):
        """Create a default icon when no icon is specified"""
        try:
            # Create a simple default icon - 128x128 blue square with "Py" text
            img = Image.new('RGBA', (128, 128), (70, 130, 180, 255))  # Steel blue
            draw = ImageDraw.Draw(img)
            
            # Try to use a built-in font, fallback to default if not available
            try:
                from PIL import ImageFont
                # Try to get a reasonable font size
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw "Py" text in white
            text = "Py"
            if font:
                # Get text bounding box to center it
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (128 - text_width) // 2
                y = (128 - text_height) // 2
                draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
            else:
                # Fallback without font
                draw.text((45, 55), text, fill=(255, 255, 255, 255))
            
            return img
        except Exception as e:
            self.printer.warning(f"Failed to create default icon: {str(e)}")
            return None
    
    def convert_and_copy_icon(self, bundle_dir):
        """Convert icon to ICO format and copy to bin folder, or create default icon"""
        icon_path = self.get_icon_path()
        bin_dir = Path(bundle_dir) / "bin"
        bin_dir.mkdir(exist_ok=True)
        ico_path = bin_dir / "icon.ico"
        
        try:
            if icon_path:
                # Use specified icon
                with Image.open(icon_path) as img:
                    # Convert to RGBA if not already
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # Create multiple sizes for better ICO support
                    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                    
                    if icon_path.suffix.lower() == '.ico':
                        # If already ICO, just copy it
                        import shutil
                        shutil.copy2(icon_path, ico_path)
                    else:
                        # Convert to ICO with multiple sizes
                        img.save(ico_path, format='ICO', sizes=sizes)
                    
                    self.printer.dim(f"Icon converted and copied to bin/icon.ico")
            else:
                # Create and use default icon
                default_img = self._create_default_icon()
                if default_img:
                    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                    default_img.save(ico_path, format='ICO', sizes=sizes)
                    self.printer.dim("Default icon created and copied to bin/icon.ico")
                else:
                    self.printer.warning("Could not create default icon")
                    return None
            
            return ico_path
                
        except Exception as e:
            self.printer.warning(f"Failed to handle icon: {str(e)}")
            return None


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
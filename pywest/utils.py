class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

class StylePrinter:
    """Stylized output printer with color support"""
    
    @staticmethod
    def info(message, prefix="ℹ"):
        """Print informational message"""
        print(Colors.BRIGHT_BLUE + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def success(message, prefix="✓"):
        """Print success message"""
        print(Colors.BRIGHT_GREEN + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def warning(message, prefix="⚠ "):
        """Print warning message"""
        print(Colors.BRIGHT_YELLOW + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def error(message, prefix="✗"):
        """Print error message"""
        print(Colors.BRIGHT_RED + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def step(message, prefix="→"):
        """Print step message"""
        print(Colors.BRIGHT_CYAN + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def dim(message):
        """Print dimmed message"""
        print(Colors.DIM + message + Colors.RESET)
    
    _last_progress_length = 0
    
    @staticmethod
    def progress(message, prefix="◯"):
        """Print progress message (no newline)"""
        full_message = Colors.YELLOW + prefix + Colors.RESET + " " + message
        # Store the visible length (excluding ANSI codes)
        StylePrinter._last_progress_length = len(prefix + " " + message)
        print(full_message, end="", flush=True)
    
    @staticmethod
    def progress_done(message="Done"):
        """Print completion message, clearing the progress line"""
        # Clear exactly the length of the last progress message
        clear_length = max(StylePrinter._last_progress_length, len("✓ " + message))
        print("\r" + " " * clear_length + "\r" + Colors.BRIGHT_GREEN + "✓" + Colors.RESET + " " + message)


class HeaderPrinter:
    """Print formatted headers and banners"""
    
    @staticmethod
    def print_banner(title="PyWest Bundler"):
        """Print application banner"""
        print("\n" + Colors.BOLD + Colors.BRIGHT_CYAN + "🚀 " + title + Colors.RESET)
        print(Colors.DIM + "─" * 50 + Colors.RESET)

    @staticmethod
    def print_project_info(project_name, output_path, dependency_count=0):
        """Print project information summary"""
        print("Project: " + project_name)
        print("Output: " + str(output_path))
        if dependency_count > 0:
            print("Dependencies: " + str(dependency_count))
        print("")

    @staticmethod
    def print_completion_info(bundle_path, bundle_type="folder", file_size=None, compression_level=None):
        """Print bundle completion information"""
        print(Colors.BRIGHT_GREEN + "✅ Bundle created successfully!" + Colors.RESET)
        print("   Location: " + str(bundle_path))
        
        if bundle_type == "folder":
            print("   Run with: " + str(bundle_path / 'run.bat'))
            print("   Install with: " + str(bundle_path / 'setup.bat'))
        else:
            if file_size:
                print(f"   Size: {file_size / (1024*1024):.1f} MB")
            if compression_level is not None:
                print(f"   Compression level: {compression_level}")

import zipfile
import shutil
from pathlib import Path


class ArchiveManager:
    """Manage ZIP archive creation"""
    
    def __init__(self, compression_level=6):
        self.compression_level = compression_level
    
    def create_zip_archive(self, bundle_dir, output_path, archive_name):
        """Create ZIP archive from bundle directory"""
        archive_path = Path(output_path) / archive_name
        
        if archive_path.exists():
            raise ValueError(f"ZIP file already exists: {archive_path}")
        
        if not (0 <= self.compression_level <= 9):
            raise ValueError(f"Invalid compression level: {self.compression_level}")
        
        try:
            compression_method, compress_level = self._get_zip_compression_settings()
            
            with zipfile.ZipFile(archive_path, 'w', compression_method, compresslevel=compress_level) as zipf:
                self._add_directory_to_zip(zipf, bundle_dir)
            
            # Remove the bundle directory after successful archive creation
            shutil.rmtree(bundle_dir)
            
            return archive_path
            
        except Exception as e:
            if archive_path.exists():
                archive_path.unlink()
            raise Exception(f"Failed to create ZIP archive: {str(e)}")
    
    def _get_zip_compression_settings(self):
        """Convert compression level (0-9) to zipfile settings"""
        if self.compression_level == 0:
            return zipfile.ZIP_STORED, None
        elif self.compression_level <= 3:
            return zipfile.ZIP_DEFLATED, self.compression_level + 3
        elif self.compression_level <= 6:
            return zipfile.ZIP_DEFLATED, 6
        else:
            return zipfile.ZIP_DEFLATED, 9
    
    def _add_directory_to_zip(self, zipf, source_dir):
        """Add directory contents to ZIP file"""
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)
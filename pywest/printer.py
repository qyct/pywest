"""
printer.py - Stylized output printing functionality
"""

from .constants import Colors


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
    
    @staticmethod
    def progress(message, prefix="◐"):
        """Print progress message (no newline)"""
        print(Colors.YELLOW + prefix + Colors.RESET + " " + message, end="", flush=True)
    
    @staticmethod
    def progress_done(message="Done"):
        """Print completion message, clearing the progress line"""
        print("\r" + " " * 80, end="")
        print("\r" + Colors.BRIGHT_GREEN + "✓" + Colors.RESET + " " + message)


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
        print("ℹ Project: " + project_name)
        print("ℹ Output: " + str(output_path))
        if dependency_count > 0:
            print("ℹ Dependencies: " + str(dependency_count))
        print()

    @staticmethod
    def print_completion_info(bundle_path, bundle_type="folder", file_size=None, compression_level=None):
        """Print bundle completion information"""
        print("\n" + Colors.BRIGHT_GREEN + "✅ Bundle created successfully!" + Colors.RESET)
        print("   Location: " + str(bundle_path))
        
        if bundle_type == "folder":
            print("   Run with: " + str(bundle_path / 'run.bat'))
            print("   Install with: " + str(bundle_path / 'setup.bat'))
        else:
            if file_size:
                print(f"   Size: {file_size / (1024*1024):.1f} MB")
            if compression_level is not None:
                print(f"   Compression level: {compression_level}")
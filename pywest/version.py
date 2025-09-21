"""
version.py - Version information and package metadata
"""

import sys
from pathlib import Path
from constants import PyWestConstants


class VersionInfo:
    """PyWest version and build information"""
    
    VERSION = "1.0.0"
    BUILD_DATE = "2024"
    AUTHOR = "PyWest Development Team"
    DESCRIPTION = "Python Project Bundler for Windows"
    
    PYTHON_MIN_VERSION = (3, 8)
    SUPPORTED_PLATFORMS = ["Windows"]
    
    @classmethod
    def get_version_string(cls):
        """Get formatted version string"""
        return f"PyWest {cls.VERSION}"
    
    @classmethod
    def get_full_version_info(cls):
        """Get complete version information"""
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        return {
            'version': cls.VERSION,
            'build_date': cls.BUILD_DATE,
            'author': cls.AUTHOR,
            'description': cls.DESCRIPTION,
            'python_version': python_version,
            'platform': sys.platform,
            'supported_platforms': cls.SUPPORTED_PLATFORMS
        }
    
    @classmethod
    def print_version_banner(cls):
        """Print version banner"""
        from constants import Colors
        
        print(f"{Colors.BOLD}{Colors.BRIGHT_CYAN}PyWest {cls.VERSION}{Colors.RESET}")
        print(f"{Colors.DIM}{cls.DESCRIPTION}{Colors.RESET}")
        print(f"{Colors.DIM}Running on Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}{Colors.RESET}")
        print()


class FeatureInfo:
    """Information about PyWest features and capabilities"""
    
    SUPPORTED_BUNDLE_TYPES = ["folder", "zip"]
    SUPPORTED_PYTHON_VERSIONS = PyWestConstants.SUPPORTED_PYTHON_VERSIONS
    SUPPORTED_ARCHIVE_FORMATS = ["ZIP"]
    
    @classmethod
    def get_feature_list(cls):
        """Get list of available features"""
        features = [
            "Bundle Python projects with embeddable Python",
            "Support for pyproject.toml configuration",
            "Automatic dependency installation",
            "GUI installer with shortcuts and registry entries",
            "ZIP archive creation",
            "Multiple Python version support",
            "Portable bundle creation"
        ]
        
        # Add 7-Zip support if available
        try:
            import py7zr
            features.append("7-Zip archive creation (py7zr available)")
            cls.SUPPORTED_ARCHIVE_FORMATS.append("7Z")
            if "7zip" not in cls.SUPPORTED_BUNDLE_TYPES:
                cls.SUPPORTED_BUNDLE_TYPES.append("7zip")
        except ImportError:
            features.append("7-Zip archive creation (install py7zr)")
        
        return features
    
    @classmethod
    def print_feature_summary(cls):
        """Print feature summary"""
        from constants import Colors
        
        features = cls.get_feature_list()
        
        print(f"{Colors.BOLD}Features:{Colors.RESET}")
        for feature in features:
            print(f"  • {feature}")
        print()


class SystemInfo:
    """System and environment information"""
    
    @staticmethod
    def get_system_info():
        """Get current system information"""
        import platform
        import os
        
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'python_executable': sys.executable,
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'user_home': str(Path.home()),
            'pywest_cache': str(Path.home() / PyWestConstants.CACHE_DIR_NAME)
        }
    
    @staticmethod
    def print_system_info():
        """Print system information"""
        from constants import Colors
        
        info = SystemInfo.get_system_info()
        
        print(f"{Colors.BOLD}System Information:{Colors.RESET}")
        print(f"  Platform: {info['platform']} {info['architecture']}")
        print(f"  Python: {info['python_version'].split()[0]}")
        print(f"  Cache Directory: {info['pywest_cache']}")
        print()


class PackageInfo:
    """Package and dependency information"""
    
    CORE_DEPENDENCIES = ["tomllib (Python 3.11+)"]
    OPTIONAL_DEPENDENCIES = [
        "py7zr (7-Zip archive support)",
        "dearpygui (GUI installer - bundled)",
        "pywin32 (Windows integration - bundled)"
    ]
    
    @classmethod
    def get_dependency_status(cls):
        """Get status of all dependencies"""
        status = {}
        
        # Check core dependencies
        try:
            import tomllib
            status['tomllib'] = True
        except ImportError:
            status['tomllib'] = False
        
        # Check optional dependencies
        try:
            import py7zr
            status['py7zr'] = True
        except ImportError:
            status['py7zr'] = False
        
        return status
    
    @classmethod
    def print_dependency_status(cls):
        """Print dependency status"""
        from constants import Colors
        
        status = cls.get_dependency_status()
        
        print(f"{Colors.BOLD}Dependencies:{Colors.RESET}")
        
        # Core dependencies
        print("  Core:")
        for dep in cls.CORE_DEPENDENCIES:
            name = dep.split()[0]
            if status.get(name.lower(), True):
                print(f"    {Colors.BRIGHT_GREEN}✓{Colors.RESET} {dep}")
            else:
                print(f"    {Colors.BRIGHT_RED}✗{Colors.RESET} {dep}")
        
        # Optional dependencies
        print("  Optional:")
        for dep in cls.OPTIONAL_DEPENDENCIES:
            name = dep.split()[0]
            if "bundled" in dep:
                print(f"    {Colors.BRIGHT_BLUE}◦{Colors.RESET} {dep}")
            elif status.get(name.lower(), False):
                print(f"    {Colors.BRIGHT_GREEN}✓{Colors.RESET} {dep}")
            else:
                print(f"    {Colors.BRIGHT_YELLOW}○{Colors.RESET} {dep}")
        print()


class AboutInfo:
    """Complete about information"""
    
    @staticmethod
    def print_about():
        """Print complete about information"""
        VersionInfo.print_version_banner()
        FeatureInfo.print_feature_summary()
        SystemInfo.print_system_info()
        PackageInfo.print_dependency_status()
    
    @staticmethod
    def get_about_dict():
        """Get about information as dictionary"""
        return {
            'version': VersionInfo.get_full_version_info(),
            'features': FeatureInfo.get_feature_list(),
            'system': SystemInfo.get_system_info(),
            'dependencies': PackageInfo.get_dependency_status()
        }
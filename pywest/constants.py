"""
constants.py - Constants and color definitions
"""


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


class PyWestConstants:
    """Application constants"""
    DEFAULT_PYTHON_VERSION = "3.12.10"
    DEFAULT_COMPRESSION_LEVEL = 6
    SUPPORTED_PYTHON_VERSIONS = ['3.12.10', '3.11.9']
    
    # URLs
    PYTHON_BASE_URL = "https://www.python.org/ftp/python"
    GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
    
    # File patterns
    EXCLUDE_PATTERNS = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    MAIN_FILE_CANDIDATES = ['main.py', '__main__.py']
    
    # Required dependencies for installer
    REQUIRED_INSTALLER_DEPS = ["dearpygui", "pywin32"]
    
    # Cache directory
    CACHE_DIR_NAME = ".pywest"
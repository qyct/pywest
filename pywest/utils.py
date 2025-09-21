"""
pywest.utils - Utility classes for styling and output
"""

import zipfile


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
    """Stylized output printer"""
    
    @staticmethod
    def info(message, prefix="ℹ"):
        print(Colors.BRIGHT_BLUE + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def success(message, prefix="✓"):
        print(Colors.BRIGHT_GREEN + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def warning(message, prefix="⚠ "):
        print(Colors.BRIGHT_YELLOW + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def error(message, prefix="✗"):
        print(Colors.BRIGHT_RED + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def step(message, prefix="→"):
        print(Colors.BRIGHT_CYAN + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def dim(message):
        print(Colors.DIM + message + Colors.RESET)
    
    @staticmethod
    def progress(message, prefix="◐"):
        print(Colors.YELLOW + prefix + Colors.RESET + " " + message, end="", flush=True)
    
    @staticmethod
    def progress_done(message="Done"):
        # Clear the entire line before printing the done message
        print("\r" + " " * 80, end="")  # Clear with spaces
        print("\r" + Colors.BRIGHT_GREEN + "✓" + Colors.RESET + " " + message)


def get_compression_level_for_zip(level):
    """Convert compression level (0-9) to zipfile compression method and compresslevel"""
    if level == 0:
        return zipfile.ZIP_STORED, None
    elif level <= 3:
        return zipfile.ZIP_DEFLATED, level + 3  # 3-6 for zipfile
    elif level <= 6:
        return zipfile.ZIP_DEFLATED, 6
    else:
        return zipfile.ZIP_DEFLATED, 9


def get_7zip_compression_args(level):
    """Get 7-Zip compression arguments for given level"""
    compression_methods = {
        0: ['-mx0'],  # Store
        1: ['-mx1'],  # Fastest
        2: ['-mx3'],  # Fast
        3: ['-mx5'],  # Normal
        4: ['-mx5'],  # Normal
        5: ['-mx7'],  # Maximum
        6: ['-mx7'],  # Maximum (default)
        7: ['-mx9'],  # Ultra
        8: ['-mx9', '-md64m'],  # Ultra with larger dictionary
        9: ['-mx9', '-md128m', '-mfb273', '-mc1000']  # Ultra maximum
    }
    return compression_methods.get(level, ['-mx7'])
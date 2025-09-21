"""
pywest.cli - Main CLI interface for pywest bundler
"""

import sys
import argparse
from pathlib import Path

from .bundler import PyWest
from .utils import StylePrinter


def main():
    parser = argparse.ArgumentParser(description='pywest - Python Project Bundler for Windows')
    parser.add_argument('project_name', nargs='?', help='Name of the project directory to bundle')
    parser.add_argument('--zip', '-z', action='store_true', help='Create bundle as ZIP instead of folder')
    parser.add_argument('--7zip', '-7', action='store_true', help='Create bundle as 7Z instead of folder')
    parser.add_argument('--compression', '-c', type=int, default=6, choices=range(0, 10),
                       help='Compression level (0-9, default: 6). 0=store, 1=fastest, 6=default, 9=best')
    parser.add_argument('--python', default='3.12.10', 
                       choices=['3.12.10', '3.11.9'], 
                       help='Python version to use (default: 3.12.10)')
    parser.add_argument('--name', '-n', 
                       help='Custom name for the bundle (default: <project_name>_bundle)')
    
    args = parser.parse_args()
    
    # Validate compression arguments
    if args.zip and args._7zip:
        StylePrinter.error("Cannot use both --zip and --7zip options simultaneously")
        sys.exit(1)
    
    pywest = PyWest()
    pywest.python_version = args.python
    pywest.python_embed_url = f"https://www.python.org/ftp/python/{args.python}/python-{args.python}-embed-amd64.zip"
    pywest.compression_level = args.compression
    
    if not args.project_name:
        pywest.print_cli_info()
        return
    
    # Check for 7-Zip availability if needed
    if args._7zip and not pywest.check_7zip_available():
        StylePrinter.error("7-Zip not found in system PATH")
        StylePrinter.info("Please install 7-Zip from https://www.7-zip.org/ and ensure it's in your PATH")
        sys.exit(1)
    
    try:
        # Determine bundle type
        if args._7zip:
            bundle_type = '7zip'
        elif args.zip:
            bundle_type = 'zip'
        else:
            bundle_type = 'folder'
            
        result = pywest.bundle_project(args.project_name, bundle_type, args.name)
        
        if result is None:
            # User cancelled the operation
            sys.exit(0)
            
    except KeyboardInterrupt:
        StylePrinter.warning("Operation cancelled by user")
        sys.exit(1)
    except (PermissionError, FileNotFoundError, NotADirectoryError) as e:
        StylePrinter.error(str(e))
        sys.exit(1)
    except Exception as e:
        StylePrinter.error("Unexpected error: " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
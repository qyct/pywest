"""
pywest - A tool to pack Python projects with embeddable Python for Windows
"""

import os
import sys
import argparse
import shutil
import zipfile
import urllib.request
import tempfile
import subprocess
from pathlib import Path
import time

# Use tomllib (Python 3.11+ builtin)
import tomllib


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
        print(f"{Colors.BRIGHT_BLUE}{prefix}{Colors.RESET} {message}")
    
    @staticmethod
    def success(message, prefix="✓"):
        print(f"{Colors.BRIGHT_GREEN}{prefix}{Colors.RESET} {message}")
    
    @staticmethod
    def warning(message, prefix="⚠"):
        print(f"{Colors.BRIGHT_YELLOW}{prefix}{Colors.RESET} {message}")
    
    @staticmethod
    def error(message, prefix="✗"):
        print(f"{Colors.BRIGHT_RED}{prefix}{Colors.RESET} {message}")
    
    @staticmethod
    def step(message, prefix="→"):
        print(f"{Colors.BRIGHT_CYAN}{prefix}{Colors.RESET} {message}")
    
    @staticmethod
    def dim(message):
        print(f"{Colors.DIM}{message}{Colors.RESET}")
    
    @staticmethod
    def progress(message, prefix="◐"):
        print(f"{Colors.YELLOW}{prefix}{Colors.RESET} {message}", end="", flush=True)
    
    @staticmethod
    def progress_done(message="Done"):
        print(f"\r{Colors.BRIGHT_GREEN}✓{Colors.RESET} {message}")


class PyWest:
    def __init__(self):
        self.python_version = "3.12.10"  # Default Python version
        self.python_embed_url = f"https://www.python.org/ftp/python/{self.python_version}/python-{self.python_version}-embed-amd64.zip"
        self.printer = StylePrinter()
    
    def print_cli_info(self):
        """Print CLI information"""
        print(f"""
{Colors.BOLD}{Colors.BRIGHT_CYAN}pywest{Colors.RESET} - Python Project Bundler for Windows

{Colors.BOLD}Usage:{Colors.RESET}
    {Colors.BRIGHT_WHITE}pywest{Colors.RESET}                           Show this help information
    {Colors.BRIGHT_WHITE}pywest{Colors.RESET} {Colors.CYAN}<project_name>{Colors.RESET}            Bundle project as folder (default)
    {Colors.BRIGHT_WHITE}pywest{Colors.RESET} {Colors.CYAN}<project_name>{Colors.RESET} {Colors.YELLOW}--zip{Colors.RESET}      Bundle project as ZIP file
    
{Colors.BOLD}Options:{Colors.RESET}
    {Colors.YELLOW}--zip, -z{Colors.RESET}                        Create bundle as ZIP instead of folder
    {Colors.YELLOW}--python{Colors.RESET} {Colors.CYAN}VERSION{Colors.RESET}                 Specify Python version (default: 3.12.10, also supports: 3.11.9)
    
{Colors.BOLD}Description:{Colors.RESET}
    pywest bundles Python projects with embeddable Python for Windows distribution.
    It reads dependencies from project configuration (if available) and creates a portable package.
    
{Colors.BOLD}Requirements:{Colors.RESET}
    - Windows environment
    - Project configuration file (optional - if present, dependencies will be installed)
        """)
    
    def load_pyproject(self, project_path):
        """Load and parse pyproject.toml"""
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return None
        
        try:
            with open(pyproject_path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            self.printer.warning(f"Could not parse pyproject.toml: {e}")
            return None
    
    def get_entry_point(self, pyproject_data):
        """Extract entry point from pyproject.toml"""
        if not pyproject_data:
            return None, None
            
        try:
            scripts = pyproject_data['project']['scripts']
            if len(scripts) != 1:
                self.printer.warning("Multiple entry points found, using first one")
            
            entry_name, entry_point = next(iter(scripts.items()))
            return entry_name, entry_point
        except KeyError:
            return None, None
    
    def get_dependencies(self, pyproject_data):
        """Extract dependencies from pyproject.toml"""
        dependencies = []
        
        if not pyproject_data:
            return dependencies
        
        # Get main dependencies
        if 'project' in pyproject_data and 'dependencies' in pyproject_data['project']:
            dependencies.extend(pyproject_data['project']['dependencies'])
        
        return dependencies
    
    def download_embed_python(self, temp_dir):
        """Download and extract embeddable Python"""
        embed_zip_path = temp_dir / f"python-{self.python_version}-embed.zip"
        
        self.printer.progress(f"Downloading Python {self.python_version} embeddable...")
        
        # Suppress urllib output by redirecting stderr temporarily
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            urllib.request.urlretrieve(self.python_embed_url, embed_zip_path)
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        self.printer.progress_done(f"Python {self.python_version} downloaded")
        
        python_dir = temp_dir / "python"
        python_dir.mkdir()
        
        with zipfile.ZipFile(embed_zip_path, 'r') as zip_ref:
            zip_ref.extractall(python_dir)
        
        return python_dir
    
    def setup_pip_in_embed(self, python_dir):
        """Setup pip in embeddable Python"""
        self.printer.progress("Setting up pip...")
        
        # Download get-pip.py
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = python_dir / "get-pip.py"
        
        # Suppress urllib output
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            urllib.request.urlretrieve(get_pip_url, get_pip_path)
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        # Find and uncomment import site in pth file
        pth_files = list(python_dir.glob("*._pth"))
        if pth_files:
            pth_file = pth_files[0]
            with open(pth_file, 'r') as f:
                content = f.read()
            
            # Uncomment import site
            content = content.replace("#import site", "import site")
            
            with open(pth_file, 'w') as f:
                f.write(content)
        
        # Install pip (suppress output)
        python_exe = python_dir / "python.exe"
        with open(os.devnull, 'w') as devnull:
            subprocess.run([str(python_exe), str(get_pip_path), "--no-warn-script-location"], 
                         stdout=devnull, stderr=devnull, check=True)
        
        # Clean up get-pip.py
        get_pip_path.unlink()
        
        self.printer.progress_done("Pip configured")
    
    def install_dependencies(self, python_dir, dependencies):
        """Install dependencies using pip"""
        if not dependencies:
            self.printer.dim("No dependencies to install")
            return
        
        python_exe = python_dir / "python.exe"
        
        if len(dependencies) == 1:
            self.printer.progress(f"Installing {dependencies[0]}...")
        else:
            self.printer.progress(f"Installing {len(dependencies)} dependencies...")
        
        for dep in dependencies:
            with open(os.devnull, 'w') as devnull:
                subprocess.run([
                    str(python_exe), "-m", "pip", "install", dep,
                    "--no-warn-script-location", "--quiet"
                ], stdout=devnull, stderr=devnull, check=True)
        
        if len(dependencies) == 1:
            self.printer.progress_done(f"{dependencies[0]} installed")
        else:
            self.printer.progress_done(f"{len(dependencies)} dependencies installed")
    
    def create_run_script(self, bundle_dir, entry_name, entry_point, project_name):
        """Create run.bat script"""
        if entry_point:
            # If entry point is defined, use it
            module_name, func_name = entry_point.split(':')
            bat_content = f"""@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe -c "import sys; sys.path.insert(0, '.'); from {module_name} import {func_name}; {func_name}()"

pause
"""
        else:
            # If no entry point, try to find main.py or create a simple runner
            main_files = ['main.py', f'{project_name}.py', '__main__.py']
            main_file = None
            
            for mf in main_files:
                if (bundle_dir / mf).exists():
                    main_file = mf
                    break
            
            if main_file:
                bat_content = f"""@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe {main_file} %*

pause
"""
            else:
                # Create a generic Python launcher
                bat_content = f"""@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

echo Starting Python environment for {project_name}
echo Use 'bin\\python.exe script.py' to run Python scripts
echo.

bin\\python.exe

pause
"""
        
        bat_path = bundle_dir / "run.bat"
        with open(bat_path, 'w') as f:
            f.write(bat_content)
    
    def copy_project_files(self, project_path, bundle_dir, exclude_pyproject=True):
        """Copy project files to bundle directory"""
        self.printer.progress("Copying project files...")
        
        # Files and directories to exclude
        exclude_items = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
        if exclude_pyproject:
            exclude_items.add('pyproject.toml')
        
        file_count = 0
        # Copy all relevant files and directories
        for item in project_path.iterdir():
            if item.name in exclude_items:
                continue
            
            dest = bundle_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                file_count += len(list(item.rglob('*')))
            else:
                shutil.copy2(item, dest)
                file_count += 1
        
        self.printer.progress_done(f"Copied {file_count} project files")
    
    def create_bundle_folder(self, project_path, output_path):
        """Create bundle as a folder"""
        project_path = Path(project_path).resolve()
        project_name = project_path.name
        
        # Print header
        print(f"\n{Colors.BOLD}{Colors.BRIGHT_CYAN}🚀 PyWest Bundler{Colors.RESET}")
        print(f"{Colors.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
        
        # Load pyproject.toml (optional)
        pyproject_data = self.load_pyproject(project_path)
        entry_name, entry_point = self.get_entry_point(pyproject_data)
        dependencies = self.get_dependencies(pyproject_data)
        
        # Create bundle directory
        bundle_name = f"{project_name}_bundle"
        bundle_dir = output_path / bundle_name
        
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)
        bundle_dir.mkdir(parents=True)
        
        self.printer.info(f"Project: {Colors.BRIGHT_WHITE}{project_name}{Colors.RESET}")
        self.printer.info(f"Output: {Colors.BRIGHT_WHITE}{bundle_dir}{Colors.RESET}")
        
        if dependencies:
            self.printer.info(f"Dependencies: {Colors.BRIGHT_WHITE}{len(dependencies)}{Colors.RESET}")
        
        print()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download and setup embeddable Python
            python_dir = self.download_embed_python(temp_path)
            self.setup_pip_in_embed(python_dir)
            self.install_dependencies(python_dir, dependencies)
            
            # Copy Python to bundle bin directory
            self.printer.progress("Setting up Python environment...")
            bin_dir = bundle_dir / "bin"
            shutil.copytree(python_dir, bin_dir)
            self.printer.progress_done("Python environment ready")
            
            # Copy project files (exclude pyproject.toml from bundle)
            self.copy_project_files(project_path, bundle_dir, exclude_pyproject=True)
            
            # Create run script
            self.printer.progress("Generating launcher...")
            self.create_run_script(bundle_dir, entry_name, entry_point, project_name)
            self.printer.progress_done("Launcher created")
        
        print(f"\n{Colors.BRIGHT_GREEN}✅ Bundle created successfully!{Colors.RESET}")
        self.printer.dim(f"   Location: {bundle_dir}")
        self.printer.dim(f"   Run with: {bundle_dir / 'run.bat'}")
        
        return bundle_dir
    
    def create_bundle_zip(self, project_path, output_path):
        """Create bundle as a ZIP file"""
        # First create folder bundle
        bundle_dir = self.create_bundle_folder(project_path, output_path)
        
        # Create ZIP file
        zip_path = output_path / f"{bundle_dir.name}.zip"
        
        print()  # Add spacing
        self.printer.progress(f"Creating ZIP archive...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in bundle_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(bundle_dir.parent)
                    zipf.write(file_path, arcname)
        
        # Remove the folder bundle
        shutil.rmtree(bundle_dir)
        
        self.printer.progress_done("ZIP archive created")
        
        print(f"\n{Colors.BRIGHT_GREEN}✅ ZIP bundle created successfully!{Colors.RESET}")
        self.printer.dim(f"   Location: {zip_path}")
        
        return zip_path
    
    def bundle_project(self, project_name, bundle_type='folder'):
        """Bundle the project"""
        project_path = Path(project_name).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_name}' not found")
        
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_name}' is not a directory")
        
        # Output adjacent to project directory
        output_path = project_path.parent
        
        if bundle_type == 'zip':
            return self.create_bundle_zip(project_path, output_path)
        else:
            return self.create_bundle_folder(project_path, output_path)


def main():
    parser = argparse.ArgumentParser(description='pywest - Python Project Bundler for Windows')
    parser.add_argument('project_name', nargs='?', help='Name of the project directory to bundle')
    parser.add_argument('--zip', '-z', action='store_true', help='Create bundle as ZIP instead of folder')
    parser.add_argument('--python', default='3.12.10', 
                       choices=['3.12.10', '3.11.9'], 
                       help='Python version to use (default: 3.12.10)')
    
    args = parser.parse_args()
    
    pywest = PyWest()
    pywest.python_version = args.python
    pywest.python_embed_url = f"https://www.python.org/ftp/python/{args.python}/python-{args.python}-embed-amd64.zip"
    
    if not args.project_name:
        pywest.print_cli_info()
        return
    
    try:
        bundle_type = 'zip' if args.zip else 'folder'
        result = pywest.bundle_project(args.project_name, bundle_type)
        
    except Exception as e:
        StylePrinter.error(f"Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
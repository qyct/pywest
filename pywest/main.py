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

# Use tomllib for Python 3.11+ or fallback to toml
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
        # Add compatibility function for older toml library
        def loads(data):
            return tomllib.loads(data)
        tomllib.loads = loads
    except ImportError:
        print("Error: Neither tomllib nor toml library is available")
        sys.exit(1)


class PyWest:
    def __init__(self):
        self.python_version = "3.11.9"  # Default Python version
        self.python_embed_url = f"https://www.python.org/ftp/python/{self.python_version}/python-{self.python_version}-embed-amd64.zip"
    
    def print_cli_info(self):
        """Print CLI information"""
        print("""
pywest - Python Project Bundler for Windows

Usage:
    pywest                           Show this help information
    pywest <project_name>            Bundle project as folder (default)
    pywest <project_name> --zip      Bundle project as ZIP file
    
Options:
    --zip, -z                        Create bundle as ZIP instead of folder
    --python-version VERSION         Specify Python version (default: 3.11.9)
    
Description:
    pywest bundles Python projects with embeddable Python for Windows distribution.
    It reads dependencies from pyproject.toml (if available) and creates a portable package.
    
Requirements:
    - Windows environment
    - pyproject.toml file (optional - if present, dependencies will be installed)
        """)
    
    def load_pyproject(self, project_path):
        """Load and parse pyproject.toml"""
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return None
        
        try:
            with open(pyproject_path, 'rb') as f:
                if hasattr(tomllib, 'load'):
                    return tomllib.load(f)
                else:
                    # Fallback for older toml library
                    content = f.read().decode('utf-8')
                    return tomllib.loads(content)
        except Exception as e:
            print(f"Warning: Could not parse pyproject.toml: {e}")
            return None
    
    def get_entry_point(self, pyproject_data):
        """Extract entry point from pyproject.toml"""
        if not pyproject_data:
            return None, None
            
        try:
            scripts = pyproject_data['project']['scripts']
            if len(scripts) != 1:
                print("Warning: Multiple entry points found, using first one")
            
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
        
        print(f"Downloading Python {self.python_version} embeddable...")
        urllib.request.urlretrieve(self.python_embed_url, embed_zip_path)
        
        python_dir = temp_dir / "python"
        python_dir.mkdir()
        
        with zipfile.ZipFile(embed_zip_path, 'r') as zip_ref:
            zip_ref.extractall(python_dir)
        
        return python_dir
    
    def setup_pip_in_embed(self, python_dir):
        """Setup pip in embeddable Python"""
        print("Setting up pip in embeddable Python...")
        
        # Download get-pip.py
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = python_dir / "get-pip.py"
        urllib.request.urlretrieve(get_pip_url, get_pip_path)
        
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
        
        # Install pip
        python_exe = python_dir / "python.exe"
        subprocess.run([str(python_exe), str(get_pip_path)], check=True)
        
        # Clean up get-pip.py
        get_pip_path.unlink()
    
    def install_dependencies(self, python_dir, dependencies):
        """Install dependencies using pip"""
        if not dependencies:
            print("No dependencies to install")
            return
        
        print("Installing dependencies...")
        python_exe = python_dir / "python.exe"
        
        for dep in dependencies:
            print(f"Installing {dep}...")
            subprocess.run([
                str(python_exe), "-m", "pip", "install", dep,
                "--no-warn-script-location"
            ], check=True)
    
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
        
        print(f"Created run.bat script")
    
    def copy_project_files(self, project_path, bundle_dir, exclude_pyproject=True):
        """Copy project files to bundle directory"""
        print("Copying project files...")
        
        # Files and directories to exclude
        exclude_items = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
        if exclude_pyproject:
            exclude_items.add('pyproject.toml')
        
        # Copy all relevant files and directories
        for item in project_path.iterdir():
            if item.name in exclude_items:
                continue
            
            dest = bundle_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
            else:
                shutil.copy2(item, dest)
    
    def create_bundle_folder(self, project_path, output_path):
        """Create bundle as a folder"""
        project_path = Path(project_path).resolve()
        project_name = project_path.name
        
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
        
        print(f"Creating bundle folder: {bundle_dir}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download and setup embeddable Python
            python_dir = self.download_embed_python(temp_path)
            self.setup_pip_in_embed(python_dir)
            self.install_dependencies(python_dir, dependencies)
            
            # Copy Python to bundle bin directory
            bin_dir = bundle_dir / "bin"
            shutil.copytree(python_dir, bin_dir)
            
            # Copy project files (exclude pyproject.toml from bundle)
            self.copy_project_files(project_path, bundle_dir, exclude_pyproject=True)
            
            # Create run script
            self.create_run_script(bundle_dir, entry_name, entry_point, project_name)
        
        print(f"Bundle created successfully at: {bundle_dir}")
        return bundle_dir
    
    def create_bundle_zip(self, project_path, output_path):
        """Create bundle as a ZIP file"""
        # First create folder bundle
        bundle_dir = self.create_bundle_folder(project_path, output_path)
        
        # Create ZIP file
        zip_path = output_path / f"{bundle_dir.name}.zip"
        
        print(f"Creating ZIP file: {zip_path}")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in bundle_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(bundle_dir.parent)
                    zipf.write(file_path, arcname)
        
        # Remove the folder bundle
        shutil.rmtree(bundle_dir)
        
        print(f"ZIP bundle created successfully at: {zip_path}")
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
    parser.add_argument('--python-version', default='3.11.9', help='Python version to use (default: 3.11.9)')
    
    args = parser.parse_args()
    
    pywest = PyWest()
    pywest.python_version = args.python_version
    pywest.python_embed_url = f"https://www.python.org/ftp/python/{args.python_version}/python-{args.python_version}-embed-amd64.zip"
    
    if not args.project_name:
        pywest.print_cli_info()
        return
    
    try:
        bundle_type = 'zip' if args.zip else 'folder'
        result = pywest.bundle_project(args.project_name, bundle_type)
        print(f"\n✅ Successfully created bundle!")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
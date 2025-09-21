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
        print(Colors.BRIGHT_BLUE + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def success(message, prefix="✓"):
        print(Colors.BRIGHT_GREEN + prefix + Colors.RESET + " " + message)
    
    @staticmethod
    def warning(message, prefix="⚠"):
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
        print("\r" + Colors.BRIGHT_GREEN + "✓" + Colors.RESET + " " + message + "             ")  # Extra spaces to clear progress text


class PyWest:
    def __init__(self):
        self.python_version = "3.12.10"  # Default Python version
        self.python_embed_url = "https://www.python.org/ftp/python/" + self.python_version + "/python-" + self.python_version + "-embed-amd64.zip"
        self.printer = StylePrinter()
    
    def print_cli_info(self):
        """Print CLI information"""
        print("\npywest - Python Project Bundler for Windows\n")
        print("Usage:")
        print("    pywest                           Show this help information")
        print("    pywest <project_name>            Bundle project as folder (default)")
        print("    pywest <project_name> --zip      Bundle project as ZIP file")
        print("\nOptions:")
        print("    --zip, -z                        Create bundle as ZIP instead of folder")
        print("    --python VERSION                 Specify Python version (default: 3.12.10, also supports: 3.11.9)")
        print("    --name, -n NAME                  Custom name for the bundle (default: <project_name>_bundle)")
        print("\nExamples:")
        print("    pywest my_app                    Create my_app_bundle folder")
        print("    pywest my_app --zip              Create my_app_bundle.zip")
        print("    pywest my_app --name MyApp       Create MyApp folder")
        print("    pywest my_app --zip --name MyApp Create MyApp.zip")
        print("\nDescription:")
        print("    pywest bundles Python projects with embeddable Python for Windows distribution.")
        print("    It reads dependencies from project configuration (if available) and creates a portable package.")
        print("\nRequirements:")
        print("    - Windows environment")
        print("    - Project configuration file (optional - if present, dependencies will be installed)")
    
    def load_pyproject(self, project_path):
        """Load and parse pyproject.toml"""
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            return None
        
        try:
            with open(pyproject_path, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            self.printer.warning("Could not parse pyproject.toml: " + str(e))
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
    
    def download_embed_python(self, bundle_dir):
        """Download and extract embeddable Python directly to bundle"""
        embed_zip_path = bundle_dir / ("python-" + self.python_version + "-embed.zip")
        
        self.printer.progress("Downloading Python " + self.python_version + " embeddable...")
        
        # Suppress urllib output by redirecting stderr temporarily
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            urllib.request.urlretrieve(self.python_embed_url, embed_zip_path)
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        self.printer.progress_done("Python " + self.python_version + " downloaded")
        
        # Extract directly to bin directory
        bin_dir = bundle_dir / "bin"
        bin_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(embed_zip_path, 'r') as zip_ref:
            zip_ref.extractall(bin_dir)
        
        # Clean up zip file
        embed_zip_path.unlink()
        
        return bin_dir
    
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
            self.printer.progress("Installing " + dependencies[0] + "...")
        else:
            self.printer.progress("Installing " + str(len(dependencies)) + " dependencies...")
        
        for dep in dependencies:
            with open(os.devnull, 'w') as devnull:
                subprocess.run([
                    str(python_exe), "-m", "pip", "install", dep,
                    "--no-warn-script-location", "--quiet"
                ], stdout=devnull, stderr=devnull, check=True)
        
        if len(dependencies) == 1:
            self.printer.progress_done(dependencies[0] + " installed")
        else:
            self.printer.progress_done(str(len(dependencies)) + " dependencies installed")
    
    def create_run_script(self, bundle_dir, entry_name, entry_point, project_name):
        """Create run.bat script"""
        if entry_point:
            # If entry point is defined, use it
            module_name, func_name = entry_point.split(':')
            bat_content = """@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe -c "import sys; sys.path.insert(0, '.'); from """ + module_name + """ import """ + func_name + """; """ + func_name + """()"

pause
"""
        else:
            # If no entry point, try to find main.py or create a simple runner
            main_files = ['main.py', project_name + '.py', '__main__.py']
            main_file = None
            
            for mf in main_files:
                if (bundle_dir / mf).exists():
                    main_file = mf
                    break
            
            if main_file:
                bat_content = """@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe """ + main_file + """ %*

pause
"""
            else:
                # Create a generic Python launcher
                bat_content = """@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

echo Starting Python environment for """ + project_name + """
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
        
        self.printer.progress_done("Copied " + str(file_count) + " project files")
    
    def create_bundle_folder(self, project_path, output_path, bundle_name=None):
        """Create bundle as a folder"""
        project_path = Path(project_path).resolve()
        project_name = project_path.name
        
        # Print header
        print("\n" + Colors.BOLD + Colors.BRIGHT_CYAN + "🚀 PyWest Bundler" + Colors.RESET)
        print(Colors.DIM + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + Colors.RESET)
        
        # Load pyproject.toml (optional)
        pyproject_data = self.load_pyproject(project_path)
        entry_name, entry_point = self.get_entry_point(pyproject_data)
        dependencies = self.get_dependencies(pyproject_data)
        
        # Create bundle directory
        if bundle_name is None:
            bundle_name = project_name + "_bundle"
        bundle_dir = output_path / bundle_name
        
        # Check if bundle directory already exists
        if bundle_dir.exists():
            self.printer.warning("Bundle directory already exists: " + str(bundle_dir))
            response = input(Colors.YELLOW + "?" + Colors.RESET + " Overwrite existing bundle? [y/N]: ").strip().lower()
            
            if response not in ('y', 'yes'):
                self.printer.info("Bundle creation cancelled")
                return None
            
            # Attempt to remove existing directory
            try:
                self.printer.progress("Removing existing bundle...")
                shutil.rmtree(bundle_dir)
                self.printer.progress_done("Existing bundle removed")
            except PermissionError as e:
                raise PermissionError("Cannot remove existing bundle directory. Files may be in use or you lack permissions: " + str(e))
            except Exception as e:
                raise Exception("Failed to remove existing bundle directory: " + str(e))
        
        # Create new bundle directory
        try:
            bundle_dir.mkdir(parents=True)
        except PermissionError as e:
            raise PermissionError("Cannot create bundle directory. Check permissions: " + str(e))
        except Exception as e:
            raise Exception("Failed to create bundle directory: " + str(e))
        
        print("ℹ Project: " + project_name)
        print("ℹ Output: " + str(bundle_dir))
        
        if dependencies:
            print("ℹ Dependencies: " + str(len(dependencies)))
        
        print()
        
        try:
            # Download and setup embeddable Python directly to bundle
            python_dir = self.download_embed_python(bundle_dir)
            self.setup_pip_in_embed(python_dir)
            self.install_dependencies(python_dir, dependencies)
            
            self.printer.progress("Setting up Python environment...")
            self.printer.progress_done("Python environment ready")
            
            # Copy project files (exclude pyproject.toml from bundle)
            self.copy_project_files(project_path, bundle_dir, exclude_pyproject=True)
            
            # Create run script
            self.printer.progress("Generating launcher...")
            self.create_run_script(bundle_dir, entry_name, entry_point, project_name)
            self.printer.progress_done("Launcher created")
            
        except PermissionError as e:
            # Clean up partial bundle on write error
            if bundle_dir.exists():
                try:
                    shutil.rmtree(bundle_dir)
                except:
                    pass  # Best effort cleanup
            raise PermissionError("Permission denied while creating bundle. Check file permissions and ensure no files are in use: " + str(e))
        except Exception as e:
            # Clean up partial bundle on any error
            if bundle_dir.exists():
                try:
                    shutil.rmtree(bundle_dir)
                except:
                    pass  # Best effort cleanup
            raise Exception("Failed to create bundle: " + str(e))
        
        print("\n" + Colors.BRIGHT_GREEN + "✅ Bundle created successfully!" + Colors.RESET)
        print("   Location: " + str(bundle_dir))
        print("   Run with: " + str(bundle_dir / 'run.bat'))
        
        return bundle_dir
    
    def create_bundle_zip(self, project_path, output_path, bundle_name=None):
        """Create bundle as a ZIP file"""
        project_path = Path(project_path).resolve()
        project_name = project_path.name
        
        # Determine ZIP name
        if bundle_name is None:
            zip_name = project_name + "_bundle.zip"
        else:
            # If custom bundle name provided, ensure .zip extension
            if bundle_name.endswith('.zip'):
                zip_name = bundle_name
            else:
                zip_name = bundle_name + ".zip"
        
        zip_path = output_path / zip_name
        
        # Check for existing ZIP file
        if zip_path.exists():
            self.printer.warning("ZIP bundle already exists: " + str(zip_path))
            response = input(Colors.YELLOW + "?" + Colors.RESET + " Overwrite existing ZIP bundle? [y/N]: ").strip().lower()
            
            if response not in ('y', 'yes'):
                self.printer.info("Bundle creation cancelled")
                return None
            
            try:
                zip_path.unlink()
                self.printer.info("Existing ZIP bundle removed")
            except PermissionError as e:
                raise PermissionError("Cannot remove existing ZIP file. File may be in use: " + str(e))
            except Exception as e:
                raise Exception("Failed to remove existing ZIP file: " + str(e))
        
        # First create folder bundle with custom name
        temp_bundle_name = bundle_name if bundle_name else (project_name + "_bundle")
        if temp_bundle_name.endswith('.zip'):
            temp_bundle_name = temp_bundle_name[:-4]  # Remove .zip extension for folder
            
        bundle_dir = self.create_bundle_folder(project_path, output_path, temp_bundle_name)
        
        if bundle_dir is None:  # User cancelled folder creation
            return None
        
        print()  # Add spacing
        
        try:
            self.printer.progress("Creating ZIP archive...")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in bundle_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(bundle_dir.parent)
                        zipf.write(file_path, arcname)
            
            # Remove the folder bundle
            shutil.rmtree(bundle_dir)
            
            self.printer.progress_done("ZIP archive created")
            
        except PermissionError as e:
            # Clean up on error
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except:
                    pass
            if bundle_dir.exists():
                try:
                    shutil.rmtree(bundle_dir)
                except:
                    pass
            raise PermissionError("Permission denied while creating ZIP archive: " + str(e))
        except Exception as e:
            # Clean up on error
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except:
                    pass
            if bundle_dir.exists():
                try:
                    shutil.rmtree(bundle_dir)
                except:
                    pass
            raise Exception("Failed to create ZIP archive: " + str(e))
        
        print("\n" + Colors.BRIGHT_GREEN + "✅ ZIP bundle created successfully!" + Colors.RESET)
        print("   Location: " + str(zip_path))
        
        return zip_path
    
    def bundle_project(self, project_name, bundle_type='folder', bundle_name=None):
        """Bundle the project"""
        project_path = Path(project_name).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError("Project directory '" + project_name + "' not found")
        
        if not project_path.is_dir():
            raise NotADirectoryError("'" + project_name + "' is not a directory")
        
        # Output adjacent to project directory
        output_path = project_path.parent
        
        try:
            if bundle_type == 'zip':
                return self.create_bundle_zip(project_path, output_path, bundle_name)
            else:
                return self.create_bundle_folder(project_path, output_path, bundle_name)
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            # Re-raise these specific exceptions as-is
            raise
        except Exception as e:
            # Wrap other exceptions with more context
            raise Exception("Bundle creation failed: " + str(e))


def main():
    parser = argparse.ArgumentParser(description='pywest - Python Project Bundler for Windows')
    parser.add_argument('project_name', nargs='?', help='Name of the project directory to bundle')
    parser.add_argument('--zip', '-z', action='store_true', help='Create bundle as ZIP instead of folder')
    parser.add_argument('--python', default='3.12.10', 
                       choices=['3.12.10', '3.11.9'], 
                       help='Python version to use (default: 3.12.10)')
    parser.add_argument('--name', '-n', 
                       help='Custom name for the bundle (default: <project_name>_bundle)')
    
    args = parser.parse_args()
    
    pywest = PyWest()
    pywest.python_version = args.python
    pywest.python_embed_url = "https://www.python.org/ftp/python/" + args.python + "/python-" + args.python + "-embed-amd64.zip"
    
    if not args.project_name:
        pywest.print_cli_info()
        return
    
    try:
        bundle_type = 'zip' if args.zip else 'folder'
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
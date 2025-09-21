"""
pywest.bundler - Main bundling functionality
"""

import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
import tempfile
from pathlib import Path

# Use tomllib (Python 3.11+ builtin)
import tomllib

# For 7z support
try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False

from .utils import Colors, StylePrinter, get_compression_level_for_zip, get_py7zr_compression_args
from .runner import create_run_script, find_main_file
from .installer import create_setup_script


class PyWest:
    def __init__(self):
        self.python_version = "3.12.10"  # Default Python version
        self.python_embed_url = f"https://www.python.org/ftp/python/{self.python_version}/python-{self.python_version}-embed-amd64.zip"
        self.compression_level = 6  # Default compression level
        self.printer = StylePrinter()
    
    def print_cli_info(self):
        """Print CLI information"""
        print("\npywest - Python Project Bundler for Windows\n")
        print("Usage:")
        print("    pywest                           Show this help information")
        print("    pywest <project_name>            Bundle project as folder (default)")
        print("    pywest <project_name> --zip      Bundle project as ZIP file")
        if PY7ZR_AVAILABLE:
            print("    pywest <project_name> --7zip     Bundle project as 7Z file")
        print("\nOptions:")
        print("    --zip, -z                        Create bundle as ZIP instead of folder")
        if PY7ZR_AVAILABLE:
            print("    --7zip, -7                       Create bundle as 7Z instead of folder")
        print("    --compression, -c LEVEL          Compression level (0-9, default: 6)")
        print("                                     0=store, 1=fastest, 6=default, 9=best")
        print("    --python VERSION                 Specify Python version (default: 3.12.10, also supports: 3.11.9)")
        print("    --name, -n NAME                  Custom name for the bundle (default: <project_name>_bundle)")
        print("\nExamples:")
        print("    pywest my_app                    Create my_app_bundle folder")
        print("    pywest my_app --zip              Create my_app_bundle.zip")
        if PY7ZR_AVAILABLE:
            print("    pywest my_app --7zip -c 9        Create my_app_bundle.7z with best compression")
        print("    pywest my_app --name MyApp       Create MyApp folder")
        print("    pywest my_app --zip --name MyApp Create MyApp.zip")
        print("\nDescription:")
        print("    pywest bundles Python projects with embeddable Python for Windows distribution.")
        print("    It reads dependencies from project configuration (if available) and creates a portable package.")
        print("    Each bundle includes setup.bat for GUI-based installation with shortcuts and registry entries.")
        print("\nRequirements:")
        print("    - Windows environment")
        if not PY7ZR_AVAILABLE:
            print("    - py7zr library (for --7zip option): pip install py7zr")
        print("    - Project configuration file (optional - if present, dependencies will be installed)")
    
    def check_py7zr_available(self):
        """Check if py7zr library is available"""
        return PY7ZR_AVAILABLE
    
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
        # Create cache directory in user home
        cache_dir = Path.home() / ".pywest"
        cache_dir.mkdir(exist_ok=True)
        
        # Cache file path
        cached_zip_path = cache_dir / f"python-{self.python_version}-embed-amd64.zip"
        
        # Check if cached version exists
        if cached_zip_path.exists():
            self.printer.progress(f"Using cached Python {self.python_version} embeddable...")
            self.printer.progress_done(f"Python {self.python_version} embeddable found in cache")
        else:
            self.printer.progress(f"Downloading Python {self.python_version} embeddable...")
            
            # Suppress urllib output by redirecting stderr temporarily
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, 'w')
            
            try:
                urllib.request.urlretrieve(self.python_embed_url, cached_zip_path)
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr
            
            self.printer.progress_done(f"Python {self.python_version} embeddable downloaded")
        
        # Extract directly to bin directory from cache
        bin_dir = bundle_dir / "bin"
        bin_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(cached_zip_path, 'r') as zip_ref:
            zip_ref.extractall(bin_dir)
        
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
        python_exe = python_dir / "python.exe"
        
        # Install DearPyGui and pywin32 first (required for setup.bat)
        self.printer.progress("Installing GUI installer dependencies...")
        required_deps = ["dearpygui", "pywin32"]
        for dep in required_deps:
            with open(os.devnull, 'w') as devnull:
                subprocess.run([
                    str(python_exe), "-m", "pip", "install", dep,
                    "--no-warn-script-location", "--quiet"
                ], stdout=devnull, stderr=devnull, check=True)
        self.printer.progress_done("GUI installer dependencies installed")
        
        if not dependencies:
            self.printer.dim("No project dependencies to install")
            return
        
        if len(dependencies) == 1:
            self.printer.progress(f"Installing {dependencies[0]}...")
        else:
            self.printer.progress(f"Installing {len(dependencies)} project dependencies...")
        
        for dep in dependencies:
            with open(os.devnull, 'w') as devnull:
                subprocess.run([
                    str(python_exe), "-m", "pip", "install", dep,
                    "--no-warn-script-location", "--quiet"
                ], stdout=devnull, stderr=devnull, check=True)
        
        if len(dependencies) == 1:
            self.printer.progress_done(f"{dependencies[0]} installed")
        else:
            self.printer.progress_done(f"{len(dependencies)} project dependencies installed")
    
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
    
    def create_bundle_folder(self, project_path, output_path, bundle_name=None):
        """Create bundle as a folder"""
        project_path = Path(project_path).resolve()
        project_name = project_path.name
        
        # Print header
        print("\n" + Colors.BOLD + Colors.BRIGHT_CYAN + "🚀 PyWest Bundler" + Colors.RESET)
        print(Colors.DIM + "─" * 50 + Colors.RESET)
        
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
            create_run_script(bundle_dir, entry_name, entry_point, project_name)
            self.printer.progress_done("Launcher created")
            
            # Create setup script and GUI installer
            self.printer.progress("Creating installer...")
            create_setup_script(bundle_dir, project_name)
            self.printer.progress_done("Installer created")
            
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
        print("   Install with: " + str(bundle_dir / 'setup.bat'))
        
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
            
            compression_method, compress_level = get_compression_level_for_zip(self.compression_level)
            
            with zipfile.ZipFile(zip_path, 'w', compression_method, compresslevel=compress_level) as zipf:
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
        print(f"   Size: {zip_path.stat().st_size / (1024*1024):.1f} MB")
        print(f"   Compression level: {self.compression_level}")
        
        return zip_path
    
    def create_bundle_7zip(self, project_path, output_path, bundle_name=None):
        """Create bundle as a 7Z file using py7zr library"""
        if not PY7ZR_AVAILABLE:
            raise Exception("py7zr library is not installed. Install it with: pip install py7zr")
            
        project_path = Path(project_path).resolve()
        project_name = project_path.name
        
        # Determine 7Z name
        if bundle_name is None:
            archive_name = project_name + "_bundle.7z"
        else:
            # If custom bundle name provided, ensure .7z extension
            if bundle_name.endswith('.7z'):
                archive_name = bundle_name
            else:
                archive_name = bundle_name + ".7z"
        
        archive_path = output_path / archive_name
        
        # Check for existing 7Z file
        if archive_path.exists():
            self.printer.warning("7Z bundle already exists: " + str(archive_path))
            response = input(Colors.YELLOW + "?" + Colors.RESET + " Overwrite existing 7Z bundle? [y/N]: ").strip().lower()
            
            if response not in ('y', 'yes'):
                self.printer.info("Bundle creation cancelled")
                return None
            
            try:
                archive_path.unlink()
                self.printer.info("Existing 7Z bundle removed")
            except PermissionError as e:
                raise PermissionError("Cannot remove existing 7Z file. File may be in use: " + str(e))
            except Exception as e:
                raise Exception("Failed to remove existing 7Z file: " + str(e))
        
        # First create folder bundle with custom name
        temp_bundle_name = bundle_name if bundle_name else (project_name + "_bundle")
        if temp_bundle_name.endswith('.7z'):
            temp_bundle_name = temp_bundle_name[:-3]  # Remove .7z extension for folder
            
        bundle_dir = self.create_bundle_folder(project_path, output_path, temp_bundle_name)
        
        if bundle_dir is None:  # User cancelled folder creation
            return None
        
        print()  # Add spacing
        
        try:
            self.printer.progress("Creating 7Z archive...")
            
            # Get compression settings for py7zr
            compression_filters = get_py7zr_compression_args(self.compression_level)
            
            with py7zr.SevenZipFile(archive_path, 'w', filters=compression_filters) as archive:
                archive.writeall(bundle_dir, bundle_dir.name)
            
            # Remove the folder bundle
            shutil.rmtree(bundle_dir)
            
            self.printer.progress_done("7Z archive created")
            
        except PermissionError as e:
            # Clean up on error
            if archive_path.exists():
                try:
                    archive_path.unlink()
                except:
                    pass
            if bundle_dir.exists():
                try:
                    shutil.rmtree(bundle_dir)
                except:
                    pass
            raise PermissionError("Permission denied while creating 7Z archive: " + str(e))
        except Exception as e:
            # Clean up on error
            if archive_path.exists():
                try:
                    archive_path.unlink()
                except:
                    pass
            if bundle_dir.exists():
                try:
                    shutil.rmtree(bundle_dir)
                except:
                    pass
            raise Exception("Failed to create 7Z archive: " + str(e))
        
        print("\n" + Colors.BRIGHT_GREEN + "✅ 7Z bundle created successfully!" + Colors.RESET)
        print("   Location: " + str(archive_path))
        print(f"   Size: {archive_path.stat().st_size / (1024*1024):.1f} MB")
        print(f"   Compression level: {self.compression_level}")
        
        return archive_path
    
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
            if bundle_type == '7zip':
                return self.create_bundle_7zip(project_path, output_path, bundle_name)
            elif bundle_type == 'zip':
                return self.create_bundle_zip(project_path, output_path, bundle_name)
            else:
                return self.create_bundle_folder(project_path, output_path, bundle_name)
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            # Re-raise these specific exceptions as-is
            raise
        except Exception as e:
            # Wrap other exceptions with more context
            raise Exception("Bundle creation failed: " + str(e))
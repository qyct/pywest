import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
import tomllib
from pathlib import Path


class StylePrinter:
    """Stylized output printer with color support"""
    
    class Colors:
        RESET = '\033[0m'
        BOLD = '\033[1m'
        DIM = '\033[2m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        CYAN = '\033[36m'
        BRIGHT_RED = '\033[91m'
        BRIGHT_GREEN = '\033[92m'
        BRIGHT_YELLOW = '\033[93m'
        BRIGHT_BLUE = '\033[94m'
        BRIGHT_CYAN = '\033[96m'

    _last_progress_length = 0

    @staticmethod
    def info(message, prefix="ℹ"):
        print(f"{StylePrinter.Colors.BRIGHT_BLUE}{prefix}{StylePrinter.Colors.RESET} {message}")
    
    @staticmethod
    def success(message, prefix="✓"):
        print(f"{StylePrinter.Colors.BRIGHT_GREEN}{prefix}{StylePrinter.Colors.RESET} {message}")
    
    @staticmethod
    def warning(message, prefix="⚠ "):
        print(f"{StylePrinter.Colors.BRIGHT_YELLOW}{prefix}{StylePrinter.Colors.RESET} {message}")
    
    @staticmethod
    def error(message, prefix="✗"):
        print(f"{StylePrinter.Colors.BRIGHT_RED}{prefix}{StylePrinter.Colors.RESET} {message}")
    
    @staticmethod
    def step(message, prefix="→"):
        print(f"{StylePrinter.Colors.BRIGHT_CYAN}{prefix}{StylePrinter.Colors.RESET} {message}")
    
    @staticmethod
    def dim(message):
        print(f"{StylePrinter.Colors.DIM}{message}{StylePrinter.Colors.RESET}")
    
    @staticmethod
    def progress(message, prefix="◯"):
        full_message = f"{StylePrinter.Colors.YELLOW}{prefix}{StylePrinter.Colors.RESET} {message}"
        StylePrinter._last_progress_length = len(f"{prefix} {message}")
        print(full_message, end="", flush=True)
    
    @staticmethod
    def progress_done(message="Done"):
        clear_length = max(StylePrinter._last_progress_length, len(f"✓ {message}"))
        print(f"\r{' ' * clear_length}\r{StylePrinter.Colors.BRIGHT_GREEN}✓{StylePrinter.Colors.RESET} {message}")

    @staticmethod
    def print_banner(title="PyWest Bundler"):
        print(f"\n{StylePrinter.Colors.BOLD}{StylePrinter.Colors.BRIGHT_CYAN}🚀 {title}{StylePrinter.Colors.RESET}")
        print(f"{StylePrinter.Colors.DIM}{'─' * 50}{StylePrinter.Colors.RESET}")

    @staticmethod
    def print_project_info(project_name, output_path, dependency_count=0):
        print(f"Project: {project_name}")
        print(f"Output: {output_path}")
        if dependency_count > 0:
            print(f"Dependencies: {dependency_count}")
        print("")

    @staticmethod
    def print_completion_info(bundle_path, bundle_type="folder", file_size=None, compression_level=None):
        print(f"{StylePrinter.Colors.BRIGHT_GREEN}✅ Bundle created successfully!{StylePrinter.Colors.RESET}")
        print(f"   Location: {bundle_path}")
        
        if bundle_type == "folder":
            print(f"   Run with: {bundle_path / 'run.bat'}")
            print(f"   Install with: {bundle_path / 'setup.bat'}")
        else:
            if file_size:
                print(f"   Size: {file_size / (1024*1024):.1f} MB")
            if compression_level is not None:
                print(f"   Compression level: {compression_level}")


class PythonManager:
    """Handle Python environment setup and management"""
    
    SUPPORTED_VERSIONS = ['3.12.10', '3.11.9']
    DEFAULT_VERSION = '3.12.10'
    BASE_URL = "https://www.python.org/ftp/python"
    
    def __init__(self):
        self.cache_dir = Path.home() / ".pywest"
        self.cache_dir.mkdir(exist_ok=True)
        self.printer = StylePrinter()
    
    def get_cached_path(self, python_version):
        filename = f"python-{python_version}-embed-amd64.zip"
        return self.cache_dir / filename
    
    def is_cached(self, python_version):
        return self.get_cached_path(python_version).exists()
    
    def download_python(self, python_version):
        """Download Python embeddable if not cached"""
        cached_path = self.get_cached_path(python_version)
        
        if self.is_cached(python_version):
            print(f"Using cached Python {python_version}...")
            return cached_path
        
        print(f"Downloading Python {python_version}...")
        embed_url = f"{self.BASE_URL}/{python_version}/python-{python_version}-embed-amd64.zip"
        
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            urllib.request.urlretrieve(embed_url, cached_path)
        except Exception as e:
            raise Exception(f"Failed to download Python {python_version}: {str(e)}")
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        return cached_path
    
    def extract_python(self, cached_path, target_dir):
        """Extract Python embeddable to target directory"""
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with zipfile.ZipFile(cached_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            python_exe = target_dir / "python.exe"
            pythonw_exe = target_dir / "pythonw.exe"
            
            if python_exe.exists() and not pythonw_exe.exists():
                shutil.copy2(python_exe, pythonw_exe)
                
        except Exception as e:
            raise Exception(f"Failed to extract Python: {str(e)}")
        
        return target_dir
    
    def setup_environment(self, python_version, target_dir, dependencies=None):
        """Download, extract and setup Python environment"""
        cached_path = self.download_python(python_version)
        self.extract_python(cached_path, target_dir)
        
        python_exe = target_dir / "python.exe"
        
        # Setup pip
        self._setup_pip(python_exe, target_dir)
        
        # Install dependencies
        if dependencies:
            self._install_dependencies(python_exe, dependencies)
        
        self.printer.progress("Setting up Python environment...")
        self.printer.progress_done("Python environment ready")
    
    def _setup_pip(self, python_exe, python_dir):
        """Setup pip in embeddable Python"""
        print("Setting up pip...")
        
        # Enable site-packages
        pth_files = list(python_dir.glob("*._pth"))
        if pth_files:
            pth_file = pth_files[0]
            with open(pth_file, 'r') as f:
                content = f.read()
            content = content.replace("#import site", "import site")
            with open(pth_file, 'w') as f:
                f.write(content)
        
        # Download and install pip
        get_pip_path = python_dir / "get-pip.py"
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        
        try:
            urllib.request.urlretrieve(get_pip_url, get_pip_path)
            self._run_silent([str(python_exe), str(get_pip_path), "--no-warn-script-location"])
        finally:
            if get_pip_path.exists():
                get_pip_path.unlink()
    
    def _install_dependencies(self, python_exe, dependencies):
        """Install project dependencies"""
        print("Installing project dependencies...")
        for dep in dependencies:
            cmd = [str(python_exe), "-m", "pip", "install", dep, "--quiet", "--no-warn-script-location"]
            result = self._run_silent(cmd)
            if result != 0:
                raise Exception(f"Failed to install {dep}")
    
    def _run_silent(self, cmd):
        """Run command silently"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        with open(os.devnull, 'w') as devnull:
            result = subprocess.run(
                cmd, stdout=devnull, stderr=devnull, check=False,
                startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode


class ScriptGenerator:
    """Generate run and setup scripts for bundled projects"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def create_run_script(self, bundle_dir, entry_point, project_name):
        """Create run.bat script for the bundle"""
        run_script_path = Path(bundle_dir) / "run.bat"
        
        if entry_point:
            script_content = self._generate_entry_point_script(entry_point, project_name)
        else:
            script_content = self._generate_fallback_script(project_name)
        
        with open(run_script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        self.printer.dim(f"Created run script: {run_script_path}")
    
    def create_setup_script(self, bundle_dir, project_name):
        """Create setup.bat script with admin elevation"""
        setup_script_path = Path(bundle_dir) / "setup.bat"
        
        script_content = """@echo off
:: Check if we are running as admin, if not, relaunch with elevation
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
:: Change to the directory of this script
cd /d "%~dp0"
:: Run bundled python with relative path to pywest.toml
bin\\python.exe -c "import os; **import**('pyweste').installer(os.path.join('bin','pywest.toml'))"
pause
"""
        
        with open(setup_script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        self.printer.dim(f"Created setup script: {setup_script_path}")
    
    def _generate_entry_point_script(self, entry_point, project_name):
        """Generate script content using entry point"""
        return f"""@echo off
cd /d "%~dp0"
title {project_name}

echo Starting {project_name}...
echo.

bin\\python.exe -c "
import sys
sys.path.insert(0, '.')
from {entry_point.replace(':', ' import ')} as main_func
main_func()
"

if errorlevel 1 (
    echo.
    echo Error: Application exited with error code %errorlevel%
    echo.
)

pause
"""
    
    def _generate_fallback_script(self, project_name):
        """Generate fallback script content"""
        return f"""@echo off
cd /d "%~dp0"
title {project_name}

echo Starting {project_name}...
echo.

bin\\python.exe -m {project_name} %*

if errorlevel 1 (
    echo.
    echo Error: Application exited with error code %errorlevel%
    echo.
)

pause
"""


class ProjectBundler:
    """Main project bundler class"""
    
    DEFAULT_COMPRESSION = 6
    EXCLUDE_PATTERNS = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    
    def __init__(self, python_version=None, compression_level=None):
        self.python_version = python_version or PythonManager.DEFAULT_VERSION
        self.compression_level = compression_level or self.DEFAULT_COMPRESSION
        
        # Validate settings
        if self.python_version not in PythonManager.SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported Python version: {self.python_version}")
        if not (0 <= self.compression_level <= 9):
            raise ValueError(f"Compression level must be between 0-9, got: {self.compression_level}")
        
        # Initialize components
        self.printer = StylePrinter()
        self.python_manager = PythonManager()
        self.script_generator = ScriptGenerator()
    
    def bundle_project(self, project_name, bundle_type='folder', bundle_name=None):
        """Main entry point for project bundling"""
        try:
            # Validate project
            project_path = self._validate_project(project_name)
            
            # Load project configuration
            config = self._load_project_config(project_path)
            
            # Create bundle
            bundle_path = self._create_bundle(project_path, config, bundle_name or f"{project_path.name}_bundle")
            
            if bundle_path is None:
                return None
            
            # Create archive if requested
            if bundle_type == 'zip':
                return self._create_zip_archive(bundle_path, bundle_name)
            
            return bundle_path
            
        except Exception as e:
            self.printer.error(f"Bundle creation failed: {str(e)}")
            raise
    
    def _validate_project(self, project_path):
        """Validate project directory exists and is accessible"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' not found")
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_path}' is not a directory")
        if not os.access(project_path, os.R_OK):
            raise PermissionError(f"No read permission for project directory: {project_path}")
        
        return project_path
    
    def _load_project_config(self, project_path):
        """Load and parse pyproject.toml if it exists"""
        pyproject_path = project_path / "pyproject.toml"
        config = {'dependencies': [], 'entry_point': None, 'name': project_path.name}
        
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                
                # Get dependencies
                if 'project' in data and 'dependencies' in data['project']:
                    config['dependencies'] = data['project']['dependencies']
                
                # Get entry point
                tool_section = data.get("tool", {})
                pywest_section = tool_section.get("pywest", {})
                entry = pywest_section.get("entry")
                if entry:
                    config['entry_point'] = entry
                
                # Get project name
                if 'project' in data and 'name' in data['project']:
                    config['name'] = data['project']['name']
                    
            except Exception as e:
                self.printer.warning(f"Could not parse pyproject.toml: {str(e)}")
        
        return config
    
    def _create_bundle(self, project_path, config, bundle_name):
        """Create complete bundle folder"""
        # Print header
        self.printer.print_banner()
        self.printer.print_project_info(
            config['name'], 
            project_path.parent / bundle_name,
            len(config['dependencies'])
        )
        
        # Create bundle directory
        bundle_dir = self._create_bundle_directory(project_path.parent, bundle_name)
        if bundle_dir is None:
            return None
        
        try:
            # Setup Python environment
            bin_dir = bundle_dir / "bin"
            self.python_manager.setup_environment(
                self.python_version, bin_dir, config['dependencies']
            )
            
            # Copy project files
            self._copy_project_files(project_path, bundle_dir)
            
            # Copy pyproject.toml to bin folder if it exists
            pyproject_source = project_path / "pyproject.toml"
            if pyproject_source.exists():
                pyproject_dest = bin_dir / "pyproject.toml"
                shutil.copy2(pyproject_source, pyproject_dest)
                self.printer.dim("Copied pyproject.toml to bin folder")
            
            # Create scripts
            self.printer.progress("Generating launcher...")
            self.script_generator.create_run_script(bundle_dir, config['entry_point'], config['name'])
            self.printer.progress_done("Launcher created")
            
            self.printer.progress("Creating setup script...")
            self.script_generator.create_setup_script(bundle_dir, config['name'])
            self.printer.progress_done("Setup script created")
            
            # Print completion info
            self.printer.print_completion_info(bundle_dir, "folder")
            
            return bundle_dir
            
        except Exception as e:
            self._cleanup_bundle(bundle_dir)
            raise Exception(f"Bundle creation failed: {str(e)}")
    
    def _create_bundle_directory(self, output_path, bundle_name):
        """Create bundle directory, handling existing directories"""
        bundle_dir = Path(output_path) / bundle_name
        
        if bundle_dir.exists():
            print(f"Bundle directory already exists: {bundle_dir}")
            response = input("Overwrite existing bundle? [y/N]: ").strip().lower()
            
            if response not in ('y', 'yes'):
                print("Bundle creation cancelled")
                return None
            
            try:
                shutil.rmtree(bundle_dir)
            except PermissionError as e:
                raise PermissionError(f"Cannot remove existing bundle directory. Files may be in use: {str(e)}")
        
        try:
            bundle_dir.mkdir(parents=True)
            return bundle_dir
        except PermissionError as e:
            raise PermissionError(f"Cannot create bundle directory. Check permissions: {str(e)}")
    
    def _copy_project_files(self, source_path, target_path):
        """Copy project files to target directory, excluding certain patterns"""
        exclude_items = set(self.EXCLUDE_PATTERNS)
        exclude_items.add('pyproject.toml')
        
        try:
            for item in source_path.iterdir():
                if item.name in exclude_items:
                    continue
                
                dest = target_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                else:
                    shutil.copy2(item, dest)
                    
        except Exception as e:
            raise Exception(f"Failed to copy project files: {str(e)}")
    
    def _create_zip_archive(self, bundle_path, bundle_name):
        """Create ZIP archive from bundle folder"""
        if bundle_name is None:
            archive_name = f"{bundle_path.name}.zip"
        else:
            archive_name = f"{bundle_name}.zip"
        
        archive_path = bundle_path.parent / archive_name
        
        if archive_path.exists():
            raise ValueError(f"ZIP file already exists: {archive_path}")
        
        try:
            compression_method, compress_level = self._get_zip_compression()
            
            with zipfile.ZipFile(archive_path, 'w', compression_method, compresslevel=compress_level) as zipf:
                for file_path in bundle_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(bundle_path.parent)
                        zipf.write(file_path, arcname)
            
            # Remove bundle directory after successful archive creation
            shutil.rmtree(bundle_path)
            
            # Print completion info
            archive_size = archive_path.stat().st_size
            self.printer.print_completion_info(
                archive_path, "zip", archive_size, self.compression_level
            )
            
            return archive_path
            
        except Exception as e:
            if archive_path.exists():
                archive_path.unlink()
            raise Exception(f"ZIP creation failed: {str(e)}")
    
    def _get_zip_compression(self):
        """Convert compression level to zipfile settings"""
        if self.compression_level == 0:
            return zipfile.ZIP_STORED, None
        elif self.compression_level <= 3:
            return zipfile.ZIP_DEFLATED, self.compression_level + 3
        elif self.compression_level <= 6:
            return zipfile.ZIP_DEFLATED, 6
        else:
            return zipfile.ZIP_DEFLATED, 9
    
    def _cleanup_bundle(self, bundle_dir):
        """Clean up partial bundle on error"""
        if bundle_dir and Path(bundle_dir).exists():
            try:
                shutil.rmtree(bundle_dir)
            except Exception:
                pass
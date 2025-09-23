import os
import sys
import shutil
import zipfile
import urllib.request
import subprocess
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
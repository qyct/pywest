import os
import subprocess
from pathlib import Path
from .ui import StylePrinter
from .dl import GetPipDownloader
from .const import PyWestConstants


class PythonEnvironment:
    """Manage Python embeddable environment setup"""
    
    def __init__(self, python_dir):
        self.python_dir = Path(python_dir)
        self.python_exe = self.python_dir / "python.exe"
        self.pythonw_exe = self.python_dir / "pythonw.exe"
        self.printer = StylePrinter()
        self.pip_downloader = GetPipDownloader()
    
    def setup_pip(self):
        """Setup pip in embeddable Python"""
        self.printer.progress("Setting up pip...")
        
        get_pip_path = self.pip_downloader.download_get_pip(self.python_dir)
        
        try:
            self._enable_site_packages()
            self._install_pip(get_pip_path)
            self.printer.progress_done("Pip configured")
        finally:
            self.pip_downloader.cleanup_get_pip(get_pip_path)
    
    def _enable_site_packages(self):
        """Enable site-packages by modifying pth files"""
        pth_files = list(self.python_dir.glob("*._pth"))
        if not pth_files:
            return
        
        pth_file = pth_files[0]
        try:
            with open(pth_file, 'r') as f:
                content = f.read()
            
            content = content.replace("#import site", "import site")
            
            with open(pth_file, 'w') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to enable site-packages: {str(e)}")
    
    def _install_pip(self, get_pip_path):
        """Install pip using get-pip.py"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        with open(os.devnull, 'w') as devnull:
            result = subprocess.run([
                str(self.python_exe), str(get_pip_path), "--no-warn-script-location"
            ], stdout=devnull, stderr=devnull, check=False, 
            startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode != 0:
                raise Exception("Failed to install pip")
    
    def install_package(self, package_name, quiet=True):
        """Install a single package using pip"""
        cmd = [str(self.python_exe), "-m", "pip", "install", package_name, "--no-warn-script-location"]
        
        if quiet:
            cmd.append("--quiet")
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        with open(os.devnull, 'w') as devnull:
            result = subprocess.run(cmd, stdout=devnull, stderr=devnull, check=False,
                                  startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode != 0:
                raise Exception(f"Failed to install {package_name}")


class DependencyInstaller:
    """Handle installation of project dependencies"""
    
    def __init__(self, python_env):
        self.python_env = python_env
        self.printer = StylePrinter()
    
    def install_required_dependencies(self):
        """Install required dependencies for GUI installer"""
        self.printer.progress("Installing GUI installer dependencies...")
        
        for dep in PyWestConstants.REQUIRED_INSTALLER_DEPS:
            self.python_env.install_package(dep)
        
        self.printer.progress_done("GUI installer dependencies installed")
    
    def install_project_dependencies(self, dependencies):
        """Install project-specific dependencies"""
        if not dependencies:
            self.printer.dim("No project dependencies to install")
            return
        
        self.printer.progress("Installing project dependencies...")
        
        for dep in dependencies:
            self.python_env.install_package(dep)
        
        self.printer.progress_done("Project dependencies installed")
    
    def install_all_dependencies(self, project_dependencies=None):
        """Install both required and project dependencies in one combined log"""
        all_deps = list(PyWestConstants.REQUIRED_INSTALLER_DEPS)
        if project_dependencies:
            all_deps.extend(project_dependencies)
        
        self.printer.progress("Installing dependencies...")
        
        for dep in all_deps:
            self.python_env.install_package(dep)
        
        self.printer.progress_done("Dependencies installed")
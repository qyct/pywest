import os
import subprocess
from pathlib import Path
from .log import StylePrinter
from .dl import GetPipDownloader
from .const import PyWestConstants


class PythonEnvironment:
    """Manage Python embeddable environment setup"""
    
    def __init__(self, python_dir):
        self.python_dir = Path(python_dir)
        self.python_exe = self.python_dir / "python.exe"
        self.printer = StylePrinter()
        self.pip_downloader = GetPipDownloader()
    
    def setup_pip(self):
        """Setup pip in embeddable Python"""
        self.printer.progress("Setting up pip...")
        
        # Download get-pip.py
        get_pip_path = self.pip_downloader.download_get_pip(self.python_dir)
        
        try:
            # Enable site-packages by uncommenting import site
            self._enable_site_packages()
            
            # Install pip
            self._install_pip(get_pip_path)
            
            self.printer.progress_done("Pip configured")
        finally:
            # Clean up get-pip.py
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
        with open(os.devnull, 'w') as devnull:
            result = subprocess.run([
                str(self.python_exe), str(get_pip_path), "--no-warn-script-location"
            ], stdout=devnull, stderr=devnull, check=False)
            
            if result.returncode != 0:
                raise Exception("Failed to install pip")
    
    def install_package(self, package_name, quiet=True):
        """Install a single package using pip"""
        cmd = [str(self.python_exe), "-m", "pip", "install", package_name, "--no-warn-script-location"]
        
        if quiet:
            cmd.append("--quiet")
        
        with open(os.devnull, 'w') as devnull:
            result = subprocess.run(cmd, stdout=devnull, stderr=devnull, check=False)
            
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
        
        if len(dependencies) == 1:
            self.printer.progress(f"Installing {dependencies[0]}...")
        else:
            self.printer.progress(f"Installing {len(dependencies)} project dependencies...")
        
        for dep in dependencies:
            self.python_env.install_package(dep)
        
        if len(dependencies) == 1:
            self.printer.progress_done(f"{dependencies[0]} installed")
        else:
            self.printer.progress_done(f"{len(dependencies)} project dependencies installed")
    
    def install_all_dependencies(self, project_dependencies=None):
        """Install both required and project dependencies"""
        self.install_required_dependencies()
        
        if project_dependencies:
            self.install_project_dependencies(project_dependencies)
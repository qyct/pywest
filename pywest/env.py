import os
import subprocess
import urllib.request
from pathlib import Path


class PythonEnvironment:
    """Manage Python embeddable environment setup"""
    
    def __init__(self, python_dir):
        self.python_dir = Path(python_dir)
        self.python_exe = self.python_dir / "python.exe"
        self.pythonw_exe = self.python_dir / "pythonw.exe"
    
    def setup_pip(self):
        """Setup pip in embeddable Python"""
        print("Setting up pip...")
        
        get_pip_path = self.python_dir / "get-pip.py"
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        
        try:
            self._enable_site_packages()
            self._download_get_pip(get_pip_url, get_pip_path)
            self._install_pip(get_pip_path)
        finally:
            if get_pip_path.exists():
                get_pip_path.unlink()
    
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
    
    def _download_get_pip(self, url, target_path):
        """Download get-pip.py"""
        try:
            urllib.request.urlretrieve(url, target_path)
        except Exception as e:
            raise Exception(f"Failed to download get-pip.py: {str(e)}")
    
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
    
    def install_dependencies(self, dependencies):
        """Install project dependencies"""
        if not dependencies:
            return
        
        print("Installing project dependencies...")
        
        for dep in dependencies:
            cmd = [str(self.python_exe), "-m", "pip", "install", dep, "--quiet", "--no-warn-script-location"]
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            with open(os.devnull, 'w') as devnull:
                result = subprocess.run(cmd, stdout=devnull, stderr=devnull, check=False,
                                      startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode != 0:
                    raise Exception(f"Failed to install {dep}")
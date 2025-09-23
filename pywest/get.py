import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

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

class PythonDownloader:
    """Handle downloading and caching Python embeddable versions"""
    
    def __init__(self):
        self.cache_dir = Path.home() / ".pywest"
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cached_path(self, python_version):
        """Get cache file path for Python version"""
        filename = f"python-{python_version}-embed-amd64.zip"
        return self.cache_dir / filename
    
    def is_cached(self, python_version):
        """Check if Python version is already cached"""
        cached_path = self.get_cached_path(python_version)
        return cached_path.exists()
    
    def download_python(self, python_version, embed_url):
        """Download Python embeddable if not cached"""
        cached_path = self.get_cached_path(python_version)
        
        if self.is_cached(python_version):
            print(f"Using cached Python {python_version}...")
            return cached_path
        
        print(f"Downloading Python {python_version}...")
        
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
    
    def download_and_extract(self, python_version, embed_url, target_dir):
        """Download and extract Python embeddable in one step"""
        cached_path = self.download_python(python_version, embed_url)
        return self.extract_python(cached_path, target_dir)
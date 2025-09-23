import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path


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
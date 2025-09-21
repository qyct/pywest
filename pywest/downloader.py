"""
downloader.py - Handle downloading and caching of Python embeddable
"""

import os
import sys
import urllib.request
import zipfile
from pathlib import Path
from .printer import StylePrinter
from .constants import PyWestConstants


class PythonDownloader:
    """Handle downloading and caching Python embeddable versions"""
    
    def __init__(self):
        self.printer = StylePrinter()
        self.cache_dir = Path.home() / PyWestConstants.CACHE_DIR_NAME
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
            self.printer.progress(f"Using cached Python {python_version} embeddable...")
            self.printer.progress_done(f"Python {python_version} embeddable found in cache")
            return cached_path
        
        self.printer.progress(f"Downloading Python {python_version} embeddable...")
        
        # Suppress urllib output
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            urllib.request.urlretrieve(embed_url, cached_path)
        except Exception as e:
            raise Exception(f"Failed to download Python {python_version}: {str(e)}")
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        self.printer.progress_done(f"Python {python_version} embeddable downloaded")
        return cached_path
    
    def extract_python(self, cached_path, target_dir):
        """Extract Python embeddable to target directory"""
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with zipfile.ZipFile(cached_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
        except Exception as e:
            raise Exception(f"Failed to extract Python: {str(e)}")
        
        return target_dir
    
    def download_and_extract(self, python_version, embed_url, target_dir):
        """Download and extract Python embeddable in one step"""
        cached_path = self.download_python(python_version, embed_url)
        return self.extract_python(cached_path, target_dir)


class GetPipDownloader:
    """Handle downloading get-pip.py for pip installation"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def download_get_pip(self, target_dir):
        """Download get-pip.py to target directory"""
        get_pip_path = Path(target_dir) / "get-pip.py"
        
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            urllib.request.urlretrieve(PyWestConstants.GET_PIP_URL, get_pip_path)
        except Exception as e:
            raise Exception(f"Failed to download get-pip.py: {str(e)}")
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr
        
        return get_pip_path
    
    def cleanup_get_pip(self, get_pip_path):
        """Remove get-pip.py after installation"""
        try:
            if Path(get_pip_path).exists():
                Path(get_pip_path).unlink()
        except Exception:
            pass  # Ignore cleanup errors
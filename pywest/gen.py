from pathlib import Path
from .utils import StylePrinter
from .const import PyWestConstants

class PyWestConstants:
    """Application constants - simplified without GUI dependencies"""
    DEFAULT_PYTHON_VERSION = "3.12.10"
    DEFAULT_COMPRESSION_LEVEL = 6
    SUPPORTED_PYTHON_VERSIONS = ['3.12.10', '3.11.9']
    
    # URLs
    PYTHON_BASE_URL = "https://www.python.org/ftp/python"
    GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
    
    # File patterns
    EXCLUDE_PATTERNS = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    MAIN_FILE_CANDIDATES = ['main.py', '__main__.py']
    
    # Cache directory
    CACHE_DIR_NAME = ".pywest"

class RunScriptGenerator:
    """Generate run scripts for bundled projects"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def create_run_script(self, bundle_dir, entry_name, entry_point, project_name):
        """Create run.bat script for the bundle"""
        bundle_dir = Path(bundle_dir)
        run_script_path = bundle_dir / "run.bat"
        
        if entry_point:
            # Use entry point from pyproject.toml
            script_content = self._generate_entry_point_script(entry_point, project_name)
        else:
            # Look for main files
            script_content = self._generate_main_file_script(bundle_dir, project_name)
        
        try:
            with open(run_script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.printer.dim(f"Created run script: {run_script_path}")
            
        except Exception as e:
            raise Exception(f"Failed to create run script: {str(e)}")
    
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
    
    def _generate_main_file_script(self, bundle_dir, project_name):
        """Generate script content looking for main files"""
        # Look for main files in the bundle directory
        main_candidates = PyWestConstants.MAIN_FILE_CANDIDATES
        main_file = None
        
        for candidate in main_candidates:
            candidate_path = bundle_dir / candidate
            if candidate_path.exists():
                main_file = candidate
                break
        
        if main_file:
            return f"""@echo off
cd /d "%~dp0"
title {project_name}

echo Starting {project_name}...
echo.

bin\\python.exe {main_file} %*

if errorlevel 1 (
    echo.
    echo Error: Application exited with error code %errorlevel%
    echo.
)

pause
"""
        else:
            # Fallback: run as module
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


class SetupScriptGenerator:
    """Generate setup/installation scripts for bundled projects"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def create_simple_setup_script(self, bundle_dir, project_name):
        """Create setup.bat script with admin elevation and pyweste installer call"""
        bundle_dir = Path(bundle_dir)
        setup_script_path = bundle_dir / "setup.bat"
        
        script_content = """@echo off
:: BatchGotAdmin
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
        
        try:
            with open(setup_script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.printer.dim(f"Created setup script: {setup_script_path}")
            
        except Exception as e:
            raise Exception(f"Failed to create setup script: {str(e)}")
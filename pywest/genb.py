from pathlib import Path
from .utils import StylePrinter


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
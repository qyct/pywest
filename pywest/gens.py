from pathlib import Path
from .utils import StylePrinter


class ScriptGenerator:
    """Generate run and setup scripts for bundled projects"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def create_run_script(self, bundle_dir, entry_point, project_name):
        """Create run.bat script for the bundle"""
        module_name, func_name = entry_point.split(':')
        run_script_path = Path(bundle_dir) / "run.bat"
        
        run_script_content = f"""
@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe -c "import sys; sys.path.insert(0, '.'); from {module_name} import {func_name}; {func_name}()"

pause
"""
     
        with open(run_script_path, 'w', encoding='utf-8') as f:
            f.write(run_script_content)
    
    def create_setup_script(self, bundle_dir, project_name):
        """Create setup.bat script with admin elevation"""
        setup_script_path = Path(bundle_dir) / "setup.bat"
        
        setup_script_content = """
@echo off
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
bin\\pythonw.exe -c "__import__('pyweste').init_installer()"
pause
"""
        
        with open(setup_script_path, 'w', encoding='utf-8') as f:
            f.write(setup_script_content)
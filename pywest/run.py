from pathlib import Path
from .const import PyWestConstants


class RunScriptGenerator:
    """Generate run.bat scripts for different project types"""
    
    def create_run_script(self, bundle_dir, entry_name, entry_point, project_name):
        """Create run.bat script based on project configuration"""
        if entry_point:
            content = self._create_entry_point_script(entry_point)
        else:
            main_file = self._find_main_file(bundle_dir, project_name)
            if main_file:
                content = self._create_main_file_script(main_file)
            else:
                content = self._create_generic_script(project_name)
        
        script_path = Path(bundle_dir) / "run.bat"
        self._write_script(script_path, content)
        return script_path
    
    def _create_entry_point_script(self, entry_point):
        """Create script content for entry point execution"""
        module_name, func_name = entry_point.split(':')
        
        # Handle the src -> core rename in module paths
        if module_name.startswith('src.'):
            module_name = module_name.replace('src.', 'core.', 1)
        elif module_name == 'src':
            module_name = 'core'
        
        return f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe -c "import sys; sys.path.insert(0, '.'); from {module_name} import {func_name}; {func_name}()"

pause
'''
    
    def _create_main_file_script(self, main_file):
        """Create script content for main file execution"""
        return f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe {main_file} %*

pause
'''
    
    def _create_generic_script(self, project_name):
        """Create generic Python launcher script"""
        return f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

echo Starting Python environment for {project_name}
echo Use 'bin\\python.exe script.py' to run Python scripts
echo.

bin\\python.exe

pause
'''
    
    def _find_main_file(self, bundle_dir, project_name):
        """Find main file in bundle directory"""
        bundle_path = Path(bundle_dir)
        candidates = list(PyWestConstants.MAIN_FILE_CANDIDATES) + [f'{project_name}.py']
        
        for candidate in candidates:
            if (bundle_path / candidate).exists():
                return candidate
        
        return None
    
    def _write_script(self, script_path, content):
        """Write script content to file"""
        try:
            with open(script_path, 'w') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"Failed to create run script: {str(e)}")


class SetupScriptGenerator:
    """Generate setup.bat scripts for GUI installers"""
    
    def create_setup_script(self, bundle_dir, project_name):
        """Create setup.bat script for GUI installer"""
        setup_content = self._generate_setup_content(project_name)
        setup_path = Path(bundle_dir) / "setup.bat"
        
        try:
            with open(setup_path, 'w') as f:
                f.write(setup_content)
            return setup_path
        except Exception as e:
            raise Exception(f"Failed to create setup script: {str(e)}")
    
    def _generate_setup_content(self, project_name):
        """Generate setup.bat content"""
        return f'''@echo off
:: Check for admin privileges
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"

:: If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\\getadmin.vbs"
    set params = %*:"="
    echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params%", "", "runas", 1 >> "%temp%\\getadmin.vbs"

    "%temp%\\getadmin.vbs"
    del "%temp%\\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"

cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

start "" /B bin\\pythonw.exe bin\\bin.py

exit
'''
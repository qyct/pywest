from pathlib import Path


class SetupScriptGenerator:
    """Generate setup.bat scripts for GUI installers"""
    
    def __init__(self):
        pass
    
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
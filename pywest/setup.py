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
title {project_name} Setup
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

echo Starting {project_name} installer...
bin\\python.exe installer.py

if %errorlevel% neq 0 (
    echo.
    echo Installation failed. Press any key to exit.
    pause >nul
)
'''


class UninstallScriptGenerator:
    """Generate uninstall scripts"""
    
    def __init__(self):
        pass
    
    def create_uninstall_script(self, install_path, app_name):
        """Create uninstall.bat script"""
        uninstall_content = self._generate_uninstall_content(app_name, install_path)
        uninstall_path = Path(install_path) / "uninstall.bat"
        
        try:
            with open(uninstall_path, 'w') as f:
                f.write(uninstall_content)
            return uninstall_path
        except Exception as e:
            raise Exception(f"Failed to create uninstall script: {str(e)}")
    
    def _generate_uninstall_content(self, app_name, install_path):
        """Generate uninstall.bat content"""
        return f'''@echo off
echo Uninstalling {app_name}...
cd /d "%~dp0"

:: Remove shortcuts
del "%USERPROFILE%\\Desktop\\{app_name}.lnk" 2>nul
del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\{app_name}.lnk" 2>nul

:: Remove from Add/Remove Programs
reg delete "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}" /f 2>nul

:: Remove installation directory
cd ..
rmdir /s /q "{install_path.name}"

echo {app_name} has been uninstalled.
pause
'''


class ScriptPermissionManager:
    """Manage script file permissions"""
    
    @staticmethod
    def set_executable_permissions(script_path):
        """Set executable permissions for script (Windows compatibility)"""
        # On Windows, .bat files are executable by default
        # This method is for future cross-platform compatibility
        pass
    
    @staticmethod
    def validate_script_path(script_path):
        """Validate script path is writable"""
        script_path = Path(script_path)
        
        # Check if directory is writable
        if not script_path.parent.exists():
            try:
                script_path.parent.mkdir(parents=True)
            except Exception as e:
                raise PermissionError(f"Cannot create script directory: {str(e)}")
        
        # Check write permissions
        try:
            test_file = script_path.parent / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise PermissionError(f"No write permission for script directory: {str(e)}")
        
        return True
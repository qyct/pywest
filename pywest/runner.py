"""
runner.py - Generate run.bat scripts for bundled projects
"""

from pathlib import Path


class RunScriptGenerator:
    """Generate run.bat scripts for different project types"""
    
    def __init__(self):
        pass
    
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
        from constants import PyWestConstants
        
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


class RunScriptValidator:
    """Validate run script creation"""
    
    @staticmethod
    def validate_entry_point(entry_point):
        """Validate entry point format"""
        if not entry_point:
            return True, None
        
        if ':' not in entry_point:
            return False, "Entry point must be in format 'module:function'"
        
        parts = entry_point.split(':')
        if len(parts) != 2:
            return False, "Entry point must contain exactly one colon"
        
        module_name, func_name = parts
        if not module_name or not func_name:
            return False, "Both module name and function name are required"
        
        return True, None
    
    @staticmethod
    def get_script_type(entry_point, main_file):
        """Determine the type of script to create"""
        if entry_point:
            return "entry_point"
        elif main_file:
            return "main_file"
        else:
            return "generic"
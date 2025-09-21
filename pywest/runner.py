"""
pywest.runner - Functions for creating run.bat scripts
"""

from pathlib import Path


def create_run_script(bundle_dir, entry_name, entry_point, project_name):
    """Create run.bat script for the bundled project"""
    if entry_point:
        # If entry point is defined, use it
        module_name, func_name = entry_point.split(':')
        bat_content = f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe -c "import sys; sys.path.insert(0, '.'); from {module_name} import {func_name}; {func_name}()"

pause
'''
    else:
        # If no entry point, try to find main.py or create a simple runner
        main_files = ['main.py', f'{project_name}.py', '__main__.py']
        main_file = None
        
        for mf in main_files:
            if (bundle_dir / mf).exists():
                main_file = mf
                break
        
        if main_file:
            bat_content = f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe {main_file} %*

pause
'''
        else:
            # Create a generic Python launcher
            bat_content = f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

echo Starting Python environment for {project_name}
echo Use 'bin\\python.exe script.py' to run Python scripts
echo.

bin\\python.exe

pause
'''
    
    bat_path = bundle_dir / "run.bat"
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    
    return bat_path


def create_run_script_content(entry_name, entry_point, project_name, has_main_file=False, main_file=None):
    """Generate run.bat content without writing to file"""
    if entry_point:
        # If entry point is defined, use it
        module_name, func_name = entry_point.split(':')
        return f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe -c "import sys; sys.path.insert(0, '.'); from {module_name} import {func_name}; {func_name}()"

pause
'''
    elif has_main_file and main_file:
        return f'''@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PATH=%~dp0bin;%PATH%

bin\\python.exe {main_file} %*

pause
'''
    else:
        # Create a generic Python launcher
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


def find_main_file(bundle_dir, project_name):
    """Find the main Python file to run"""
    main_files = ['main.py', f'{project_name}.py', '__main__.py']
    
    for mf in main_files:
        if (bundle_dir / mf).exists():
            return mf
    
    return None
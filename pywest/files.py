import shutil
from pathlib import Path
from .log import StylePrinter
from .const import PyWestConstants


class ProjectFileManager:
    """Manage project file operations"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def copy_project_files(self, source_path, target_path, exclude_pyproject=True):
        """Copy project files to target directory"""
        self.printer.progress("Copying project files...")
        
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        exclude_items = set(PyWestConstants.EXCLUDE_PATTERNS)
        if exclude_pyproject:
            exclude_items.add('pyproject.toml')
        
        file_count = 0
        
        try:
            for item in source_path.iterdir():
                if item.name in exclude_items:
                    continue
                
                dest = target_path / item.name
                
                if item.is_dir():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                    file_count += len(list(item.rglob('*')))
                else:
                    shutil.copy2(item, dest)
                    file_count += 1
            
            self.printer.progress_done(f"Copied {file_count} project files")
            return file_count
            
        except Exception as e:
            raise Exception(f"Failed to copy project files: {str(e)}")
    
    def find_main_file(self, project_path, project_name):
        """Find the main Python file to run"""
        project_path = Path(project_path)
        
        candidates = list(PyWestConstants.MAIN_FILE_CANDIDATES) + [f'{project_name}.py']
        
        for candidate in candidates:
            if (project_path / candidate).exists():
                return candidate
        
        return None
    
    def validate_project_path(self, project_path):
        """Validate project path exists and is a directory"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' not found")
        
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_path}' is not a directory")
        
        return project_path


class BundleDirectoryManager:
    """Manage bundle directory creation and cleanup"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def create_bundle_directory(self, output_path, bundle_name):
        """Create bundle directory, handling existing directories"""
        bundle_dir = Path(output_path) / bundle_name
        
        if bundle_dir.exists():
            if not self._confirm_overwrite(bundle_dir):
                return None
            
            self._remove_existing_directory(bundle_dir)
        
        try:
            bundle_dir.mkdir(parents=True)
            return bundle_dir
        except PermissionError as e:
            raise PermissionError(f"Cannot create bundle directory. Check permissions: {str(e)}")
    
    def _confirm_overwrite(self, bundle_dir):
        """Ask user confirmation to overwrite existing directory"""
        from .const import Colors
        
        self.printer.warning(f"Bundle directory already exists: {bundle_dir}")
        response = input(Colors.YELLOW + "?" + Colors.RESET + " Overwrite existing bundle? [y/N]: ").strip().lower()
        
        if response not in ('y', 'yes'):
            self.printer.info("Bundle creation cancelled")
            return False
        
        return True
    
    def _remove_existing_directory(self, bundle_dir):
        """Remove existing bundle directory"""
        try:
            self.printer.progress("Removing existing bundle...")
            shutil.rmtree(bundle_dir)
            self.printer.progress_done("Existing bundle removed")
        except PermissionError as e:
            raise PermissionError(f"Cannot remove existing bundle directory. Files may be in use: {str(e)}")
    
    def cleanup_on_error(self, bundle_dir):
        """Clean up partial bundle on error"""
        if bundle_dir and Path(bundle_dir).exists():
            try:
                shutil.rmtree(bundle_dir)
            except Exception:
                pass  # Best effort cleanup
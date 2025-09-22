import shutil
from pathlib import Path
from .ui import StylePrinter
from .const import PyWestConstants, Colors


class ProjectFileManager:
    """Manage project file operations"""
    
    def __init__(self):
        self.printer = StylePrinter()
    
    def copy_project_files(self, source_path, target_path, exclude_pyproject=True, icon_path=None):
        """Copy project files to target directory"""
        self.printer.progress("Copying project files...")
        
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        exclude_items = set(PyWestConstants.EXCLUDE_PATTERNS)
        if exclude_pyproject:
            exclude_items.add('pyproject.toml')
        
        # Exclude the icon file from main copy to avoid duplication
        if icon_path and icon_path.exists():
            exclude_items.add(icon_path.name)
        
        file_count = 0
        
        try:
            for item in source_path.iterdir():
                if item.name in exclude_items:
                    continue
                
                # Rename 'src' folder to 'core' during copy
                if item.name == 'src' and item.is_dir():
                    dest = target_path / 'core'
                    # Copy src folder with icon exclusion if icon is inside src
                    if icon_path and icon_path.exists() and icon_path.is_relative_to(item):
                        # Custom copy for src folder to exclude icon
                        self._copy_directory_excluding_file(item, dest, icon_path)
                    else:
                        shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                    file_count += len(list(item.rglob('*'))) - (1 if icon_path and icon_path.is_relative_to(item) else 0)
                else:
                    dest = target_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                        file_count += len(list(item.rglob('*')))
                    else:
                        shutil.copy2(item, dest)
                        file_count += 1
            
            # Ensure core directory exists
            core_dir = target_path / "core"
            core_dir.mkdir(exist_ok=True)
            
            # Copy icon to core folder if specified, preserving original filename
            if icon_path and icon_path.exists():
                icon_dest = core_dir / icon_path.name
                shutil.copy2(icon_path, icon_dest)
                file_count += 1
                self.printer.dim(f"Icon copied: {icon_path.name}")
            
            self.printer.progress_done(f"Copied {file_count} project files")
            return file_count
            
        except Exception as e:
            raise Exception(f"Failed to copy project files: {str(e)}")
    
    def _copy_directory_excluding_file(self, src_dir, dest_dir, exclude_file):
        """Copy directory contents excluding a specific file"""
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for item in src_dir.rglob('*'):
            if item == exclude_file:
                continue
            
            rel_path = item.relative_to(src_dir)
            dest_item = dest_dir / rel_path
            
            if item.is_dir():
                dest_item.mkdir(parents=True, exist_ok=True)
            else:
                dest_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_item)
    
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
                pass
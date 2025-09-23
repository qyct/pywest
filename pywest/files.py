import os
import shutil
from pathlib import Path

class ProjectValidator:
    """Validate project directory and structure"""
    
    def validate_project_directory(self, project_path):
        """Validate project directory exists and is accessible"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' not found")
        
        if not project_path.is_dir():
            raise NotADirectoryError(f"'{project_path}' is not a directory")
        
        if not os.access(project_path, os.R_OK):
            raise PermissionError(f"No read permission for project directory: {project_path}")
        
        return project_path

class ProjectFileManager:
    """Manage project file operations"""
    
    def __init__(self):
        self.exclude_patterns = {'.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.venv', 'venv'}
    
    def copy_project_files(self, source_path, target_path):
        """Copy project files to target directory, excluding pyproject.toml"""
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        exclude_items = set(self.exclude_patterns)
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
            
            return file_count
            
        except Exception as e:
            raise Exception(f"Failed to copy project files: {str(e)}")


class BundleDirectoryManager:
    """Manage bundle directory creation and cleanup"""
    
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
        print(f"Bundle directory already exists: {bundle_dir}")
        response = input("Overwrite existing bundle? [y/N]: ").strip().lower()
        
        if response not in ('y', 'yes'):
            print("Bundle creation cancelled")
            return False
        
        return True
    
    def _remove_existing_directory(self, bundle_dir):
        """Remove existing bundle directory"""
        try:
            shutil.rmtree(bundle_dir)
        except PermissionError as e:
            raise PermissionError(f"Cannot remove existing bundle directory. Files may be in use: {str(e)}")
    
    def cleanup_on_error(self, bundle_dir):
        """Clean up partial bundle on error"""
        if bundle_dir and Path(bundle_dir).exists():
            try:
                shutil.rmtree(bundle_dir)
            except Exception:
                pass
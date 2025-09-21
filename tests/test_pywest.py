"""
Simple tests for pywest package
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add the parent directory to Python path to import pywest
sys.path.insert(0, str(Path(__file__).parent.parent))

from pywest import PyWest, StylePrinter, Colors
from pywest.utils import get_compression_level_for_zip, get_7zip_compression_args
from pywest.run import create_run_script_content, find_main_file
from pywest.inst import create_setup_bat_content, create_installer_gui_script


class TestPyWest:
    """Test PyWest main class"""
    
    def test_pywest_init(self):
        """Test PyWest initialization"""
        pywest = PyWest()
        assert pywest.python_version == "3.12.10"
        assert pywest.compression_level == 6
        assert "3.12.10" in pywest.python_embed_url
    
    def test_check_7zip_available(self):
        """Test 7-Zip availability check"""
        pywest = PyWest()
        # This might be True or False depending on system
        result = pywest.check_7zip_available()
        assert isinstance(result, bool)
    
    def test_load_pyproject_nonexistent(self):
        """Test loading non-existent pyproject.toml"""
        pywest = PyWest()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            result = pywest.load_pyproject(temp_path)
            assert result is None
    
    def test_get_dependencies_none(self):
        """Test getting dependencies with no pyproject data"""
        pywest = PyWest()
        deps = pywest.get_dependencies(None)
        assert deps == []
    
    def test_get_entry_point_none(self):
        """Test getting entry point with no pyproject data"""
        pywest = PyWest()
        name, point = pywest.get_entry_point(None)
        assert name is None
        assert point is None


class TestStylePrinter:
    """Test StylePrinter class"""
    
    def test_style_printer_methods_exist(self):
        """Test that StylePrinter has all required methods"""
        assert hasattr(StylePrinter, 'info')
        assert hasattr(StylePrinter, 'success')
        assert hasattr(StylePrinter, 'warning')
        assert hasattr(StylePrinter, 'error')
        assert hasattr(StylePrinter, 'progress')
        assert hasattr(StylePrinter, 'progress_done')
    
    def test_colors_class(self):
        """Test Colors class has required attributes"""
        assert hasattr(Colors, 'RESET')
        assert hasattr(Colors, 'BRIGHT_GREEN')
        assert hasattr(Colors, 'BRIGHT_RED')
        assert hasattr(Colors, 'YELLOW')
        assert Colors.RESET == '\033[0m'


class TestUtils:
    """Test utility functions"""
    
    def test_get_compression_level_for_zip(self):
        """Test ZIP compression level conversion"""
        import zipfile
        
        # Test store level
        method, level = get_compression_level_for_zip(0)
        assert method == zipfile.ZIP_STORED
        
        # Test deflate levels
        method, level = get_compression_level_for_zip(6)
        assert method == zipfile.ZIP_DEFLATED
        
        method, level = get_compression_level_for_zip(9)
        assert method == zipfile.ZIP_DEFLATED
    
    def test_get_7zip_compression_args(self):
        """Test 7-Zip compression arguments"""
        # Test store
        args = get_7zip_compression_args(0)
        assert '-mx0' in args
        
        # Test maximum
        args = get_7zip_compression_args(9)
        assert '-mx9' in args
        
        # Test default fallback
        args = get_7zip_compression_args(6)
        assert isinstance(args, list)
        assert len(args) > 0


class TestRunner:
    """Test runner script functions"""
    
    def test_create_run_script_content_with_entry_point(self):
        """Test creating run script content with entry point"""
        content = create_run_script_content("myapp", "myapp.main:main", "myproject")
        assert "bin\\python.exe -c" in content
        assert "from myapp.main import main" in content
        assert "@echo off" in content
    
    def test_create_run_script_content_with_main_file(self):
        """Test creating run script content with main file"""
        content = create_run_script_content(None, None, "myproject", True, "main.py")
        assert "bin\\python.exe main.py" in content
        assert "@echo off" in content
    
    def test_create_run_script_content_generic(self):
        """Test creating generic run script content"""
        content = create_run_script_content(None, None, "myproject", False, None)
        assert "Starting Python environment for myproject" in content
        assert "@echo off" in content
    
    def test_find_main_file(self):
        """Test finding main file in project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test with no main files
            result = find_main_file(temp_path, "testproject")
            assert result is None
            
            # Test with main.py
            main_file = temp_path / "main.py"
            main_file.write_text("# test main file")
            result = find_main_file(temp_path, "testproject")
            assert result == "main.py"


class TestInstaller:
    """Test installer script functions"""
    
    def test_create_setup_bat_content(self):
        """Test creating setup.bat content"""
        content = create_setup_bat_content("MyApp")
        assert "@echo off" in content
        assert "MyApp Setup" in content
        assert "bin\\python.exe installer.py" in content
    
    def test_create_installer_gui_script(self):
        """Test creating installer GUI script"""
        script = create_installer_gui_script("TestApp")
        assert "import dearpygui.dearpygui as dpg" in script
        assert "class Installer:" in script
        assert "TestApp" in script
        assert "def run(self):" in script


class TestProjectStructure:
    """Test project structure and integration"""
    
    def test_package_imports(self):
        """Test that all modules can be imported"""
        try:
            import pywest
            from pywest import PyWest, StylePrinter, Colors, main
            from pywest.bundle import PyWest as BundlerPyWest
            from pywest.utils import StylePrinter as UtilsStylePrinter
            from pywest.run import create_run_script
            from pywest.inst import create_setup_script
        except ImportError as e:
            pytest.fail(f"Failed to import pywest modules: {e}")
    
    def test_cli_main_callable(self):
        """Test that CLI main function is callable"""
        from pywest.cli import main
        assert callable(main)


class TestFileOperations:
    """Test file operations without actual file creation"""
    
    def test_project_validation(self):
        """Test project path validation logic"""
        pywest = PyWest()
        
        # Test with non-existent path
        with pytest.raises(FileNotFoundError):
            pywest.bundle_project("nonexistent_project")
    
    def test_bundle_name_generation(self):
        """Test bundle name logic"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            project_dir = temp_path / "test_project"
            project_dir.mkdir()
            
            # Create a simple test file
            (project_dir / "main.py").write_text("print('hello')")
            
            # The project should exist now
            assert project_dir.exists()
            assert project_dir.is_dir()


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
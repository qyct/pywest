"""
Pytest configuration for pywest tests
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary test project directory"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create a simple main.py
    main_file = project_dir / "main.py"
    main_file.write_text('print("Hello from test project!")')
    
    # Create a simple pyproject.toml
    pyproject_file = project_dir / "pyproject.toml"
    pyproject_content = """[project]
name = "test-project"
version = "0.1.0"
dependencies = []

[project.scripts]
test-project = "main:main"
"""
    pyproject_file.write_text(pyproject_content)
    
    return project_dir


@pytest.fixture
def sample_pyproject_data():
    """Sample pyproject.toml data for testing"""
    return {
        'project': {
            'name': 'test-app',
            'version': '0.1.0',
            'dependencies': ['requests', 'click'],
            'scripts': {
                'test-app': 'test_app.main:main'
            }
        }
    }
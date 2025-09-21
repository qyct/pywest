# PyWest

A tool to pack Python projects with embeddable Python for Windows distribution.

## Features

- 📦 Bundle Python projects with embeddable Python
- 🗜️ Support for ZIP and 7-Zip compression with configurable levels (0-9)
- 🎯 GUI installer with DearPyGui for professional installation experience
- 🔗 Automatic shortcut creation (Desktop, Start Menu)
- 📋 Add/Remove Programs integration
- ⚙️ Smart dependency detection from pyproject.toml
- 🚀 Entry point support for seamless execution

## Installation

```bash
pip install pywest
```

Or install in development mode:

```bash
git clone https://github.com/qyct/pywest.git
cd pywest
pip install -e .
```

## Usage

### Basic Usage

```bash
# Create a folder bundle (default)
pywest my_project

# Create a ZIP bundle
pywest my_project --zip

# Create a 7-Zip bundle with maximum compression
pywest my_project --7zip -c 9

# Use custom bundle name
pywest my_project --name MyApplication --zip
```

### Command Line Options

```
Usage:
    pywest                           Show help information
    pywest <project_name>            Bundle project as folder (default)
    pywest <project_name> --zip      Bundle project as ZIP file
    pywest <project_name> --7zip     Bundle project as 7Z file

Options:
    --zip, -z                        Create bundle as ZIP instead of folder
    --7zip, -7                       Create bundle as 7Z instead of folder
    --compression, -c LEVEL          Compression level (0-9, default: 6)
                                     0=store, 1=fastest, 6=default, 9=best
    --python VERSION                 Specify Python version (default: 3.12.10, also supports: 3.11.9)
    --name, -n NAME                  Custom name for the bundle (default: <project_name>_bundle)
```

### Examples

```bash
# Basic folder bundle
pywest my_app

# ZIP with high compression
pywest my_app --zip -c 9

# 7-Zip with custom name and maximum compression
pywest my_app --7zip -c 9 --name "My Application"

# Use Python 3.11.9
pywest my_app --python 3.11.9 --zip

# Create installer-ready bundle
pywest my_app --name "MyApp"
```

## Bundle Structure

Each bundle includes:

- `bin/` - Embeddable Python installation
- `run.bat` - Direct execution launcher
- `setup.bat` - GUI installer launcher
- `installer.py` - DearPyGui-based installer
- Your project files and dependencies

## GUI Installer Features

The included `setup.bat` launches a professional installer GUI that provides:

- **Installation Path Selection** - Browse and choose installation directory
- **Desktop Shortcut** - Optional desktop shortcut creation
- **Start Menu Shortcut** - Optional start menu integration
- **Add/Remove Programs** - Register in Windows Add/Remove Programs
- **Progress Tracking** - Real-time installation progress with status updates
- **Uninstaller** - Automatic uninstaller creation for clean removal

## Requirements

- **Windows** environment (for target deployment)
- **Python 3.11+** for building
- **7-Zip** (optional, for --7zip compression)
- Project with optional `pyproject.toml` for dependency management

## Supported Python Versions

- Python 3.12.10 (default)
- Python 3.11.9

## Project Configuration

PyWest automatically reads `pyproject.toml` files and:

- Installs dependencies listed in `project.dependencies`
- Uses entry points defined in `project.scripts`
- Detects main files (`main.py`, `<project_name>.py`, `__main__.py`)

Example `pyproject.toml`:

```toml
[project]
name = "my-app"
dependencies = [
    "requests",
    "click"
]

[project.scripts]
my-app = "my_app.main:main"
```

## Bundle Distribution

Created bundles are completely portable and can be distributed as:

1. **Folder bundles** - Ready to run with `run.bat`
2. **ZIP archives** - Compressed for easy sharing
3. **7-Zip archives** - Maximum compression for minimal file size
4. **Installer packages** - Professional installation via `setup.bat`

## License

Apache License 2.0 - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/qyct/pywest/issues
- Documentation: https://github.com/qyct/pywest

---

**PyWest** - Making Python application distribution on Windows simple and professional.
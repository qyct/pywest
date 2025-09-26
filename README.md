# PyWest
*Python Windows Embedded Setup Tool*

![PyWest Logo](https://raw.githubusercontent.com/qyct/pywest/main/icon.png)

A tool to pack Python projects with embeddable Python for Windows distribution.

**🔗 GitHub Repository:** [https://github.com/qyct/pywest](https://github.com/qyct/pywest)

## Features

- 📦 Bundle Python projects with embeddable Python
- 🗜️ Support for ZIP compression with configurable levels (0-9)
- 🎯 GUI installer with professional installation experience
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

# Create a ZIP bundle with maximum compression
pywest my_project --zip -c 9

# Use custom bundle name
pywest my_project --name MyApplication --zip
```

### Command Line Options

```
Usage:
    pywest                           Show help information
    pywest <project_name>            Bundle project as folder (default)
    pywest <project_name> --zip      Bundle project as ZIP file

Options:
    --zip, -z                        Create bundle as ZIP instead of folder
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

# Custom name with maximum compression
pywest my_app --zip -c 9 --name "My Application"

# Use Python 3.11.9
pywest my_app --python 3.11.9 --zip

# Create installer-ready bundle
pywest my_app --name "MyApp"
```

## Bundle Structure

Each bundle includes:

- `bin/` - Embeddable Python installation with dependencies
- `run.bat` - Direct execution launcher
- `setup.bat` - GUI installer launcher
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
- Project with `pyproject.toml` for dependency management

## Supported Python Versions

- Python 3.12.10 (default)
- Python 3.11.9

## Project Configuration

PyWest requires a `pyproject.toml` file with proper configuration:

### Required Configuration

```toml
[project]
name = "my-app"
dependencies = [
    "requests",
    "click"
]

[tool.pywest]
entry = "myapp.main:main"        # Required: module:function entry point
```

### Optional Configuration

```toml
[tool.pywest]
entry = "myapp.main:main"        # Required entry point
icon = "src/icon.png"            # Optional: path to icon file (PNG, JPG, ICO supported)
```

### Entry Point Format

The entry point must follow the format `module.name:function_name`:

- `module.name` - Python module path (e.g., `myapp.main`)
- `function_name` - Function to call (e.g., `main`)

Example project structure:
```
my-project/
├── myapp/
│   ├── __init__.py
│   └── main.py          # Contains main() function
├── pyproject.toml
└── icon.png             # Optional
```

## Bundle Distribution

Created bundles are completely portable and can be distributed as:

1. **Folder bundles** - Ready to run with `run.bat`
2. **ZIP archives** - Compressed for easy sharing
3. **Installer packages** - Professional installation via `setup.bat`

Users can either:
- Run directly using `run.bat`
- Install permanently using `setup.bat` (creates shortcuts, uninstaller, etc.)

## Icon Support

PyWest supports various image formats for icons:
- PNG, JPG, JPEG, BMP, TIFF, GIF
- ICO files (will be resized to 256x256 if needed)
- If no icon is specified, a default icon is generated

Icons are automatically converted to 256x256 ICO format for Windows compatibility.

## Contributing

Contributions are welcome! Please visit the [GitHub repository](https://github.com/qyct/pywest) to:
- Report issues
- Submit pull requests
- View the source code
- Check the latest releases

---

**PyWest** - Making Python application distribution on Windows simple and professional.
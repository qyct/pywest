import sys
import argparse
from .core import ProjectBundler
from .utils import StylePrinter


class PyWestCLI:
    def __init__(self):
        self.printer = StylePrinter()

    def create_parser(self):
        """Create command line argument parser"""
        parser = argparse.ArgumentParser(description='pywest - Python Project Bundler for Windows')
        parser.add_argument('project_name', nargs='?', help='Name of the project directory to bundle')
        parser.add_argument('--zip', '-z', action='store_true', help='Create bundle as ZIP instead of folder')
        parser.add_argument('--compression', '-c', type=int, default=6, choices=range(0, 10),
                           help='Compression level (0-9, default: 6). 0=store, 1=fastest, 6=default, 9=best')
        parser.add_argument('--python', default='3.12.10', 
                           choices=['3.12.10', '3.11.9'], 
                           help='Python version to use (default: 3.12.10)')
        parser.add_argument('--name', '-n', 
                           help='Custom name for the bundle (default: <project_name>_bundle)')
        return parser

    def print_help_info(self):
        """Print CLI help information"""
        print("\npywest - Python Project Bundler for Windows\n")
        print("Usage:")
        print("    pywest                           Show this help information")
        print("    pywest <project_name>            Bundle project as folder (default)")
        print("    pywest <project_name> --zip      Bundle project as ZIP file")
        print("\nOptions:")
        print("    --zip, -z                        Create bundle as ZIP instead of folder")
        print("    --compression, -c LEVEL          Compression level (0-9, default: 6)")
        print("    --python VERSION                 Specify Python version (default: 3.12.10)")
        print("    --name, -n NAME                  Custom name for the bundle")
        print("\nProject Configuration:")
        print("    PyWest requires a pyproject.toml file in your project directory with")
        print("    the following [tool.pywest] section:")
        print("\n    Example pyproject.toml:")
        print("    [project]")
        print("    name = \"my-app\"")
        print("    dependencies = [")
        print("        \"requests>=2.25.0\",")
        print("        \"flask>=2.0.0\"")
        print("    ]")
        print("\n    [tool.pywest]")
        print("    entry = \"myapp.main:main\"        # Required: module:function entry point")
        print("    icon = \"src/icon.png\"             # Optional: path to icon file")
        print("\nExamples:")
        print("    pywest my-project                Bundle 'my-project' as folder")
        print("    pywest my-project --zip          Bundle 'my-project' as ZIP file")
        print("    pywest my-project -n MyApp       Bundle with custom name 'MyApp'")
        print("    pywest my-project -c 9           Bundle with maximum compression")

    def run(self):
        """Main CLI entry point"""
        parser = self.create_parser()
        args = parser.parse_args()

        if not args.project_name:
            self.print_help_info()
            return 0

        try:
            bundler = ProjectBundler(
                python_version=args.python,
                compression_level=args.compression
            )

            bundle_type = 'zip' if args.zip else 'folder'
            result = bundler.bundle_project(args.project_name, bundle_type, args.name)

            return 0 if result else 1

        except KeyboardInterrupt:
            self.printer.warning("Operation cancelled by user")
            return 1
        except Exception as _:
            return 1


def main():
    """Entry point function"""
    cli = PyWestCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
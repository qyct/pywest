from pathlib import Path


SETUP_PY_CONTENT = '''"""
GUI Installer for PROJECT_NAME_PLACEHOLDER
"""

import dearpygui.dearpygui as dpg
import os
import shutil
import subprocess
import threading
import winreg
import sys
from pathlib import Path


class Installer:
    def __init__(self, app_name="PROJECT_NAME_PLACEHOLDER"):
        self.app_name = app_name
        self.bundle_dir = Path(__file__).parent.parent
        self.default_install_path = Path.home() / "AppData" / "Local" / app_name
        self.install_path = str(self.default_install_path)
        self.create_desktop_shortcut = True
        self.create_startmenu_shortcut = True
        self.add_to_programs = True
        self.installing = False
        
    def browse_folder(self):
        """Browse for installation folder"""
        dpg.show_item("file_dialog")
    
    def folder_selected(self, sender, app_data):
        """Handle folder selection"""
        if app_data and app_data.get('file_path_name'):
            self.install_path = app_data['file_path_name']
            dpg.set_value("install_path", self.install_path)
    
    def create_desktop_shortcut(self, install_path):
        """Create desktop shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            shortcut = shell.CreateShortCut(os.path.join(desktop, f"{self.app_name}.lnk"))
            shortcut.Targetpath = str(install_path / "run.bat")
            shortcut.WorkingDirectory = str(install_path)
            shortcut.IconLocation = str(install_path / "bin" / "python.exe")
            shortcut.save()
        except:
            pass
    
    def create_startmenu_shortcut(self, install_path):
        """Create start menu shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            programs = shell.SpecialFolders("Programs")
            shortcut = shell.CreateShortCut(os.path.join(programs, f"{self.app_name}.lnk"))
            shortcut.Targetpath = str(install_path / "run.bat")
            shortcut.WorkingDirectory = str(install_path)
            shortcut.IconLocation = str(install_path / "bin" / "python.exe")
            shortcut.save()
        except:
            pass
    
    def add_to_add_remove_programs(self, install_path):
        """Add to Add/Remove Programs"""
        try:
            key_path = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\" + self.app_name
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, self.app_name)
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, 
                                str(install_path / "uninstall.bat"))
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_path))
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "PyWest Bundle")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
        except:
            pass
    
    def create_uninstaller(self, install_path):
        """Create uninstaller script"""
        uninstall_lines = [
            "@echo off",
            f"echo Uninstalling {self.app_name}...",
            'cd /d "%~dp0"',
            "",
            ":: Remove shortcuts",
            f'del "%USERPROFILE%\\\\Desktop\\\\{self.app_name}.lnk" 2>nul',
            f'del "%APPDATA%\\\\Microsoft\\\\Windows\\\\Start Menu\\\\Programs\\\\{self.app_name}.lnk" 2>nul',
            "",
            ":: Remove from Add/Remove Programs",
            f'reg delete "HKCU\\\\SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\{self.app_name}" /f 2>nul',
            "",
            ":: Remove installation directory",
            "cd ..",
            f'rmdir /s /q "{install_path.name}"',
            "",
            f"echo {self.app_name} has been uninstalled.",
            "pause"
        ]
        
        uninstall_content = "\\n".join(uninstall_lines)
        
        with open(install_path / "uninstall.bat", 'w') as f:
            f.write(uninstall_content)
    
    def install_files(self):
        """Install files with progress updates"""
        try:
            install_path = Path(self.install_path)
            install_path.mkdir(parents=True, exist_ok=True)
            
            # Get total files for progress
            total_files = sum(1 for _ in self.bundle_dir.rglob('*') if _.is_file())
            copied_files = 0
            
            dpg.set_value("status_text", "Copying files...")
            
            # Copy all files except the installer itself
            for item in self.bundle_dir.iterdir():
                if item.name in ['setup.bat']:
                    continue
                    
                dest = install_path / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                    # Count files in directory for progress
                    for _ in item.rglob('*'):
                        if _.is_file():
                            copied_files += 1
                            if total_files > 0:
                                progress = copied_files / total_files
                                dpg.set_value("progress_bar", progress)
                else:
                    shutil.copy2(item, dest)
                    copied_files += 1
                    if total_files > 0:
                        progress = copied_files / total_files
                        dpg.set_value("progress_bar", progress)
            
            # Create shortcuts and registry entries
            if self.create_desktop_shortcut:
                dpg.set_value("status_text", "Creating desktop shortcut...")
                self.create_desktop_shortcut(install_path)
            
            if self.create_startmenu_shortcut:
                dpg.set_value("status_text", "Creating start menu shortcut...")
                self.create_startmenu_shortcut(install_path)
            
            if self.add_to_programs:
                dpg.set_value("status_text", "Adding to Add/Remove Programs...")
                self.add_to_add_remove_programs(install_path)
                self.create_uninstaller(install_path)
            
            dpg.set_value("status_text", "Installation completed successfully!")
            dpg.set_value("progress_bar", 1.0)
            dpg.set_value("install_button", "Close")
            
        except Exception as e:
            dpg.set_value("status_text", f"Installation failed: {str(e)}")
            dpg.set_value("install_button", "Close")
        finally:
            self.installing = False
    
    def start_installation(self):
        """Start the installation process"""
        if self.installing:
            dpg.destroy_context()
            return
            
        if dpg.get_value("install_button") == "Close":
            dpg.destroy_context()
            return
            
        self.install_path = dpg.get_value("install_path")
        self.create_desktop_shortcut = dpg.get_value("desktop_shortcut")
        self.create_startmenu_shortcut = dpg.get_value("startmenu_shortcut") 
        self.add_to_programs = dpg.get_value("add_remove_programs")
        
        self.installing = True
        dpg.set_value("install_button", "Installing...")
        dpg.configure_item("install_button", enabled=False)
        
        # Start installation in separate thread
        thread = threading.Thread(target=self.install_files)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Run the installer GUI"""
        dpg.create_context()
        
        # File dialog for folder selection
        with dpg.file_dialog(directory_selector=True, show=False, 
                           callback=self.folder_selected, tag="file_dialog",
                           width=700, height=400):
            dpg.add_file_extension("", color=(255, 255, 255, 255))
        
        with dpg.window(tag="main_window", label=f"{self.app_name} Installer", 
                       width=400, height=320, no_resize=True, no_collapse=True):
            
            dpg.add_text(f"Welcome to {self.app_name} Setup")
            dpg.add_separator()
            
            # Installation path
            dpg.add_text("Installation path:")
            dpg.add_input_text(tag="install_path", default_value=self.install_path, width=280)
            dpg.add_same_line()
            dpg.add_button(label="Browse...", callback=self.browse_folder, width=80)
            
            dpg.add_separator()
            
            # Options
            dpg.add_text("Options:")
            dpg.add_checkbox(tag="desktop_shortcut", label="Create desktop shortcut", 
                           default_value=self.create_desktop_shortcut)
            dpg.add_checkbox(tag="startmenu_shortcut", label="Create start menu shortcut",
                           default_value=self.create_startmenu_shortcut) 
            dpg.add_checkbox(tag="add_remove_programs", label="Add to Add/Remove Programs",
                           default_value=self.add_to_programs)
            
            dpg.add_separator()
            
            # Progress
            dpg.add_text("Ready to install", tag="status_text")
            dpg.add_progress_bar(tag="progress_bar", default_value=0.0, width=-1)
            
            dpg.add_separator()
            
            # Install button
            dpg.add_button(tag="install_button", label="Install", 
                         callback=self.start_installation, width=-1, height=30)
        
        dpg.create_viewport(title=f"{self.app_name} Installer", width=420, height=340,
                          resizable=False)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        dpg.start_dearpygui()
        dpg.destroy_context()


if __name__ == "__main__":
    installer = Installer()
    installer.run()
'''


class InstallerGUIGenerator:
    """Generate GUI installer scripts using DearPyGui"""
    
    def __init__(self):
        pass
    
    def create_installer_script(self, bundle_dir, project_name):
        """Create setup.py GUI script in bin folder"""
        bin_dir = Path(bundle_dir) / "bin"
        bin_dir.mkdir(exist_ok=True)
        
        installer_content = SETUP_PY_CONTENT.replace("PROJECT_NAME_PLACEHOLDER", project_name)
        setup_path = bin_dir / "setup.py"
        
        try:
            with open(setup_path, 'w', encoding='utf-8') as f:
                f.write(installer_content)
            return setup_path
        except Exception as e:
            raise Exception(f"Failed to create setup script: {str(e)}")


class InstallerValidator:
    """Validate installer script generation"""
    
    @staticmethod
    def validate_project_name(project_name):
        """Validate project name for installer"""
        if not project_name:
            return False, "Project name cannot be empty"
        
        if len(project_name.strip()) == 0:
            return False, "Project name cannot be whitespace only"
        
        # Check for invalid Windows filename characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in project_name for char in invalid_chars):
            return False, f"Project name contains invalid characters: {invalid_chars}"
        
        return True, None
    
    @staticmethod
    def validate_installer_dependencies():
        """Check if installer dependencies are available"""
        missing_deps = []
        
        try:
            import dearpygui
        except ImportError:
            missing_deps.append("dearpygui")
        
        try:
            import win32com.client
        except ImportError:
            missing_deps.append("pywin32")
        
        if missing_deps:
            return False, f"Missing installer dependencies: {', '.join(missing_deps)}"
        
        return True, None
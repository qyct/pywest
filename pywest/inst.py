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
from PIL import Image
import tempfile


class Installer:
    def __init__(self, app_name="PROJECT_NAME_PLACEHOLDER"):
        self.app_name = app_name
        self.bundle_dir = Path(__file__).parent.parent
        self.default_install_path = Path("C:/Program Files") / app_name
        self.install_path = str(self.default_install_path)
        self.create_desktop_shortcut_value = True
        self.create_startmenu_shortcut_value = True
        self.add_to_programs_value = True
        self.installing = False
        # Find icon file in core directory (could be any .png file)
        self.icon_path = self._find_icon_file()
        
    def _find_icon_file(self):
        """Find the icon PNG file in the core directory"""
        core_dir = self.bundle_dir / "core"
        if not core_dir.exists():
            return None
        
        # Look for any PNG file in the core directory (likely the project icon)
        png_files = list(core_dir.glob("*.png"))
        return png_files[0] if png_files else None
    
    def browse_folder(self):
        """Browse for installation folder"""
        dpg.show_item("file_dialog")
    
    def folder_selected(self, sender, app_data):
        """Handle folder selection"""
        if app_data and app_data.get('file_path_name'):
            self.install_path = app_data['file_path_name']
            dpg.set_value("install_path", self.install_path)
    
    def create_desktop_shortcut_func(self, install_path):
        """Create desktop shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            shortcut = shell.CreateShortCut(os.path.join(desktop, f"{self.app_name}.lnk"))
            shortcut.Targetpath = str(install_path / "run.bat")
            shortcut.WorkingDirectory = str(install_path)
            
            # Use icon from core folder if available, otherwise python.exe
            icon_path = install_path / "core"
            icon_files = list(icon_path.glob("*.png")) if icon_path.exists() else []
            if icon_files:
                # Convert PNG to ICO temporarily for shortcut
                try:
                    png_path = icon_files[0]  # Use first PNG found
                    ico_path = png_path.with_suffix('.ico')
                    img = Image.open(png_path)
                    img.save(ico_path, format='ICO', sizes=[(16,16), (32,32), (48,48)])
                    shortcut.IconLocation = str(ico_path)
                except:
                    shortcut.IconLocation = str(install_path / "bin" / "python.exe")
            else:
                shortcut.IconLocation = str(install_path / "bin" / "python.exe")
                
            shortcut.save()
        except:
            pass
    
    def create_startmenu_shortcut_func(self, install_path):
        """Create start menu shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            programs = shell.SpecialFolders("Programs")
            shortcut = shell.CreateShortCut(os.path.join(programs, f"{self.app_name}.lnk"))
            shortcut.Targetpath = str(install_path / "run.bat")
            shortcut.WorkingDirectory = str(install_path)
            
            # Use icon from core folder if available, otherwise python.exe
            icon_path = install_path / "core"
            icon_files = list(icon_path.glob("*.png")) if icon_path.exists() else []
            if icon_files:
                # Convert PNG to ICO temporarily for shortcut
                try:
                    png_path = icon_files[0]  # Use first PNG found
                    ico_path = png_path.with_suffix('.ico')
                    img = Image.open(png_path)
                    img.save(ico_path, format='ICO', sizes=[(16,16), (32,32), (48,48)])
                    shortcut.IconLocation = str(ico_path)
                except:
                    shortcut.IconLocation = str(install_path / "bin" / "python.exe")
            else:
                shortcut.IconLocation = str(install_path / "bin" / "python.exe")
                
            shortcut.save()
        except:
            pass
    
    def add_to_add_remove_programs(self, install_path):
        """Add to Add/Remove Programs"""
        try:
            key_path = r"SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\" + self.app_name
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
            if self.create_desktop_shortcut_value:
                dpg.set_value("status_text", "Creating desktop shortcut...")
                self.create_desktop_shortcut_func(install_path)
            
            if self.create_startmenu_shortcut_value:
                dpg.set_value("status_text", "Creating start menu shortcut...")
                self.create_startmenu_shortcut_func(install_path)
            
            if self.add_to_programs_value:
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
        self.create_desktop_shortcut_value = dpg.get_value("desktop_shortcut")
        self.create_startmenu_shortcut_value = dpg.get_value("startmenu_shortcut") 
        self.add_to_programs_value = dpg.get_value("add_remove_programs")
        
        self.installing = True
        dpg.set_value("install_button", "Installing...")
        dpg.configure_item("install_button", enabled=False)
        
        # Start installation in separate thread
        thread = threading.Thread(target=self.install_files)
        thread.daemon = True
        thread.start()
    
    def load_icon_texture(self):
        """Load icon as texture for display in GUI"""
        if not self.icon_path.exists():
            return None
            
        try:
            # Load and resize icon for GUI display
            with Image.open(self.icon_path) as img:
                # Resize to 48x48 for display
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
                img = img.convert('RGBA')
                
                # Convert to format DearPyGui expects
                width, height = img.size
                img_data = list(img.getdata())
                
                # Convert RGBA tuples to flat list of floats (0-1 range)
                flat_data = []
                for pixel in img_data:
                    flat_data.extend([pixel[0]/255.0, pixel[1]/255.0, pixel[2]/255.0, pixel[3]/255.0])
                
                return dpg.add_raw_texture(width, height, flat_data, format=dpg.mvFormat_Float_rgba)
        except Exception as e:
            print(f"Could not load icon: {e}")
            return None
    
    def run(self):
        """Run the installer GUI"""
        dpg.create_context()
        
        # Load icon texture
        icon_texture = self.load_icon_texture()
        
        # Set default theme to Windows-like gray
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (240, 240, 240))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 255, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (0, 120, 215))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (225, 225, 225))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (229, 241, 251))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (204, 228, 247))
        
        dpg.bind_theme(global_theme)
        
        # File dialog for folder selection
        with dpg.file_dialog(directory_selector=True, show=False, 
                           callback=self.folder_selected, tag="file_dialog",
                           width=700, height=400):
            dpg.add_file_extension("", color=(255, 255, 255, 255))
        
        # Adjust window size based on whether we have an icon
        window_height = 340 if icon_texture else 300
        
        with dpg.window(tag="main_window", label="", 
                       width=280, height=window_height, no_resize=True, no_collapse=True,
                       no_title_bar=True):
            
            # Icon and title header
            if icon_texture:
                with dpg.group(horizontal=True):
                    dpg.add_image(icon_texture)
                    dpg.add_spacer(width=10)
                    with dpg.group():
                        dpg.add_spacer(height=10)
                        dpg.add_text(f"{self.app_name} Installer", color=(0, 0, 0))
                        dpg.add_text("Setup Wizard", color=(100, 100, 100))
                dpg.add_spacer(height=5)
            else:
                dpg.add_text(f"{self.app_name} Installer", color=(0, 0, 0))
                dpg.add_spacer(height=5)
            
            dpg.add_separator()
            
            # Installation path group
            dpg.add_text("Install Location:", color=(0, 0, 0))
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="install_path", default_value=self.install_path, width=180)
                dpg.add_button(label="...", callback=self.browse_folder, width=25)
            
            dpg.add_separator()
            
            # Checkboxes
            dpg.add_checkbox(tag="desktop_shortcut", label="Desktop shortcut", 
                           default_value=self.create_desktop_shortcut_value)
            dpg.add_checkbox(tag="startmenu_shortcut", label="Start menu shortcut",
                           default_value=self.create_startmenu_shortcut_value) 
            dpg.add_checkbox(tag="add_remove_programs", label="Add to Programs list",
                           default_value=self.add_to_programs_value)
            
            dpg.add_separator()
            
            # Progress
            dpg.add_text("Ready to install", tag="status_text", color=(0, 0, 0))
            dpg.add_progress_bar(tag="progress_bar", default_value=0.0, width=-1)
            
            dpg.add_separator()
            
            # Install button
            dpg.add_button(tag="install_button", label="Install", 
                         callback=self.start_installation, width=-1, height=30)
        
        # Adjust viewport size based on window content
        viewport_height = window_height + 20
        dpg.create_viewport(title=f"{self.app_name} Setup", width=300, height=viewport_height,
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
    
    def create_installer_script(self, bundle_dir, project_name):
        """Create bin.py GUI script in bin folder"""
        bin_dir = Path(bundle_dir) / "bin"
        bin_dir.mkdir(exist_ok=True)
        
        installer_content = SETUP_PY_CONTENT.replace("PROJECT_NAME_PLACEHOLDER", project_name)
        setup_path = bin_dir / "bin.py"
        
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
        
        try:
            import PIL
        except ImportError:
            missing_deps.append("Pillow")
        
        if missing_deps:
            return False, f"Missing installer dependencies: {', '.join(missing_deps)}"
        
        return True, None
"""
shortcuts.py - Windows shortcuts and registry management
"""

import os
import winreg
from pathlib import Path


class WindowsShortcutManager:
    """Manage Windows shortcuts creation"""
    
    def __init__(self):
        pass
    
    def create_desktop_shortcut(self, app_name, target_path, working_dir=None, icon_path=None):
        """Create desktop shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            
            shortcut_path = os.path.join(desktop, f"{app_name}.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            
            shortcut.Targetpath = str(target_path)
            
            if working_dir:
                shortcut.WorkingDirectory = str(working_dir)
            
            if icon_path:
                shortcut.IconLocation = str(icon_path)
            
            shortcut.save()
            return True
        except Exception:
            return False
    
    def create_startmenu_shortcut(self, app_name, target_path, working_dir=None, icon_path=None):
        """Create start menu shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            programs = shell.SpecialFolders("Programs")
            
            shortcut_path = os.path.join(programs, f"{app_name}.lnk")
            shortcut = shell.CreateShortCut(shortcut_path)
            
            shortcut.Targetpath = str(target_path)
            
            if working_dir:
                shortcut.WorkingDirectory = str(working_dir)
            
            if icon_path:
                shortcut.IconLocation = str(icon_path)
            
            shortcut.save()
            return True
        except Exception:
            return False
    
    def remove_desktop_shortcut(self, app_name):
        """Remove desktop shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            desktop = shell.SpecialFolders("Desktop")
            shortcut_path = os.path.join(desktop, f"{app_name}.lnk")
            
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            return True
        except Exception:
            return False
    
    def remove_startmenu_shortcut(self, app_name):
        """Remove start menu shortcut"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            programs = shell.SpecialFolders("Programs")
            shortcut_path = os.path.join(programs, f"{app_name}.lnk")
            
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            return True
        except Exception:
            return False


class WindowsRegistryManager:
    """Manage Windows registry entries for Add/Remove Programs"""
    
    def __init__(self):
        pass
    
    def add_to_programs(self, app_name, install_path, uninstall_path, version="1.0.0"):
        """Add application to Add/Remove Programs"""
        try:
            key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}"
            
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, app_name)
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(uninstall_path))
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_path))
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "PyWest Bundle")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, version)
            
            return True
        except Exception:
            return False
    
    def remove_from_programs(self, app_name):
        """Remove application from Add/Remove Programs"""
        try:
            key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            return True
        except Exception:
            return False
    
    def is_registered(self, app_name):
        """Check if application is registered in Add/Remove Programs"""
        try:
            key_path = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{app_name}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path):
                return True
        except Exception:
            return False


class InstallerOptionsManager:
    """Manage installer options and settings"""
    
    def __init__(self, app_name):
        self.app_name = app_name
        self.shortcut_manager = WindowsShortcutManager()
        self.registry_manager = WindowsRegistryManager()
    
    def apply_installation_options(self, install_path, options):
        """Apply selected installation options"""
        results = {}
        
        # Create shortcuts if requested
        if options.get('desktop_shortcut', False):
            run_bat_path = Path(install_path) / "run.bat"
            icon_path = Path(install_path) / "bin" / "python.exe"
            
            results['desktop_shortcut'] = self.shortcut_manager.create_desktop_shortcut(
                self.app_name, run_bat_path, install_path, icon_path
            )
        
        if options.get('startmenu_shortcut', False):
            run_bat_path = Path(install_path) / "run.bat"
            icon_path = Path(install_path) / "bin" / "python.exe"
            
            results['startmenu_shortcut'] = self.shortcut_manager.create_startmenu_shortcut(
                self.app_name, run_bat_path, install_path, icon_path
            )
        
        # Add to Add/Remove Programs if requested
        if options.get('add_to_programs', False):
            uninstall_path = Path(install_path) / "uninstall.bat"
            results['add_to_programs'] = self.registry_manager.add_to_programs(
                self.app_name, install_path, uninstall_path
            )
        
        return results
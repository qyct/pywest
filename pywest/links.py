import os
import winreg
from pathlib import Path
import win32com.client


class WindowsShortcutManager:
    """Manage Windows shortcuts creation"""
    
    def __init__(self):
        pass
    
    def create_desktop_shortcut(self, app_name, target_path, working_dir=None, icon_path=None):
        """Create desktop shortcut"""
        try:
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
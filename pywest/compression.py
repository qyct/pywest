"""
compression.py - Compression utilities for different archive formats
"""

import zipfile

# Optional 7-zip support
try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False


class CompressionUtils:
    """Utilities for handling different compression formats"""
    
    @staticmethod
    def is_py7zr_available():
        """Check if py7zr library is available"""
        return PY7ZR_AVAILABLE
    
    @staticmethod
    def get_zip_compression_settings(level):
        """Convert compression level (0-9) to zipfile settings"""
        if level == 0:
            return zipfile.ZIP_STORED, None
        elif level <= 3:
            return zipfile.ZIP_DEFLATED, level + 3
        elif level <= 6:
            return zipfile.ZIP_DEFLATED, 6
        else:
            return zipfile.ZIP_DEFLATED, 9
    
    @staticmethod
    def get_7zip_compression_filters(level):
        """Get py7zr compression filters for given level"""
        if not PY7ZR_AVAILABLE:
            return None
        
        if level == 0:
            return [{"id": py7zr.FILTER_COPY}]
        elif level <= 2:
            return [{"id": py7zr.FILTER_LZMA2, "preset": 1}]
        elif level <= 4:
            return [{"id": py7zr.FILTER_LZMA2, "preset": 6}]
        elif level <= 6:
            return [{"id": py7zr.FILTER_LZMA2, "preset": 7}]
        elif level <= 8:
            return [{"id": py7zr.FILTER_LZMA2, "preset": 8}]
        else:
            return [{"id": py7zr.FILTER_LZMA2, "preset": 9}]


class ArchiveValidator:
    """Validate archive creation parameters"""
    
    @staticmethod
    def validate_zip_creation(zip_path, compression_level):
        """Validate ZIP archive creation parameters"""
        if zip_path.exists():
            return False, f"ZIP file already exists: {zip_path}"
        
        if not (0 <= compression_level <= 9):
            return False, f"Invalid compression level: {compression_level}"
        
        return True, None
    
    @staticmethod
    def validate_7zip_creation(archive_path, compression_level):
        """Validate 7-Zip archive creation parameters"""
        if not PY7ZR_AVAILABLE:
            return False, "py7zr library not available"
        
        if archive_path.exists():
            return False, f"7Z file already exists: {archive_path}"
        
        if not (0 <= compression_level <= 9):
            return False, f"Invalid compression level: {compression_level}"
        
        return True, None
    
    @staticmethod
    def get_archive_extension(bundle_name, archive_type):
        """Get proper archive extension for bundle name"""
        extensions = {'zip': '.zip', '7zip': '.7z'}
        target_ext = extensions.get(archive_type, '')
        
        if not target_ext:
            return bundle_name
        
        if bundle_name.endswith(target_ext):
            return bundle_name
        else:
            return bundle_name + target_ext
    
    @staticmethod
    def get_folder_name_from_archive(archive_name, archive_type):
        """Get folder name by removing archive extension"""
        extensions = {'.zip': 4, '.7z': 3}
        
        for ext, length in extensions.items():
            if archive_name.endswith(ext):
                return archive_name[:-length]
        
        return archive_name
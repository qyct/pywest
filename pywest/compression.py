"""
compression.py - Compression utilities for different archive formats
"""

import zipfile
import py7zr


class CompressionUtils:
    """Utilities for handling different compression formats"""
    
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


class CompressionLevelMapper:
    """Map compression levels to human-readable descriptions"""
    
    LEVEL_DESCRIPTIONS = {
        0: "Store (no compression)",
        1: "Fastest compression",
        2: "Fast compression", 
        3: "Fast compression",
        4: "Normal compression",
        5: "Normal compression",
        6: "Good compression (default)",
        7: "Better compression",
        8: "Better compression",
        9: "Best compression (slowest)"
    }
    
    @classmethod
    def get_description(cls, level):
        """Get description for compression level"""
        return cls.LEVEL_DESCRIPTIONS.get(level, "Unknown compression level")
    
    @classmethod
    def get_recommended_level(cls, archive_type, file_size_mb=None):
        """Get recommended compression level based on archive type and size"""
        if archive_type == 'zip':
            return 6  # Good balance for ZIP
        elif archive_type == '7zip':
            if file_size_mb and file_size_mb > 100:
                return 7  # Better compression for larger files
            else:
                return 6  # Default for smaller files
        else:
            return 6  # Default fallback


class CompressionEstimator:
    """Estimate compression ratios and times"""
    
    # Rough estimates based on typical file types
    COMPRESSION_RATIOS = {
        'text': {0: 1.0, 1: 0.7, 3: 0.5, 6: 0.4, 9: 0.35},
        'binary': {0: 1.0, 1: 0.9, 3: 0.8, 6: 0.75, 9: 0.7},
        'mixed': {0: 1.0, 1: 0.8, 3: 0.65, 6: 0.55, 9: 0.5}
    }
    
    @classmethod
    def estimate_compressed_size(cls, original_size_mb, compression_level, content_type='mixed'):
        """Estimate compressed file size"""
        ratios = cls.COMPRESSION_RATIOS.get(content_type, cls.COMPRESSION_RATIOS['mixed'])
        
        # Find closest compression level in our ratio table
        closest_level = min(ratios.keys(), key=lambda x: abs(x - compression_level))
        ratio = ratios[closest_level]
        
        return original_size_mb * ratio
    
    @classmethod
    def estimate_compression_time(cls, file_size_mb, compression_level):
        """Estimate compression time in seconds (very rough)"""
        # Base time per MB (seconds) - these are rough estimates
        base_times = {
            0: 0.1,   # Store - very fast
            1: 0.2,   # Fast
            3: 0.4,   # Normal  
            6: 0.8,   # Good
            9: 2.0    # Best - slow
        }
        
        closest_level = min(base_times.keys(), key=lambda x: abs(x - compression_level))
        base_time = base_times[closest_level]
        
        return file_size_mb * base_time
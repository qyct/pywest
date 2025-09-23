import zipfile
import shutil
from pathlib import Path


class ArchiveManager:
    """Manage ZIP archive creation"""
    
    def __init__(self, compression_level=6):
        self.compression_level = compression_level
    
    def create_zip_archive(self, bundle_dir, output_path, archive_name):
        """Create ZIP archive from bundle directory"""
        archive_path = Path(output_path) / archive_name
        
        if archive_path.exists():
            raise ValueError(f"ZIP file already exists: {archive_path}")
        
        if not (0 <= self.compression_level <= 9):
            raise ValueError(f"Invalid compression level: {self.compression_level}")
        
        try:
            compression_method, compress_level = self._get_zip_compression_settings()
            
            with zipfile.ZipFile(archive_path, 'w', compression_method, compresslevel=compress_level) as zipf:
                self._add_directory_to_zip(zipf, bundle_dir)
            
            # Remove the bundle directory after successful archive creation
            shutil.rmtree(bundle_dir)
            
            return archive_path
            
        except Exception as e:
            if archive_path.exists():
                archive_path.unlink()
            raise Exception(f"Failed to create ZIP archive: {str(e)}")
    
    def _get_zip_compression_settings(self):
        """Convert compression level (0-9) to zipfile settings"""
        if self.compression_level == 0:
            return zipfile.ZIP_STORED, None
        elif self.compression_level <= 3:
            return zipfile.ZIP_DEFLATED, self.compression_level + 3
        elif self.compression_level <= 6:
            return zipfile.ZIP_DEFLATED, 6
        else:
            return zipfile.ZIP_DEFLATED, 9
    
    def _add_directory_to_zip(self, zipf, source_dir):
        """Add directory contents to ZIP file"""
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)
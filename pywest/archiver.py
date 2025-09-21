"""
archiver.py - Handle creation of ZIP and 7-Zip archives
"""

import zipfile
import shutil
from pathlib import Path
from printer import StylePrinter
from compression import CompressionUtils, ArchiveValidator

try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False


class ZipArchiver:
    """Create ZIP archives from bundle directories"""
    
    def __init__(self, compression_level=6):
        self.compression_level = compression_level
        self.printer = StylePrinter()
        self.compression_utils = CompressionUtils()
    
    def create_zip_archive(self, bundle_dir, output_path, archive_name):
        """Create ZIP archive from bundle directory"""
        archive_path = Path(output_path) / archive_name
        
        # Validate archive creation
        validator = ArchiveValidator()
        is_valid, error_msg = validator.validate_zip_creation(archive_path, self.compression_level)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            self.printer.progress("Creating ZIP archive...")
            
            compression_method, compress_level = self.compression_utils.get_zip_compression_settings(
                self.compression_level
            )
            
            with zipfile.ZipFile(archive_path, 'w', compression_method, compresslevel=compress_level) as zipf:
                self._add_directory_to_zip(zipf, bundle_dir)
            
            self.printer.progress_done("ZIP archive created")
            return archive_path
            
        except Exception as e:
            # Clean up on failure
            if archive_path.exists():
                archive_path.unlink()
            raise Exception(f"Failed to create ZIP archive: {str(e)}")
    
    def _add_directory_to_zip(self, zipf, source_dir):
        """Add directory contents to ZIP file"""
        source_path = Path(source_dir)
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(source_path.parent)
                zipf.write(file_path, arcname)


class SevenZipArchiver:
    """Create 7-Zip archives from bundle directories"""
    
    def __init__(self, compression_level=6):
        self.compression_level = compression_level
        self.printer = StylePrinter()
        self.compression_utils = CompressionUtils()
    
    def create_7zip_archive(self, bundle_dir, output_path, archive_name):
        """Create 7-Zip archive from bundle directory"""
        if not PY7ZR_AVAILABLE:
            raise Exception("py7zr library is not installed. Install it with: pip install py7zr")
        
        archive_path = Path(output_path) / archive_name
        
        # Validate archive creation
        validator = ArchiveValidator()
        is_valid, error_msg = validator.validate_7zip_creation(archive_path, self.compression_level)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            self.printer.progress("Creating 7Z archive...")
            
            compression_filters = self.compression_utils.get_7zip_compression_filters(
                self.compression_level
            )
            
            with py7zr.SevenZipFile(archive_path, 'w', filters=compression_filters) as archive:
                archive.writeall(bundle_dir, Path(bundle_dir).name)
            
            self.printer.progress_done("7Z archive created")
            return archive_path
            
        except Exception as e:
            # Clean up on failure
            if archive_path.exists():
                archive_path.unlink()
            raise Exception(f"Failed to create 7Z archive: {str(e)}")


class ArchiveManager:
    """Manage archive creation workflow"""
    
    def __init__(self, compression_level=6):
        self.compression_level = compression_level
        self.zip_archiver = ZipArchiver(compression_level)
        self.seven_zip_archiver = SevenZipArchiver(compression_level)
        self.printer = StylePrinter()
    
    def create_archive(self, bundle_dir, output_path, archive_name, archive_type):
        """Create archive based on specified type"""
        if archive_type == 'zip':
            return self._create_zip_workflow(bundle_dir, output_path, archive_name)
        elif archive_type == '7zip':
            return self._create_7zip_workflow(bundle_dir, output_path, archive_name)
        else:
            raise ValueError(f"Unsupported archive type: {archive_type}")
    
    def _create_zip_workflow(self, bundle_dir, output_path, archive_name):
        """Complete ZIP creation workflow"""
        validator = ArchiveValidator()
        final_name = validator.get_archive_extension(archive_name, 'zip')
        
        try:
            archive_path = self.zip_archiver.create_zip_archive(bundle_dir, output_path, final_name)
            
            # Remove source bundle directory after successful archive creation
            shutil.rmtree(bundle_dir)
            
            return archive_path
            
        except Exception as e:
            # Clean up bundle directory on failure
            if Path(bundle_dir).exists():
                shutil.rmtree(bundle_dir)
            raise
    
    def _create_7zip_workflow(self, bundle_dir, output_path, archive_name):
        """Complete 7-Zip creation workflow"""
        validator = ArchiveValidator()
        final_name = validator.get_archive_extension(archive_name, '7zip')
        
        try:
            archive_path = self.seven_zip_archiver.create_7zip_archive(bundle_dir, output_path, final_name)
            
            # Remove source bundle directory after successful archive creation
            shutil.rmtree(bundle_dir)
            
            return archive_path
            
        except Exception as e:
            # Clean up bundle directory on failure
            if Path(bundle_dir).exists():
                shutil.rmtree(bundle_dir)
            raise


class ArchiveInfoProvider:
    """Provide information about created archives"""
    
    @staticmethod
    def get_archive_info(archive_path):
        """Get information about created archive"""
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            return None
        
        file_size = archive_path.stat().st_size
        
        return {
            'path': archive_path,
            'size_bytes': file_size,
            'size_mb': file_size / (1024 * 1024),
            'extension': archive_path.suffix
        }
    
    @staticmethod
    def print_archive_completion(archive_path, compression_level):
        """Print archive creation completion information"""
        from printer import HeaderPrinter
        
        info = ArchiveInfoProvider.get_archive_info(archive_path)
        if not info:
            return
        
        archive_type = 'ZIP' if info['extension'] == '.zip' else '7Z'
        
        HeaderPrinter.print_completion_info(
            bundle_path=info['path'],
            bundle_type=archive_type.lower(),
            file_size=info['size_bytes'],
            compression_level=compression_level
        )
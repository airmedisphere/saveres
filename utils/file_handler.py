import os
import mimetypes
import magic
from typing import Optional, Tuple
from utils.logger import log_error, log_info

class FileHandler:
    """Advanced file handling utilities"""
    
    def __init__(self):
        # Initialize python-magic for better MIME type detection
        try:
            self.magic_mime = magic.Magic(mime=True)
        except:
            self.magic_mime = None
    
    def get_file_info(self, file_path: str) -> Tuple[str, str, str]:
        """Get comprehensive file information"""
        try:
            # Get basic info
            filename = os.path.basename(file_path)
            name, extension = os.path.splitext(filename)
            
            # Get MIME type using multiple methods
            mime_type = self.get_mime_type(file_path)
            
            return filename, extension.lower(), mime_type
            
        except Exception as e:
            log_error(e, f"get_file_info: {file_path}")
            return os.path.basename(file_path), "", "application/octet-stream"
    
    def get_mime_type(self, file_path: str) -> str:
        """Get MIME type using multiple detection methods"""
        try:
            # Method 1: Use python-magic if available
            if self.magic_mime and os.path.exists(file_path):
                try:
                    mime_type = self.magic_mime.from_file(file_path)
                    if mime_type and mime_type != "application/octet-stream":
                        return mime_type
                except:
                    pass
            
            # Method 2: Use mimetypes module
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                return mime_type
            
            # Method 3: Extension-based detection
            extension = os.path.splitext(file_path)[1].lower()
            extension_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp',
                '.mp4': 'video/mp4',
                '.avi': 'video/x-msvideo',
                '.mkv': 'video/x-matroska',
                '.mov': 'video/quicktime',
                '.wmv': 'video/x-ms-wmv',
                '.flv': 'video/x-flv',
                '.webm': 'video/webm',
                '.m4v': 'video/mp4',
                '.3gp': 'video/3gpp',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.flac': 'audio/flac',
                '.ogg': 'audio/ogg',
                '.aac': 'audio/aac',
                '.m4a': 'audio/mp4',
                '.wma': 'audio/x-ms-wma',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed',
                '.7z': 'application/x-7z-compressed',
                '.txt': 'text/plain',
                '.json': 'application/json',
                '.xml': 'application/xml',
                '.html': 'text/html',
                '.css': 'text/css',
                '.js': 'application/javascript'
            }
            
            return extension_map.get(extension, "application/octet-stream")
            
        except Exception as e:
            log_error(e, f"get_mime_type: {file_path}")
            return "application/octet-stream"
    
    def is_media_file(self, file_path: str) -> bool:
        """Check if file is a media file"""
        try:
            mime_type = self.get_mime_type(file_path)
            return mime_type.startswith(('image/', 'video/', 'audio/'))
        except:
            return False
    
    def get_media_category(self, file_path: str) -> str:
        """Get media category (photo, video, audio, document)"""
        try:
            mime_type = self.get_mime_type(file_path)
            
            if mime_type.startswith('image/'):
                if mime_type == 'image/gif':
                    return 'animation'
                return 'photo'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
            else:
                return 'document'
                
        except:
            return 'document'

# Global file handler instance
file_handler = FileHandler()
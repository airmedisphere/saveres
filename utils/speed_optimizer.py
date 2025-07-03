import asyncio
import aiofiles
import time
import os
import mimetypes
from typing import Optional, Callable, Any
from pyrogram import Client
from pyrogram.types import Message
from config import CHUNK_SIZE, MAX_RETRIES, PROGRESS_UPDATE_INTERVAL
from utils.logger import log_error, log_info

class SpeedOptimizer:
    """Advanced speed optimization utilities"""
    
    def __init__(self):
        self.download_speeds = {}
        self.upload_speeds = {}
        self.last_progress_update = {}
    
    async def optimized_download(self, client: Client, message: Message, 
                               file_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """Ultra-fast download with speed optimization and original format preservation"""
        try:
            start_time = time.time()
            user_id = getattr(client, 'user_id', 0)
            
            # Use streaming download for better performance
            async def progress_wrapper(current: int, total: int):
                if progress_callback:
                    now = time.time()
                    if user_id not in self.last_progress_update or \
                       now - self.last_progress_update.get(user_id, 0) >= PROGRESS_UPDATE_INTERVAL:
                        
                        # Calculate speed
                        elapsed = now - start_time
                        if elapsed > 0:
                            speed = current / elapsed / 1024 / 1024  # MB/s
                            self.download_speeds[user_id] = speed
                        
                        await progress_callback(current, total, speed)
                        self.last_progress_update[user_id] = now
            
            # Download with optimized settings - preserve original filename and format
            downloaded_file = await client.download_media(
                message,
                file_name=file_path,
                progress=progress_wrapper,
                progress_args=()
            )
            
            return downloaded_file is not None
            
        except Exception as e:
            log_error(e, f"optimized_download: {file_path}")
            return False
    
    def get_media_type_and_attributes(self, message: Message, file_path: str) -> tuple:
        """Determine the correct media type and extract attributes from the original message"""
        try:
            # Get file extension and MIME type
            file_extension = os.path.splitext(file_path)[1].lower()
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Extract attributes from the original message
            if message.photo:
                return 'photo', {
                    'width': message.photo.width,
                    'height': message.photo.height
                }
            
            elif message.video:
                return 'video', {
                    'duration': message.video.duration,
                    'width': message.video.width,
                    'height': message.video.height,
                    'thumb': message.video.thumbs[0] if message.video.thumbs else None,
                    'supports_streaming': True
                }
            
            elif message.animation:
                return 'animation', {
                    'duration': message.animation.duration,
                    'width': message.animation.width,
                    'height': message.animation.height,
                    'thumb': message.animation.thumbs[0] if message.animation.thumbs else None
                }
            
            elif message.audio:
                return 'audio', {
                    'duration': message.audio.duration,
                    'performer': message.audio.performer,
                    'title': message.audio.title,
                    'thumb': message.audio.thumbs[0] if message.audio.thumbs else None
                }
            
            elif message.voice:
                return 'voice', {
                    'duration': message.voice.duration
                }
            
            elif message.video_note:
                return 'video_note', {
                    'duration': message.video_note.duration,
                    'length': message.video_note.length,
                    'thumb': message.video_note.thumbs[0] if message.video_note.thumbs else None
                }
            
            elif message.sticker:
                return 'sticker', {
                    'width': message.sticker.width,
                    'height': message.sticker.height,
                    'is_animated': message.sticker.is_animated,
                    'is_video': message.sticker.is_video,
                    'set_name': message.sticker.set_name,
                    'emoji': message.sticker.emoji
                }
            
            elif message.document:
                # Check if it's a specific media type based on MIME type or extension
                if mime_type:
                    if mime_type.startswith('image/'):
                        return 'photo', {}
                    elif mime_type.startswith('video/'):
                        return 'video', {
                            'supports_streaming': True
                        }
                    elif mime_type.startswith('audio/'):
                        return 'audio', {}
                
                # Check by file extension
                if file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']:
                    if file_extension == '.gif':
                        return 'animation', {}
                    return 'photo', {}
                elif file_extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']:
                    return 'video', {
                        'supports_streaming': True
                    }
                elif file_extension in ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma']:
                    return 'audio', {}
                elif file_extension in ['.webm'] and message.document.mime_type == 'video/webm':
                    return 'video', {
                        'supports_streaming': True
                    }
                
                # Default to document for unknown types
                return 'document', {
                    'file_name': message.document.file_name,
                    'mime_type': message.document.mime_type
                }
            
            # Default fallback
            return 'document', {}
            
        except Exception as e:
            log_error(e, f"get_media_type_and_attributes")
            return 'document', {}
    
    async def optimized_upload(self, client: Client, chat_id: int, file_path: str,
                             caption: str = None, reply_to_message_id: int = None,
                             progress_callback: Optional[Callable] = None,
                             original_message: Message = None) -> bool:
        """Ultra-fast upload with original format preservation"""
        try:
            start_time = time.time()
            user_id = getattr(client, 'user_id', 0)
            
            async def progress_wrapper(current: int, total: int):
                if progress_callback:
                    now = time.time()
                    if user_id not in self.last_progress_update or \
                       now - self.last_progress_update.get(user_id, 0) >= PROGRESS_UPDATE_INTERVAL:
                        
                        # Calculate speed
                        elapsed = now - start_time
                        if elapsed > 0:
                            speed = current / elapsed / 1024 / 1024  # MB/s
                            self.upload_speeds[user_id] = speed
                        
                        await progress_callback(current, total, speed)
                        self.last_progress_update[user_id] = now
            
            # Determine the correct media type and attributes
            if original_message:
                media_type, attributes = self.get_media_type_and_attributes(original_message, file_path)
            else:
                # Fallback to file extension detection
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                    media_type, attributes = 'photo', {}
                elif file_extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']:
                    media_type, attributes = 'video', {'supports_streaming': True}
                elif file_extension in ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma']:
                    media_type, attributes = 'audio', {}
                elif file_extension == '.gif':
                    media_type, attributes = 'animation', {}
                else:
                    media_type, attributes = 'document', {}
            
            # Upload based on the determined media type
            if media_type == 'photo':
                await client.send_photo(
                    chat_id, file_path, 
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
                )
            
            elif media_type == 'video':
                await client.send_video(
                    chat_id, file_path, 
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper,
                    duration=attributes.get('duration'),
                    width=attributes.get('width'),
                    height=attributes.get('height'),
                    supports_streaming=attributes.get('supports_streaming', True)
                )
            
            elif media_type == 'animation':
                await client.send_animation(
                    chat_id, file_path, 
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper,
                    duration=attributes.get('duration'),
                    width=attributes.get('width'),
                    height=attributes.get('height')
                )
            
            elif media_type == 'audio':
                await client.send_audio(
                    chat_id, file_path, 
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper,
                    duration=attributes.get('duration'),
                    performer=attributes.get('performer'),
                    title=attributes.get('title')
                )
            
            elif media_type == 'voice':
                await client.send_voice(
                    chat_id, file_path, 
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper,
                    duration=attributes.get('duration')
                )
            
            elif media_type == 'video_note':
                await client.send_video_note(
                    chat_id, file_path, 
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper,
                    duration=attributes.get('duration'),
                    length=attributes.get('length')
                )
            
            elif media_type == 'sticker':
                await client.send_sticker(
                    chat_id, file_path, 
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
                )
            
            else:  # document
                await client.send_document(
                    chat_id, file_path, 
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper,
                    file_name=attributes.get('file_name'),
                    force_document=False  # Let Telegram decide the best format
                )
            
            return True
            
        except Exception as e:
            log_error(e, f"optimized_upload: {file_path}")
            return False
    
    async def retry_operation(self, operation: Callable, max_retries: int = MAX_RETRIES,
                            delay: float = 1.0, backoff: float = 2.0) -> Any:
        """Retry failed operations with exponential backoff"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = delay * (backoff ** attempt)
                    log_info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    log_error(e, f"Operation failed after {max_retries} attempts")
        
        raise last_exception
    
    def get_download_speed(self, user_id: int) -> float:
        """Get current download speed for user"""
        return self.download_speeds.get(user_id, 0.0)
    
    def get_upload_speed(self, user_id: int) -> float:
        """Get current upload speed for user"""
        return self.upload_speeds.get(user_id, 0.0)
    
    def format_speed(self, speed: float) -> str:
        """Format speed in human readable format"""
        if speed < 1:
            return f"{speed * 1024:.1f} KB/s"
        else:
            return f"{speed:.1f} MB/s"

# Global speed optimizer instance
speed_optimizer = SpeedOptimizer()
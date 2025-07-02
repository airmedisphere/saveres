import asyncio
import aiofiles
import time
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
        """Ultra-fast download with speed optimization"""
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
            
            # Download with optimized settings
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
    
    async def optimized_upload(self, client: Client, chat_id: int, file_path: str,
                             caption: str = None, reply_to_message_id: int = None,
                             progress_callback: Optional[Callable] = None) -> bool:
        """Ultra-fast upload with speed optimization"""
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
            
            # Determine file type and upload accordingly
            import os
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                await client.send_photo(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
                )
            elif file_extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
                await client.send_video(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
                )
            elif file_extension in ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a']:
                await client.send_audio(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
                )
            elif file_extension == '.gif':
                await client.send_animation(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
                )
            else:
                await client.send_document(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=reply_to_message_id,
                    progress=progress_wrapper
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
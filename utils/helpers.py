import os
import asyncio
import aiofiles
import time
from typing import Optional, Dict, Any
from pyrogram.types import Message
from pyrogram import Client
from config import DOWNLOAD_DIR, MAX_FILE_SIZE

class DownloadManager:
    def __init__(self):
        self.active_downloads: Dict[int, bool] = {}
        self.download_stats: Dict[int, Dict[str, Any]] = {}
        
    def is_downloading(self, user_id: int) -> bool:
        return self.active_downloads.get(user_id, False)
    
    def start_download(self, user_id: int):
        self.active_downloads[user_id] = True
        self.download_stats[user_id] = {
            'start_time': time.time(),
            'current_file': 0,
            'total_files': 0,
            'status': 'downloading'
        }
    
    def stop_download(self, user_id: int):
        self.active_downloads[user_id] = False
        if user_id in self.download_stats:
            del self.download_stats[user_id]
    
    def update_stats(self, user_id: int, current: int, total: int):
        if user_id in self.download_stats:
            self.download_stats[user_id].update({
                'current_file': current,
                'total_files': total
            })

download_manager = DownloadManager()

async def ensure_download_dir():
    """Ensure download directory exists"""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def cleanup_file(file_path: str):
    """Safely remove file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass

async def get_file_size(file_path: str) -> int:
    """Get file size in MB"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except:
        return 0

def format_progress(current: int, total: int) -> str:
    """Format progress percentage"""
    if total == 0:
        return "0%"
    return f"{(current * 100 / total):.1f}%"

def format_time(seconds: int) -> str:
    """Format time in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

async def safe_edit_message(client: Client, chat_id: int, message_id: int, text: str):
    """Safely edit message with error handling"""
    try:
        await client.edit_message_text(chat_id, message_id, text)
    except Exception:
        pass

async def safe_delete_message(client: Client, chat_id: int, message_id: int):
    """Safely delete message with error handling"""
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass

def extract_chat_info(url: str) -> tuple:
    """Extract chat ID and message ID from URL"""
    try:
        parts = url.split("/")
        if "t.me/c/" in url:
            chat_id = int("-100" + parts[4])
            msg_range = parts[-1].replace("?single", "").split("-")
        elif "t.me/b/" in url:
            chat_id = parts[4]
            msg_range = parts[-1].replace("?single", "").split("-")
        else:
            chat_id = parts[3]
            msg_range = parts[-1].replace("?single", "").split("-")
        
        from_id = int(msg_range[0].strip())
        to_id = int(msg_range[1].strip()) if len(msg_range) > 1 else from_id
        
        return chat_id, from_id, to_id
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

class RateLimiter:
    def __init__(self, max_requests: int = 30, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, list] = {}
    
    async def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.time_window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True

rate_limiter = RateLimiter()
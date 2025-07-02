import os
import asyncio
import aiofiles
from pyrogram import Client, enums
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import API_ID, API_HASH, DOWNLOAD_DIR, MAX_CONCURRENT_DOWNLOADS, DOWNLOAD_TIMEOUT, MAX_FILE_SIZE
from database.db import db
from utils.helpers import (
    download_manager, ensure_download_dir, cleanup_file, 
    get_file_size, format_progress, format_time, safe_edit_message,
    safe_delete_message, extract_chat_info, rate_limiter
)
from utils.logger import log_error, log_info
import time
from typing import Optional, List, Dict, Any

class AdvancedDownloader:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        self.active_sessions: Dict[int, Client] = {}
    
    async def get_user_session(self, user_id: int) -> Optional[Client]:
        """Get or create user session"""
        try:
            if user_id in self.active_sessions:
                return self.active_sessions[user_id]
            
            session_string = await db.get_session(user_id)
            if not session_string:
                return None
            
            client = Client(
                f"session_{user_id}",
                session_string=session_string,
                api_id=API_ID,
                api_hash=API_HASH
            )
            
            await client.connect()
            self.active_sessions[user_id] = client
            return client
            
        except Exception as e:
            log_error(e, f"get_user_session for user {user_id}")
            return None
    
    async def close_user_session(self, user_id: int):
        """Close user session"""
        try:
            if user_id in self.active_sessions:
                await self.active_sessions[user_id].disconnect()
                del self.active_sessions[user_id]
        except Exception as e:
            log_error(e, f"close_user_session for user {user_id}")
    
    async def download_with_progress(self, client: Client, message: Message, 
                                   progress_msg: Message, user_id: int) -> Optional[str]:
        """Download media with progress tracking"""
        try:
            await ensure_download_dir()
            
            # Create unique filename
            timestamp = int(time.time())
            filename = f"{user_id}_{timestamp}_{message.id}"
            
            async def progress_callback(current: int, total: int):
                try:
                    progress = format_progress(current, total)
                    await safe_edit_message(
                        client, progress_msg.chat.id, progress_msg.id,
                        f"📥 **Downloading:** {progress}\n"
                        f"📁 **Size:** {current / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB"
                    )
                except Exception:
                    pass
            
            # Download with timeout
            file_path = await asyncio.wait_for(
                client.download_media(
                    message,
                    file_name=os.path.join(DOWNLOAD_DIR, filename),
                    progress=progress_callback
                ),
                timeout=DOWNLOAD_TIMEOUT
            )
            
            # Check file size
            if file_path and await get_file_size(file_path) > MAX_FILE_SIZE:
                await cleanup_file(file_path)
                raise ValueError(f"File too large (max {MAX_FILE_SIZE}MB)")
            
            return file_path
            
        except asyncio.TimeoutError:
            raise TimeoutError("Download timeout")
        except Exception as e:
            log_error(e, f"download_with_progress for user {user_id}")
            raise
    
    async def upload_with_progress(self, bot: Client, chat_id: int, file_path: str,
                                 message: Message, progress_msg: Message, 
                                 caption: str = None) -> bool:
        """Upload media with progress tracking"""
        try:
            async def progress_callback(current: int, total: int):
                try:
                    progress = format_progress(current, total)
                    await safe_edit_message(
                        bot, progress_msg.chat.id, progress_msg.id,
                        f"📤 **Uploading:** {progress}\n"
                        f"📁 **Size:** {current / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB"
                    )
                except Exception:
                    pass
            
            # Determine file type and send accordingly
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension in ['.jpg', '.jpeg', '.png', '.webp']:
                await bot.send_photo(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=message.id,
                    progress=progress_callback
                )
            elif file_extension in ['.mp4', '.avi', '.mkv', '.mov']:
                await bot.send_video(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=message.id,
                    progress=progress_callback
                )
            elif file_extension in ['.mp3', '.wav', '.flac', '.ogg']:
                await bot.send_audio(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=message.id,
                    progress=progress_callback
                )
            elif file_extension == '.gif':
                await bot.send_animation(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=message.id,
                    progress=progress_callback
                )
            else:
                await bot.send_document(
                    chat_id, file_path, caption=caption,
                    reply_to_message_id=message.id,
                    progress=progress_callback
                )
            
            return True
            
        except Exception as e:
            log_error(e, f"upload_with_progress")
            return False
    
    async def process_single_message(self, bot: Client, user_client: Client,
                                   chat_id: int, msg_id: int, user_id: int,
                                   original_message: Message) -> bool:
        """Process a single message download"""
        async with self.semaphore:
            try:
                # Get message
                msg = await user_client.get_messages(chat_id, msg_id)
                if not msg or msg.empty:
                    return False
                
                # Handle text messages
                if msg.text and not msg.media:
                    await bot.send_message(
                        original_message.chat.id,
                        msg.text,
                        entities=msg.entities,
                        reply_to_message_id=original_message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
                    return True
                
                # Handle media messages
                if msg.media:
                    progress_msg = await bot.send_message(
                        original_message.chat.id,
                        "📥 **Preparing download...**",
                        reply_to_message_id=original_message.id
                    )
                    
                    try:
                        # Download
                        file_path = await self.download_with_progress(
                            user_client, msg, progress_msg, user_id
                        )
                        
                        if not file_path:
                            await safe_edit_message(
                                bot, progress_msg.chat.id, progress_msg.id,
                                "❌ **Download failed**"
                            )
                            return False
                        
                        # Upload
                        await safe_edit_message(
                            bot, progress_msg.chat.id, progress_msg.id,
                            "📤 **Preparing upload...**"
                        )
                        
                        success = await self.upload_with_progress(
                            bot, original_message.chat.id, file_path,
                            original_message, progress_msg, msg.caption
                        )
                        
                        # Cleanup
                        await cleanup_file(file_path)
                        await safe_delete_message(bot, progress_msg.chat.id, progress_msg.id)
                        
                        if success:
                            # Update stats
                            file_size = await get_file_size(file_path) if os.path.exists(file_path) else 0
                            await db.update_download_stats(user_id, "media", int(file_size))
                            await db.update_user_stats(user_id)
                        
                        return success
                        
                    except Exception as e:
                        await safe_edit_message(
                            bot, progress_msg.chat.id, progress_msg.id,
                            f"❌ **Error:** {str(e)}"
                        )
                        return False
                
                return False
                
            except Exception as e:
                log_error(e, f"process_single_message for user {user_id}")
                return False
    
    async def process_batch_download(self, bot: Client, user_id: int, url: str,
                                   original_message: Message) -> bool:
        """Process batch download from URL"""
        try:
            # Check rate limit
            if not await rate_limiter.is_allowed(user_id):
                await bot.send_message(
                    original_message.chat.id,
                    "⚠️ **Rate limit exceeded. Please wait before making more requests.**",
                    reply_to_message_id=original_message.id
                )
                return False
            
            # Check if user is already downloading
            if download_manager.is_downloading(user_id):
                await bot.send_message(
                    original_message.chat.id,
                    "⚠️ **You already have an active download. Use /cancel to stop it.**",
                    reply_to_message_id=original_message.id
                )
                return False
            
            # Get user session
            user_client = await self.get_user_session(user_id)
            if not user_client:
                await bot.send_message(
                    original_message.chat.id,
                    "❌ **Please /login first to download restricted content.**",
                    reply_to_message_id=original_message.id
                )
                return False
            
            # Extract chat info
            try:
                chat_id, from_id, to_id = extract_chat_info(url)
            except ValueError as e:
                await bot.send_message(
                    original_message.chat.id,
                    f"❌ **Invalid URL:** {str(e)}",
                    reply_to_message_id=original_message.id
                )
                return False
            
            # Start download process
            download_manager.start_download(user_id)
            total_messages = to_id - from_id + 1
            
            status_msg = await bot.send_message(
                original_message.chat.id,
                f"🚀 **Starting batch download...**\n"
                f"📊 **Total messages:** {total_messages}\n"
                f"⏳ **Progress:** 0/{total_messages}",
                reply_to_message_id=original_message.id
            )
            
            successful_downloads = 0
            failed_downloads = 0
            start_time = time.time()
            
            # Process messages
            for current_id in range(from_id, to_id + 1):
                if not download_manager.is_downloading(user_id):
                    break
                
                try:
                    success = await self.process_single_message(
                        bot, user_client, chat_id, current_id, user_id, original_message
                    )
                    
                    if success:
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                    
                    # Update progress every 5 messages
                    if (current_id - from_id + 1) % 5 == 0:
                        progress = current_id - from_id + 1
                        elapsed_time = int(time.time() - start_time)
                        
                        await safe_edit_message(
                            bot, status_msg.chat.id, status_msg.id,
                            f"📥 **Downloading...**\n"
                            f"📊 **Progress:** {progress}/{total_messages}\n"
                            f"✅ **Success:** {successful_downloads}\n"
                            f"❌ **Failed:** {failed_downloads}\n"
                            f"⏱️ **Time:** {format_time(elapsed_time)}"
                        )
                    
                    # Small delay to prevent flooding
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    log_error(e, f"Error processing message {current_id}")
                    failed_downloads += 1
            
            # Final status
            total_time = int(time.time() - start_time)
            await safe_edit_message(
                bot, status_msg.chat.id, status_msg.id,
                f"🎉 **Download completed!**\n"
                f"✅ **Successful:** {successful_downloads}\n"
                f"❌ **Failed:** {failed_downloads}\n"
                f"⏱️ **Total time:** {format_time(total_time)}"
            )
            
            download_manager.stop_download(user_id)
            return True
            
        except Exception as e:
            log_error(e, f"process_batch_download for user {user_id}")
            download_manager.stop_download(user_id)
            return False
    
    async def cancel_download(self, user_id: int) -> bool:
        """Cancel ongoing download"""
        try:
            if download_manager.is_downloading(user_id):
                download_manager.stop_download(user_id)
                await self.close_user_session(user_id)
                return True
            return False
        except Exception as e:
            log_error(e, f"cancel_download for user {user_id}")
            return False

# Global downloader instance
advanced_downloader = AdvancedDownloader()
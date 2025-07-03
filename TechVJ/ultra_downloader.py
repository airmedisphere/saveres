import os
import asyncio
import aiofiles
import time
from pyrogram import Client, enums
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, MessageNotModified
from config import (
    API_ID, API_HASH, DOWNLOAD_DIR, MAX_CONCURRENT_DOWNLOADS, 
    MAX_CONCURRENT_UPLOADS, DOWNLOAD_TIMEOUT, UPLOAD_TIMEOUT, MAX_FILE_SIZE
)
from database.db import db
from utils.helpers import (
    download_manager, ensure_download_dir, cleanup_file, 
    get_file_size, format_progress, format_time, safe_edit_message,
    safe_delete_message, rate_limiter
)
from utils.url_parser import url_parser
from utils.speed_optimizer import speed_optimizer
from utils.logger import log_error, log_info
from typing import Optional, List, Dict, Any

class UltraDownloader:
    """Ultra-fast downloader with advanced features and original format preservation"""
    
    def __init__(self):
        self.download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        self.upload_semaphore = asyncio.Semaphore(MAX_CONCURRENT_UPLOADS)
        self.active_sessions: Dict[int, Client] = {}
        self.download_stats: Dict[int, Dict] = {}
    
    async def get_user_session(self, user_id: int) -> Optional[Client]:
        """Get or create optimized user session"""
        try:
            if user_id in self.active_sessions:
                return self.active_sessions[user_id]
            
            session_string = await db.get_session(user_id)
            if not session_string:
                return None
            
            client = Client(
                f"ultra_session_{user_id}",
                session_string=session_string,
                api_id=API_ID,
                api_hash=API_HASH,
                workers=50,  # Increased workers for this session
                sleep_threshold=5
            )
            
            await client.connect()
            client.user_id = user_id  # Store user_id for reference
            self.active_sessions[user_id] = client
            return client
            
        except Exception as e:
            log_error(e, f"get_user_session for user {user_id}")
            return None
    
    async def close_user_session(self, user_id: int):
        """Close user session safely"""
        try:
            if user_id in self.active_sessions:
                await self.active_sessions[user_id].disconnect()
                del self.active_sessions[user_id]
        except Exception as e:
            log_error(e, f"close_user_session for user {user_id}")
    
    def get_original_filename(self, message: Message, user_id: int, timestamp: int) -> str:
        """Get the original filename preserving the extension and format"""
        try:
            # Try to get original filename from different media types
            original_name = None
            
            if message.document and message.document.file_name:
                original_name = message.document.file_name
            elif message.video and message.video.file_name:
                original_name = message.video.file_name
            elif message.audio and message.audio.file_name:
                original_name = message.audio.file_name
            elif message.photo:
                # For photos, create a name with proper extension
                original_name = f"photo_{message.id}.jpg"
            elif message.video:
                original_name = f"video_{message.id}.mp4"
            elif message.audio:
                original_name = f"audio_{message.id}.mp3"
            elif message.animation:
                original_name = f"animation_{message.id}.gif"
            elif message.voice:
                original_name = f"voice_{message.id}.ogg"
            elif message.video_note:
                original_name = f"video_note_{message.id}.mp4"
            elif message.sticker:
                original_name = f"sticker_{message.id}.webp"
            else:
                original_name = f"file_{message.id}"
            
            # Clean filename and preserve extension
            if original_name:
                # Split name and extension
                name_part, ext_part = os.path.splitext(original_name)
                # Clean the name part
                clean_name = "".join(c for c in name_part if c.isalnum() or c in (' ', '-', '_')).strip()
                # Ensure we have a name
                if not clean_name:
                    clean_name = f"file_{message.id}"
                # Combine with timestamp and extension
                filename = f"{user_id}_{timestamp}_{clean_name}{ext_part}"
            else:
                filename = f"{user_id}_{timestamp}_file_{message.id}"
            
            return filename
            
        except Exception as e:
            log_error(e, f"get_original_filename")
            return f"{user_id}_{timestamp}_file_{message.id}"
    
    async def download_with_ultra_speed(self, client: Client, message: Message, 
                                      progress_msg: Message, user_id: int) -> Optional[str]:
        """Ultra-fast download with advanced progress tracking and original format preservation"""
        async with self.download_semaphore:
            try:
                await ensure_download_dir()
                
                # Create unique filename preserving original format
                timestamp = int(time.time())
                filename = self.get_original_filename(message, user_id, timestamp)
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                
                # Progress callback with speed tracking
                async def progress_callback(current: int, total: int, speed: float = 0):
                    try:
                        progress = format_progress(current, total)
                        speed_text = speed_optimizer.format_speed(speed) if speed > 0 else "Calculating..."
                        
                        eta = ""
                        if speed > 0 and current > 0:
                            remaining = total - current
                            eta_seconds = remaining / (speed * 1024 * 1024)
                            eta = f" • ETA: {format_time(int(eta_seconds))}"
                        
                        # Show file type being downloaded
                        file_type = "Unknown"
                        if message.photo:
                            file_type = "Photo"
                        elif message.video:
                            file_type = "Video"
                        elif message.audio:
                            file_type = "Audio"
                        elif message.animation:
                            file_type = "Animation/GIF"
                        elif message.document:
                            file_type = f"Document ({message.document.mime_type or 'Unknown'})"
                        elif message.voice:
                            file_type = "Voice Message"
                        elif message.video_note:
                            file_type = "Video Note"
                        elif message.sticker:
                            file_type = "Sticker"
                        
                        await safe_edit_message(
                            client, progress_msg.chat.id, progress_msg.id,
                            f"📥 **Downloading {file_type}:** {progress}\n"
                            f"📁 **Size:** {current / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB\n"
                            f"🚀 **Speed:** {speed_text}{eta}\n"
                            f"📄 **File:** {os.path.basename(filename)}"
                        )
                    except MessageNotModified:
                        pass
                    except Exception:
                        pass
                
                # Download with retry mechanism
                async def download_operation():
                    return await speed_optimizer.optimized_download(
                        client, message, file_path, progress_callback
                    )
                
                success = await asyncio.wait_for(
                    speed_optimizer.retry_operation(download_operation),
                    timeout=DOWNLOAD_TIMEOUT
                )
                
                if not success or not os.path.exists(file_path):
                    raise ValueError("Download failed")
                
                # Check file size
                file_size_mb = await get_file_size(file_path)
                if file_size_mb > MAX_FILE_SIZE:
                    await cleanup_file(file_path)
                    raise ValueError(f"File too large ({file_size_mb:.1f}MB > {MAX_FILE_SIZE}MB)")
                
                return file_path
                
            except asyncio.TimeoutError:
                raise TimeoutError("Download timeout")
            except Exception as e:
                log_error(e, f"download_with_ultra_speed for user {user_id}")
                raise
    
    async def upload_with_ultra_speed(self, bot: Client, chat_id: int, file_path: str,
                                    message: Message, progress_msg: Message, 
                                    caption: str = None, original_message: Message = None) -> bool:
        """Ultra-fast upload with original format preservation"""
        async with self.upload_semaphore:
            try:
                # Progress callback with speed tracking
                async def progress_callback(current: int, total: int, speed: float = 0):
                    try:
                        progress = format_progress(current, total)
                        speed_text = speed_optimizer.format_speed(speed) if speed > 0 else "Calculating..."
                        
                        eta = ""
                        if speed > 0 and current > 0:
                            remaining = total - current
                            eta_seconds = remaining / (speed * 1024 * 1024)
                            eta = f" • ETA: {format_time(int(eta_seconds))}"
                        
                        # Show file type being uploaded
                        file_type = "File"
                        if original_message:
                            if original_message.photo:
                                file_type = "Photo"
                            elif original_message.video:
                                file_type = "Video"
                            elif original_message.audio:
                                file_type = "Audio"
                            elif original_message.animation:
                                file_type = "Animation/GIF"
                            elif original_message.document:
                                file_type = f"Document"
                            elif original_message.voice:
                                file_type = "Voice Message"
                            elif original_message.video_note:
                                file_type = "Video Note"
                            elif original_message.sticker:
                                file_type = "Sticker"
                        
                        await safe_edit_message(
                            bot, progress_msg.chat.id, progress_msg.id,
                            f"📤 **Uploading {file_type}:** {progress}\n"
                            f"📁 **Size:** {current / (1024*1024):.1f} MB / {total / (1024*1024):.1f} MB\n"
                            f"🚀 **Speed:** {speed_text}{eta}\n"
                            f"📄 **File:** {os.path.basename(file_path)}"
                        )
                    except MessageNotModified:
                        pass
                    except Exception:
                        pass
                
                # Upload with retry mechanism and original format preservation
                async def upload_operation():
                    return await speed_optimizer.optimized_upload(
                        bot, chat_id, file_path, caption, 
                        message.id, progress_callback, original_message
                    )
                
                success = await asyncio.wait_for(
                    speed_optimizer.retry_operation(upload_operation),
                    timeout=UPLOAD_TIMEOUT
                )
                
                return success
                
            except Exception as e:
                log_error(e, f"upload_with_ultra_speed")
                return False
    
    async def process_single_message(self, bot: Client, user_client: Client,
                                   chat_id: str, msg_id: int, user_id: int,
                                   original_message: Message) -> bool:
        """Process a single message with ultra-fast download and original format preservation"""
        try:
            # Get message with retry
            async def get_message_operation():
                return await user_client.get_messages(chat_id, msg_id)
            
            msg = await speed_optimizer.retry_operation(get_message_operation)
            
            if not msg or msg.empty:
                log_info(f"Message {msg_id} not found or empty")
                return False
            
            # Handle text messages
            if msg.text and not msg.media:
                try:
                    await bot.send_message(
                        original_message.chat.id,
                        msg.text,
                        entities=msg.entities,
                        reply_to_message_id=original_message.id,
                        parse_mode=enums.ParseMode.HTML
                    )
                    return True
                except Exception as e:
                    log_error(e, f"Failed to send text message {msg_id}")
                    return False
            
            # Handle media messages
            if msg.media:
                # Determine media type for progress message
                media_type = "File"
                if msg.photo:
                    media_type = "Photo"
                elif msg.video:
                    media_type = "Video"
                elif msg.audio:
                    media_type = "Audio"
                elif msg.animation:
                    media_type = "Animation/GIF"
                elif msg.document:
                    media_type = f"Document"
                elif msg.voice:
                    media_type = "Voice Message"
                elif msg.video_note:
                    media_type = "Video Note"
                elif msg.sticker:
                    media_type = "Sticker"
                
                progress_msg = await bot.send_message(
                    original_message.chat.id,
                    f"🚀 **Processing {media_type} (Message {msg_id})**\n"
                    f"📥 **Initializing ultra-fast download...**\n"
                    f"⚡ **Preserving original format...**",
                    reply_to_message_id=original_message.id
                )
                
                try:
                    # Download with ultra speed and original format
                    file_path = await self.download_with_ultra_speed(
                        user_client, msg, progress_msg, user_id
                    )
                    
                    if not file_path:
                        await safe_edit_message(
                            bot, progress_msg.chat.id, progress_msg.id,
                            f"❌ **{media_type} download failed**"
                        )
                        return False
                    
                    # Upload with ultra speed and original format preservation
                    await safe_edit_message(
                        bot, progress_msg.chat.id, progress_msg.id,
                        f"📤 **Initializing ultra-fast {media_type} upload...**\n"
                        f"⚡ **Maintaining original quality...**"
                    )
                    
                    success = await self.upload_with_ultra_speed(
                        bot, original_message.chat.id, file_path,
                        original_message, progress_msg, msg.caption, msg
                    )
                    
                    # Cleanup
                    await cleanup_file(file_path)
                    await safe_delete_message(bot, progress_msg.chat.id, progress_msg.id)
                    
                    if success:
                        # Update stats
                        file_size = await get_file_size(file_path) if os.path.exists(file_path) else 0
                        await db.update_download_stats(user_id, media_type.lower(), int(file_size * 1024 * 1024))
                        await db.update_user_stats(user_id)
                    
                    return success
                    
                except Exception as e:
                    await safe_edit_message(
                        bot, progress_msg.chat.id, progress_msg.id,
                        f"❌ **{media_type} Error:** {str(e)[:100]}..."
                    )
                    return False
            
            return False
            
        except Exception as e:
            log_error(e, f"process_single_message {msg_id} for user {user_id}")
            return False
    
    async def process_ultra_batch_download(self, bot: Client, user_id: int, url: str,
                                         original_message: Message) -> bool:
        """Process ultra-fast batch download from URL with original format preservation"""
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
            
            # Parse URL with advanced parser
            try:
                chat_id, from_id, to_id, url_type = url_parser.parse_url(url)
                log_info(f"Parsed URL: chat_id={chat_id}, from_id={from_id}, to_id={to_id}, type={url_type}")
            except ValueError as e:
                await bot.send_message(
                    original_message.chat.id,
                    f"❌ **Invalid URL:** {str(e)}\n\n"
                    "**Supported formats:**\n"
                    "• `https://t.me/channel/123`\n"
                    "• `https://t.me/c/1234567890/123`\n"
                    "• `https://t.me/channel/100-200`\n"
                    "• `https://t.me/b/botname/123`",
                    reply_to_message_id=original_message.id
                )
                return False
            
            # Get user session for private content
            user_client = None
            if url_type in ["private", "bot"]:
                user_client = await self.get_user_session(user_id)
                if not user_client:
                    await bot.send_message(
                        original_message.chat.id,
                        "❌ **Please /login first to download restricted content.**",
                        reply_to_message_id=original_message.id
                    )
                    return False
            else:
                # For public channels, use the bot's session
                user_client = bot
            
            # Start download process
            download_manager.start_download(user_id)
            total_messages = to_id - from_id + 1
            
            status_msg = await bot.send_message(
                original_message.chat.id,
                f"🚀 **Ultra-Fast Batch Download Started!**\n"
                f"📊 **Total messages:** {total_messages}\n"
                f"⚡ **Concurrent downloads:** {MAX_CONCURRENT_DOWNLOADS}\n"
                f"📈 **Progress:** 0/{total_messages}\n"
                f"🎯 **Success rate:** 0%\n"
                f"📄 **Original format preservation:** ✅",
                reply_to_message_id=original_message.id
            )
            
            successful_downloads = 0
            failed_downloads = 0
            start_time = time.time()
            
            # Create tasks for concurrent processing
            tasks = []
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
            
            async def process_message_with_semaphore(msg_id):
                async with semaphore:
                    if not download_manager.is_downloading(user_id):
                        return False
                    return await self.process_single_message(
                        bot, user_client, chat_id, msg_id, user_id, original_message
                    )
            
            # Create all tasks
            for current_id in range(from_id, to_id + 1):
                task = asyncio.create_task(process_message_with_semaphore(current_id))
                tasks.append(task)
            
            # Process tasks with progress updates
            completed = 0
            for task in asyncio.as_completed(tasks):
                if not download_manager.is_downloading(user_id):
                    # Cancel remaining tasks
                    for remaining_task in tasks:
                        if not remaining_task.done():
                            remaining_task.cancel()
                    break
                
                try:
                    success = await task
                    completed += 1
                    
                    if success:
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                    
                    # Update progress every 10 completed messages or every 5 seconds
                    if completed % 10 == 0 or (time.time() - start_time) % 5 < 1:
                        elapsed_time = int(time.time() - start_time)
                        success_rate = (successful_downloads / completed * 100) if completed > 0 else 0
                        
                        # Calculate ETA
                        if completed > 0 and elapsed_time > 0:
                            avg_time_per_msg = elapsed_time / completed
                            remaining_msgs = total_messages - completed
                            eta = int(avg_time_per_msg * remaining_msgs)
                            eta_text = f"⏱️ **ETA:** {format_time(eta)}\n"
                        else:
                            eta_text = ""
                        
                        await safe_edit_message(
                            bot, status_msg.chat.id, status_msg.id,
                            f"🚀 **Ultra-Fast Download in Progress...**\n"
                            f"📊 **Progress:** {completed}/{total_messages}\n"
                            f"✅ **Success:** {successful_downloads}\n"
                            f"❌ **Failed:** {failed_downloads}\n"
                            f"📈 **Success rate:** {success_rate:.1f}%\n"
                            f"{eta_text}"
                            f"⏰ **Elapsed:** {format_time(elapsed_time)}\n"
                            f"📄 **Original format:** ✅ Preserved"
                        )
                    
                except Exception as e:
                    log_error(e, f"Error processing task")
                    failed_downloads += 1
                    completed += 1
            
            # Final status
            total_time = int(time.time() - start_time)
            success_rate = (successful_downloads / total_messages * 100) if total_messages > 0 else 0
            avg_speed = successful_downloads / total_time if total_time > 0 else 0
            
            await safe_edit_message(
                bot, status_msg.chat.id, status_msg.id,
                f"🎉 **Ultra-Fast Download Completed!**\n\n"
                f"📊 **Results:**\n"
                f"✅ **Successful:** {successful_downloads}\n"
                f"❌ **Failed:** {failed_downloads}\n"
                f"📈 **Success rate:** {success_rate:.1f}%\n"
                f"⚡ **Average speed:** {avg_speed:.1f} files/sec\n"
                f"⏱️ **Total time:** {format_time(total_time)}\n"
                f"📄 **Original format:** ✅ All files preserved\n\n"
                f"🚀 **Ultra-fast processing with original quality completed!**"
            )
            
            download_manager.stop_download(user_id)
            return True
            
        except Exception as e:
            log_error(e, f"process_ultra_batch_download for user {user_id}")
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

# Global ultra downloader instance
ultra_downloader = UltraDownloader()
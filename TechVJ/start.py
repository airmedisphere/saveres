import os
import asyncio 
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 
from config import API_ID, API_HASH, ERROR_MESSAGE, ADMINS
from database.db import db
from TechVJ.strings import HELP_TXT, START_TXT, SETTINGS_TXT
from TechVJ.ultra_downloader import ultra_downloader
from utils.url_parser import url_parser
from utils.logger import log_error, log_info
from utils.helpers import download_manager

# Start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    try:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
        
        buttons = [[
            InlineKeyboardButton("🔐 Login", callback_data="login"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ],[
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            InlineKeyboardButton("📊 Stats", callback_data="stats")
        ],[
            InlineKeyboardButton("🚀 Speed Test", callback_data="speed_test"),
            InlineKeyboardButton("📈 Performance", callback_data="performance")
        ],[
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/airworksbeyond"),
            InlineKeyboardButton("📢 Updates", url="https://t.me/airworksbeyond")
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.send_message(
            chat_id=message.chat.id, 
            text=START_TXT.format(name=message.from_user.mention), 
            reply_markup=reply_markup, 
            reply_to_message_id=message.id
        )
        
    except Exception as e:
        log_error(e, "send_start")

# Help command
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    try:
        buttons = [[
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await client.send_message(
            chat_id=message.chat.id, 
            text=HELP_TXT,
            reply_markup=reply_markup
        )
    except Exception as e:
        log_error(e, "send_help")

# Cancel command
@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    try:
        success = await ultra_downloader.cancel_download(message.from_user.id)
        if success:
            await client.send_message(
                chat_id=message.chat.id, 
                text="✅ **Download cancelled successfully.**\n🚀 **Ultra-fast downloader stopped.**",
                reply_to_message_id=message.id
            )
        else:
            await client.send_message(
                chat_id=message.chat.id, 
                text="ℹ️ **No active download to cancel.**",
                reply_to_message_id=message.id
            )
    except Exception as e:
        log_error(e, "send_cancel")

# Stats command
@Client.on_message(filters.command(["stats"]))
async def send_stats(client: Client, message: Message):
    try:
        user_data = await db.col.find_one({'id': message.from_user.id})
        if not user_data:
            await message.reply("❌ **User data not found.**")
            return
        
        download_count = user_data.get('download_count', 0)
        join_date = user_data.get('join_date', 'Unknown')
        last_used = user_data.get('last_used', 'Never')
        
        # Get speed stats
        from utils.speed_optimizer import speed_optimizer
        download_speed = speed_optimizer.get_download_speed(message.from_user.id)
        upload_speed = speed_optimizer.get_upload_speed(message.from_user.id)
        
        stats_text = f"""
📊 **Your Ultra-Fast Statistics**

👤 **User:** {message.from_user.mention}
🆔 **User ID:** `{message.from_user.id}`
📅 **Joined:** {join_date}
🕐 **Last Used:** {last_used}
📥 **Downloads:** {download_count}
⭐ **Premium:** {'Yes' if user_data.get('is_premium', False) else 'No'}

🚀 **Performance Stats:**
📥 **Download Speed:** {speed_optimizer.format_speed(download_speed)}
📤 **Upload Speed:** {speed_optimizer.format_speed(upload_speed)}
⚡ **Status:** {'Ultra-Fast Mode' if download_speed > 5 else 'Standard Mode'}
        """
        
        buttons = [[
            InlineKeyboardButton("🔙 Back", callback_data="start")
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await message.reply(stats_text, reply_markup=reply_markup)
        
    except Exception as e:
        log_error(e, "send_stats")

# Settings command
@Client.on_message(filters.command(["settings"]))
async def send_settings(client: Client, message: Message):
    try:
        settings = await db.get_user_settings(message.from_user.id)
        
        buttons = [
            [InlineKeyboardButton(
                f"🗑️ Auto Delete: {'✅' if settings.get('auto_delete', True) else '❌'}", 
                callback_data="toggle_auto_delete"
            )],
            [InlineKeyboardButton(
                f"🔔 Notifications: {'✅' if settings.get('notification', True) else '❌'}", 
                callback_data="toggle_notification"
            )],
            [InlineKeyboardButton(
                f"🎥 Quality: {settings.get('quality', 'ultra').title()}", 
                callback_data="toggle_quality"
            )],
            [InlineKeyboardButton(
                f"⚡ Ultra Mode: {'✅' if settings.get('ultra_mode', True) else '❌'}", 
                callback_data="toggle_ultra_mode"
            )],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(SETTINGS_TXT, reply_markup=reply_markup)
        
    except Exception as e:
        log_error(e, "send_settings")

# Handle URL messages with ultra-fast processing
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "cancel", "stats", "settings", "login", "logout", "broadcast"]))
async def handle_url(client: Client, message: Message):
    try:
        text = message.text.strip()
        
        # Validate URL using advanced parser
        if not url_parser.validate_url(text):
            await message.reply(
                "❌ **Invalid Telegram URL format!**\n\n"
                "**✅ Supported formats:**\n"
                "• `https://t.me/channel/123`\n"
                "• `https://t.me/channel/100-200`\n"
                "• `https://t.me/c/1234567890/123`\n"
                "• `https://t.me/c/1234567890/100-200`\n"
                "• `https://t.me/b/botname/123`\n\n"
                "**💡 Tips:**\n"
                "• Use ranges for batch download (e.g., 100-200)\n"
                "• Login first for private channels\n"
                "• Check URL format carefully"
            )
            return
        
        # Parse URL to check type
        try:
            chat_id, from_id, to_id, url_type = url_parser.parse_url(text)
        except ValueError as e:
            await message.reply(f"❌ **URL parsing error:** {str(e)}")
            return
        
        # Check if user has session for restricted content
        if url_type in ["private", "bot"]:
            session = await db.get_session(message.from_user.id)
            if not session:
                await message.reply(
                    "🔐 **Login required for restricted content!**\n\n"
                    "Use /login to access private channels and bots.\n"
                    "Public channels don't require login."
                )
                return
        
        # Show processing message
        processing_msg = await message.reply(
            f"🚀 **Ultra-Fast Downloader Activated!**\n\n"
            f"📊 **Target:** {url_type.title()} content\n"
            f"📈 **Messages:** {to_id - from_id + 1}\n"
            f"⚡ **Mode:** Ultra-Fast Processing\n"
            f"🔄 **Initializing...**"
        )
        
        # Process the download with ultra speed
        success = await ultra_downloader.process_ultra_batch_download(
            client, message.from_user.id, text, message
        )
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        if not success:
            await message.reply("❌ **Download failed. Please try again or check the URL.**")
        
    except Exception as e:
        log_error(e, "handle_url")
        if ERROR_MESSAGE:
            await message.reply(f"❌ **Error:** {str(e)[:200]}...")

# Callback query handler with new features
@Client.on_callback_query()
async def callback_handler(client: Client, callback_query):
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if data == "start":
            buttons = [[
                InlineKeyboardButton("🔐 Login", callback_data="login"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ],[
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("📊 Stats", callback_data="stats")
            ],[
                InlineKeyboardButton("🚀 Speed Test", callback_data="speed_test"),
                InlineKeyboardButton("📈 Performance", callback_data="performance")
            ],[
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/airworksbeyond"),
                InlineKeyboardButton("📢 Updates", url="https://t.me/airworksbeyond")
            ]]
            
            reply_markup = InlineKeyboardMarkup(buttons)
            await callback_query.edit_message_text(
                START_TXT.format(name=callback_query.from_user.mention),
                reply_markup=reply_markup
            )
            
        elif data == "help":
            buttons = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await callback_query.edit_message_text(HELP_TXT, reply_markup=reply_markup)
            
        elif data == "settings":
            settings = await db.get_user_settings(user_id)
            buttons = [
                [InlineKeyboardButton(
                    f"🗑️ Auto Delete: {'✅' if settings.get('auto_delete', True) else '❌'}", 
                    callback_data="toggle_auto_delete"
                )],
                [InlineKeyboardButton(
                    f"🔔 Notifications: {'✅' if settings.get('notification', True) else '❌'}", 
                    callback_data="toggle_notification"
                )],
                [InlineKeyboardButton(
                    f"🎥 Quality: {settings.get('quality', 'ultra').title()}", 
                    callback_data="toggle_quality"
                )],
                [InlineKeyboardButton(
                    f"⚡ Ultra Mode: {'✅' if settings.get('ultra_mode', True) else '❌'}", 
                    callback_data="toggle_ultra_mode"
                )],
                [InlineKeyboardButton("🔙 Back", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await callback_query.edit_message_text(SETTINGS_TXT, reply_markup=reply_markup)
            
        elif data == "stats":
            user_data = await db.col.find_one({'id': user_id})
            if user_data:
                download_count = user_data.get('download_count', 0)
                join_date = user_data.get('join_date', 'Unknown')
                last_used = user_data.get('last_used', 'Never')
                
                from utils.speed_optimizer import speed_optimizer
                download_speed = speed_optimizer.get_download_speed(user_id)
                upload_speed = speed_optimizer.get_upload_speed(user_id)
                
                stats_text = f"""
📊 **Your Ultra-Fast Statistics**

👤 **User:** {callback_query.from_user.mention}
🆔 **User ID:** `{user_id}`
📅 **Joined:** {join_date}
🕐 **Last Used:** {last_used}
📥 **Downloads:** {download_count}
⭐ **Premium:** {'Yes' if user_data.get('is_premium', False) else 'No'}

🚀 **Performance Stats:**
📥 **Download Speed:** {speed_optimizer.format_speed(download_speed)}
📤 **Upload Speed:** {speed_optimizer.format_speed(upload_speed)}
⚡ **Status:** {'Ultra-Fast Mode' if download_speed > 5 else 'Standard Mode'}
                """
                
                buttons = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
                reply_markup = InlineKeyboardMarkup(buttons)
                await callback_query.edit_message_text(stats_text, reply_markup=reply_markup)
        
        elif data == "speed_test":
            await callback_query.edit_message_text(
                "🚀 **Ultra-Fast Speed Test**\n\n"
                "**Current Performance:**\n"
                f"⚡ **Max Concurrent Downloads:** {MAX_CONCURRENT_DOWNLOADS}\n"
                f"📤 **Max Concurrent Uploads:** {MAX_CONCURRENT_UPLOADS}\n"
                f"🔄 **Chunk Size:** 1MB\n"
                f"⏱️ **Timeout:** 10 minutes\n"
                f"📁 **Max File Size:** 4GB\n\n"
                "**Features:**\n"
                "✅ Ultra-fast concurrent processing\n"
                "✅ Advanced retry mechanism\n"
                "✅ Real-time speed tracking\n"
                "✅ Smart progress updates\n"
                "✅ Automatic error recovery",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="start")
                ]])
            )
        
        elif data == "performance":
            from config import MAX_CONCURRENT_DOWNLOADS, MAX_CONCURRENT_UPLOADS
            await callback_query.edit_message_text(
                "📈 **Performance Metrics**\n\n"
                f"🚀 **Ultra-Fast Engine Status:** Active\n"
                f"⚡ **Concurrent Downloads:** {MAX_CONCURRENT_DOWNLOADS}\n"
                f"📤 **Concurrent Uploads:** {MAX_CONCURRENT_UPLOADS}\n"
                f"🔄 **Active Sessions:** {len(ultra_downloader.active_sessions)}\n"
                f"📊 **Processing Mode:** Ultra-Fast\n\n"
                "**Optimizations:**\n"
                "✅ Advanced URL parsing\n"
                "✅ Smart session management\n"
                "✅ Concurrent processing\n"
                "✅ Speed optimization\n"
                "✅ Error recovery system",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="start")
                ]])
            )
            
        elif data.startswith("toggle_"):
            settings = await db.get_user_settings(user_id)
            
            if data == "toggle_auto_delete":
                settings['auto_delete'] = not settings.get('auto_delete', True)
            elif data == "toggle_notification":
                settings['notification'] = not settings.get('notification', True)
            elif data == "toggle_quality":
                current_quality = settings.get('quality', 'ultra')
                quality_cycle = {'ultra': 'high', 'high': 'medium', 'medium': 'ultra'}
                settings['quality'] = quality_cycle[current_quality]
            elif data == "toggle_ultra_mode":
                settings['ultra_mode'] = not settings.get('ultra_mode', True)
            
            await db.update_user_settings(user_id, settings)
            
            # Update settings display
            buttons = [
                [InlineKeyboardButton(
                    f"🗑️ Auto Delete: {'✅' if settings.get('auto_delete', True) else '❌'}", 
                    callback_data="toggle_auto_delete"
                )],
                [InlineKeyboardButton(
                    f"🔔 Notifications: {'✅' if settings.get('notification', True) else '❌'}", 
                    callback_data="toggle_notification"
                )],
                [InlineKeyboardButton(
                    f"🎥 Quality: {settings.get('quality', 'ultra').title()}", 
                    callback_data="toggle_quality"
                )],
                [InlineKeyboardButton(
                    f"⚡ Ultra Mode: {'✅' if settings.get('ultra_mode', True) else '❌'}", 
                    callback_data="toggle_ultra_mode"
                )],
                [InlineKeyboardButton("🔙 Back", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await callback_query.edit_message_reply_markup(reply_markup=reply_markup)
            
        elif data == "login":
            session = await db.get_session(user_id)
            if session:
                await callback_query.answer("✅ You are already logged in!", show_alert=True)
            else:
                await callback_query.answer("Please use /login command to login", show_alert=True)
        
        await callback_query.answer()
        
    except Exception as e:
        log_error(e, "callback_handler")
        await callback_query.answer("❌ An error occurred", show_alert=True)
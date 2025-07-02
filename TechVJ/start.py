import os
import asyncio 
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 
from config import API_ID, API_HASH, ERROR_MESSAGE, ADMINS
from database.db import db
from TechVJ.strings import HELP_TXT, START_TXT, SETTINGS_TXT
from TechVJ.advanced_downloader import advanced_downloader
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
        success = await advanced_downloader.cancel_download(message.from_user.id)
        if success:
            await client.send_message(
                chat_id=message.chat.id, 
                text="✅ **Download cancelled successfully.**",
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
        
        stats_text = f"""
📊 **Your Statistics**

👤 **User:** {message.from_user.mention}
🆔 **User ID:** `{message.from_user.id}`
📅 **Joined:** {join_date}
🕐 **Last Used:** {last_used}
📥 **Downloads:** {download_count}
⭐ **Premium:** {'Yes' if user_data.get('is_premium', False) else 'No'}
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
                f"🎥 Quality: {settings.get('quality', 'high').title()}", 
                callback_data="toggle_quality"
            )],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(SETTINGS_TXT, reply_markup=reply_markup)
        
    except Exception as e:
        log_error(e, "send_settings")

# Handle URL messages
@Client.on_message(filters.text & filters.private & ~filters.command(["start", "help", "cancel", "stats", "settings", "login", "logout", "broadcast"]))
async def handle_url(client: Client, message: Message):
    try:
        if "https://t.me/" not in message.text:
            await message.reply("❌ **Please send a valid Telegram URL.**")
            return
        
        # Check if user has session for restricted content
        session = await db.get_session(message.from_user.id)
        if not session and ("t.me/c/" in message.text or "t.me/b/" in message.text):
            await message.reply(
                "🔐 **Please /login first to access restricted content.**\n\n"
                "For public channels, login is not required."
            )
            return
        
        # Process the download
        await advanced_downloader.process_batch_download(
            client, message.from_user.id, message.text, message
        )
        
    except Exception as e:
        log_error(e, "handle_url")
        if ERROR_MESSAGE:
            await message.reply(f"❌ **Error:** {str(e)}")

# Callback query handler
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
                    f"🎥 Quality: {settings.get('quality', 'high').title()}", 
                    callback_data="toggle_quality"
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
                
                stats_text = f"""
📊 **Your Statistics**

👤 **User:** {callback_query.from_user.mention}
🆔 **User ID:** `{user_id}`
📅 **Joined:** {join_date}
🕐 **Last Used:** {last_used}
📥 **Downloads:** {download_count}
⭐ **Premium:** {'Yes' if user_data.get('is_premium', False) else 'No'}
                """
                
                buttons = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
                reply_markup = InlineKeyboardMarkup(buttons)
                await callback_query.edit_message_text(stats_text, reply_markup=reply_markup)
            
        elif data.startswith("toggle_"):
            settings = await db.get_user_settings(user_id)
            
            if data == "toggle_auto_delete":
                settings['auto_delete'] = not settings.get('auto_delete', True)
            elif data == "toggle_notification":
                settings['notification'] = not settings.get('notification', True)
            elif data == "toggle_quality":
                current_quality = settings.get('quality', 'high')
                settings['quality'] = 'low' if current_quality == 'high' else 'high'
            
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
                    f"🎥 Quality: {settings.get('quality', 'high').title()}", 
                    callback_data="toggle_quality"
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
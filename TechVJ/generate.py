# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import traceback
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import API_ID, API_HASH
from database.db import db
from utils.logger import log_error, log_info
from TechVJ.ultra_downloader import ultra_downloader

SESSION_STRING_SIZE = 351

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    try:
        user_data = await db.get_session(message.from_user.id)  
        if user_data is None:
            await message.reply("❌ **You are not logged in.**")
            return 
        
        # Close active session
        await ultra_downloader.close_user_session(message.from_user.id)
        
        # Remove session from database
        await db.set_session(message.from_user.id, session=None)  
        await message.reply("✅ **Logged out successfully!**")
        
        log_info(f"User {message.from_user.id} logged out")
        
    except Exception as e:
        log_error(e, "logout")
        await message.reply("❌ **Error during logout. Please try again.**")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    try:
        user_data = await db.get_session(message.from_user.id)
        if user_data is not None:
            await message.reply(
                "⚠️ **You are already logged in!**\n\n"
                "Use /logout to logout first, then login again."
            )
            return 
        
        user_id = int(message.from_user.id)
        
        # Step 1: Get phone number
        phone_number_msg = await bot.ask(
            chat_id=user_id, 
            text="📱 **Please send your phone number**\n\n"
                 "**Format:** Include country code\n"
                 "**Example:** `+1234567890`\n\n"
                 "Send /cancel to cancel the process.",
            timeout=300
        )
        
        if phone_number_msg.text == '/cancel':
            return await phone_number_msg.reply('❌ **Login cancelled!**')
        
        phone_number = phone_number_msg.text.strip()
        
        # Validate phone number format
        if not phone_number.startswith('+') or len(phone_number) < 10:
            await phone_number_msg.reply(
                "❌ **Invalid phone number format!**\n\n"
                "Please include country code (e.g., +1234567890)"
            )
            return
        
        # Step 2: Send OTP
        client = Client(":memory:", API_ID, API_HASH)
        await client.connect()
        
        loading_msg = await phone_number_msg.reply("📤 **Sending OTP...**")
        
        try:
            code = await client.send_code(phone_number)
            await loading_msg.edit("✅ **OTP sent successfully!**")
        except PhoneNumberInvalid:
            await loading_msg.edit('❌ **Invalid phone number!**')
            await client.disconnect()
            return
        except Exception as e:
            await loading_msg.edit(f'❌ **Error sending OTP:** {str(e)}')
            await client.disconnect()
            return
        
        # Step 3: Get OTP
        phone_code_msg = await bot.ask(
            user_id, 
            "🔐 **Enter the OTP you received**\n\n"
            "**Format:** Separate digits with spaces\n"
            "**Example:** If OTP is `12345`, send `1 2 3 4 5`\n\n"
            "Send /cancel to cancel the process.",
            filters=filters.text, 
            timeout=300
        )
        
        if phone_code_msg.text == '/cancel':
            await client.disconnect()
            return await phone_code_msg.reply('❌ **Login cancelled!**')
        
        try:
            phone_code = phone_code_msg.text.replace(" ", "").strip()
            await client.sign_in(phone_number, code.phone_code_hash, phone_code)
        except PhoneCodeInvalid:
            await phone_code_msg.reply('❌ **Invalid OTP!**')
            await client.disconnect()
            return
        except PhoneCodeExpired:
            await phone_code_msg.reply('❌ **OTP expired! Please try again.**')
            await client.disconnect()
            return
        except SessionPasswordNeeded:
            # Step 4: Handle 2FA
            two_step_msg = await bot.ask(
                user_id, 
                "🔒 **Two-Factor Authentication Enabled**\n\n"
                "Please enter your 2FA password:\n\n"
                "Send /cancel to cancel the process.",
                filters=filters.text, 
                timeout=300
            )
            
            if two_step_msg.text == '/cancel':
                await client.disconnect()
                return await two_step_msg.reply('❌ **Login cancelled!**')
            
            try:
                password = two_step_msg.text.strip()
                await client.check_password(password=password)
            except PasswordHashInvalid:
                await two_step_msg.reply('❌ **Invalid 2FA password!**')
                await client.disconnect()
                return
        
        # Step 5: Generate session string
        processing_msg = await bot.send_message(user_id, "⚙️ **Processing login...**")
        
        try:
            string_session = await client.export_session_string()
            await client.disconnect()
            
            if len(string_session) < SESSION_STRING_SIZE:
                await processing_msg.edit('❌ **Invalid session string generated!**')
                return
            
            # Save session to database
            await db.set_session(message.from_user.id, session=string_session)
            
            # Success message
            await processing_msg.edit(
                "🎉 **Login successful!**\n\n"
                "✅ You can now download restricted content\n"
                "🔐 Your session is securely stored\n"
                "⚡ Ultra-fast downloads enabled\n"
                "📄 Original format preservation active\n\n"
                "**Note:** If you get AUTH_KEY errors, /logout and /login again."
            )
            
            log_info(f"User {message.from_user.id} logged in successfully")
            
        except Exception as e:
            await processing_msg.edit(f"❌ **Login error:** {str(e)}")
            await client.disconnect()
            log_error(e, f"login for user {message.from_user.id}")
            return
            
    except TimeoutError:
        await message.reply("⏰ **Login timeout! Please try again.**")
    except Exception as e:
        log_error(e, f"main login for user {message.from_user.id}")
        await message.reply("❌ **Unexpected error during login. Please try again.**")

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN
from utils.logger import log_info, log_error
import asyncio

class Bot(Client):

    def __init__(self):
        super().__init__(
            "AdvancedSaveBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=100,  # Increased workers for better performance
            sleep_threshold=10
        )

    async def start(self):
        try:
            await super().start()
            me = await self.get_me()
            log_info(f"🚀 Bot Started Successfully!")
            log_info(f"👤 Bot Name: {me.first_name}")
            log_info(f"🆔 Bot Username: @{me.username}")
            log_info(f"🔢 Bot ID: {me.id}")
            log_info("🎉 Advanced Save Restricted Content Bot is now running!")
            
            # Send startup message to admin
            try:
                from config import ADMINS
                if ADMINS:
                    startup_msg = (
                        "🚀 **Bot Started Successfully!**\n\n"
                        f"🤖 **Bot:** @{me.username}\n"
                        f"🆔 **ID:** `{me.id}`\n"
                        f"⚡ **Status:** Online and Ready\n"
                        f"🔧 **Version:** Advanced v2.0"
                    )
                    await self.send_message(ADMINS[0], startup_msg)
            except Exception as e:
                log_error(e, "send startup message")
                
        except Exception as e:
            log_error(e, "bot start")

    async def stop(self, *args):
        try:
            await super().stop()
            log_info("🛑 Bot Stopped Successfully!")
            
            # Send shutdown message to admin
            try:
                from config import ADMINS
                if ADMINS:
                    shutdown_msg = "🛑 **Bot Stopped**\n\nBot has been shut down gracefully."
                    await self.send_message(ADMINS[0], shutdown_msg)
            except Exception as e:
                log_error(e, "send shutdown message")
                
        except Exception as e:
            log_error(e, "bot stop")

if __name__ == "__main__":
    try:
        bot = Bot()
        log_info("🔄 Starting bot...")
        bot.run()
    except KeyboardInterrupt:
        log_info("🛑 Bot stopped by user")
    except Exception as e:
        log_error(e, "main")

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
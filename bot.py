# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, WORKERS, SLEEP_THRESHOLD
from utils.logger import log_info, log_error
import asyncio

class UltraBot(Client):

    def __init__(self):
        super().__init__(
            "UltraFastSaveBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="TechVJ"),
            workers=WORKERS,  # Ultra-fast workers
            sleep_threshold=SLEEP_THRESHOLD,  # Reduced sleep threshold
            max_concurrent_transmissions=50  # Increased concurrent transmissions
        )

    async def start(self):
        try:
            await super().start()
            me = await self.get_me()
            log_info(f"🚀 Ultra-Fast Bot Started Successfully!")
            log_info(f"👤 Bot Name: {me.first_name}")
            log_info(f"🆔 Bot Username: @{me.username}")
            log_info(f"🔢 Bot ID: {me.id}")
            log_info(f"⚡ Workers: {WORKERS}")
            log_info(f"🚀 Max Concurrent: 50")
            log_info("🎉 Ultra-Fast Save Restricted Content Bot is now running!")
            
            # Send startup message to admin
            try:
                from config import ADMINS
                if ADMINS:
                    startup_msg = (
                        "🚀 **Ultra-Fast Bot Started Successfully!**\n\n"
                        f"🤖 **Bot:** @{me.username}\n"
                        f"🆔 **ID:** `{me.id}`\n"
                        f"⚡ **Status:** Ultra-Fast Mode Active\n"
                        f"🔧 **Version:** Ultra-Fast v3.0\n"
                        f"🚀 **Workers:** {WORKERS}\n"
                        f"📊 **Max Concurrent:** 50\n"
                        f"⚡ **Performance:** Maximum Speed"
                    )
                    await self.send_message(ADMINS[0], startup_msg)
            except Exception as e:
                log_error(e, "send startup message")
                
        except Exception as e:
            log_error(e, "bot start")

    async def stop(self, *args):
        try:
            await super().stop()
            log_info("🛑 Ultra-Fast Bot Stopped Successfully!")
            
            # Send shutdown message to admin
            try:
                from config import ADMINS
                if ADMINS:
                    shutdown_msg = "🛑 **Ultra-Fast Bot Stopped**\n\nBot has been shut down gracefully."
                    await self.send_message(ADMINS[0], shutdown_msg)
            except Exception as e:
                log_error(e, "send shutdown message")
                
        except Exception as e:
            log_error(e, "bot stop")

if __name__ == "__main__":
    try:
        bot = UltraBot()
        log_info("🔄 Starting ultra-fast bot...")
        bot.run()
    except KeyboardInterrupt:
        log_info("🛑 Ultra-fast bot stopped by user")
    except Exception as e:
        log_error(e, "main")

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
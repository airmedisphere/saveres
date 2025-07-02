from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from database.db import db
from pyrogram import Client, filters
from config import ADMINS
import asyncio
import datetime
import time
from utils.logger import log_error, log_info

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        return False, "Error"
    except Exception as e:
        log_error(e, f"broadcast_messages to user {user_id}")
        return False, "Error"

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_handler(bot, message):
    try:
        users = await db.get_all_users()
        b_msg = message.reply_to_message
        
        if not b_msg:
            return await message.reply_text("**❌ Reply to a message to broadcast it**")
        
        sts = await message.reply_text('📡 **Starting broadcast...**')
        start_time = time.time()
        total_users = await db.total_users_count()
        
        done = 0
        blocked = 0
        deleted = 0
        failed = 0
        success = 0
        
        log_info(f"Starting broadcast to {total_users} users")
        
        async for user in users:
            if 'id' in user:
                pti, sh = await broadcast_messages(int(user['id']), b_msg)
                if pti:
                    success += 1
                elif pti == False:
                    if sh == "Blocked":
                        blocked += 1
                    elif sh == "Deleted":
                        deleted += 1
                    elif sh == "Error":
                        failed += 1
                done += 1
                
                # Update status every 20 users
                if not done % 20:
                    elapsed_time = int(time.time() - start_time)
                    try:
                        await sts.edit(
                            f"📡 **Broadcasting...**\n\n"
                            f"👥 **Total Users:** {total_users}\n"
                            f"✅ **Completed:** {done}/{total_users}\n"
                            f"🎯 **Success:** {success}\n"
                            f"🚫 **Blocked:** {blocked}\n"
                            f"🗑️ **Deleted:** {deleted}\n"
                            f"❌ **Failed:** {failed}\n"
                            f"⏱️ **Time:** {elapsed_time}s"
                        )
                    except:
                        pass
            else:
                done += 1
                failed += 1
        
        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        
        final_msg = (
            f"🎉 **Broadcast Completed!**\n\n"
            f"⏱️ **Time Taken:** {time_taken}\n"
            f"👥 **Total Users:** {total_users}\n"
            f"✅ **Successful:** {success}\n"
            f"🚫 **Blocked:** {blocked}\n"
            f"🗑️ **Deleted:** {deleted}\n"
            f"❌ **Failed:** {failed}\n\n"
            f"📊 **Success Rate:** {(success/total_users*100):.1f}%"
        )
        
        await sts.edit(final_msg)
        log_info(f"Broadcast completed: {success}/{total_users} successful")
        
    except Exception as e:
        log_error(e, "broadcast_handler")
        await message.reply_text("❌ **Error during broadcast. Check logs for details.**")

# Admin stats command
@Client.on_message(filters.command("adminstats") & filters.user(ADMINS))
async def admin_stats(bot, message):
    try:
        total_users = await db.total_users_count()
        
        # Get additional stats
        pipeline = [
            {"$group": {
                "_id": None,
                "total_downloads": {"$sum": "$download_count"},
                "premium_users": {"$sum": {"$cond": ["$is_premium", 1, 0]}},
                "logged_in_users": {"$sum": {"$cond": [{"$ne": ["$session", None]}, 1, 0]}}
            }}
        ]
        
        stats_result = await db.col.aggregate(pipeline).to_list(1)
        stats = stats_result[0] if stats_result else {}
        
        stats_text = f"""
📊 **Admin Statistics**

👥 **Total Users:** {total_users}
🔐 **Logged In Users:** {stats.get('logged_in_users', 0)}
⭐ **Premium Users:** {stats.get('premium_users', 0)}
📥 **Total Downloads:** {stats.get('total_downloads', 0)}

📈 **Engagement Rate:** {(stats.get('logged_in_users', 0)/total_users*100):.1f}%
💎 **Premium Rate:** {(stats.get('premium_users', 0)/total_users*100):.1f}%
        """
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        log_error(e, "admin_stats")
        await message.reply_text("❌ **Error fetching admin stats.**")
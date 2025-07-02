import motor.motor_asyncio
from config import DB_NAME, DB_URI
from utils.logger import log_error, log_info
from typing import Optional, Dict, Any
import asyncio

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.channels_col = self.db.channels
        self.stats_col = self.db.stats

    def new_user(self, id, name):
        return dict(
            id=id,
            name=name,
            session=None,
            join_date=None,
            last_used=None,
            download_count=0,
            is_premium=False,
            settings={
                'auto_delete': True,
                'notification': True,
                'quality': 'high'
            }
        )
    
    async def add_user(self, id, name):
        try:
            user = self.new_user(id, name)
            await self.col.insert_one(user)
            log_info(f"New user added: {id} - {name}")
        except Exception as e:
            log_error(e, "add_user")
    
    async def is_user_exist(self, id):
        try:
            user = await self.col.find_one({'id': int(id)})
            return bool(user)
        except Exception as e:
            log_error(e, "is_user_exist")
            return False
    
    async def total_users_count(self):
        try:
            count = await self.col.count_documents({})
            return count
        except Exception as e:
            log_error(e, "total_users_count")
            return 0

    async def get_all_users(self):
        try:
            return self.col.find({})
        except Exception as e:
            log_error(e, "get_all_users")
            return []

    async def delete_user(self, user_id):
        try:
            await self.col.delete_many({'id': int(user_id)})
            log_info(f"User deleted: {user_id}")
        except Exception as e:
            log_error(e, "delete_user")

    async def set_session(self, id, session):
        try:
            await self.col.update_one(
                {'id': int(id)}, 
                {'$set': {'session': session}},
                upsert=True
            )
        except Exception as e:
            log_error(e, "set_session")

    async def get_session(self, id):
        try:
            user = await self.col.find_one({'id': int(id)})
            return user.get('session') if user else None
        except Exception as e:
            log_error(e, "get_session")
            return None

    async def update_user_stats(self, user_id: int, download_count: int = 1):
        try:
            await self.col.update_one(
                {'id': int(user_id)},
                {
                    '$inc': {'download_count': download_count},
                    '$set': {'last_used': None}
                }
            )
        except Exception as e:
            log_error(e, "update_user_stats")

    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        try:
            user = await self.col.find_one({'id': int(user_id)})
            return user.get('settings', {}) if user else {}
        except Exception as e:
            log_error(e, "get_user_settings")
            return {}

    async def update_user_settings(self, user_id: int, settings: Dict[str, Any]):
        try:
            await self.col.update_one(
                {'id': int(user_id)},
                {'$set': {'settings': settings}}
            )
        except Exception as e:
            log_error(e, "update_user_settings")

    # Channel management
    async def add_channel(self, channel_id: int, channel_name: str, added_by: int):
        try:
            channel_data = {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'added_by': added_by,
                'added_date': None,
                'total_messages': 0,
                'downloaded_messages': 0
            }
            await self.channels_col.insert_one(channel_data)
        except Exception as e:
            log_error(e, "add_channel")

    async def get_user_channels(self, user_id: int):
        try:
            return await self.channels_col.find({'added_by': user_id}).to_list(None)
        except Exception as e:
            log_error(e, "get_user_channels")
            return []

    # Statistics
    async def update_download_stats(self, user_id: int, file_type: str, file_size: int):
        try:
            stats_data = {
                'user_id': user_id,
                'file_type': file_type,
                'file_size': file_size,
                'download_date': None
            }
            await self.stats_col.insert_one(stats_data)
        except Exception as e:
            log_error(e, "update_download_stats")

db = Database(DB_URI, DB_NAME)
# Advanced downloader module for backward compatibility
# This module provides compatibility with the ultra_downloader

from TechVJ.ultra_downloader import ultra_downloader

# Export the ultra_downloader as advanced_downloader for compatibility
advanced_downloader = ultra_downloader

# Additional compatibility functions
async def close_user_session(user_id: int):
    """Close user session - compatibility function"""
    return await ultra_downloader.close_user_session(user_id)

async def cancel_download(user_id: int):
    """Cancel download - compatibility function"""
    return await ultra_downloader.cancel_download(user_id)

async def process_batch_download(bot, user_id: int, url: str, original_message):
    """Process batch download - compatibility function"""
    return await ultra_downloader.process_ultra_batch_download(bot, user_id, url, original_message)
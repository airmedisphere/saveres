import os

# Bot token @Botfather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Your API ID from my.telegram.org
API_ID = int(os.environ.get("API_ID", "22649259"))

# Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "545169590ffbfe0bf8bade55e3a1cfde")

# Your Owner / Admin Id For Broadcast 
ADMINS = list(map(int, os.environ.get("ADMINS", "6221765779").split()))

# Your Mongodb Database Url
DB_URI = os.environ.get("DB_URI", "mongodb+srv://worksbeyondworks:12aoRiYgxljiPYyK@cluster0.cbkwr4g.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "airsaver")

# Redis URL for caching (optional)
REDIS_URL = os.environ.get("REDIS_URL", "")

# If You Want Error Message In Your Personal Message Then Turn It True Else False
ERROR_MESSAGE = bool(os.environ.get('ERROR_MESSAGE', True))

# Download directory
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads/")

# Max concurrent downloads
MAX_CONCURRENT_DOWNLOADS = int(os.environ.get("MAX_CONCURRENT_DOWNLOADS", "5"))

# Download timeout in seconds
DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "300"))

# Max file size in MB
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "2000"))

# Enable logging
ENABLE_LOGGING = bool(os.environ.get("ENABLE_LOGGING", True))
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

# Ultra-fast download settings (Optimized for maximum speed)
MAX_CONCURRENT_DOWNLOADS = int(os.environ.get("MAX_CONCURRENT_DOWNLOADS", "50"))  # Increased to 50
MAX_CONCURRENT_UPLOADS = int(os.environ.get("MAX_CONCURRENT_UPLOADS", "25"))     # Increased to 25
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "2097152"))  # 2MB chunks for faster transfer
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))      # Reduced retries for speed

# Timeout settings (optimized for speed)
DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", "900"))  # 15 minutes
UPLOAD_TIMEOUT = int(os.environ.get("UPLOAD_TIMEOUT", "900"))      # 15 minutes
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "60")) # 60 seconds

# Max file size in MB (increased)
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", "4000"))  # 4GB

# Enable logging
ENABLE_LOGGING = bool(os.environ.get("ENABLE_LOGGING", True))

# Performance settings (Ultra-fast mode)
WORKERS = int(os.environ.get("WORKERS", "300"))  # Increased workers for maximum speed
SLEEP_THRESHOLD = int(os.environ.get("SLEEP_THRESHOLD", "3"))  # Reduced sleep threshold

# Progress update frequency (in seconds) - faster updates
PROGRESS_UPDATE_INTERVAL = int(os.environ.get("PROGRESS_UPDATE_INTERVAL", "1"))

# Enable direct streaming (faster for large files)
ENABLE_STREAMING = bool(os.environ.get("ENABLE_STREAMING", True))

# Advanced speed optimization settings
ENABLE_ULTRA_MODE = bool(os.environ.get("ENABLE_ULTRA_MODE", True))
MAX_BATCH_SIZE = int(os.environ.get("MAX_BATCH_SIZE", "1000"))  # Maximum messages in a batch
CONCURRENT_SESSION_LIMIT = int(os.environ.get("CONCURRENT_SESSION_LIMIT", "10"))  # Max concurrent user sessions
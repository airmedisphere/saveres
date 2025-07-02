import logging
import os
from datetime import datetime
from config import ENABLE_LOGGING

def setup_logger():
    """Setup logging configuration"""
    if not ENABLE_LOGGING:
        return logging.getLogger(__name__)
    
    # Create logs directory
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logger()

def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    if ENABLE_LOGGING:
        logger.error(f"Error in {context}: {str(error)}", exc_info=True)

def log_info(message: str):
    """Log info message"""
    if ENABLE_LOGGING:
        logger.info(message)

def log_warning(message: str):
    """Log warning message"""
    if ENABLE_LOGGING:
        logger.warning(message)
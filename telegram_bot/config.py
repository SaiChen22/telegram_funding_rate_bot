import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the Telegram bot"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Funding Rate Alert Thresholds (in percentage)
    UPPER_THRESHOLD = float(os.getenv('UPPER_THRESHOLD', '0.6'))  # 0.6% default
    LOWER_THRESHOLD = float(os.getenv('LOWER_THRESHOLD', '-1.0'))  # -1.0% default
    
    # Monitoring Configuration
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 minutes default
    
    # Binance API Configuration
    BINANCE_BASE_URL = "https://fapi.binance.com"
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'funding_bot.log')
    
    # Bot Settings
    MAX_MESSAGE_LENGTH = 4096  # Telegram message limit
    BATCH_SIZE = 50  # Number of rates to show per message
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required. Please set it in your .env file.")
        
        if cls.UPPER_THRESHOLD <= cls.LOWER_THRESHOLD:
            raise ValueError("UPPER_THRESHOLD must be greater than LOWER_THRESHOLD")
        
        if cls.CHECK_INTERVAL < 60:
            raise ValueError("CHECK_INTERVAL must be at least 60 seconds to avoid API rate limits")
        
        return True

# Default configuration values
DEFAULT_CONFIG = {
    'UPPER_THRESHOLD': 0.6,
    'LOWER_THRESHOLD': -1.0,
    'CHECK_INTERVAL': 300,
    'LOG_LEVEL': 'INFO'
}
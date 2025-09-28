#!/usr/bin/env python3
"""
Binance Futures Funding Rate Monitor Bot

This bot monitors Binance futures funding rates and sends Telegram alerts
when rates cross specified thresholds (default: 0.6% high, -1.0% low).

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from config import Config
from telegram_bot import FundingRateBot

# Global variable to hold the bot instance
bot_instance = None

def setup_logging():
    """Configure logging for the application"""
    config = Config()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from telegram library
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    
    if bot_instance and bot_instance.monitor and bot_instance.monitor.monitoring:
        asyncio.create_task(bot_instance.monitor.stop_monitoring())
    
    sys.exit(0)

async def main():
    """Main application entry point"""
    global bot_instance
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("Binance Funding Rate Monitor Bot Starting")
    logger.info("=" * 50)
    
    try:
        # Validate configuration
        config = Config()
        config.validate()
        logger.info("Configuration validated successfully")
        
        # Log configuration
        logger.info(f"Upper threshold: {config.UPPER_THRESHOLD}%")
        logger.info(f"Lower threshold: {config.LOWER_THRESHOLD}%")
        logger.info(f"Check interval: {config.CHECK_INTERVAL}s")
        
        # Create and run bot
        bot_instance = FundingRateBot()
        logger.info("Bot initialized successfully")
        
        # Start the bot
        await bot_instance.run()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your .env file or environment variables")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    
    finally:
        logger.info("Bot shutdown complete")

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        ('telegram', 'telegram'),
        ('aiohttp', 'aiohttp'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall them with:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def print_banner():
    """Print application banner"""
    banner = """
    ╔════════════════════════════════════════════════════╗
    ║        Binance Futures Funding Rate Monitor        ║
    ║                    Telegram Bot                    ║
    ╚════════════════════════════════════════════════════╝
    
    🚀 Features:
    • Monitor all Binance futures funding rates
    • Real-time alerts via Telegram
    • Configurable thresholds
    • Interactive bot commands
    
    📋 Setup:
    1. Copy .env.template to .env
    2. Add your Telegram bot token
    3. Run: python main.py
    
    """
    print(banner)

if __name__ == "__main__":
    print_banner()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    try:
        # Run the bot
        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
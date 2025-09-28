#!/usr/bin/env python3
"""
Simple launcher for the Binance Funding Rate Monitor Bot
"""

import sys
import logging
from telegram_bot import FundingRateBot

def setup_logging():
    """Configure basic logging"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Reduce telegram library noise
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

def main():
    """Main function"""
    print("🚀 Starting Binance Funding Rate Monitor Bot...")
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        from config import Config
        config = Config()
        config.validate()
        logger.info("Configuration validated successfully")
        
        # Create and run bot
        bot = FundingRateBot()
        logger.info("Bot initialized successfully")
        
        # This will run the bot using run_polling() which handles its own event loop
        import asyncio
        asyncio.run(bot.run())
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Bot error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        sys.exit(0)
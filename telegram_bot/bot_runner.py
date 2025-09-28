#!/usr/bin/env python3
"""
Binance Funding Rate Monitor Bot - Railway Deployment Ready
"""

import sys
import logging
import asyncio
import nest_asyncio
import os

# Enable nested event loops
nest_asyncio.apply()

# Import health server for Railway
try:
    from health_server import start_health_server_sync
    HEALTH_SERVER_AVAILABLE = True
except ImportError:
    HEALTH_SERVER_AVAILABLE = False

def setup_logging():
    """Configure basic logging"""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/funding_bot.log')
        ]
    )
    # Reduce telegram library noise
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

async def run_bot():
    """Async function to run the bot"""
    from telegram_bot import FundingRateBot
    
    logger = logging.getLogger(__name__)
    
    try:
        # Start health server for Railway
        if HEALTH_SERVER_AVAILABLE:
            health_port = int(os.getenv('PORT', 8000))
            logger.info(f"Starting health server on port {health_port}")
            start_health_server_sync(health_port)
        
        # Validate configuration
        from config import Config
        config = Config()
        config.validate()
        logger.info("Configuration validated successfully")
        logger.info(f"Upper threshold: {config.UPPER_THRESHOLD}%")
        logger.info(f"Lower threshold: {config.LOWER_THRESHOLD}%")
        logger.info(f"Check interval: {config.CHECK_INTERVAL}s")
        
        # Create and run bot
        bot = FundingRateBot()
        logger.info("Bot initialized successfully")
        logger.info("Starting bot polling...")
        
        # Run the bot
        await bot.run()
        return 0
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file")
        return 1
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1

def main():
    """Main function"""
    print("🚀 Starting Binance Funding Rate Monitor Bot...")
    print("Press Ctrl+C to stop the bot")
    
    setup_logging()
    
    try:
        # Use asyncio.run for clean event loop management
        return asyncio.run(run_bot())
            
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
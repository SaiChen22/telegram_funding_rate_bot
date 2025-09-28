#!/usr/bin/env python3
"""
Webhook Setup Script for Telegram Bot on Vercel
Run this script to set up the webhook URL for your deployed bot
"""

import os
import sys
import asyncio
import aiohttp
from telegram import Bot

# Add the telegram_bot directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'telegram_bot'))

from config import Config

async def setup_webhook(webhook_url):
    """Set up webhook for the Telegram bot"""
    try:
        config = Config()
        config.validate()
        
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        
        # Set webhook
        await bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set successfully: {webhook_url}")
        
        # Get webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"📋 Webhook Info:")
        print(f"   URL: {webhook_info.url}")
        print(f"   Pending updates: {webhook_info.pending_update_count}")
        print(f"   Last error: {webhook_info.last_error_message or 'None'}")
        
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False
    
    return True

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python setup_webhook.py <webhook_url>")
        print("Example: python setup_webhook.py https://your-app.vercel.app/api/webhook")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    
    if not webhook_url.startswith('https://'):
        print("❌ Webhook URL must use HTTPS")
        sys.exit(1)
    
    print(f"🔧 Setting up webhook: {webhook_url}")
    
    success = asyncio.run(setup_webhook(webhook_url))
    
    if success:
        print("\n🎉 Webhook setup completed!")
        print("Your bot should now receive updates via webhook.")
    else:
        print("\n❌ Webhook setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
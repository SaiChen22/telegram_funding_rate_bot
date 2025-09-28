import json
import os
import sys
import asyncio
from urllib.parse import parse_qs

# Add the telegram_bot directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram_bot'))

from telegram import Update
from telegram.ext import Application
import logging

# Import our bot components
from config import Config
from telegram_bot import FundingRateBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global bot instance
bot_instance = None
application = None

def get_bot_instance():
    """Get or create bot instance"""
    global bot_instance, application
    
    if bot_instance is None:
        try:
            config = Config()
            config.validate()
            bot_instance = FundingRateBot()
            application = bot_instance.application
            logger.info("Bot instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create bot instance: {e}")
            raise
    
    return bot_instance, application

async def handle_webhook(request_body, headers):
    """Handle incoming webhook from Telegram"""
    try:
        bot, app = get_bot_instance()
        
        # Parse the JSON update from Telegram
        update_data = json.loads(request_body)
        update = Update.de_json(update_data, app.bot)
        
        # Process the update
        await app.process_update(update)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Get request method and body
        method = request.get('httpMethod', 'GET')
        body = request.get('body', '')
        headers = request.get('headers', {})
        
        logger.info(f"Received {method} request")
        
        if method == 'GET':
            # Health check endpoint
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                },
                'body': json.dumps({
                    'status': 'healthy',
                    'message': 'Telegram Funding Rate Bot Webhook'
                })
            }
        
        elif method == 'POST':
            # Handle Telegram webhook
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(handle_webhook(body, headers))
                return result
            finally:
                loop.close()
        
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# For local testing
if __name__ == '__main__':
    # Test the webhook locally
    test_request = {
        'httpMethod': 'GET',
        'body': '',
        'headers': {}
    }
    
    result = handler(test_request)
    print(json.dumps(result, indent=2))
# 🤖 Telegram Funding Rate Bot

A Telegram bot that monitors Binance futures funding rates and sends alerts when they cross specified thresholds.

## Features
- Real-time monitoring of Binance futures funding rates
- Telegram alerts when rates cross 0.6% or -1.0%  
- Interactive bot commands
- Multiple API endpoint fallbacks
- Enhanced error handling

## Quick Start

1. Install dependencies:
```bash
cd telegram_bot
pip install -r requirements.txt
```

2. Set up your Telegram bot token:
```bash
cp .env.template .env
# Edit .env and add your bot token from @BotFather
```

3. Run the bot:
```bash
python bot_runner.py
```

## Bot Commands
- `/start` - Initialize bot
- `/monitor` - Start monitoring
- `/stop` - Stop monitoring  
- `/rates` - Show current rates
- `/help` - Show help

## Configuration
Edit `.env` file to customize thresholds and settings.

## Deployment
Works on Heroku, Railway, Google Cloud Run, or any VPS.
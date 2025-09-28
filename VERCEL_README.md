# Telegram Funding Rate Bot - Vercel Deployment

## 🚀 Deploy to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Set Environment Variables
```bash
vercel env add TELEGRAM_BOT_TOKEN
vercel env add TELEGRAM_CHAT_ID
vercel env add UPPER_THRESHOLD
vercel env add LOWER_THRESHOLD
vercel env add CHECK_INTERVAL
```

Or set them via Vercel dashboard:
- `TELEGRAM_BOT_TOKEN`: Your bot token from @BotFather
- `TELEGRAM_CHAT_ID`: Your chat ID (optional, for alerts)
- `UPPER_THRESHOLD`: `0.6`
- `LOWER_THRESHOLD`: `-1.0`
- `CHECK_INTERVAL`: `300`

### 4. Deploy
```bash
vercel --prod
```

### 5. Set Webhook
After deployment, run:
```bash
python setup_webhook.py https://your-app.vercel.app/api/webhook
```

## 📋 How It Works

- **Webhook Mode**: The bot runs in webhook mode instead of polling
- **Serverless**: Each request is handled by a serverless function
- **API Endpoint**: `/api/webhook` receives updates from Telegram
- **Health Check**: GET request to `/api/webhook` returns health status

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `1234567890:ABC...` |
| `TELEGRAM_CHAT_ID` | Chat ID for alerts | `-1234567890` |
| `UPPER_THRESHOLD` | High funding rate alert | `0.6` |
| `LOWER_THRESHOLD` | Low funding rate alert | `-1.0` |
| `CHECK_INTERVAL` | Check interval (seconds) | `300` |

## 📱 Bot Commands

- `/start` - Initialize the bot
- `/monitor` - Start monitoring funding rates
- `/stop` - Stop monitoring
- `/status` - Check monitoring status
- `/rates` - Show current funding rates
- `/top` - Show highest/lowest rates
- `/settings` - Configure thresholds

## ⚠️ Important Notes

1. **Webhook URL must be HTTPS** - Vercel provides this automatically
2. **Polling vs Webhook** - This version uses webhooks, not polling
3. **Cold Starts** - First request may be slower due to serverless nature
4. **Monitoring** - For continuous monitoring, consider using a cron job service

## 🐛 Troubleshooting

### Check webhook status:
```bash
python setup_webhook.py https://your-app.vercel.app/api/webhook
```

### View logs:
```bash
vercel logs
```

### Test webhook locally:
```bash
vercel dev
```
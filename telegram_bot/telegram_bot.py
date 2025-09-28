import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Set
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from config import Config
from funding_monitor import FundingRateMonitor
from binance_client import BinanceClient

logger = logging.getLogger(__name__)

class FundingRateBot:
    """Telegram bot for monitoring Binance futures funding rates"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
        
        self.application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        self.monitor: FundingRateMonitor = None
        self.binance_client = BinanceClient()
        
        # Track authorized users (you can extend this with a database)
        self.authorized_users: Set[int] = set()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up command and callback handlers"""
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("monitor", self.monitor_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("rates", self.rates_command))
        self.application.add_handler(CommandHandler("top", self.top_rates_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        self.authorized_users.add(user_id)
        
        welcome_text = (
            "🚀 **Binance Funding Rate Monitor Bot** 🚀\n\n"
            "I'll help you monitor funding rates across all Binance futures and alert you "
            f"when rates hit {self.config.UPPER_THRESHOLD}% or {self.config.LOWER_THRESHOLD}%\n\n"
            "**Available Commands:**\n"
            "• /monitor - Start monitoring funding rates\n"
            "• /stop - Stop monitoring\n" 
            "• /status - Check monitoring status\n"
            "• /rates - Show current funding rates\n"
            "• /top - Show highest/lowest rates\n"
            "• /settings - Configure alert thresholds\n"
            "• /help - Show this help message\n\n"
            "Use /monitor to get started!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🟢 Start Monitoring", callback_data="start_monitoring")],
            [InlineKeyboardButton("📊 Show Current Rates", callback_data="show_rates")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "**📖 Funding Rate Bot Help**\n\n"
            "**Commands:**\n"
            "• `/monitor` - Start monitoring funding rates\n"
            "• `/stop` - Stop monitoring\n"
            "• `/status` - Check current monitoring status\n"
            "• `/rates [symbol]` - Show funding rates (optionally for specific symbol)\n"
            "• `/top [n]` - Show top N highest/lowest rates (default: 10)\n"
            "• `/settings` - Configure alert thresholds\n\n"
            "**Current Thresholds:**\n"
            f"• High Alert: ≥ {self.config.UPPER_THRESHOLD}%\n"
            f"• Low Alert: ≤ {self.config.LOWER_THRESHOLD}%\n\n"
            "**About Funding Rates:**\n"
            "Funding rates are periodic payments between traders. "
            "High positive rates mean long positions pay shorts, "
            "while negative rates mean shorts pay longs.\n\n"
            f"Monitoring checks rates every {self.config.CHECK_INTERVAL // 60} minutes."
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monitor command"""
        if not self._is_authorized(update):
            return
        
        if self.monitor and self.monitor.monitoring:
            await update.message.reply_text("🟢 Monitoring is already active!")
            return
        
        # Create monitor with alert callback
        self.monitor = FundingRateMonitor(
            alert_callback=self._send_funding_alert,
            upper_threshold=self.config.UPPER_THRESHOLD,
            lower_threshold=self.config.LOWER_THRESHOLD,
            check_interval=self.config.CHECK_INTERVAL
        )
        
        await self.monitor.start_monitoring()
        
        keyboard = [[InlineKeyboardButton("🔴 Stop Monitoring", callback_data="stop_monitoring")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🟢 **Monitoring Started!**\n\n"
            f"• Checking rates every {self.config.CHECK_INTERVAL // 60} minutes\n"
            f"• High alert threshold: **{self.config.UPPER_THRESHOLD}%**\n"
            f"• Low alert threshold: **{self.config.LOWER_THRESHOLD}%**\n\n"
            f"You'll receive alerts when funding rates cross these thresholds.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        if not self._is_authorized(update):
            return
        
        if not self.monitor or not self.monitor.monitoring:
            await update.message.reply_text("🔴 Monitoring is not active.")
            return
        
        await self.monitor.stop_monitoring()
        
        keyboard = [[InlineKeyboardButton("🟢 Start Monitoring", callback_data="start_monitoring")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔴 **Monitoring Stopped**\n\n"
            "You will no longer receive funding rate alerts.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not self._is_authorized(update):
            return
        
        if not self.monitor:
            status = "🔴 **Not Monitoring**"
            details = "Use /monitor to start monitoring funding rates."
        elif self.monitor.monitoring:
            status = "🟢 **Actively Monitoring**"
            details = (
                f"• Check interval: {self.config.CHECK_INTERVAL // 60} minutes\n"
                f"• Thresholds: {self.config.UPPER_THRESHOLD}% / {self.config.LOWER_THRESHOLD}%\n"
                f"• Tracked symbols: {len(self.monitor.get_current_rates())}\n"
                f"• Active alerts: {self.monitor.get_alerts_count()}"
            )
        else:
            status = "🔴 **Stopped**"
            details = "Monitoring was stopped. Use /monitor to restart."
        
        message = f"{status}\n\n{details}"
        
        keyboard = []
        if self.monitor and self.monitor.monitoring:
            keyboard.append([InlineKeyboardButton("🔴 Stop", callback_data="stop_monitoring")])
        else:
            keyboard.append([InlineKeyboardButton("🟢 Start", callback_data="start_monitoring")])
        
        keyboard.append([InlineKeyboardButton("📊 Current Rates", callback_data="show_rates")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def rates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rates command"""
        if not self._is_authorized(update):
            return
        
        # Get symbol from args if provided
        symbol = None
        if context.args:
            symbol = context.args[0].upper()
        
        await update.message.reply_text("📊 Fetching current funding rates...")
        
        try:
            if symbol:
                # Get rate for specific symbol
                rate_data = await self.binance_client.get_funding_rate_for_symbol(symbol)
                if rate_data:
                    message = self._format_single_rate(rate_data)
                else:
                    message = f"❌ Could not find funding rate for {symbol}"
            else:
                # Get all rates
                rates = await self.binance_client.get_funding_rates()
                message = self._format_rates_summary(rates[:20])  # Show top 20
                
        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            message = "❌ Error fetching funding rates. Please try again later."
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def top_rates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /top command"""
        if not self._is_authorized(update):
            return
        
        # Get number from args if provided
        limit = 10
        if context.args:
            try:
                limit = min(int(context.args[0]), 50)  # Max 50
            except ValueError:
                pass
        
        await update.message.reply_text("📊 Fetching top funding rates...")
        
        try:
            rates = await self.binance_client.get_funding_rates()
            
            # Sort by funding rate
            sorted_rates = sorted(rates, key=lambda x: x['funding_rate'], reverse=True)
            
            highest = sorted_rates[:limit]
            lowest = sorted_rates[-limit:][::-1]  # Reverse for ascending order
            
            message = f"**🔝 Top {limit} Highest Rates:**\n"
            for i, rate in enumerate(highest, 1):
                message += f"{i}. `{rate['symbol']}`: **{rate['funding_rate']:+.4f}%**\n"
            
            message += f"\n**🔻 Top {limit} Lowest Rates:**\n"
            for i, rate in enumerate(lowest, 1):
                message += f"{i}. `{rate['symbol']}`: **{rate['funding_rate']:+.4f}%**\n"
            
        except Exception as e:
            logger.error(f"Error fetching top rates: {e}")
            message = "❌ Error fetching funding rates. Please try again later."
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        if not self._is_authorized(update):
            return
        
        keyboard = [
            [InlineKeyboardButton("📈 Set High Threshold", callback_data="set_high_threshold")],
            [InlineKeyboardButton("📉 Set Low Threshold", callback_data="set_low_threshold")],
            [InlineKeyboardButton("⏰ Set Check Interval", callback_data="set_interval")],
            [InlineKeyboardButton("🔄 Reset Alerts", callback_data="reset_alerts")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = (
            "⚙️ **Current Settings**\n\n"
            f"• High Alert: **{self.config.UPPER_THRESHOLD}%**\n"
            f"• Low Alert: **{self.config.LOWER_THRESHOLD}%**\n"
            f"• Check Interval: **{self.config.CHECK_INTERVAL // 60} minutes**\n\n"
            "Choose what you'd like to adjust:"
        )
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_monitoring":
            await self.monitor_command(update, context)
        elif query.data == "stop_monitoring":
            await self.stop_command(update, context)
        elif query.data == "show_rates":
            await self.rates_command(update, context)
        elif query.data == "settings":
            await self.settings_command(update, context)
        elif query.data == "reset_alerts":
            if self.monitor:
                self.monitor.reset_alerts()
            await query.edit_message_text("✅ Alert history reset!", parse_mode='Markdown')
    
    async def _send_funding_alert(self, alert_info: Dict):
        """Send funding rate alert to all authorized users"""
        symbol = alert_info['symbol']
        rate = alert_info['funding_rate']
        alert_type = alert_info['alert_type']
        mark_price = alert_info['mark_price']
        
        # Format alert message
        emoji = "🔴" if alert_type == "HIGH" else "🟢"
        direction = "above" if alert_type == "HIGH" else "below"
        threshold = alert_info['threshold']
        
        message = (
            f"{emoji} **FUNDING RATE ALERT** {emoji}\n\n"
            f"**Symbol:** `{symbol}`\n"
            f"**Rate:** **{rate:+.4f}%**\n"
            f"**Threshold:** {direction} {threshold}%\n"
            f"**Mark Price:** ${mark_price:,.4f}\n"
            f"**Time:** {alert_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
            f"{'📈 Long positions paying shorts' if rate > 0 else '📉 Short positions paying longs'}"
        )
        
        # Send to all authorized users
        for user_id in self.authorized_users:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send alert to user {user_id}: {e}")
    
    def _is_authorized(self, update: Update) -> bool:
        """Check if user is authorized"""
        user_id = update.effective_user.id
        if user_id not in self.authorized_users:
            self.authorized_users.add(user_id)  # Auto-authorize for now
        return True
    
    def _format_single_rate(self, rate_data: Dict) -> str:
        """Format single funding rate for display"""
        return (
            f"**📊 {rate_data['symbol']} Funding Rate**\n\n"
            f"**Rate:** **{rate_data['funding_rate']:+.4f}%**\n"
            f"**Mark Price:** ${rate_data['mark_price']:,.4f}\n"
            f"**Updated:** {rate_data['timestamp'].strftime('%H:%M:%S UTC')}\n\n"
            f"{'📈 Longs pay shorts' if rate_data['funding_rate'] > 0 else '📉 Shorts pay longs'}"
        )
    
    def _format_rates_summary(self, rates: List[Dict]) -> str:
        """Format funding rates summary"""
        if not rates:
            return "❌ No funding rates available"
        
        message = f"**📊 Current Funding Rates** ({len(rates)} shown)\n\n"
        
        for rate in rates:
            symbol = rate['symbol']
            funding_rate = rate['funding_rate']
            
            # Add emoji indicators for extreme rates
            if funding_rate >= self.config.UPPER_THRESHOLD:
                indicator = "🔴"
            elif funding_rate <= self.config.LOWER_THRESHOLD:
                indicator = "🟢"
            elif funding_rate >= 0.3:
                indicator = "🟠"
            elif funding_rate <= -0.3:
                indicator = "🟡"
            else:
                indicator = "⚪"
            
            message += f"{indicator} `{symbol}`: **{funding_rate:+.4f}%**\n"
        
        message += f"\n*Updated: {datetime.now().strftime('%H:%M:%S UTC')}*"
        return message
    
    async def run(self):
        """Start the bot"""
        logger.info("Starting Funding Rate Bot...")
        await self.application.run_polling()

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    try:
        bot = FundingRateBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)
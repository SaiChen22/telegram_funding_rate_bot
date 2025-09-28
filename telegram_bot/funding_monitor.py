import asyncio
import logging
from typing import Dict, List, Set, Callable, Optional
from datetime import datetime, timedelta
from binance_client import BinanceClient

logger = logging.getLogger(__name__)

class FundingRateMonitor:
    """Monitor funding rates and trigger alerts when thresholds are hit"""
    
    def __init__(self, 
                 alert_callback: Callable[[Dict], None],
                 upper_threshold: float = 0.6,
                 lower_threshold: float = -1.0,
                 check_interval: int = 300):  # 5 minutes default
        
        self.binance_client = BinanceClient()
        self.alert_callback = alert_callback
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.check_interval = check_interval
        
        # Track which symbols have already triggered alerts to avoid spam
        self.alerted_symbols: Set[str] = set()
        self.last_rates: Dict[str, float] = {}
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
    async def check_funding_rates(self):
        """Check all funding rates and trigger alerts for threshold breaches"""
        try:
            funding_rates = await self.binance_client.get_funding_rates()
            
            if not funding_rates:
                logger.warning("No funding rates retrieved")
                return
            
            alerts_triggered = 0
            
            for rate_data in funding_rates:
                symbol = rate_data['symbol']
                funding_rate = rate_data['funding_rate']
                
                # Store the current rate
                self.last_rates[symbol] = funding_rate
                
                # Check if thresholds are breached
                alert_triggered = False
                alert_type = None
                
                if funding_rate >= self.upper_threshold:
                    alert_type = "HIGH"
                    alert_triggered = True
                elif funding_rate <= self.lower_threshold:
                    alert_type = "LOW" 
                    alert_triggered = True
                
                # Only send alert if we haven't already alerted for this symbol
                # or if the rate has crossed back and is now on the other side
                if alert_triggered:
                    alert_key = f"{symbol}_{alert_type}"
                    if alert_key not in self.alerted_symbols:
                        self.alerted_symbols.add(alert_key)
                        
                        # Remove opposite alert if it exists
                        opposite_type = "LOW" if alert_type == "HIGH" else "HIGH"
                        opposite_key = f"{symbol}_{opposite_type}"
                        self.alerted_symbols.discard(opposite_key)
                        
                        alert_info = {
                            'symbol': symbol,
                            'funding_rate': funding_rate,
                            'threshold': self.upper_threshold if alert_type == "HIGH" else self.lower_threshold,
                            'alert_type': alert_type,
                            'mark_price': rate_data['mark_price'],
                            'next_funding_time': rate_data['next_funding_time'],
                            'timestamp': rate_data['timestamp']
                        }
                        
                        await self.alert_callback(alert_info)
                        alerts_triggered += 1
                        
                        logger.info(f"Alert triggered for {symbol}: {funding_rate:.4f}% ({alert_type})")
                
                # Clear alert if rate returns to normal range
                else:
                    # Remove any existing alerts for this symbol
                    keys_to_remove = [key for key in self.alerted_symbols if key.startswith(f"{symbol}_")]
                    for key in keys_to_remove:
                        self.alerted_symbols.remove(key)
            
            logger.info(f"Checked {len(funding_rates)} rates, triggered {alerts_triggered} alerts")
            
        except Exception as e:
            logger.error(f"Error checking funding rates: {e}")
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self.monitoring:
            logger.warning("Monitoring already started")
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started funding rate monitoring (interval: {self.check_interval}s)")
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        if not self.monitoring:
            logger.warning("Monitoring not started")
            return
        
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped funding rate monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                await self.check_funding_rates()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_current_rates(self) -> Dict[str, float]:
        """Get the last known rates for all symbols"""
        return self.last_rates.copy()
    
    def get_alerts_count(self) -> int:
        """Get the number of symbols currently being alerted"""
        return len(self.alerted_symbols)
    
    def reset_alerts(self):
        """Reset all alert tracking (useful for testing or manual reset)"""
        self.alerted_symbols.clear()
        logger.info("Reset all alert tracking")
    
    def update_thresholds(self, upper: float, lower: float):
        """Update alert thresholds"""
        self.upper_threshold = upper
        self.lower_threshold = lower
        self.reset_alerts()  # Reset alerts when thresholds change
        logger.info(f"Updated thresholds: upper={upper}%, lower={lower}%")

# Example usage and testing
async def example_alert_callback(alert_info: Dict):
    """Example callback function for alerts"""
    symbol = alert_info['symbol']
    rate = alert_info['funding_rate']
    alert_type = alert_info['alert_type']
    
    print(f"🚨 FUNDING RATE ALERT 🚨")
    print(f"Symbol: {symbol}")
    print(f"Rate: {rate:.4f}%")
    print(f"Type: {alert_type} ({'Above' if alert_type == 'HIGH' else 'Below'} threshold)")
    print(f"Mark Price: ${alert_info['mark_price']:.4f}")
    print(f"Time: {alert_info['timestamp']}")
    print("-" * 40)

if __name__ == "__main__":
    # Test the monitor
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_monitor():
        monitor = FundingRateMonitor(
            alert_callback=example_alert_callback,
            upper_threshold=0.01,  # Low threshold for testing
            lower_threshold=-0.01, # Low threshold for testing
            check_interval=10      # Check every 10 seconds
        )
        
        await monitor.start_monitoring()
        
        # Let it run for 1 minute
        await asyncio.sleep(60)
        
        await monitor.stop_monitoring()
        
        print(f"Final stats: {len(monitor.get_current_rates())} rates tracked")
    
    # asyncio.run(test_monitor())
import logging
from core.config import Config
from data.data_fetcher import DataFetcher
from strategies.ai_strategy import AITradingStrategy
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.config = Config()
        self.data_fetcher = DataFetcher(self.config)
        self.strategy = AITradingStrategy(self.config)
        self.running = False

    def initialize(self, symbol, source='yahoo'):
        """Initialize the trading bot with historical data"""
        logger.info(f"Initializing trading bot for {symbol} using {source}")
        historical_data = self.data_fetcher.get_historical_data(symbol, source=source)
        self.strategy.train(historical_data)
        return historical_data

    def execute_trade(self, symbol, action, size):
        """Execute trading action"""
        logger.info(f"Executing {action} order for {symbol}, size: {size}")
        # Implement actual trading logic here using exchange APIs
        pass

    def run(self, symbol, source='yahoo', interval=60):
        """Run the trading bot"""
        self.running = True
        historical_data = self.initialize(symbol, source)

        while self.running:
            try:
                # Get current price
                current_price = self.data_fetcher.get_realtime_price(symbol, source)

                # Update data and generate signals
                latest_data = historical_data.copy()
                latest_data.loc[time.time()] = [current_price] * len(latest_data.columns)
                signals = self.strategy.generate_signals(latest_data)

                # Get trading decision
                decision = self.strategy.should_trade(current_price, balance=10000)  # Example balance

                if decision['action'] != 'hold':
                    self.execute_trade(symbol, decision['action'], decision['size'])

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                time.sleep(interval)

    def stop(self):
        """Stop the trading bot"""
        self.running = False
        logger.info("Trading bot stopped")

if __name__ == "__main__":
    bot = TradingBot()
    try:
        bot.run("AAPL")  # Example: trading Apple stock
    except KeyboardInterrupt:
        bot.stop()

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

try:
    from core.config import Config
    from core.trader import SmartTrader
    from core.exchange_selector import ExchangeSelector
    from data.data_fetcher import DataFetcher
    from dashboard.trading_dashboard import TradingDashboard
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    raise

def main():
    try:
        logger.info("Initializing AI Smart Trading Bot Dashboard...")

        # Initialize components
        logger.debug("Creating configuration...")
        config = Config()

        logger.debug("Initializing data fetcher...")
        data_fetcher = DataFetcher(config)

        logger.debug("Initializing trader...")
        trader = SmartTrader(config)

        logger.debug("Initializing exchange selector...")
        exchange_selector = ExchangeSelector(config, data_fetcher)

        # Initialize dashboard with components
        logger.debug("Creating dashboard...")
        dashboard = TradingDashboard(
            trader=trader,
            data_fetcher=data_fetcher,
            exchange_selector=exchange_selector
        )

        # Expose port for user access
        logger.info("Starting dashboard server...")
        dashboard.run(debug=True, host='0.0.0.0', port=8050)

    except Exception as e:
        logger.error(f"Failed to start dashboard: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()

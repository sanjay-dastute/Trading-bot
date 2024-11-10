import logging
from dotenv import load_dotenv
from src.core.config import Config
from src.core.trader import SmartTrader
from src.dashboard.trading_dashboard import TradingDashboard
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the AI Smart Trading Bot"""
    try:
        logger.info("Starting AI Smart Trading Bot initialization...")

        # Load environment variables
        logger.info("Loading environment variables...")
        load_dotenv()

        # Initialize configuration
        logger.info("Initializing configuration...")
        try:
            config = Config()
            logger.info("Configuration initialized successfully")
        except Exception as config_error:
            logger.error(f"Failed to initialize configuration: {str(config_error)}")
            raise

        # Initialize dashboard
        logger.info("Initializing dashboard...")
        try:
            dashboard = TradingDashboard()
            logger.info("Dashboard initialized successfully")
        except Exception as dashboard_error:
            logger.error(f"Failed to initialize dashboard: {str(dashboard_error)}")
            raise

        # Start the dashboard server
        logger.info("Starting dashboard server on http://0.0.0.0:8050...")
        dashboard.run(debug=True, host='0.0.0.0', port=8050)

    except Exception as e:
        logger.error(f"Critical error in AI Smart Trading Bot: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

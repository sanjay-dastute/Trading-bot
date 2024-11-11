import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    SUPPORTED_EXCHANGES = [
        'binance', 'kucoin', 'bybit', 'gateio', 'mexc',
        'bitget', 'okx', 'woo', 'coinbase'
    ]

    def __init__(self):
        load_dotenv()
        self._validate_credentials()

    def _validate_credentials(self):
        """Validate and log available exchange credentials."""
        self.available_exchanges = []
        for exchange in self.SUPPORTED_EXCHANGES:
            if self._has_valid_credentials(exchange):
                self.available_exchanges.append(exchange)
                logger.info(f"Valid credentials found for {exchange.upper()}")
            else:
                logger.warning(f"No valid credentials found for {exchange.upper()}")

    def _has_valid_credentials(self, exchange):
        """Check if valid credentials exist for an exchange."""
        credentials = self.get_exchange_credentials(exchange)
        return credentials.get('api_key') and credentials.get('secret_key')

    def get_exchange_credentials(self, exchange):
        """Get credentials for a specific exchange."""
        exchange = exchange.lower()
        if exchange not in self.SUPPORTED_EXCHANGES:
            logger.error(f"Unsupported exchange: {exchange}")
            return {'api_key': None, 'secret_key': None}

        return {
            'api_key': os.getenv(f'{exchange.upper()}_API_KEY'),
            'secret_key': os.getenv(f'{exchange.upper()}_SECRET_KEY')
        }

    @property
    def trading_params(self):
        """Get trading parameters with safe defaults."""
        return {
            'risk_level': os.getenv('RISK_LEVEL', 'low'),  # Changed default to low for safety
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', 100)),  # Reduced default
            'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', 1)),  # Reduced default
            'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', 3)),  # Adjusted for risk
            'max_trades_per_day': int(os.getenv('MAX_TRADES_PER_DAY', 5)),  # Added daily trade limit
            'min_volume_threshold': float(os.getenv('MIN_VOLUME_THRESHOLD', 1000000))  # Added volume threshold
        }

    def get_available_exchanges(self):
        """Get list of exchanges with valid credentials."""
        return self.available_exchanges

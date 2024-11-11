import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    SUPPORTED_EXCHANGES = [
        'binance', 'kucoin', 'bybit', 'gateio', 'mexc',
        'bitget', 'okx', 'woo', 'coinbase'
    ]

    def __init__(self):
        load_dotenv()
        self.trading_config = self._load_trading_config()
        self._validate_credentials()

    def _load_trading_config(self) -> Dict[str, Any]:
        """Load trading configuration with safe defaults."""
        return {
            'risk_level': os.getenv('RISK_LEVEL', 'low'),
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '100')),
            'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', '1')),
            'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', '3')),
            'max_trades_per_day': int(os.getenv('MAX_TRADES_PER_DAY', '5')),
            'min_volume_threshold': float(os.getenv('MIN_VOLUME_THRESHOLD', '1000000')),
            'leverage': int(os.getenv('DEFAULT_LEVERAGE', '1')),
            'min_profit_threshold': float(os.getenv('MIN_PROFIT_THRESHOLD', '0.5')),
            'max_loss_threshold': float(os.getenv('MAX_LOSS_THRESHOLD', '0.2')),
            'volatility_threshold': float(os.getenv('VOLATILITY_THRESHOLD', '2.0')),
            'trading_enabled': os.getenv('TRADING_ENABLED', 'true').lower() == 'true'
        }

    def _validate_credentials(self):
        """Validate and log available exchange credentials."""
        self.available_exchanges = []
        for exchange in self.SUPPORTED_EXCHANGES:
            if self._has_valid_credentials(exchange):
                self.available_exchanges.append(exchange)
                logger.info(f"Valid credentials found for {exchange.upper()}")
            else:
                logger.warning(f"No valid credentials found for {exchange.upper()}")

    def _has_valid_credentials(self, exchange: str) -> bool:
        """Check if valid credentials exist for an exchange."""
        credentials = self.get_exchange_credentials(exchange)
        return bool(credentials and credentials.get('api_key') and credentials.get('secret'))

    def get_exchange_credentials(self, exchange: str) -> Optional[Dict[str, str]]:
        """Get credentials for a specific exchange."""
        exchange = exchange.lower()
        if exchange not in self.SUPPORTED_EXCHANGES:
            logger.error(f"Unsupported exchange: {exchange}")
            return None

        api_key = os.getenv(f'{exchange.upper()}_API_KEY')
        secret = os.getenv(f'{exchange.upper()}_SECRET_KEY')

        if api_key and secret:
            return {
                'api_key': api_key,
                'secret': secret,
                'name': exchange
            }
        return None

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.trading_config.get(key, default)

    @property
    def trading_params(self) -> Dict[str, Any]:
        """Get trading parameters."""
        return self.trading_config

    def get_available_exchanges(self) -> list:
        """Get list of exchanges with valid credentials."""
        return self.available_exchanges

    def is_exchange_enabled(self, exchange: str) -> bool:
        """Check if exchange is enabled."""
        return exchange.lower() in self.available_exchanges

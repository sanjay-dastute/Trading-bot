"""
Base Exchange Class for Cryptocurrency Trading
Supports multiple exchanges with comprehensive trading features
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
import ccxt.async_support as ccxt
from datetime import datetime
from src.core.key_manager import KeyManager

class BaseExchange(ABC):
    """Base class for all cryptocurrency exchange implementations"""

    def __init__(self, exchange_id: str, config: Dict[str, Any]):
        """
        Initialize exchange with configuration and secure key management

        Args:
            exchange_id: Exchange identifier (e.g., 'binance', 'kucoin')
            config: Configuration dictionary including optional encryption password
        """
        self.exchange_id = exchange_id
        self.name = exchange_id  # Add name attribute
        self.config = config
        self.exchange: Optional[ccxt.Exchange] = None
        self.logger = logging.getLogger(__name__)
        self.key_manager = KeyManager()

    async def initialize(self) -> bool:
        """Initialize exchange connection with secure key management"""
        try:
            # Try to get keys from secure storage first
            api_credentials = self._get_api_credentials()

            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class({
                'apiKey': api_credentials.get('api_key'),
                'secret': api_credentials.get('secret'),
                'password': api_credentials.get('passphrase', ''),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                # Add proxy support for location-restricted APIs
                'proxies': {
                    'http': self.config.get('http_proxy', ''),
                    'https': self.config.get('https_proxy', '')
                } if self.config.get('use_proxy') else None
            })
            await self.exchange.load_markets()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.exchange_id}: {str(e)}")
            return False

    def _get_api_credentials(self) -> Dict[str, str]:
        """Get API credentials from secure storage or config"""
        try:
            # Try to get keys from secure storage first
            if 'encryption_password' in self.config:
                keys = self.key_manager.get_exchange_keys(
                    self.exchange_id,
                    self.config['encryption_password']
                )
                if keys:
                    return {
                        'api_key': keys.get('api_key'),
                        'secret': keys.get('secret'),  # Changed to match config naming
                        'passphrase': keys.get('passphrase')
                    }

            # Fall back to config-based keys
            return {
                'api_key': self.config.get('api_key'),
                'secret': self.config.get('secret'),  # Changed to match config naming
                'passphrase': self.config.get('passphrase')
            }
        except Exception as e:
            self.logger.error(f"Failed to get API credentials: {str(e)}")
            return {}

    def is_configured(self) -> bool:
        """Check if exchange is properly configured with API keys"""
        credentials = self._get_api_credentials()
        return bool(credentials.get('api_key') and credentials.get('secret_key'))

    async def validate_credentials(self) -> bool:
        """Validate API credentials"""
        try:
            if not self.is_configured():
                return False
            # Try to fetch balance as a validation test
            await self.get_balance()
            return True
        except Exception as e:
            self.logger.error(f"Failed to validate credentials: {str(e)}")
            return False

    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()

    @abstractmethod
    async def get_balance(self, currency: str = None) -> Dict:
        """Get account balance for specific currency or all currencies"""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker information"""
        pass

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book for a trading pair"""
        try:
            return await self.exchange.fetch_order_book(symbol, limit)
        except Exception as e:
            self.logger.error(f"Failed to fetch order book: {str(e)}")
            return {}

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List:
        """Get recent trades for analysis"""
        try:
            return await self.exchange.fetch_trades(symbol, limit=limit)
        except Exception as e:
            self.logger.error(f"Failed to fetch recent trades: {str(e)}")
            return []

    @abstractmethod
    async def create_order(self, symbol: str, order_type: str, side: str,
                          amount: float, price: Optional[float] = None) -> Dict:
        """
        Create a new order

        Args:
            symbol: Trading pair symbol
            order_type: Type of order (market/limit)
            side: Buy or sell
            amount: Amount to trade
            price: Price for limit orders
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an existing order"""
        pass

    async def get_ohlcv(self, symbol: str, timeframe: str = '1m',
                        limit: int = 100) -> List:
        """Get OHLCV candlestick data"""
        try:
            return await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV data: {str(e)}")
            return []

    async def get_market_info(self, symbol: str) -> dict:
        """Get market information for a symbol"""
        try:
            # Try to get market info even if exchange is not initialized
            if not hasattr(self, 'exchange') or self.exchange is None:
                await self.initialize()

            if not self.exchange:
                self.logger.error("Exchange not initialized")
                return {
                    'symbol': symbol,
                    'base': symbol.split('/')[0],
                    'quote': symbol.split('/')[1],
                    'active': False,
                    'info': {'error': 'Exchange not initialized'}
                }

            try:
                # Try to get market info from exchange
                market = self.exchange.market(symbol)
                if market:
                    return {
                        'symbol': market.get('symbol', symbol),
                        'base': market.get('base', symbol.split('/')[0]),
                        'quote': market.get('quote', symbol.split('/')[1]),
                        'active': market.get('active', True),
                        'precision': market.get('precision', {'price': 8, 'amount': 8}),
                        'limits': market.get('limits', {'amount': {'min': 0.0001}}),
                        'info': market.get('info', {})
                    }
            except Exception as e:
                self.logger.warning(f"Failed to get market info from exchange: {str(e)}")
                # Return basic market info if exchange call fails
                return {
                    'symbol': symbol,
                    'base': symbol.split('/')[0],
                    'quote': symbol.split('/')[1],
                    'active': True,
                    'precision': {'price': 8, 'amount': 8},
                    'limits': {'amount': {'min': 0.0001}},
                    'info': {'error': str(e)}
                }

        except Exception as e:
            self.logger.error(f"Failed to get market info: {str(e)}")
            return {
                'symbol': symbol,
                'base': symbol.split('/')[0],
                'quote': symbol.split('/')[1],
                'active': False,
                'info': {'error': str(e)}
            }

    async def calculate_risk_metrics(self, symbol: str) -> Dict:
        """Calculate risk metrics for zero-loss trading"""
        try:
            ohlcv = await self.get_ohlcv(symbol, timeframe='1h', limit=24)
            if not ohlcv:
                return {}

            # Calculate basic volatility and trend metrics
            closes = [candle[4] for candle in ohlcv]
            highs = [candle[2] for candle in ohlcv]
            lows = [candle[3] for candle in ohlcv]

            volatility = (max(highs) - min(lows)) / min(lows) * 100
            trend = (closes[-1] - closes[0]) / closes[0] * 100

            return {
                'volatility': volatility,
                'trend': trend,
                'risk_score': self._calculate_risk_score(volatility, trend),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {str(e)}")
            return {}

    def _calculate_risk_score(self, volatility: float, trend: float) -> float:
        """Calculate risk score based on volatility and trend"""
        # Lower score means lower risk
        risk_score = (abs(volatility) * 0.7 + abs(trend) * 0.3) / 100
        return min(max(risk_score, 0), 1)  # Normalize between 0 and 1

    def get_exchange_info(self) -> Dict:
        """Get exchange configuration and capability information"""
        return {
            'exchange_id': self.exchange_id,
            'configured': self.is_configured(),
            'features': {
                'spot_trading': True,
                'margin_trading': False,
                'futures_trading': False,
                'lending': False,
                'staking': False
            },
            'requirements': self.key_manager.get_exchange_requirements(self.exchange_id)
        }

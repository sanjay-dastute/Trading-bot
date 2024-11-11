import yfinance as yf
import ccxt
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DataFetcher:
    """Fetches historical and real-time data from various sources"""

    EXCHANGE_CLASSES = {
        'binance': ccxt.binance,
        'kucoin': ccxt.kucoin,
        'bybit': ccxt.bybit,
        'gateio': ccxt.gateio,
        'mexc': ccxt.mexc,
        'bitget': ccxt.bitget,
        'okx': ccxt.okx,
        'woo': ccxt.woo,
        'coinbase': ccxt.coinbase
    }

    def __init__(self, config):
        self.config = config
        self.exchanges = {}
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Initialize exchange connections based on available credentials."""
        for exchange_id in self.EXCHANGE_CLASSES:
            try:
                credentials = self.config.get_exchange_credentials(exchange_id)
                if credentials['api_key'] and credentials['secret_key']:
                    exchange_class = self.EXCHANGE_CLASSES[exchange_id]
                    self.exchanges[exchange_id] = exchange_class({
                        'apiKey': credentials['api_key'],
                        'secret': credentials['secret_key']
                    })
                    logger.info(f"Successfully initialized {exchange_id.upper()} exchange")
            except Exception as e:
                logger.warning(f"Failed to initialize {exchange_id.upper()} exchange: {str(e)}")

    def get_historical_data(self, symbol, timeframe='1d', limit=1000, source='binance'):
        """
        Fetch historical data from various sources

        Args:
            symbol (str): Trading pair or stock symbol
            timeframe (str): Time interval (1m, 5m, 1h, 1d, etc.)
            limit (int): Number of candles to fetch
            source (str): Exchange ID ('binance', 'kucoin', etc.)
        """
        try:
            if source in self.exchanges:
                exchange = self.exchanges[source]
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                return df
            else:
                available_exchanges = list(self.exchanges.keys())
                if available_exchanges:
                    logger.warning(f"Source {source} not available. Using {available_exchanges[0]} instead.")
                    return self.get_historical_data(symbol, timeframe, limit, available_exchanges[0])
                else:
                    raise ValueError("No exchanges available. Please configure API keys.")

        except Exception as e:
            logger.error(f"Error fetching historical data from {source}: {str(e)}")
            raise

    def get_realtime_price(self, symbol, source='binance'):
        """Get real-time price data"""
        try:
            if source in self.exchanges:
                exchange = self.exchanges[source]
                ticker = exchange.fetch_ticker(symbol)
                return ticker['last']
            else:
                available_exchanges = list(self.exchanges.keys())
                if available_exchanges:
                    logger.warning(f"Source {source} not available. Using {available_exchanges[0]} instead.")
                    return self.get_realtime_price(symbol, available_exchanges[0])
                else:
                    raise ValueError("No exchanges available. Please configure API keys.")

        except Exception as e:
            logger.error(f"Error fetching real-time price from {source}: {str(e)}")
            raise

    def get_available_exchanges(self):
        """Get list of initialized exchanges."""
        return list(self.exchanges.keys())

    async def get_market_data(self, exchange_id: str, symbol: str) -> Optional[Dict]:
        """Get market data including volume, bid/ask prices"""
        try:
            if exchange_id not in self.exchanges:
                return None

            exchange = self.exchanges[exchange_id]
            ticker = exchange.fetch_ticker(symbol)

            return {
                'volume_24h': ticker.get('quoteVolume', 0),
                'bid': ticker.get('bid', 0),
                'ask': ticker.get('ask', 0),
                'last': ticker.get('last', 0)
            }

        except Exception as e:
            logger.error(f"Error fetching market data from {exchange_id}: {str(e)}")
            return None

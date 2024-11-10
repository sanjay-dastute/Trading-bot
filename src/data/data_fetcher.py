import yfinance as yf
import ccxt
import pandas as pd
from datetime import datetime, timedelta

class DataFetcher:
    """Fetches historical and real-time data from various sources"""

    def __init__(self, config):
        self.config = config
        self.exchanges = {
            'binance': ccxt.binance({
                'apiKey': config.binance_credentials['api_key'],
                'secret': config.binance_credentials['secret_key']
            }),
            'coinbase': ccxt.coinbasepro({
                'apiKey': config.coinbase_credentials['api_key'],
                'secret': config.coinbase_credentials['secret_key']
            })
        }

    def get_historical_data(self, symbol, timeframe='1d', limit=1000, source='yahoo'):
        """
        Fetch historical data from various sources

        Args:
            symbol (str): Trading pair or stock symbol
            timeframe (str): Time interval (1m, 5m, 1h, 1d, etc.)
            limit (int): Number of candles to fetch
            source (str): Data source ('yahoo', 'binance', 'coinbase')
        """
        if source == 'yahoo':
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f'{limit}d', interval=timeframe)
            return df

        elif source in self.exchanges:
            exchange = self.exchanges[source]
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df

        else:
            raise ValueError(f"Unsupported data source: {source}")

    def get_realtime_price(self, symbol, source='yahoo'):
        """Get real-time price data"""
        if source == 'yahoo':
            ticker = yf.Ticker(symbol)
            return ticker.info['regularMarketPrice']

        elif source in self.exchanges:
            exchange = self.exchanges[source]
            ticker = exchange.fetch_ticker(symbol)
            return ticker['last']

        else:
            raise ValueError(f"Unsupported data source: {source}")

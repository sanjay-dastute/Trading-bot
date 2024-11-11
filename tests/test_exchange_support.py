"""
Comprehensive test suite for verifying exchange support and functionality
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.api.exchanges import (
    BinanceExchange,
    KucoinExchange,
    GateioExchange,
    BybitExchange,
    MexcExchange,
    BitgetExchange,
    OkxExchange,
    WooExchange,
    CoinbaseExchange
)
from src.core.key_manager import KeyManager
from src.core.config import Config
from src.core.exchange_selector import ExchangeSelector
from src.api.base_exchange import BaseExchange

@pytest.fixture
def mock_market_data():
    return {
        'symbol': 'BTC/USDT',
        'base': 'BTC',
        'quote': 'USDT',
        'active': True,
        'precision': {'price': 2, 'amount': 8},
        'limits': {'amount': {'min': 0.0001}},
        'info': {}
    }

@pytest.fixture
def config():
    """Mock configuration with test API keys"""
    mock_config = Mock()
    mock_config.get_exchange_credentials = lambda x: {
        'api_key': 'test_key',
        'secret': 'test_secret'
    } if x.lower() in [
        'binance', 'kucoin', 'gateio', 'bybit', 'mexc',
        'bitget', 'okx', 'woo', 'coinbase'
    ] else None
    mock_config.get = lambda x, default=None: default
    return mock_config

@pytest.fixture
def key_manager():
    """Mock key manager"""
    return Mock(
        get_credentials=lambda x: {
            'api_key': 'test_key',
            'secret': 'test_secret'
        }
    )

@pytest.fixture
def data_fetcher():
    """Mock data fetcher"""
    return Mock()

@pytest.mark.asyncio
async def test_exchange_initialization():
    """Test initialization of all supported exchanges"""
    config = Config()
    exchanges = [
        BinanceExchange(config),
        KucoinExchange(config),
        GateioExchange(config),
        BybitExchange(config),
        MexcExchange(config),
        BitgetExchange(config),
        OkxExchange(config),
        WooExchange(config),
        CoinbaseExchange(config)
    ]

    for exchange in exchanges:
        assert exchange is not None
        assert hasattr(exchange, 'name')
        assert hasattr(exchange, 'initialize')
        assert hasattr(exchange, 'get_market_info')
        assert hasattr(exchange, 'calculate_risk_metrics')

@pytest.mark.asyncio
async def test_optional_api_keys(mock_market_data, config):
    """Test that exchanges work with optional API keys"""
    with patch('ccxt.async_support.Exchange.fetch_markets') as mock_markets, \
         patch('ccxt.async_support.Exchange.market') as mock_market, \
         patch('ccxt.async_support.Exchange.load_markets') as mock_load_markets:
        # Mock the markets response
        mock_markets.return_value = {'BTC/USDT': mock_market_data}
        mock_market.return_value = mock_market_data
        mock_load_markets.return_value = {'BTC/USDT': mock_market_data}

        # Test with no API keys
        selector = ExchangeSelector(config, Mock())
        # Exchanges should work without API keys for public endpoints
        assert len(selector.exchanges) > 0

        # Test market info retrieval without API keys
        for exchange in selector.exchanges.values():
            # Initialize exchange
            await exchange.initialize()

            # Get market info
            market_info = await exchange.get_market_info('BTC/USDT')
            assert market_info is not None
            assert 'symbol' in market_info
            assert market_info['symbol'] == 'BTC/USDT'
            assert 'base' in market_info
            assert market_info['base'] == 'BTC'
            assert 'quote' in market_info
            assert market_info['quote'] == 'USDT'

            # Should not be able to trade without API keys
            assert not exchange.is_configured()

            # Clean up
            await exchange.close()

@pytest.mark.asyncio
async def test_exchange_selection():
    """Test AI-driven exchange selection"""
    config = Mock()
    data_fetcher = Mock()
    selector = ExchangeSelector(config, data_fetcher)

    # Mock market data
    mock_market_data = {
        'ticker': {
            'ask': 100.1,
            'bid': 100.0,
            'quoteVolume': 150000
        },
        'orderbook': {
            'bids': [(100.0, 1000)],
            'asks': [(100.1, 1000)]
        }
    }

    # Mock risk metrics
    mock_risk_metrics = {
        'volatility': 1.5,
        'trend': 2,
        'risk_score': 0.2
    }

    with patch.object(selector, 'analyze_exchanges') as mock_analyze:
        mock_analyze.return_value = [{
            'exchange_id': 'binance',
            'score': 0.85,
            'risk_metrics': mock_risk_metrics,
            'market_info': mock_market_data,
            'profit_potential': 0.6
        }]

        exchange_id, details = await selector.select_best_exchange('BTC/USDT')
        assert exchange_id == 'binance'
        assert details['profit_potential'] >= 0.5
        assert details['risk_level'] == 'low'

@pytest.mark.asyncio
async def test_zero_loss_trading():
    """Test zero-loss trading validation"""
    config = Mock()
    selector = ExchangeSelector(config, Mock())

    # Test high-risk conditions (should reject)
    high_risk = {
        'volatility': 3.0,
        'risk_score': 0.8
    }
    high_risk_market = {
        'ticker': {
            'ask': 101,
            'bid': 99,
            'quoteVolume': 50000
        }
    }
    assert not selector._validate_trading_conditions(high_risk, high_risk_market)

    # Test safe conditions (should accept)
    safe_risk = {
        'volatility': 1.5,
        'risk_score': 0.2
    }
    safe_market = {
        'ticker': {
            'ask': 100.1,
            'bid': 100.0,
            'quoteVolume': 150000
        }
    }
    assert selector._validate_trading_conditions(safe_risk, safe_market)

@pytest.mark.asyncio
async def test_profit_calculation():
    """Test profit calculation and validation"""
    config = Mock()
    selector = ExchangeSelector(config, Mock())

    market_info = {
        'ticker': {
            'ask': 100.1,
            'bid': 100.0,
            'quoteVolume': 150000
        },
        'orderbook': {
            'bids': [(100.0, 1000), (99.9, 2000)],
            'asks': [(100.1, 1500), (100.2, 2500)]
        }
    }

    profit = selector._calculate_profit_potential(market_info)
    assert profit > 0
    assert profit <= selector.max_spread

@pytest.mark.asyncio
async def test_exchange_api_integration(mock_market_data, config):
    """Test actual exchange API integration with mocked responses"""
    exchanges = {
        'binance': BinanceExchange,
        'kucoin': KucoinExchange,
        'gateio': GateioExchange,
        'bybit': BybitExchange,
        'mexc': MexcExchange,
        'bitget': BitgetExchange,
        'okx': OkxExchange,
        'woo': WooExchange,
        'coinbase': CoinbaseExchange
    }

    mock_risk_metrics = {
        'volatility': 0.015,  # 1.5% volatility
        'risk_score': 0.75,   # Good risk score
        'market_depth': 1000000,
        'spread': 0.001,      # 0.1% spread
        'volume_24h': 100000000,
        'price_change_24h': 0.02,
        'recommendation': 'TRADE',
        'min_trade_amount': 0.001,
        'max_trade_amount': 10.0
    }

    with patch('ccxt.async_support.Exchange.fetch_markets') as mock_markets, \
         patch('ccxt.async_support.Exchange.market') as mock_market, \
         patch('ccxt.async_support.Exchange.load_markets') as mock_load_markets, \
         patch('ccxt.async_support.Exchange.fetch_ohlcv') as mock_ohlcv, \
         patch.object(BaseExchange, 'calculate_risk_metrics', return_value=mock_risk_metrics):

        mock_markets.return_value = {'BTC/USDT': mock_market_data}
        mock_market.return_value = mock_market_data
        mock_load_markets.return_value = {'BTC/USDT': mock_market_data}
        mock_ohlcv.return_value = [
            [1000, 50000, 50100, 49900, 50050, 1000],  # timestamp, open, high, low, close, volume
            [2000, 50050, 50200, 49950, 50150, 1100],
            [3000, 50150, 50300, 50000, 50250, 1200],
        ]

        for name, exchange_class in exchanges.items():
            exchange = exchange_class(config)

            try:
                await exchange.initialize()

                market_info = await exchange.get_market_info('BTC/USDT')
                assert market_info is not None
                assert 'symbol' in market_info
                assert market_info['symbol'] == 'BTC/USDT'
                assert 'base' in market_info
                assert market_info['base'] == 'BTC'
                assert 'quote' in market_info
                assert market_info['quote'] == 'USDT'

                assert not exchange.is_configured()

                risk_metrics = await exchange.calculate_risk_metrics('BTC/USDT')
                assert risk_metrics is not None
                assert 'volatility' in risk_metrics
                assert 'risk_score' in risk_metrics
                assert risk_metrics.get('risk_score', float('inf')) <= 1.0
                assert risk_metrics.get('recommendation') in ['TRADE', 'WAIT', 'AVOID']

            except Exception as e:
                pytest.fail(f"Exchange {name} failed: {str(e)}")

            finally:
                await exchange.close()

if __name__ == '__main__':
    pytest.main([__file__])

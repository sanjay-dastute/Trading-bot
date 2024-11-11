"""
Test suite for ExchangeSelector
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.core.exchange_selector import ExchangeSelector

@pytest.fixture
def config():
    """Mock configuration"""
    return Mock(
        get_exchange_credentials=lambda x: {'api_key': 'test', 'secret': 'test'} if x in [
            'binance', 'kucoin', 'bybit'
        ] else None
    )

@pytest.fixture
def data_fetcher():
    """Mock data fetcher"""
    return Mock()

@pytest.fixture
def exchange_selector(config, data_fetcher):
    """Create ExchangeSelector instance"""
    return ExchangeSelector(config, data_fetcher)

@pytest.mark.asyncio
async def test_zero_loss_validation(exchange_selector):
    """Test zero-loss trading validation"""
    # Test case with high risk conditions
    high_risk_metrics = {
        'volatility': 3.0,  # Above max threshold
        'risk_score': 0.8,  # Above max threshold
    }
    high_risk_market = {
        'ticker': {
            'ask': 100.5,
            'bid': 99.0,  # High spread
            'quoteVolume': 50000  # Low liquidity
        }
    }
    assert not exchange_selector._validate_trading_conditions(high_risk_metrics, high_risk_market)

    # Test case with acceptable conditions
    safe_metrics = {
        'volatility': 1.5,
        'risk_score': 0.3,
    }
    safe_market = {
        'ticker': {
            'ask': 100.1,
            'bid': 100.0,
            'quoteVolume': 150000
        }
    }
    assert exchange_selector._validate_trading_conditions(safe_metrics, safe_market)

@pytest.mark.asyncio
async def test_profit_calculation(exchange_selector):
    """Test profit potential calculation"""
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

    profit = exchange_selector._calculate_profit_potential(market_info)
    assert profit > 0
    assert profit <= exchange_selector.max_spread

@pytest.mark.asyncio
async def test_exchange_selection(exchange_selector):
    """Test exchange selection with mock data"""
    symbol = 'BTC/USDT'

    # Mock exchange analysis data
    mock_metrics = [{
        'exchange_id': 'binance',
        'score': 0.85,
        'risk_metrics': {'risk_score': 0.2, 'volatility': 1.5},
        'market_info': {
            'ticker': {
                'ask': 100.1,
                'bid': 100.0,
                'quoteVolume': 150000
            }
        },
        'profit_potential': 0.6
    }]

    with patch.object(exchange_selector, 'analyze_exchanges', return_value=mock_metrics):
        exchange_id, details = await exchange_selector.select_best_exchange(symbol)

        assert exchange_id == 'binance'
        assert details['confidence'] >= 85
        assert details['profit_potential'] >= 0.5
        assert details['risk_level'] == 'low'

@pytest.mark.asyncio
async def test_risk_management(exchange_selector):
    """Test risk management features"""
    # Test high-risk scenario
    high_risk = {
        'volatility': 100,
        'trend': -5,
        'risk_score': 0.9
    }
    market_info = {
        'ticker': {
            'ask': 101,
            'bid': 99,
            'quoteVolume': 50000
        }
    }

    score = exchange_selector._calculate_exchange_score(high_risk, market_info)
    assert score < 0.3  # Should have low score due to high risk

    # Test low-risk scenario
    low_risk = {
        'volatility': 1.5,
        'trend': 2,
        'risk_score': 0.2
    }
    safe_market = {
        'ticker': {
            'ask': 100.1,
            'bid': 100.0,
            'quoteVolume': 150000
        }
    }

    score = exchange_selector._calculate_exchange_score(low_risk, safe_market)
    assert score > 0.7  # Should have high score due to low risk

if __name__ == '__main__':
    pytest.main([__file__])

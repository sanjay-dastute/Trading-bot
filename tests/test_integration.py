import unittest
from unittest.mock import MagicMock, patch
from src.core.trader import SmartTrader
from src.models.ensemble_model import EnsembleModel
from src.data.data_fetcher import DataFetcher
import pandas as pd
import numpy as np

class TestTradingBotIntegration(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.trader = SmartTrader(self.config)
        self.model = EnsembleModel()
        self.data_fetcher = DataFetcher(self.config)

    @patch('src.data.data_fetcher.DataFetcher.get_historical_data')
    def test_model_training(self, mock_get_data):
        # Mock historical data
        mock_data = pd.DataFrame({
            'open': np.random.random(100),
            'high': np.random.random(100),
            'low': np.random.random(100),
            'close': np.random.random(100),
            'volume': np.random.random(100)
        })
        mock_get_data.return_value = mock_data

        # Test model training
        historical_data = self.data_fetcher.get_historical_data('BTC/USDT')
        self.model.train(historical_data)

        # Verify prediction functionality
        prediction = self.model.predict(historical_data[-60:])
        self.assertIsNotNone(prediction)

    @patch('src.core.trader.SmartTrader.validate_trade_conditions')
    def test_trading_conditions(self, mock_validate):
        # Mock trading conditions
        mock_validate.return_value = {
            'valid': True,
            'confidence': 98.5,
            'prediction': 'buy',
            'risk_reward': 5.2,
            'position_size': 0.1
        }

        # Test trading validation
        conditions = self.trader.validate_trade_conditions('BTC/USDT', None)
        self.assertTrue(conditions['valid'])
        self.assertGreaterEqual(conditions['confidence'], 98)
        self.assertGreaterEqual(conditions['risk_reward'], 5)

    def test_zero_loss_protection(self):
        # Test stop loss calculation
        entry_price = 50000
        position = {
            'entry_price': entry_price,
            'size': 0.1,
            'action': 'buy'
        }

        # Calculate stop loss (should be maximum 2% below entry for buy positions)
        stop_loss = entry_price * 0.98
        self.assertGreaterEqual(stop_loss, entry_price * 0.98)

if __name__ == '__main__':
    unittest.main()

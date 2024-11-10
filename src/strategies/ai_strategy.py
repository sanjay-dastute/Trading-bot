import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from .base_strategy import BaseStrategy

class AITradingStrategy(BaseStrategy):
    """AI-powered trading strategy using LSTM neural network"""

    def __init__(self, config):
        super().__init__(config)
        self.model = self._build_model()
        self.scaler = MinMaxScaler()


    def _build_model(self):
        """Build and compile LSTM model"""
        model = Sequential([
            LSTM(units=50, return_sequences=True, input_shape=(60, 5)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50),
            Dropout(0.2),
            Dense(units=1)
        ])
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def prepare_data(self, data):
        """Prepare data for LSTM model"""
        features = ['open', 'high', 'low', 'close', 'volume']
        scaled_data = self.scaler.fit_transform(data[features])

        X, y = [], []
        for i in range(60, len(scaled_data)):
            X.append(scaled_data[i-60:i])
            y.append(scaled_data[i, 3])  # Predicting close price
        return np.array(X), np.array(y)

    def train(self, data):
        """Train the AI model"""
        X, y = self.prepare_data(data)
        self.model.fit(X, y, epochs=50, batch_size=32, validation_split=0.1)

    def generate_signals(self, data):
        """Generate trading signals using AI predictions"""
        X, _ = self.prepare_data(data)
        if len(X) == 0:
            return data

        predictions = self.model.predict(X)
        predictions = self.scaler.inverse_transform(
            np.concatenate([np.zeros((len(predictions), 4)), predictions.reshape(-1, 1)], axis=1)
        )[:, -1]

        signals = pd.Series(index=data.index, data=0)
        signals.iloc[60:] = np.where(predictions > data['close'].iloc[60:], 1, -1)

        data['signal'] = signals
        return data

    def calculate_position_size(self, price, balance):
        """Calculate position size based on risk management"""
        risk_per_trade = balance * (float(self.config['risk_level_percent']) / 100)
        position_size = min(
            risk_per_trade / price,
            float(self.config['max_position_size'])
        )
        return position_size

    def should_trade(self, current_price, balance):
        """Determine if a trade should be executed"""
        if self.last_signal is None:
            return {'action': 'hold', 'size': 0}

        position_size = self.calculate_position_size(current_price, balance)

        if self.last_signal > 0 and self.position is None:
            return {'action': 'buy', 'size': position_size}
        elif self.last_signal < 0 and self.position is not None:
            return {'action': 'sell', 'size': self.position}

        return {'action': 'hold', 'size': 0}

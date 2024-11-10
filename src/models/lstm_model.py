import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

class LSTMModel:
    def __init__(self, sequence_length=60, n_features=5):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = self._build_model()

    def _build_model(self):
        model = Sequential([
            LSTM(units=100, return_sequences=True, input_shape=(self.sequence_length, self.n_features)),
            Dropout(0.2),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=25),
            Dropout(0.2),
            Dense(units=1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
        return model

    def train(self, X_train, y_train, epochs=50, batch_size=32, validation_split=0.1):
        return self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )

    def predict(self, X):
        return self.model.predict(X)

    def get_confidence(self, X, y_true, window=20):
        """Calculate prediction confidence based on recent accuracy"""
        predictions = self.predict(X[-window:])
        accuracy = np.mean(np.abs(predictions - y_true[-window:]) / y_true[-window:])
        confidence = max(0, 1 - accuracy)
        return confidence * 100  # Return as percentage

import numpy as np
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from .lstm_model import LSTMModel

class EnsembleModel:
    """Ensemble model combining LSTM, XGBoost, and Random Forest for consensus-based predictions"""

    def __init__(self, sequence_length=60, n_features=5):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_model = LSTMModel(sequence_length, n_features)
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.xgb_model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.1,
            random_state=42
        )

    def prepare_data_for_traditional_models(self, X):
        """Flatten 3D data for RF and XGB models"""
        return X.reshape(X.shape[0], -1)

    def train(self, X_train, y_train, validation_split=0.1):
        """Train all models in the ensemble"""
        # Train LSTM
        self.lstm_model.train(X_train, y_train, validation_split=validation_split)

        # Prepare data for traditional models
        X_flat = self.prepare_data_for_traditional_models(X_train)

        # Train Random Forest
        self.rf_model.fit(X_flat, y_train)

        # Train XGBoost
        self.xgb_model.fit(X_flat, y_train)

    def predict(self, X):
        """Get predictions from all models"""
        lstm_pred = self.lstm_model.predict(X)
        X_flat = self.prepare_data_for_traditional_models(X)
        rf_pred = self.rf_model.predict(X_flat).reshape(-1, 1)
        xgb_pred = self.xgb_model.predict(X_flat).reshape(-1, 1)

        return lstm_pred, rf_pred, xgb_pred

    def get_consensus_prediction(self, X, threshold=0.02):
        """Get consensus prediction if models agree within threshold"""
        lstm_pred, rf_pred, xgb_pred = self.predict(X)

        # Calculate mean and standard deviation of predictions
        predictions = np.hstack([lstm_pred, rf_pred, xgb_pred])
        mean_pred = np.mean(predictions, axis=1)
        std_pred = np.std(predictions, axis=1)

        # Check if models agree (low standard deviation)
        consensus_reached = std_pred / mean_pred < threshold

        return {
            'prediction': mean_pred,
            'consensus': consensus_reached,
            'confidence': 1 - (std_pred / mean_pred) * 100,  # Convert to percentage
            'individual_predictions': {
                'lstm': lstm_pred,
                'rf': rf_pred,
                'xgb': xgb_pred
            }
        }

    def validate_prediction(self, X, confidence_threshold=98):
        """Validate prediction meets confidence threshold"""
        consensus_data = self.get_consensus_prediction(X)

        return {
            'valid': consensus_data['confidence'] >= confidence_threshold,
            'confidence': consensus_data['confidence'],
            'prediction': consensus_data['prediction'],
            'consensus': consensus_data['consensus']
        }

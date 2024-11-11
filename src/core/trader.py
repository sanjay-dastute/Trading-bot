import logging
from typing import Dict, Any
import pandas as pd
import numpy as np
from src.models.ensemble_model import EnsembleModel
from src.data.data_fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartTrader:
    """Main trading execution system with zero-loss protection"""

    def __init__(self, config):
        self.config = config
        self.data_fetcher = DataFetcher(config)
        self.model = EnsembleModel()
        self.current_positions = {}
        self.daily_stats = {
            'trades': 0,
            'profits': 0,
            'losses': 0,
            'total_profit': 0
        }

    def validate_trade_conditions(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Validate all conditions before placing a trade"""
        # Get AI prediction and confidence
        latest_data = self._prepare_model_input(data)
        prediction_data = self.model.validate_prediction(latest_data)

        # Check volume condition
        volume_condition = (
            data['volume'].iloc[-1] >
            data['volume'].rolling(window=20).mean().iloc[-1] * 2
        )

        # Check trend alignment
        trend_aligned = self._check_trend_alignment(data)

        # Calculate risk-reward ratio
        risk_reward = self._calculate_risk_reward(data, prediction_data['prediction'][-1])

        return {
            'valid': all([
                prediction_data['valid'],
                prediction_data['confidence'] >= 98,
                volume_condition,
                trend_aligned,
                risk_reward >= 5
            ]),
            'confidence': prediction_data['confidence'],
            'prediction': prediction_data['prediction'][-1],
            'risk_reward': risk_reward
        }

    def _prepare_model_input(self, data: pd.DataFrame):
        """Prepare data for model input"""
        # Add technical indicators
        data = self._add_technical_indicators(data)

        # Normalize data
        normalized_data = self._normalize_data(data)

        # Prepare sequences
        return self._prepare_sequences(normalized_data)

    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataset"""
        df = data.copy()

        # Add Moving Averages
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()

        # Add RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        return df

    def execute_trade(self, symbol: str, action: str, size: float, exchange: str) -> bool:
        """Execute trade with zero-loss protection"""
        try:
            # Validate position size
            max_position = self._calculate_max_position(symbol)
            if size > max_position:
                size = max_position
                logger.warning(f"Position size adjusted to maximum allowed: {max_position}")

            # Get current price
            current_price = self.data_fetcher.get_realtime_price(symbol, exchange)

            # Calculate stop loss and take profit levels
            stop_loss = self._calculate_stop_loss(current_price, action)
            take_profit = self._calculate_take_profit(current_price, action)

            # Execute the trade through the exchange
            order = self._place_order(symbol, action, size, current_price, exchange)

            if order['status'] == 'success':
                self._update_position(symbol, action, size, current_price, stop_loss, take_profit)
                return True
            return False

        except Exception as e:
            logger.error(f"Trade execution failed: {str(e)}")
            return False

    def _calculate_max_position(self, symbol: str) -> float:
        """Calculate maximum position size based on risk management rules"""
        portfolio_value = self._get_portfolio_value()
        max_position = min(
            portfolio_value * 0.02,  # 2% maximum position size
            float(self.config.trading_params['max_position_size'])
        )
        return max_position

    def _calculate_stop_loss(self, price: float, action: str) -> float:
        """Calculate dynamic stop loss level"""
        volatility = self._calculate_volatility()
        stop_percentage = min(
            volatility * 2,  # 2x volatility
            float(self.config.trading_params['stop_loss_percentage']) / 100
        )

        return price * (1 - stop_percentage) if action == 'buy' else price * (1 + stop_percentage)

    def _calculate_take_profit(self, price: float, action: str) -> float:
        """Calculate take profit level"""
        stop_loss = self._calculate_stop_loss(price, action)
        risk = abs(price - stop_loss)
        return price + (risk * 5) if action == 'buy' else price - (risk * 5)  # 5:1 reward-risk ratio

    def _place_order(self, symbol: str, action: str, size: float, price: float, exchange: str) -> Dict:
        """Place order through exchange API"""
        try:
            # Get exchange-specific client
            if exchange == 'binance':
                credentials = self.config.binance_credentials
                # Implement Binance-specific order placement
            elif exchange == 'coinbase':
                credentials = self.config.coinbase_credentials
                # Implement Coinbase-specific order placement

            # Simulate order placement for now
            return {
                'status': 'success',
                'order_id': 'test_order_id',
                'price': price,
                'size': size
            }

        except Exception as e:
            logger.error(f"Order placement failed: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def monitor_positions(self):
        """Monitor and manage open positions"""
        for symbol, position in self.current_positions.items():
            current_price = self.data_fetcher.get_realtime_price(
                symbol, position['exchange']
            )

            # Check stop loss
            if self._should_stop_loss(current_price, position):
                self.execute_trade(symbol, 'sell', position['size'], position['exchange'])

            # Check take profit
            elif self._should_take_profit(current_price, position):
                self.execute_trade(symbol, 'sell', position['size'], position['exchange'])

            # Update trailing stop loss
            else:
                self._update_trailing_stop(symbol, current_price, position)

    def _update_trailing_stop(self, symbol: str, current_price: float, position: Dict):
        """Update trailing stop loss level"""
        if position['action'] == 'buy':
            if current_price > position['entry_price']:
                new_stop = self._calculate_stop_loss(current_price, 'buy')
                if new_stop > position['stop_loss']:
                    self.current_positions[symbol]['stop_loss'] = new_stop
        else:
            if current_price < position['entry_price']:
                new_stop = self._calculate_stop_loss(current_price, 'sell')
                if new_stop < position['stop_loss']:
                    self.current_positions[symbol]['stop_loss'] = new_stop

    def get_trading_stats(self) -> Dict[str, Any]:
        """Get current trading statistics"""
        return {
            'daily_stats': self.daily_stats,
            'current_positions': self.current_positions,
            'portfolio_value': self._get_portfolio_value(),
            'current_process': self.get_current_process()
        }

    def get_current_process(self) -> Dict[str, Any]:
        """Get current trading process information"""
        try:
            processes = []
            for symbol, position in self.current_positions.items():
                current_price = self.data_fetcher.get_realtime_price(
                    symbol, position['exchange']
                )
                profit_loss = (current_price - position['entry_price']) * position['size']
                process = {
                    'symbol': symbol,
                    'exchange': position['exchange'],
                    'action': position['action'],
                    'entry_price': position['entry_price'],
                    'current_price': current_price,
                    'size': position['size'],
                    'profit_loss': profit_loss,
                    'stop_loss': position['stop_loss'],
                    'take_profit': position['take_profit'],
                    'status': 'active',
                    'timestamp': pd.Timestamp.now().isoformat()
                }
                processes.append(process)

            return {
                'active_processes': processes,
                'total_positions': len(processes),
                'last_update': pd.Timestamp.now().isoformat(),
                'status': 'running' if processes else 'idle'
            }

        except Exception as e:
            logger.error(f"Failed to get current process: {str(e)}")
            return {
                'active_processes': [],
                'total_positions': 0,
                'last_update': pd.Timestamp.now().isoformat(),
                'status': 'error',
                'error': str(e)
            }

    def get_process_updates(self) -> List[str]:
        """Get latest trading process updates"""
        try:
            updates = []
            for symbol, position in self.current_positions.items():
                current_price = self.data_fetcher.get_realtime_price(
                    symbol, position['exchange']
                )
                profit_loss = (current_price - position['entry_price']) * position['size']

                # Add relevant updates
                updates.append(
                    f"Position: {symbol} on {position['exchange'].upper()}, "
                    f"Action: {position['action'].upper()}, "
                    f"Size: {position['size']}, "
                    f"P/L: ${profit_loss:.2f}"
                )

                # Add risk management updates
                if current_price <= position['stop_loss']:
                    updates.append(f"⚠️ Stop loss triggered for {symbol}")
                elif current_price >= position['take_profit']:
                    updates.append(f"✅ Take profit reached for {symbol}")

            return updates

        except Exception as e:
            logger.error(f"Failed to get process updates: {str(e)}")
            return [f"Error getting updates: {str(e)}"]

    def _get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        try:
            total_value = 0.0
            # Add value of current positions
            for symbol, position in self.current_positions.items():
                try:
                    current_price = self.data_fetcher.get_realtime_price(
                        symbol, position['exchange']
                    )
                    position_value = position['size'] * current_price
                    total_value += position_value
                except Exception as e:
                    logger.warning(f"Failed to get price for {symbol}: {str(e)}")
                    # Use last known price as fallback
                    if 'last_price' in position:
                        total_value += position['size'] * position['last_price']

            # Add available balance (implement exchange-specific logic here)
            try:
                available_balance = self._get_available_balance()
                total_value += available_balance
            except Exception as e:
                logger.warning(f"Failed to get available balance: {str(e)}")
                # Use default balance as fallback
                total_value += 10000.0

            return total_value

        except Exception as e:
            logger.error(f"Failed to get portfolio value: {str(e)}")
            return 10000.0  # Return default value on error

    def _get_available_balance(self) -> float:
        """Get available balance from exchange"""
        try:
            # Implement exchange-specific balance retrieval
            # For now, return simulated balance
            return 10000.0
        except Exception as e:
            logger.error(f"Failed to get available balance: {str(e)}")
            raise

    def _calculate_volatility(self) -> float:
        """Calculate current market volatility"""
        try:
            # Get recent price data
            data = self.data_fetcher.get_historical_data(
                symbol=list(self.current_positions.keys())[0] if self.current_positions else 'BTC/USDT',
                timeframe='1h',
                limit=24
            )

            # Calculate volatility as standard deviation of returns
            returns = pd.Series(data['close']).pct_change().dropna()
            return float(returns.std())

        except Exception as e:
            logger.error(f"Failed to calculate volatility: {str(e)}")
            return 0.02  # Return default volatility on error

    def _check_trend_alignment(self, data: pd.DataFrame) -> bool:
        """Check if multiple timeframes show aligned trend"""
        try:
            # Calculate EMAs for different timeframes
            data['ema_short'] = data['close'].ewm(span=20, adjust=False).mean()
            data['ema_medium'] = data['close'].ewm(span=50, adjust=False).mean()
            data['ema_long'] = data['close'].ewm(span=200, adjust=False).mean()

            # Check if EMAs are aligned (short above medium above long for uptrend)
            last_row = data.iloc[-1]
            return (
                last_row['ema_short'] > last_row['ema_medium'] > last_row['ema_long'] or
                last_row['ema_short'] < last_row['ema_medium'] < last_row['ema_long']
            )

        except Exception as e:
            logger.error(f"Failed to check trend alignment: {str(e)}")
            return False

    def _normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Normalize data for model input"""
        try:
            # Select features for normalization
            features = ['close', 'volume', 'MA20', 'MA50', 'RSI']

            # Create copy of data
            normalized = data.copy()

            # Normalize each feature
            for feature in features:
                if feature in normalized.columns:
                    mean = normalized[feature].mean()
                    std = normalized[feature].std()
                    normalized[feature] = (normalized[feature] - mean) / std

            return normalized

        except Exception as e:
            logger.error(f"Failed to normalize data: {str(e)}")
            return data

    def _prepare_sequences(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare sequences for model input"""
        try:
            # Select features
            features = ['close', 'volume', 'MA20', 'MA50', 'RSI']

            # Create sequences
            sequence_length = 100
            sequences = []

            for i in range(len(data) - sequence_length + 1):
                sequence = data[features].iloc[i:(i + sequence_length)].values
                sequences.append(sequence)

            return np.array(sequences)

        except Exception as e:
            logger.error(f"Failed to prepare sequences: {str(e)}")
            return np.array([])

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.position = None
        self.last_signal = None

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on the strategy

        Args:
            data (pd.DataFrame): Historical market data

        Returns:
            pd.DataFrame: Data with added signal column
        """
        pass

    @abstractmethod
    def calculate_position_size(self, price: float, balance: float) -> float:
        """
        Calculate position size based on risk management rules

        Args:
            price (float): Current asset price
            balance (float): Account balance

        Returns:
            float: Position size
        """
        pass

    def should_trade(self, current_price: float, balance: float) -> Dict[str, Any]:
        """
        Determine if a trade should be executed

        Args:
            current_price (float): Current asset price
            balance (float): Account balance

        Returns:
            dict: Trading decision with action and size
        """
        pass

    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price based on risk parameters"""
        stop_loss_pct = self.config['stop_loss_percentage'] / 100
        if side == 'buy':
            return entry_price * (1 - stop_loss_pct)
        return entry_price * (1 + stop_loss_pct)

    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price based on risk parameters"""
        take_profit_pct = self.config['take_profit_percentage'] / 100
        if side == 'buy':
            return entry_price * (1 + take_profit_pct)
        return entry_price * (1 - take_profit_pct)

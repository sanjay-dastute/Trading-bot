from abc import ABC, abstractmethod

class BaseExchange(ABC):
    """Base class for all exchange implementations"""

    @abstractmethod
    def connect(self):
        """Establish connection to the exchange"""
        pass

    @abstractmethod
    def get_balance(self):
        """Get account balance"""
        pass

    @abstractmethod
    def place_order(self, symbol, side, quantity, price=None):
        """Place a new order"""
        pass

    @abstractmethod
    def get_market_data(self, symbol):
        """Get market data for a symbol"""
        pass

    @abstractmethod
    def cancel_order(self, order_id):
        """Cancel an existing order"""
        pass

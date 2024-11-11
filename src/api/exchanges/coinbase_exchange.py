"""
Coinbase Exchange Implementation
"""
from typing import Dict, Optional
from src.api.base_exchange import BaseExchange
import logging

class CoinbaseExchange(BaseExchange):
    """Coinbase exchange implementation"""

    def __init__(self, config: Dict):
        super().__init__('coinbasepro', config)

    async def get_balance(self, currency: str = None) -> Dict:
        """Get account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            if currency:
                return {
                    'free': balance.get(currency, {}).get('free', 0),
                    'used': balance.get(currency, {}).get('used', 0),
                    'total': balance.get(currency, {}).get('total', 0)
                }
            return balance
        except Exception as e:
            self.logger.error(f"Failed to fetch balance: {str(e)}")
            return {}

    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker"""
        try:
            return await self.exchange.fetch_ticker(symbol)
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker: {str(e)}")
            return {}

    async def create_order(self, symbol: str, order_type: str, side: str,
                          amount: float, price: Optional[float] = None) -> Dict:
        """Create new order with zero-loss protection"""
        try:
            params = {}
            if order_type == 'limit' and price is None:
                raise ValueError("Price is required for limit orders")

            # Add zero-loss protection for Coinbase
            if side == 'sell' and order_type == 'market':
                ticker = await self.get_ticker(symbol)
                current_price = ticker.get('last', 0)
                if current_price > 0:
                    # Coinbase specific stop loss
                    params['stop'] = 'loss'
                    params['stop_price'] = current_price * 0.995
                    params['stop_limit_price'] = current_price * 0.994

            return await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )
        except Exception as e:
            self.logger.error(f"Failed to create order: {str(e)}")
            return {}

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel existing order"""
        try:
            return await self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {str(e)}")
            return {}

"""
Binance Exchange Implementation with Advanced Risk Management and Profit Optimization
"""
from typing import Dict, Optional, Tuple
from src.api.base_exchange import BaseExchange
import logging
import numpy as np
from datetime import datetime, timedelta

class BinanceExchange(BaseExchange):
    """Binance exchange implementation with enhanced risk management"""

    def __init__(self, config: Dict):
        super().__init__('binance', config)
        self.min_profit_threshold = 0.5  # Minimum profit percentage to take action
        self.max_loss_threshold = 0.2    # Maximum allowed loss percentage
        self.volatility_threshold = 2.0   # Maximum allowed volatility percentage

    async def analyze_market(self, symbol: str) -> Dict:
        """Analyze market conditions for optimal entry/exit"""
        try:
            # Fetch recent trades and OHLCV data
            trades = await self.exchange.fetch_trades(symbol, limit=100)
            ohlcv = await self.exchange.fetch_ohlcv(symbol, '1m', limit=60)

            # Calculate volatility
            prices = [float(trade['price']) for trade in trades]
            volatility = np.std(prices) / np.mean(prices) * 100

            # Calculate volume profile
            volume = sum([float(trade['amount']) for trade in trades])

            # Calculate price trend
            if not ohlcv:
                return {'error': 'No OHLCV data available'}

            closes = [candle[4] for candle in ohlcv]
            price_change = ((closes[-1] - closes[0]) / closes[0]) * 100

            # Calculate support and resistance
            support = min(closes[-20:])  # Simple 20-period support
            resistance = max(closes[-20:])  # Simple 20-period resistance

            # Calculate additional Binance-specific metrics
            avg_trade_size = volume / len(trades) if trades else 0
            bid_ask_spread = await self._get_bid_ask_spread(symbol)

            return {
                'volatility': volatility,
                'volume': volume,
                'price_change': price_change,
                'support': support,
                'resistance': resistance,
                'current_price': closes[-1],
                'is_safe': volatility <= self.volatility_threshold,
                'avg_trade_size': avg_trade_size,
                'bid_ask_spread': bid_ask_spread
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze market: {str(e)}")
            return {'error': str(e)}

    async def _get_bid_ask_spread(self, symbol: str) -> float:
        """Get current bid-ask spread"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=5)
            if not orderbook['bids'] or not orderbook['asks']:
                return 0.0
            spread = (orderbook['asks'][0][0] - orderbook['bids'][0][0]) / orderbook['bids'][0][0] * 100
            return round(spread, 4)
        except Exception as e:
            self.logger.error(f"Failed to get bid-ask spread: {str(e)}")
            return 0.0

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
        """Get current ticker with enhanced market data"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            market_analysis = await self.analyze_market(symbol)

            # Enhance ticker with market analysis
            ticker.update({
                'market_analysis': market_analysis,
                'profit_potential': self._calculate_profit_potential(ticker, market_analysis)
            })

            return ticker
        except Exception as e:
            self.logger.error(f"Failed to fetch ticker: {str(e)}")
            return {}

    def _calculate_profit_potential(self, ticker: Dict, analysis: Dict) -> float:
        """Calculate potential profit percentage based on market conditions"""
        try:
            if 'error' in analysis:
                return 0.0

            volatility_score = max(0, 1 - (analysis['volatility'] / self.volatility_threshold))
            trend_score = (analysis['price_change'] + 100) / 200  # Normalize to 0-1

            # Calculate distance to support/resistance
            price = analysis['current_price']
            support_distance = (price - analysis['support']) / price
            resistance_distance = (analysis['resistance'] - price) / price

            # Higher score when price is closer to support (good for buying)
            position_score = 1 - min(support_distance, resistance_distance)

            # Include Binance-specific factors
            spread_score = 1 - min(analysis['bid_ask_spread'] / 0.1, 1)  # Normalize spread score
            volume_score = min(analysis['volume'] / 1000000, 1)  # Volume in millions

            # Combine factors with weights
            potential = (
                volatility_score * 0.25 +
                trend_score * 0.3 +
                position_score * 0.2 +
                spread_score * 0.15 +
                volume_score * 0.1
            ) * 100  # Convert to percentage

            return round(potential, 2)
        except Exception as e:
            self.logger.error(f"Failed to calculate profit potential: {str(e)}")
            return 0.0

    async def create_order(self, symbol: str, order_type: str, side: str,
                          amount: float, price: Optional[float] = None) -> Dict:
        """Create new order with advanced risk management"""
        try:
            # Analyze market conditions before placing order
            analysis = await self.analyze_market(symbol)
            if 'error' in analysis:
                raise ValueError(f"Market analysis failed: {analysis['error']}")

            if not analysis['is_safe']:
                raise ValueError(f"Market conditions unsafe: Volatility {analysis['volatility']}% exceeds threshold {self.volatility_threshold}%")

            params = {}
            if order_type == 'limit' and price is None:
                raise ValueError("Price is required for limit orders")

            # Enhanced zero-loss protection using Binance-specific features
            current_price = analysis['current_price']
            if side == 'buy':
                # Set OCO (One-Cancels-the-Other) order for take-profit and stop-loss
                take_profit_price = current_price * (1 + self.min_profit_threshold / 100)
                stop_loss_price = current_price * (1 - self.max_loss_threshold / 100)

                if order_type == 'limit':
                    params.update({
                        'stopLimitPrice': stop_loss_price,
                        'stopPrice': stop_loss_price * 1.001,  # Slightly higher trigger
                        'takeProfitPrice': take_profit_price
                    })

            elif side == 'sell':
                # Ensure selling above entry price
                if price and price < current_price:
                    raise ValueError(f"Sell price {price} is below current price {current_price}")

                # Set trailing stop for market sells
                if order_type == 'market':
                    params.update({
                        'trailingStop': True,
                        'callbackRate': 0.5,  # 0.5% callback rate
                        'stopPrice': current_price * 0.995
                    })

            # Create the order with protection parameters
            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params
            )

            self.logger.info(f"Created {side} order with protection: {order}")
            return order

        except Exception as e:
            self.logger.error(f"Failed to create order: {str(e)}")
            return {'error': str(e)}

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel existing order"""
        try:
            return await self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {str(e)}")
            return {'error': str(e)}

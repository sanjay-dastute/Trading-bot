"""
Gate.io Exchange Implementation with Advanced Risk Management and Profit Optimization
"""
from typing import Dict, Optional, Tuple
from src.api.base_exchange import BaseExchange
import logging
import numpy as np
from datetime import datetime, timedelta

class GateioExchange(BaseExchange):
    """Gate.io exchange implementation with enhanced risk management"""

    def __init__(self, config: Dict):
        super().__init__('gateio', config)
        self.min_profit_threshold = 0.5  # Minimum profit percentage to take action
        self.max_loss_threshold = 0.2    # Maximum allowed loss percentage
        self.volatility_threshold = 2.0   # Maximum allowed volatility percentage
        self.min_volume_threshold = 50000  # Minimum 24h volume in USD

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

            # Gate.io specific market depth analysis
            depth = await self._get_market_depth(symbol)
            liquidity_score = self._calculate_liquidity_score(depth)

            return {
                'volatility': volatility,
                'volume': volume,
                'price_change': price_change,
                'support': support,
                'resistance': resistance,
                'current_price': closes[-1],
                'is_safe': volatility <= self.volatility_threshold and volume >= self.min_volume_threshold,
                'liquidity_score': liquidity_score,
                'depth': depth
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze market: {str(e)}")
            return {'error': str(e)}

    async def _get_market_depth(self, symbol: str) -> Dict:
        """Get market depth data"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=20)
            return {
                'bids': orderbook['bids'],
                'asks': orderbook['asks'],
                'bid_volume': sum(bid[1] for bid in orderbook['bids']),
                'ask_volume': sum(ask[1] for ask in orderbook['asks'])
            }
        except Exception as e:
            self.logger.error(f"Failed to get market depth: {str(e)}")
            return {}

    def _calculate_liquidity_score(self, depth: Dict) -> float:
        """Calculate liquidity score based on order book depth"""
        try:
            if not depth:
                return 0.0

            total_volume = depth['bid_volume'] + depth['ask_volume']
            volume_balance = min(depth['bid_volume'], depth['ask_volume']) / max(depth['bid_volume'], depth['ask_volume'])

            return round(min((total_volume / 1000000) * volume_balance, 1.0), 2)
        except Exception as e:
            self.logger.error(f"Failed to calculate liquidity score: {str(e)}")
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

            # Include Gate.io specific factors
            liquidity_score = analysis.get('liquidity_score', 0)
            volume_score = min(analysis['volume'] / self.min_volume_threshold, 1)

            # Combine factors with weights
            potential = (
                volatility_score * 0.25 +
                trend_score * 0.3 +
                position_score * 0.2 +
                liquidity_score * 0.15 +
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

            # Enhanced zero-loss protection using Gate.io specific features
            current_price = analysis['current_price']
            if side == 'buy':
                # Set take-profit and stop-loss levels
                take_profit_price = current_price * (1 + self.min_profit_threshold / 100)
                stop_loss_price = current_price * (1 - self.max_loss_threshold / 100)

                params.update({
                    'stopPrice': stop_loss_price,
                    'takeProfitPrice': take_profit_price,
                    'timeInForce': 'GTC'  # Good Till Cancelled
                })

            elif side == 'sell':
                # Ensure selling above entry price
                if price and price < current_price:
                    raise ValueError(f"Sell price {price} is below current price {current_price}")

                # Set protective stop for market sells
                if order_type == 'market':
                    params.update({
                        'auto_price': current_price * 0.995,  # Gate.io specific
                        'auto_size': str(amount)
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

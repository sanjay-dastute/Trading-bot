"""
Bitget Exchange Implementation with Advanced Risk Management and Profit Optimization
"""
from typing import Dict, Optional, Tuple
from src.api.base_exchange import BaseExchange
import logging
import numpy as np
from datetime import datetime, timedelta

class BitgetExchange(BaseExchange):
    """Bitget exchange implementation with enhanced risk management"""

    def __init__(self, config: Dict):
        super().__init__('bitget', config)
        self.min_profit_threshold = 0.5  # Minimum profit percentage to take action
        self.max_loss_threshold = 0.2    # Maximum allowed loss percentage
        self.volatility_threshold = 2.0   # Maximum allowed volatility percentage
        self.min_volume_threshold = 75000  # Minimum 24h volume in USD
        self.grid_trading = config.get('grid_trading', False)  # Grid trading flag
        self.grid_levels = config.get('grid_levels', 5)  # Number of grid levels

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

            # Bitget specific market analysis
            grid_levels = await self._calculate_grid_levels(symbol) if self.grid_trading else None
            market_depth = await self._analyze_market_depth(symbol)

            return {
                'volatility': volatility,
                'volume': volume,
                'price_change': price_change,
                'support': support,
                'resistance': resistance,
                'current_price': closes[-1],
                'is_safe': volatility <= self.volatility_threshold and volume >= self.min_volume_threshold,
                'grid_levels': grid_levels,
                'market_depth': market_depth
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze market: {str(e)}")
            return {'error': str(e)}

    async def _calculate_grid_levels(self, symbol: str) -> Dict:
        """Calculate grid trading levels"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']

            # Calculate grid range (±2% from current price)
            upper_price = current_price * 1.02
            lower_price = current_price * 0.98

            # Calculate price levels
            price_step = (upper_price - lower_price) / (self.grid_levels - 1)
            levels = [lower_price + i * price_step for i in range(self.grid_levels)]

            return {
                'levels': levels,
                'price_step': price_step,
                'upper_bound': upper_price,
                'lower_bound': lower_price
            }
        except Exception as e:
            self.logger.error(f"Failed to calculate grid levels: {str(e)}")
            return {}

    async def _analyze_market_depth(self, symbol: str) -> Dict:
        """Analyze market depth for liquidity assessment"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=20)
            bid_volume = sum(bid[1] for bid in orderbook['bids'])
            ask_volume = sum(ask[1] for ask in orderbook['asks'])
            spread = (orderbook['asks'][0][0] - orderbook['bids'][0][0]) / orderbook['bids'][0][0] * 100

            return {
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'spread': spread,
                'is_liquid': spread < 0.1 and min(bid_volume, ask_volume) > self.min_volume_threshold / 100
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze market depth: {str(e)}")
            return {'error': str(e)}

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
            return {'error': str(e)}

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
            return {'error': str(e)}

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

            # Include Bitget specific factors
            market_depth = analysis.get('market_depth', {})
            liquidity_score = 1 if market_depth.get('is_liquid', False) else 0
            grid_score = 1 if analysis.get('grid_levels') else 0

            # Combine factors with weights
            potential = (
                volatility_score * 0.2 +
                trend_score * 0.25 +
                position_score * 0.2 +
                liquidity_score * 0.25 +
                grid_score * 0.1
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

            # Enhanced zero-loss protection using Bitget specific features
            current_price = analysis['current_price']

            if side == 'buy':
                # Set take-profit and stop-loss levels
                take_profit_price = current_price * (1 + self.min_profit_threshold / 100)
                stop_loss_price = current_price * (1 - self.max_loss_threshold / 100)

                # Bitget specific order parameters
                params.update({
                    'stopLossPrice': stop_loss_price,
                    'takeProfitPrice': take_profit_price,
                    'timeInForceValue': 'GTC',
                    'postOnly': True  # Ensure we're always maker
                })

                # Add grid trading parameters if enabled
                if self.grid_trading and analysis.get('grid_levels'):
                    grid_params = self._prepare_grid_order(analysis['grid_levels'], side)
                    params.update(grid_params)

            elif side == 'sell':
                # Ensure selling above entry price
                if price and price < current_price:
                    raise ValueError(f"Sell price {price} is below current price {current_price}")

                # Set trailing stop for market sells
                if order_type == 'market':
                    params.update({
                        'stopLossPrice': current_price * 0.995,
                        'timeInForceValue': 'GTC',
                        'triggerPrice': current_price * 0.997  # Additional protection
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

    def _prepare_grid_order(self, grid_levels: Dict, side: str) -> Dict:
        """Prepare grid trading order parameters"""
        try:
            if not grid_levels or 'levels' not in grid_levels:
                return {}

            return {
                'gridLevels': len(grid_levels['levels']),
                'upperPrice': grid_levels['upper_bound'],
                'lowerPrice': grid_levels['lower_bound'],
                'gridType': 'arithmetic',  # Arithmetic grid spacing
                'side': side
            }
        except Exception as e:
            self.logger.error(f"Failed to prepare grid order: {str(e)}")
            return {}

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel existing order"""
        try:
            return await self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {str(e)}")
            return {'error': str(e)}

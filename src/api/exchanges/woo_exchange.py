"""
WOO Exchange Implementation with Advanced Risk Management and Profit Optimization
"""
from typing import Dict, Optional, Tuple
from src.api.base_exchange import BaseExchange
import logging
import numpy as np
from datetime import datetime, timedelta

class WooExchange(BaseExchange):
    """WOO exchange implementation with enhanced risk management"""

    def __init__(self, config: Dict):
        super().__init__('woo', config)
        self.min_profit_threshold = 0.5  # Minimum profit percentage to take action
        self.max_loss_threshold = 0.2    # Maximum allowed loss percentage
        self.volatility_threshold = 2.0   # Maximum allowed volatility percentage
        self.min_volume_threshold = 150000  # Minimum 24h volume in USD
        self.use_woo_x = config.get('use_woo_x', True)  # WOO X network integration
        self.deep_liquidity = config.get('deep_liquidity', True)  # Deep liquidity routing

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

            # WOO specific market analysis
            liquidity_score = await self._analyze_liquidity(symbol)
            network_stats = await self._get_network_stats(symbol) if self.use_woo_x else None
            orderbook_depth = await self._analyze_orderbook_depth(symbol)

            return {
                'volatility': volatility,
                'volume': volume,
                'price_change': price_change,
                'support': support,
                'resistance': resistance,
                'current_price': closes[-1],
                'is_safe': volatility <= self.volatility_threshold and volume >= self.min_volume_threshold,
                'liquidity_score': liquidity_score,
                'network_stats': network_stats,
                'orderbook_depth': orderbook_depth
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze market: {str(e)}")
            return {'error': str(e)}

    async def _analyze_liquidity(self, symbol: str) -> Dict:
        """Analyze WOO X liquidity metrics"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=50)
            bid_volume = sum(bid[1] for bid in orderbook['bids'])
            ask_volume = sum(ask[1] for ask in orderbook['asks'])
            spread = (orderbook['asks'][0][0] - orderbook['bids'][0][0]) / orderbook['bids'][0][0] * 100

            # WOO specific liquidity scoring
            depth_score = min(bid_volume, ask_volume) / self.min_volume_threshold
            spread_score = 1 - min(spread / 0.1, 1)  # Normalize spread score (0.1% reference)

            return {
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'spread': spread,
                'depth_score': depth_score,
                'spread_score': spread_score,
                'is_liquid': spread < 0.1 and depth_score > 1
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze liquidity: {str(e)}")
            return {'error': str(e)}

    async def _get_network_stats(self, symbol: str) -> Dict:
        """Get WOO X network statistics"""
        try:
            # WOO X specific network stats
            network_info = await self.exchange.fetch_status()
            return {
                'network_status': network_info.get('status', 'unknown'),
                'network_latency': network_info.get('latency', 0),
                'is_optimal': network_info.get('status') == 'ok' and network_info.get('latency', 1000) < 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get network stats: {str(e)}")
            return {'error': str(e)}

    async def _analyze_orderbook_depth(self, symbol: str) -> Dict:
        """Analyze orderbook depth for deep liquidity routing"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=100)

            # Calculate cumulative depths at different price levels
            bid_depths = []
            ask_depths = []

            for i in range(len(orderbook['bids'])):
                cumulative_volume = sum(bid[1] for bid in orderbook['bids'][:i+1])
                price_level = orderbook['bids'][i][0]
                bid_depths.append({'price': price_level, 'volume': cumulative_volume})

            for i in range(len(orderbook['asks'])):
                cumulative_volume = sum(ask[1] for ask in orderbook['asks'][:i+1])
                price_level = orderbook['asks'][i][0]
                ask_depths.append({'price': price_level, 'volume': cumulative_volume})

            return {
                'bid_depths': bid_depths,
                'ask_depths': ask_depths,
                'total_bid_depth': bid_depths[-1]['volume'] if bid_depths else 0,
                'total_ask_depth': ask_depths[-1]['volume'] if ask_depths else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze orderbook depth: {str(e)}")
            return {'error': str(e)}

    async def get_balance(self, currency: str = None) -> Dict:
        """Get account balance with WOO X support"""
        try:
            params = {'network': 'WOO_X'} if self.use_woo_x else {}
            balance = await self.exchange.fetch_balance(params=params)
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

            # Include WOO specific factors
            liquidity = analysis.get('liquidity_score', {})
            liquidity_score = (liquidity.get('depth_score', 0) + liquidity.get('spread_score', 0)) / 2
            network_score = 1 if analysis.get('network_stats', {}).get('is_optimal', False) else 0

            # Combine factors with weights
            potential = (
                volatility_score * 0.15 +
                trend_score * 0.20 +
                position_score * 0.15 +
                liquidity_score * 0.30 +  # Higher weight for WOO's deep liquidity
                network_score * 0.20
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

            # Enhanced zero-loss protection using WOO specific features
            current_price = analysis['current_price']

            if side == 'buy':
                # Set take-profit and stop-loss levels
                take_profit_price = current_price * (1 + self.min_profit_threshold / 100)
                stop_loss_price = current_price * (1 - self.max_loss_threshold / 100)

                # WOO specific order parameters
                params.update({
                    'stopLoss': {
                        'price': stop_loss_price,
                        'triggerPrice': stop_loss_price
                    },
                    'takeProfit': {
                        'price': take_profit_price,
                        'triggerPrice': take_profit_price
                    },
                    'postOnly': True  # Ensure we're always maker
                })

                if self.deep_liquidity:
                    params['routing'] = 'deep_liquidity'

            elif side == 'sell':
                # Ensure selling above entry price
                if price and price < current_price:
                    raise ValueError(f"Sell price {price} is below current price {current_price}")

                # Set trailing stop for market sells
                if order_type == 'market':
                    params.update({
                        'stopLoss': {
                            'price': current_price * 0.995,
                            'triggerPrice': current_price * 0.995
                        },
                        'trailingStop': {
                            'callbackRate': 0.2  # 0.2% callback rate
                        }
                    })

            # Add WOO X network parameters if enabled
            if self.use_woo_x:
                params['network'] = 'WOO_X'

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
            params = {'network': 'WOO_X'} if self.use_woo_x else {}
            return await self.exchange.cancel_order(order_id, symbol, params=params)
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {str(e)}")
            return {'error': str(e)}

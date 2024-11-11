"""
OKX Exchange Implementation with Advanced Risk Management and Profit Optimization
"""
from typing import Dict, Optional, Tuple
from src.api.base_exchange import BaseExchange
import logging
import numpy as np
from datetime import datetime, timedelta

class OkxExchange(BaseExchange):
    """OKX exchange implementation with enhanced risk management"""

    def __init__(self, config: Dict):
        super().__init__('okx', config)
        self.min_profit_threshold = 0.5  # Minimum profit percentage to take action
        self.max_loss_threshold = 0.2    # Maximum allowed loss percentage
        self.volatility_threshold = 2.0   # Maximum allowed volatility percentage
        self.min_volume_threshold = 100000  # Minimum 24h volume in USD
        self.portfolio_margin = config.get('portfolio_margin', False)  # Portfolio margin mode
        self.unified_account = config.get('unified_account', True)  # Unified account mode

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

            # OKX specific market analysis
            funding_rate = await self._get_funding_rate(symbol)
            margin_ratio = await self._get_margin_ratio(symbol) if self.portfolio_margin else None
            market_depth = await self._analyze_market_depth(symbol)

            return {
                'volatility': volatility,
                'volume': volume,
                'price_change': price_change,
                'support': support,
                'resistance': resistance,
                'current_price': closes[-1],
                'is_safe': volatility <= self.volatility_threshold and volume >= self.min_volume_threshold,
                'funding_rate': funding_rate,
                'margin_ratio': margin_ratio,
                'market_depth': market_depth
            }
        except Exception as e:
            self.logger.error(f"Failed to analyze market: {str(e)}")
            return {'error': str(e)}

    async def _get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate for perpetual contracts"""
        try:
            funding_rate = await self.exchange.fetch_funding_rate(symbol)
            return funding_rate.get('fundingRate', 0)
        except Exception as e:
            self.logger.error(f"Failed to get funding rate: {str(e)}")
            return 0.0

    async def _get_margin_ratio(self, symbol: str) -> float:
        """Get current margin ratio for portfolio margin mode"""
        try:
            if not self.portfolio_margin:
                return None

            # OKX specific margin ratio calculation
            positions = await self.exchange.fetch_positions([symbol])
            if not positions:
                return None

            total_collateral = sum(float(pos['collateral']) for pos in positions)
            total_margin = sum(float(pos['initialMargin']) for pos in positions)

            return total_collateral / total_margin if total_margin > 0 else None
        except Exception as e:
            self.logger.error(f"Failed to get margin ratio: {str(e)}")
            return None

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
        """Get account balance with unified account support"""
        try:
            params = {'unified': self.unified_account}  # OKX unified account parameter
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

            # Include OKX specific factors
            market_depth = analysis.get('market_depth', {})
            liquidity_score = 1 if market_depth.get('is_liquid', False) else 0
            funding_score = max(0, 1 - abs(analysis.get('funding_rate', 0)) * 100)  # Lower absolute funding rate is better
            margin_score = 1 if analysis.get('margin_ratio', 1) > 1.5 else 0  # Healthy margin ratio > 150%

            # Combine factors with weights
            potential = (
                volatility_score * 0.15 +
                trend_score * 0.20 +
                position_score * 0.15 +
                liquidity_score * 0.20 +
                funding_score * 0.15 +
                margin_score * 0.15
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

            # Enhanced zero-loss protection using OKX specific features
            current_price = analysis['current_price']

            if side == 'buy':
                # Set take-profit and stop-loss levels
                take_profit_price = current_price * (1 + self.min_profit_threshold / 100)
                stop_loss_price = current_price * (1 - self.max_loss_threshold / 100)

                # OKX specific order parameters
                params.update({
                    'stopLoss': stop_loss_price,
                    'takeProfit': take_profit_price,
                    'tpTriggerPxType': 'last',
                    'slTriggerPxType': 'last',
                    'reduceOnly': False,
                    'unified': self.unified_account
                })

                if self.portfolio_margin:
                    params['tdMode'] = 'cross'  # Use cross margin for portfolio margin mode

            elif side == 'sell':
                # Ensure selling above entry price
                if price and price < current_price:
                    raise ValueError(f"Sell price {price} is below current price {current_price}")

                # Set trailing stop for market sells
                if order_type == 'market':
                    params.update({
                        'stopLoss': current_price * 0.995,
                        'tpTriggerPxType': 'last',
                        'slTriggerPxType': 'last',
                        'triggerPrice': current_price * 0.997,  # Additional protection
                        'unified': self.unified_account
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
            params = {'unified': self.unified_account}  # Include unified account parameter
            return await self.exchange.cancel_order(order_id, symbol, params=params)
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {str(e)}")
            return {'error': str(e)}

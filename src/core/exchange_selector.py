"""
AI-driven Exchange Selector for optimal trading
"""
from typing import Dict, List, Optional, Tuple
import logging
from src.api.base_exchange import BaseExchange
from src.api.exchanges.binance_exchange import BinanceExchange
from src.api.exchanges.kucoin_exchange import KucoinExchange
from src.api.exchanges.bybit_exchange import BybitExchange
from src.api.exchanges.gateio_exchange import GateioExchange
from src.api.exchanges.mexc_exchange import MexcExchange
from src.api.exchanges.bitget_exchange import BitgetExchange
from src.api.exchanges.okx_exchange import OkxExchange
from src.api.exchanges.woo_exchange import WooExchange
from src.api.exchanges.coinbase_exchange import CoinbaseExchange

class ExchangeSelector:
    """AI-driven exchange selector for optimal trading conditions"""

    def __init__(self, config, data_fetcher):
        """Initialize ExchangeSelector with config and data fetcher"""
        self.config = config
        self.data_fetcher = data_fetcher
        self.logger = logging.getLogger(__name__)

        # Trading thresholds for zero-loss guarantee
        self.min_profit_threshold = 0.5  # Minimum 0.5% profit potential
        self.max_loss_threshold = 0.2    # Maximum 0.2% loss tolerance
        self.max_volatility = 2.0        # Maximum 2% volatility
        self.min_liquidity = 100000      # Minimum liquidity in quote currency
        self.max_spread = 0.1            # Maximum 0.1% spread

        # Initialize exchanges
        self.exchanges = self._initialize_exchanges()

        # Performance tracking
        self.exchange_performance = {}

    def _initialize_exchanges(self) -> Dict[str, BaseExchange]:
        """Initialize all supported exchanges"""
        exchanges = {}
        exchange_classes = {
            'binance': BinanceExchange,
            'kucoin': KucoinExchange,
            'bybit': BybitExchange,
            'gateio': GateioExchange,
            'mexc': MexcExchange,
            'bitget': BitgetExchange,
            'okx': OkxExchange,
            'woo': WooExchange,
            'coinbase': CoinbaseExchange
        }

        for exchange_id, exchange_class in exchange_classes.items():
            try:
                # Only initialize if API keys are configured
                if self.config.get_exchange_credentials(exchange_id):
                    exchanges[exchange_id] = exchange_class(self.config)
            except Exception as e:
                self.logger.warning(f"Failed to initialize {exchange_id}: {str(e)}")
                continue

        return exchanges

    async def analyze_exchanges(self, symbol: str) -> List[Dict]:
        """Analyze all available exchanges for the best trading conditions"""
        exchange_metrics = []

        for exchange_id, exchange in self.exchanges.items():
            try:
                # Skip exchanges without API keys
                if not exchange.config.get('api_key'):
                    continue

                # Get market metrics
                risk_metrics = await exchange.calculate_risk_metrics(symbol)
                market_info = await exchange.get_market_info(symbol)

                if not risk_metrics or not market_info:
                    continue

                # Validate zero-loss conditions
                if not self._validate_trading_conditions(risk_metrics, market_info):
                    self.logger.info(f"Skipping {exchange_id} due to high risk conditions")
                    continue

                # Calculate exchange score
                score = self._calculate_exchange_score(risk_metrics, market_info)
                profit_potential = self._calculate_profit_potential(market_info)

                # Only include exchanges with sufficient profit potential
                if profit_potential < self.min_profit_threshold:
                    continue

                exchange_metrics.append({
                    'exchange_id': exchange_id,
                    'score': score,
                    'risk_metrics': risk_metrics,
                    'market_info': market_info,
                    'profit_potential': profit_potential
                })

            except Exception as e:
                self.logger.error(f"Failed to analyze {exchange_id}: {str(e)}")
                continue

        return sorted(exchange_metrics, key=lambda x: x['score'], reverse=True)

    def _validate_trading_conditions(self, risk_metrics: Dict, market_info: Dict) -> bool:
        """Validate trading conditions for zero-loss guarantee"""
        try:
            # Check volatility
            if risk_metrics.get('volatility', 100) > self.max_volatility:
                return False

            # Check spread
            ticker = market_info.get('ticker', {})
            spread = (ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('bid', 1) * 100
            if spread > self.max_spread:
                return False

            # Check liquidity
            volume = ticker.get('quoteVolume', 0)
            if volume < self.min_liquidity:
                return False

            # Check risk score
            if risk_metrics.get('risk_score', 1) > 0.7:  # Maximum 70% risk score
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to validate trading conditions: {str(e)}")
            return False

    def _calculate_profit_potential(self, market_info: Dict) -> float:
        """Calculate potential profit percentage based on market conditions"""
        try:
            ticker = market_info.get('ticker', {})
            orderbook = market_info.get('orderbook', {})

            # Calculate based on order book depth and spread
            spread = (ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('bid', 1) * 100

            # Calculate order book depth
            bid_depth = sum(bid[1] for bid in orderbook.get('bids', [])[:5])
            ask_depth = sum(ask[1] for ask in orderbook.get('asks', [])[:5])

            # Base profit potential on spread and liquidity
            base_profit = spread * 0.8  # 80% of spread as base profit

            # Adjust based on liquidity
            liquidity_factor = min(1, (bid_depth + ask_depth) / (2 * self.min_liquidity))

            return base_profit * liquidity_factor

        except Exception as e:
            self.logger.error(f"Failed to calculate profit potential: {str(e)}")
            return 0

    async def select_best_exchange(self, symbol: str, available_exchanges: List[str] = None) -> Tuple[Optional[str], Dict]:
        """Select the best exchange for trading based on current conditions"""
        try:
            # Filter exchanges based on availability if specified
            exchanges_to_analyze = {
                exchange_id: exchange
                for exchange_id, exchange in self.exchanges.items()
                if not available_exchanges or exchange_id in available_exchanges
            }

            if not exchanges_to_analyze:
                return None, {
                    'error': 'No available exchanges to analyze',
                    'exchange_metrics': {}
                }

            exchange_metrics = await self.analyze_exchanges(symbol)

            if not exchange_metrics:
                return None, {
                    'error': 'No exchanges meet zero-loss criteria',
                    'exchange_metrics': {}
                }

            best_exchange = exchange_metrics[0]

            # Update performance tracking
            self._update_performance(best_exchange['exchange_id'], best_exchange['score'])

            return best_exchange['exchange_id'], {
                'confidence': min(best_exchange['score'] * 100, 100),
                'profit_potential': best_exchange['profit_potential'],
                'risk_level': 'low' if best_exchange['risk_metrics']['risk_score'] < 0.3 else 'medium',
                'exchange_metrics': {
                    e['exchange_id']: {
                        'score': e['score'],
                        'liquidity': e['market_info'].get('quoteVolume', 0),
                        'spread': e['market_info'].get('spread', 0),
                        'volume_24h': e['market_info'].get('volume24h', 0),
                        'risk_score': e['risk_metrics'].get('risk_score', 0),
                        'profit_potential': e['profit_potential']
                    } for e in exchange_metrics
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to select best exchange: {str(e)}")
            return None, {
                'error': str(e),
                'exchange_metrics': {}
            }

    def _calculate_exchange_score(self, risk_metrics: Dict, market_info: Dict) -> float:
        """Calculate exchange score based on various metrics with emphasis on zero-loss"""
        try:
            # Extract metrics
            volatility = risk_metrics.get('volatility', 100)
            trend = risk_metrics.get('trend', 0)
            risk_score = risk_metrics.get('risk_score', 1)

            ticker = market_info.get('ticker', {})
            spread = (ticker.get('ask', 0) - ticker.get('bid', 0)) / ticker.get('bid', 1) * 100
            volume = ticker.get('quoteVolume', 0)

            # Normalize metrics
            norm_spread = 1 - (min(spread, self.max_spread) / self.max_spread)
            norm_volume = min(volume / self.min_liquidity, 1)
            norm_risk = 1 - risk_score
            norm_trend = (trend + 100) / 200
            norm_volatility = 1 - (min(volatility, self.max_volatility) / self.max_volatility)

            # Calculate weighted score with emphasis on risk management
            weights = {
                'spread': 0.15,
                'volume': 0.15,
                'risk': 0.30,    # Increased weight for risk
                'trend': 0.25,
                'volatility': 0.15
            }

            score = (
                weights['spread'] * norm_spread +
                weights['volume'] * norm_volume +
                weights['risk'] * norm_risk +
                weights['trend'] * norm_trend +
                weights['volatility'] * norm_volatility
            )

            # Apply zero-loss adjustment
            if spread > self.max_spread or volume < self.min_liquidity:
                score *= 0.5

            return min(max(score, 0), 1)

        except Exception as e:
            self.logger.error(f"Failed to calculate exchange score: {str(e)}")
            return 0

    def _update_performance(self, exchange_id: str, score: float):
        """Update exchange performance tracking"""
        if exchange_id not in self.exchange_performance:
            self.exchange_performance[exchange_id] = []

        self.exchange_performance[exchange_id].append(score)

        # Keep only last 100 scores
        if len(self.exchange_performance[exchange_id]) > 100:
            self.exchange_performance[exchange_id] = self.exchange_performance[exchange_id][-100:]

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from core.trader import SmartTrader
from core.config import Config
from data.data_fetcher import DataFetcher
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class TradingDashboard:
    def __init__(self, trader=None, data_fetcher=None, exchange_selector=None):
        try:
            logger.info("Initializing TradingDashboard...")
            self.app = dash.Dash(__name__)

            # Use provided components or create new ones if not provided
            logger.debug("Setting up dashboard components...")
            self.config = Config()
            self.trader = trader if trader is not None else SmartTrader(self.config)
            self.data_fetcher = data_fetcher if data_fetcher is not None else DataFetcher(self.config)
            self.exchange_selector = exchange_selector

            # Track available exchanges
            self.available_exchanges = self.data_fetcher.get_available_exchanges()
            logger.info(f"Available exchanges: {self.available_exchanges}")

            # Add async callback support
            logger.debug("Enabling async callbacks...")
            self._enable_async_callbacks()

            logger.debug("Creating dashboard layout...")
            self.app.layout = self._create_layout()

            logger.debug("Setting up callbacks...")
            self._setup_callbacks()

            logger.info("TradingDashboard initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize TradingDashboard: {str(e)}", exc_info=True)
            raise

    def _enable_async_callbacks(self):
        def async_callback(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return asyncio.run(func(*args, **kwargs))
            return wrapper

        # Patch Dash's callback decorator to support async functions
        original_callback = self.app.callback
        def patched_callback(*args, **kwargs):
            def wrap_func(func):
                if asyncio.iscoroutinefunction(func):
                    return original_callback(*args, **kwargs)(async_callback(func))
                return original_callback(*args, **kwargs)(func)
            return wrap_func
        self.app.callback = patched_callback

    def _create_layout(self):
        # Get available exchanges for dropdown
        exchange_options = [
            {'label': exchange.upper(), 'value': exchange}
            for exchange in self.available_exchanges
        ]

        return html.Div([
            # Header
            html.H1("AI Smart Trading Bot Dashboard",
                   style={'textAlign': 'center', 'marginBottom': 30}),

            # Trading Controls
            html.Div([
                html.Div([
                    html.Label("Trading Pair:"),
                    dcc.Input(id='symbol-input', value='BTC/USDT', type='text'),
                    html.Label("Available Exchanges:"),
                    dcc.Dropdown(
                        id='exchange-dropdown',
                        options=exchange_options,
                        value=self.available_exchanges[0] if self.available_exchanges else None,
                        multi=True,  # Allow multiple exchange selection
                        placeholder="Select exchanges for trading..."
                    ),
                    html.Div(id='exchange-status', style={'margin': '10px 0'}),
                    html.Button('Start Trading', id='start-button', style={'marginRight': '10px'}),
                    html.Button('Stop Trading', id='stop-button'),
                ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px'})
            ]),

            # AI Exchange Selection Panel
            html.Div([
                html.H3("AI Exchange Selection", style={'textAlign': 'center'}),
                html.Div([
                    html.Div(id='selected-exchange'),
                    html.Div(id='exchange-metrics'),
                    dcc.Interval(id='exchange-update', interval=5000)
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
            ]),

            # Trading Process Visualization
            html.Div([
                html.H3("Real-time Trading Process"),
                html.Div([
                    html.Div(id='current-process'),
                    html.Div(id='process-log', style={'maxHeight': '200px', 'overflow': 'auto'}),
                    dcc.Store(id='process-log-store', data=[]),  # Store for process log
                    dcc.Interval(id='process-update', interval=1000)
                ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
            ]),

            # Trading Statistics
            html.Div([
                html.H3("Trading Performance"),
                html.Div([
                    html.Div(id='total-profit'),
                    html.Div(id='win-rate'),
                    html.Div(id='current-positions')
                ], style={'display': 'flex', 'justifyContent': 'space-around', 'padding': '20px'}),
                dcc.Interval(id='stats-update', interval=5000)
            ]),

            # Risk Management
            html.Div([
                html.H3("Risk Management"),
                html.Div([
                    html.Label("Maximum Position Size (% of Portfolio):"),
                    dcc.Slider(
                        id='position-size-slider',
                        min=0.1, max=5, step=0.1, value=1,
                        marks={i/2: str(i/2) for i in range(2, 11)}
                    ),
                    html.Label("Stop Loss (%):"),
                    dcc.Slider(
                        id='stop-loss-slider',
                        min=0.5, max=5, step=0.1, value=1,
                        marks={i/2: str(i/2) for i in range(1, 11)}
                    ),
                    html.Label("Take Profit (%):"),
                    dcc.Slider(
                        id='take-profit-slider',
                        min=1, max=10, step=0.5, value=3,
                        marks={i: str(i) for i in range(1, 11)}
                    )
                ], style={'padding': '20px'})
            ])
        ])

    def _setup_callbacks(self):
        @self.app.callback(
            [Output('selected-exchange', 'children'),
             Output('exchange-metrics', 'children'),
             Output('exchange-status', 'children')],
            [Input('exchange-update', 'n_intervals'),
             Input('symbol-input', 'value'),
             Input('exchange-dropdown', 'value')]
        )
        async def update_exchange_selection(n_intervals, symbol, selected_exchanges):
            try:
                if not selected_exchanges:
                    return (
                        "No exchanges selected",
                        "Please select at least one exchange",
                        html.Div("⚠️ No exchanges selected", style={'color': 'orange'})
                    )

                if not isinstance(selected_exchanges, list):
                    selected_exchanges = [selected_exchanges]

                # Get best exchange among selected ones
                best_exchange, metrics = await self.exchange_selector.select_best_exchange(
                    symbol, selected_exchanges
                )

                if not best_exchange:
                    error_msg = f"Error: {metrics.get('error', 'Unknown error')}"
                    return (
                        "No suitable exchange found",
                        error_msg,
                        html.Div("❌ No suitable exchange found", style={'color': 'red'})
                    )

                # Format metrics for display
                metrics_display = []
                for exchange_id, exchange_data in metrics['exchange_metrics'].items():
                    is_best = exchange_id == best_exchange
                    metrics_display.append(html.Div([
                        html.H4([
                            exchange_id.upper(),
                            html.Span(" (AI Selected)" if is_best else "",
                                    style={'color': 'green', 'fontSize': '0.8em'})
                        ]),
                        html.P(f"Estimated Profit: {exchange_data.get('estimated_profit', 0):.2f}%",
                              style={'color': 'green', 'fontWeight': 'bold'}),
                        html.P(f"Score: {exchange_data['score']:.2f}"),
                        html.P(f"Volume 24h: ${exchange_data['volume_24h']:,.2f}"),
                        html.P(f"Spread: {exchange_data['spread']:.4f}%"),
                        html.P(f"Risk Score: {exchange_data['risk_score']:.2f}"),
                        html.Div([
                            html.P("Risk Analysis:", style={'fontWeight': 'bold'}),
                            html.Ul([
                                html.Li(f"Market Liquidity: {'High' if exchange_data['volume_24h'] > 1000000 else 'Medium' if exchange_data['volume_24h'] > 100000 else 'Low'}"),
                                html.Li(f"Spread Risk: {'Low' if exchange_data['spread'] < 0.1 else 'Medium' if exchange_data['spread'] < 0.5 else 'High'}"),
                                html.Li(f"Overall Risk: {'Low' if exchange_data['risk_score'] < 0.3 else 'Medium' if exchange_data['risk_score'] < 0.7 else 'High'}")
                            ])
                        ])
                    ], style={
                        'margin': '10px',
                        'padding': '15px',
                        'border': '2px solid #ddd' if not is_best else '2px solid #4CAF50',
                        'borderRadius': '5px',
                        'backgroundColor': '#f8f9fa'
                    }))
                status_color = 'green' if metrics['confidence'] >= 90 else 'orange'
                status_icon = '✅' if metrics['confidence'] >= 90 else '⚠️'

                return (
                    f"Selected Exchange: {best_exchange.upper()} (Confidence: {metrics['confidence']:.1f}%)",
                    html.Div(metrics_display),
                    html.Div(f"{status_icon} Trading ready on {best_exchange.upper()}",
                            style={'color': status_color})
                )

            except Exception as e:
                logger.error(f"Error in exchange selection: {str(e)}")
                return (
                    "Error in exchange selection",
                    str(e),
                    html.Div("❌ Error selecting exchange", style={'color': 'red'})
                )

        @self.app.callback(
            [Output('process-log', 'children'),
             Output('process-log-store', 'data'),
             Output('current-process', 'children')],
            [Input('process-update', 'n_intervals')],
            [State('process-log-store', 'data')]
        )
        def update_trading_process(n_intervals, current_log):
            try:
                # Get latest process updates
                new_updates = self.trader.get_process_updates()
                current_process = self.trader.get_current_process()

                if not new_updates and not current_process:
                    return dash.no_update, current_log, dash.no_update

                # Add timestamps to updates
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_updates = [f"[{timestamp}] {update}" for update in new_updates]

                # Update log
                updated_log = (current_log or []) + formatted_updates
                if len(updated_log) > 100:  # Keep last 100 entries
                    updated_log = updated_log[-100:]

                # Format for display
                log_display = [html.P(entry) for entry in reversed(updated_log)]

                # Format current process
                if current_process:
                    process_display = html.Div([
                        html.H4("Current Trading Process"),
                        html.Div([
                            html.P(f"Action: {current_process['action']}", style={'fontWeight': 'bold'}),
                            html.P(f"Status: {current_process['status']}",
                                  style={'color': 'green' if current_process['status'] == 'success' else 'orange'}),
                            html.P(f"Exchange: {current_process.get('exchange', 'N/A').upper()}"),
                            html.P(f"Symbol: {current_process.get('symbol', 'N/A')}"),
                            html.P(f"Current P/L: ${current_process.get('profit_loss', 0):.2f}",
                                  style={'color': 'green' if current_process.get('profit_loss', 0) >= 0 else 'red',
                                        'fontWeight': 'bold'}),
                            html.P(f"Risk Level: {current_process.get('risk_level', 'N/A')}",
                                  style={'color': 'green' if current_process.get('risk_level') == 'Low' else
                                                'orange' if current_process.get('risk_level') == 'Medium' else 'red'})
                        ], style={'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px'})
                    ])
                else:
                    process_display = html.Div("No active trading process",
                                            style={'padding': '10px', 'color': '#666'})
                return html.Div(log_display), updated_log, process_display

            except Exception as e:
                logger.error(f"Error updating process log: {str(e)}")
                return (
                    html.Div([html.P(f"Error: {str(e)}")]),
                    current_log,
                    html.Div("Error in trading process", style={'color': 'red'})
                )

        @self.app.callback(
            [Output('total-profit', 'children'),
             Output('win-rate', 'children'),
             Output('current-positions', 'children')],
            [Input('stats-update', 'n_intervals')]
        )
        def update_stats(n_intervals):
            try:
                stats = self.trader.get_trading_stats()

                profit_color = 'green' if stats['total_profit'] >= 0 else 'red'
                total_profit = html.Div([
                    html.H4("Total Profit"),
                    html.P(f"${stats['total_profit']:,.2f}",
                          style={'color': profit_color, 'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                win_rate = html.Div([
                    html.H4("Win Rate"),
                    html.P(f"{stats['win_rate']:.1f}%",
                          style={'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                positions = html.Div([
                    html.H4("Current Positions"),
                    html.Div([
                        html.P(
                            f"{pos['symbol']}: {pos['size']} @ {pos['entry_price']:.2f}",
                            style={'margin': '5px 0'}
                        )
                        for pos in stats['positions']
                    ] if stats['positions'] else [html.P("No active positions")])
                ])

                return total_profit, win_rate, positions

            except Exception as e:
                logger.error(f"Error updating stats: {str(e)}")
                error_div = html.Div([
                    html.P(f"Error: {str(e)}", style={'color': 'red'})
                ])
                return error_div, error_div, error_div

    def run(self, debug=True, host='0.0.0.0', port=8050):
        self.app.run_server(debug=debug, host=host, port=port, dev_tools_hot_reload=False)

if __name__ == '__main__':
    dashboard = TradingDashboard()
    dashboard.run()

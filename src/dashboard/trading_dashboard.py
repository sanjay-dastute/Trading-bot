import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.core.trader import SmartTrader
from src.core.config import Config
from src.data.data_fetcher import DataFetcher

class TradingDashboard:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.config = Config()
        self.trader = SmartTrader(self.config)
        self.data_fetcher = DataFetcher(self.config)

        self.app.layout = self._create_layout()
        self._setup_callbacks()

    def _create_layout(self):
        return html.Div([
            # Header
            html.H1("AI Smart Trading Bot Dashboard",
                   style={'textAlign': 'center', 'marginBottom': 30}),

            # Trading Controls
            html.Div([
                html.Div([
                    html.Label("Trading Pair:"),
                    dcc.Input(id='symbol-input', value='BTC/USDT', type='text'),
                    html.Label("Exchange:"),
                    dcc.Dropdown(
                        id='exchange-dropdown',
                        options=[
                            {'label': 'Binance', 'value': 'binance'},
                            {'label': 'Coinbase', 'value': 'coinbase'}
                        ],
                        value='binance'
                    ),
                    html.Button('Start Trading', id='start-button'),
                    html.Button('Stop Trading', id='stop-button'),
                ], style={'width': '30%', 'display': 'inline-block', 'padding': '20px'})
            ]),

            # Main Content
            html.Div([
                # Price Chart and Signals
                html.Div([
                    dcc.Graph(id='price-chart'),
                    dcc.Interval(id='chart-update', interval=5000)
                ], style={'width': '70%', 'display': 'inline-block'}),

                # AI Analysis Panel
                html.Div([
                    html.H3("AI Trading Analysis"),
                    html.Div(id='ai-confidence'),
                    html.Div(id='model-consensus'),
                    html.Div(id='risk-analysis'),
                    dcc.Interval(id='ai-update', interval=10000)
                ], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top'})
            ]),

            # Trading Statistics
            html.Div([
                html.H3("Trading Performance"),
                html.Div([
                    html.Div(id='total-profit'),
                    html.Div(id='win-rate'),
                    html.Div(id='current-positions')
                ]),
                dcc.Interval(id='stats-update', interval=5000)
            ]),

            # Risk Management
            html.Div([
                html.H3("Risk Management"),
                html.Div([
                    html.Label("Maximum Position Size (% of Portfolio):"),
                    dcc.Slider(id='position-size-slider', min=0.1, max=5, step=0.1, value=2),
                    html.Label("Stop Loss (%):"),
                    dcc.Slider(id='stop-loss-slider', min=0.5, max=5, step=0.1, value=2),
                    html.Label("Take Profit (%):"),
                    dcc.Slider(id='take-profit-slider', min=1, max=10, step=0.5, value=6)
                ])
            ])
        ])

    def _setup_callbacks(self):
        @self.app.callback(
            [Output('price-chart', 'figure'),
             Output('ai-confidence', 'children'),
             Output('model-consensus', 'children'),
             Output('risk-analysis', 'children')],
            [Input('chart-update', 'n_intervals')],
            [State('symbol-input', 'value'),
             State('exchange-dropdown', 'value')]
        )
        def update_charts(n_intervals, symbol, exchange):
            try:
                # Get historical data
                data = self.data_fetcher.get_historical_data(symbol, source=exchange)
                if data is None or data.empty:
                    raise ValueError(f"No data available for {symbol} on {exchange}")

                # Get AI analysis
                latest_data = data.tail(60)  # Last 60 candles for AI analysis
                trade_conditions = self.trader.validate_trade_conditions(symbol, latest_data)

                # Create price chart
                fig = go.Figure()

                # Add candlestick chart
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    name='Price'
                ))

                # Add signals if available
                if 'signal' in data.columns:
                    buy_signals = data[data['signal'] == 1]
                    sell_signals = data[data['signal'] == -1]

                    fig.add_trace(go.Scatter(
                        x=buy_signals.index,
                        y=buy_signals['close'],
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=15, color='green'),
                        name='Buy Signal'
                    ))

                    fig.add_trace(go.Scatter(
                        x=sell_signals.index,
                        y=sell_signals['close'],
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=15, color='red'),
                        name='Sell Signal'
                    ))

                # Update layout
                fig.update_layout(
                    title=f'{symbol} Price Chart',
                    yaxis_title='Price',
                    xaxis_title='Date',
                    template='plotly_dark'
                )

                # Create AI analysis components with color coding
                confidence = trade_conditions['confidence']
                confidence_color = 'green' if confidence >= 98 else 'orange' if confidence >= 90 else 'red'

                ai_confidence = html.Div([
                    html.H4("AI Confidence"),
                    html.P(f"{confidence:.2f}%",
                          style={'color': confidence_color, 'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                model_consensus = html.Div([
                    html.H4("Model Consensus"),
                    html.P("Strong Agreement" if confidence >= 98 else
                          "Partial Agreement" if confidence >= 90 else "Disagreement",
                          style={'color': confidence_color, 'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                risk_analysis = html.Div([
                    html.H4("Risk Analysis"),
                    html.P(f"Risk-Reward Ratio: {trade_conditions['risk_reward']:.2f}",
                          style={'color': 'green' if trade_conditions['risk_reward'] >= 3 else 'orange',
                                'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                return fig, ai_confidence, model_consensus, risk_analysis

            except Exception as e:
                # Return error state with informative message
                empty_fig = go.Figure()
                empty_fig.add_annotation(text=f"Error: {str(e)}", showarrow=False)
                error_div = html.Div([
                    html.H4("Error"),
                    html.P(str(e), style={'color': 'red'})
                ])
                return empty_fig, error_div, error_div, error_div

        @self.app.callback(
            [Output('total-profit', 'children'),
             Output('win-rate', 'children'),
             Output('current-positions', 'children')],
            [Input('stats-update', 'n_intervals')]
        )
        def update_stats(n_intervals):
            try:
                stats = self.trader.get_trading_stats()

                # Format profit with color based on performance
                profit = stats['daily_stats']['total_profit']
                profit_color = 'green' if profit > 0 else 'red' if profit < 0 else 'orange'

                total_profit = html.Div([
                    html.H4("Total Profit"),
                    html.P(f"${profit:.2f}",
                          style={'color': profit_color, 'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                # Calculate and format win rate
                trades = stats['daily_stats'].get('trades', 0)
                wins = stats['daily_stats'].get('profits', 0)
                win_rate = (wins / trades * 100) if trades > 0 else 0
                win_rate_color = 'green' if win_rate >= 70 else 'orange' if win_rate >= 50 else 'red'

                win_rate_div = html.Div([
                    html.H4("Win Rate"),
                    html.P(f"{win_rate:.2f}% ({wins}/{trades} trades)",
                          style={'color': win_rate_color, 'fontSize': '1.2em', 'fontWeight': 'bold'})
                ])

                # Format current positions
                positions_list = [
                    html.Li(
                        f"{symbol}: {pos['size']} @ ${pos['entry_price']:.2f}",
                        style={'color': 'green' if pos.get('unrealized_profit', 0) > 0 else 'red'}
                    )
                    for symbol, pos in stats['current_positions'].items()
                ] if stats['current_positions'] else [html.Li("No active positions")]

                positions = html.Div([
                    html.H4("Current Positions"),
                    html.Ul(positions_list, style={'listStyleType': 'none', 'padding': '0'})
                ])

                return total_profit, win_rate_div, positions

            except Exception as e:
                error_div = html.Div([
                    html.H4("Error"),
                    html.P(str(e), style={'color': 'red'})
                ])
                return error_div, error_div, error_div

    def run(self, debug=True, host='0.0.0.0', port=8050):
        self.app.run_server(debug=debug, host=host, port=port)

if __name__ == '__main__':
    dashboard = TradingDashboard()
    dashboard.run()

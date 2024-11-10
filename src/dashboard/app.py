import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from data.data_fetcher import DataFetcher
from strategies.ai_strategy import AITradingStrategy

# Initialize components
config = Config()
data_fetcher = DataFetcher(config)
strategy = AITradingStrategy(config)

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("AI Trading Bot Dashboard"),

    # Symbol input
    html.Div([
        html.Label("Trading Symbol:"),
        dcc.Input(id='symbol-input', value='AAPL', type='text'),
        html.Button('Update', id='submit-button', n_clicks=0)
    ]),

    # Main price chart
    dcc.Graph(id='price-chart'),

    # Trading statistics
    html.Div([
        html.H3("Trading Statistics"),
        html.Div(id='trading-stats')
    ]),

    # Auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(
    [Output('price-chart', 'figure'),
     Output('trading-stats', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('symbol-input', 'value')]
)
def update_data(n_intervals, n_clicks, symbol):
    # Fetch historical data
    df = data_fetcher.get_historical_data(symbol, limit=100)

    # Generate trading signals
    df_with_signals = strategy.generate_signals(df)

    # Create price chart
    fig = go.Figure()

    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))

    # Add signals if available
    if 'signal' in df_with_signals.columns:
        buy_signals = df_with_signals[df_with_signals['signal'] == 1]
        sell_signals = df_with_signals[df_with_signals['signal'] == -1]

        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Close'],
            mode='markers',
            marker=dict(symbol='triangle-up', size=15, color='green'),
            name='Buy Signal'
        ))

        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals['Close'],
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

    # Calculate statistics
    stats = html.Div([
        html.P(f"Current Price: ${df['Close'].iloc[-1]:.2f}"),
        html.P(f"Daily Change: {((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100):.2f}%"),
        html.P(f"Volume: {df['Volume'].iloc[-1]:,.0f}")
    ])

    return fig, stats

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)

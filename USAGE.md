# AI Smart Trading Bot - Usage Guide

## Dashboard Overview

The AI Smart Trading Bot provides a comprehensive dashboard at `http://localhost:8050` with the following features:

### 1. Trading Controls
- Symbol selection (e.g., BTC/USDT)
- Exchange selection
- Start/Stop trading buttons
- Risk management settings

### 2. AI Trading Process
The bot uses an ensemble of AI models for maximum accuracy:
- LSTM (Long Short-Term Memory) for price prediction
- XGBoost for pattern recognition
- Random Forest for market sentiment analysis

#### Zero-Loss Protection System
1. Pre-trade Validation:
   - Multiple AI model consensus required
   - Minimum 98% prediction confidence threshold
   - Market sentiment confirmation
   - Technical indicator cross-validation

2. Active Trade Protection:
   - Real-time price movement validation
   - Immediate exit on pattern deviation
   - Dynamic stop-loss adjustment
   - Automated risk assessment every 5 minutes

3. Position Management:
   - Small initial position with scaling
   - Multiple take-profit levels
   - Partial profit booking
   - Risk-free position after 1% profit

### 3. Trading Statistics
- Total profit/loss
- Win rate
- Current positions
- Risk metrics

## Configuration Guide

### API Key Setup

1. **Binance API Keys**
   - Go to Binance Account → API Management
   - Create new API key with trading permissions
   - Copy API key and secret to `.env`:
   ```env
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_SECRET_KEY=your_binance_secret_key
   ```

2. **Coinbase API Keys**
   - Go to Coinbase Pro → API → New API Key
   - Enable trading permissions
   - Copy API key and secret to `.env`:
   ```env
   COINBASE_API_KEY=your_coinbase_api_key
   COINBASE_SECRET_KEY=your_coinbase_secret_key
   ```

### Risk Management Settings

Configure risk parameters in `.env`:
```env
MAX_POSITION_SIZE=0.02  # Maximum 2% of portfolio per trade
MAX_DAILY_DRAWDOWN=0.01  # Stop trading if 1% portfolio loss
MIN_CONFIDENCE_THRESHOLD=0.98  # Minimum 98% AI confidence required
```

## Trading Strategies

### 1. Entry Conditions
- AI confidence score > 98%
- Minimum 3 indicator confirmations
- Volume > 200% of 20-day average
- Market trend alignment
- Risk-reward ratio minimum 5:1

### 2. Exit Conditions
- Take profit targets reached
- Stop loss triggered
- Pattern deviation detected
- AI confidence drops below threshold

## Monitoring and Alerts

The dashboard provides real-time monitoring of:
1. AI Model Performance
   - Prediction accuracy
   - Confidence levels
   - Model consensus

2. Risk Metrics
   - Position sizes
   - Stop loss levels
   - Portfolio exposure

3. Trading Performance
   - Profit/Loss tracking
   - Win rate
   - Average trade duration

## Troubleshooting

Common issues and solutions:

1. **Connection Issues**
   - Verify API keys are correct
   - Check internet connection
   - Ensure exchange is operational

2. **Trading Issues**
   - Verify sufficient balance
   - Check trading permissions
   - Confirm minimum trade requirements

3. **Dashboard Issues**
   - Clear browser cache
   - Restart the application
   - Check port availability

## Support

For technical support:
1. Check the GitHub issues
2. Review error logs in `logs/` directory
3. Create a new issue with detailed information

## Best Practices

1. Start with paper trading
2. Use small position sizes initially
3. Monitor the system regularly
4. Keep API keys secure
5. Regularly backup configuration
6. Update the bot frequently

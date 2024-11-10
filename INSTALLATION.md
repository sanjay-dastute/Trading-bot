# AI Smart Trading Bot - Installation Guide

## Prerequisites
- Python 3.12 or higher
- pip (Python package manager)
- Git

## Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/sanjay-dastute/Trading-bot.git
cd Trading-bot
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

2. Configure your trading platform API keys in `.env`:
```env
# Binance Configuration
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key

# Coinbase Configuration
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_secret_key

# Risk Management Settings
MAX_POSITION_SIZE=0.02  # 2% of portfolio
MAX_DAILY_DRAWDOWN=0.01  # 1% maximum loss
MIN_CONFIDENCE_THRESHOLD=0.98  # 98% AI prediction confidence
```

## Running Tests
```bash
python -m pytest tests/
```

## Starting the Trading Bot

1. Start the bot with dashboard:
```bash
python src/main.py
```

2. Access the dashboard at `http://localhost:8050`

## Platform Support
The bot supports multiple trading platforms:
- Binance
- Coinbase
- Interactive Brokers (coming soon)
- Alpaca (coming soon)

## Security Notes
- Never share your API keys
- Store .env file securely
- Use separate API keys for testing and production
- Enable IP restrictions on API keys when possible

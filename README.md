# AI Smart Trading Bot

An advanced AI-powered trading bot that supports multiple trading platforms and implements sophisticated trading strategies.

## Features

- Multi-platform support (Binance, Coinbase, etc.)
- AI-powered trading strategies
- Real-time market data analysis
- Risk management system
- Interactive dashboard
- Automated trading execution

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sanjay-dastute/Trading-bot.git
cd Trading-bot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your environment:
```bash
cp .env.example .env
```
Edit the `.env` file with your API keys and preferences.

## Configuration

1. Open `.env` file and add your trading platform API keys:
```
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
```

2. Configure trading parameters:
```
RISK_LEVEL=medium
MAX_POSITION_SIZE=1000
STOP_LOSS_PERCENTAGE=2
TAKE_PROFIT_PERCENTAGE=6
```

## Usage

1. Start the trading bot:
```bash
python src/main.py
```

2. Access the dashboard:
```bash
python src/dashboard/app.py
```
Navigate to `http://localhost:8050` in your web browser.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT License

## Disclaimer

Trading cryptocurrencies and stocks carries risk. This software is for educational purposes only. Always do your own research before trading.

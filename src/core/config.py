import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()

    @property
    def binance_credentials(self):
        return {
            'api_key': os.getenv('BINANCE_API_KEY'),
            'secret_key': os.getenv('BINANCE_SECRET_KEY')
        }

    @property
    def coinbase_credentials(self):
        return {
            'api_key': os.getenv('COINBASE_API_KEY'),
            'secret_key': os.getenv('COINBASE_SECRET_KEY')
        }

    @property
    def alpha_vantage_credentials(self):
        return {
            'api_key': os.getenv('ALPHA_VANTAGE_API_KEY')
        }

    @property
    def trading_params(self):
        return {
            'risk_level': os.getenv('RISK_LEVEL', 'medium'),
            'max_position_size': float(os.getenv('MAX_POSITION_SIZE', 1000)),
            'stop_loss_percentage': float(os.getenv('STOP_LOSS_PERCENTAGE', 2)),
            'take_profit_percentage': float(os.getenv('TAKE_PROFIT_PERCENTAGE', 6))
        }

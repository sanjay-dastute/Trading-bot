#!/usr/bin/env python3
"""
Migration script for API keys from environment variables to secure storage
"""
import os
import sys
import logging
from pathlib import Path
from getpass import getpass
sys.path.append(str(Path(__file__).parent.parent))

from src.core.key_manager import KeyManager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_keys():
    """Migrate API keys from .env to secure storage"""
    try:
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        if not env_path.exists():
            logger.error("No .env file found")
            return False

        load_dotenv(env_path)

        # Initialize key manager
        key_manager = KeyManager()

        # Get encryption password
        password = getpass("Enter encryption password for secure storage: ")
        confirm_password = getpass("Confirm encryption password: ")

        if password != confirm_password:
            logger.error("Passwords do not match")
            return False

        # Exchange mapping
        exchanges = {
            'BINANCE': 'binance',
            'KUCOIN': 'kucoin',
            'GATEIO': 'gateio',
            'BYBIT': 'bybit',
            'MEXC': 'mexc',
            'BITGET': 'bitget',
            'OKX': 'okx',
            'BLOFIN': 'blofin',
            'WOO': 'woo',
            'COINBASE': 'coinbase'
        }

        migrated = False
        # Migrate keys for each exchange
        for env_name, exchange_id in exchanges.items():
            api_key = os.getenv(f'{env_name}_API_KEY')
            secret_key = os.getenv(f'{env_name}_SECRET_KEY')
            passphrase = os.getenv(f'{env_name}_PASSPHRASE')

            if api_key and secret_key:
                keys = {
                    'api_key': api_key,
                    'secret_key': secret_key
                }
                if passphrase:
                    keys['passphrase'] = passphrase

                if key_manager.set_exchange_keys(exchange_id, keys, password):
                    logger.info(f"Successfully migrated keys for {exchange_id}")
                    migrated = True
                else:
                    logger.warning(f"Failed to migrate keys for {exchange_id}")

        if migrated:
            logger.info("\nMigration completed successfully!")
            logger.info("You can now remove the API keys from your .env file")
            logger.info("Make sure to keep your encryption password safe!")
        else:
            logger.info("No API keys found to migrate")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == '__main__':
    sys.exit(0 if migrate_keys() else 1)

"""
Secure API Key Management System for Trading Bot
"""
from typing import Dict, Optional, List
import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
from pathlib import Path

class KeyManager:
    """Manages secure storage and retrieval of exchange API keys"""

    def __init__(self, config_dir: str = None):
        self.logger = logging.getLogger(__name__)
        self.config_dir = config_dir or os.path.join(str(Path.home()), '.trading_bot')
        self.keys_file = os.path.join(self.config_dir, 'exchange_keys.enc')
        self.salt_file = os.path.join(self.config_dir, 'salt')

        # Supported exchanges
        self.supported_exchanges = {
            'kucoin': {'required_keys': ['api_key', 'secret_key', 'passphrase']},
            'gateio': {'required_keys': ['api_key', 'secret_key']},
            'bybit': {'required_keys': ['api_key', 'secret_key']},
            'mexc': {'required_keys': ['api_key', 'secret_key']},
            'bitget': {'required_keys': ['api_key', 'secret_key', 'passphrase']},
            'okx': {'required_keys': ['api_key', 'secret_key', 'passphrase']},
            'blofin': {'required_keys': ['api_key', 'secret_key']},
            'woo': {'required_keys': ['api_key', 'secret_key']},
            'binance': {'required_keys': ['api_key', 'secret_key']},
            'coinbase': {'required_keys': ['api_key', 'secret_key']}
        }

        self._initialize_storage()
        self._load_or_create_salt()

    def _initialize_storage(self):
        """Initialize secure storage directory"""
        try:
            os.makedirs(self.config_dir, mode=0o700, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create config directory: {e}")
            raise

    def _load_or_create_salt(self):
        """Load existing salt or create new one"""
        try:
            if os.path.exists(self.salt_file):
                with open(self.salt_file, 'rb') as f:
                    self.salt = f.read()
            else:
                self.salt = os.urandom(16)
                with open(self.salt_file, 'wb') as f:
                    f.write(self.salt)
                os.chmod(self.salt_file, 0o600)
        except Exception as e:
            self.logger.error(f"Failed to handle salt: {e}")
            raise

    def _get_encryption_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def set_exchange_keys(self, exchange: str, keys: Dict[str, str], password: str) -> bool:
        """
        Securely store API keys for an exchange

        Args:
            exchange: Exchange name (lowercase)
            keys: Dictionary of API keys
            password: Encryption password

        Returns:
            bool: Success status
        """
        try:
            exchange = exchange.lower()
            if exchange not in self.supported_exchanges:
                raise ValueError(f"Unsupported exchange: {exchange}")

            # Validate required keys
            required_keys = self.supported_exchanges[exchange]['required_keys']
            missing_keys = [k for k in required_keys if k not in keys]
            if missing_keys:
                raise ValueError(f"Missing required keys for {exchange}: {missing_keys}")

            # Load existing keys
            stored_keys = self.get_all_keys(password) or {}

            # Update keys for the specified exchange
            stored_keys[exchange] = keys

            # Encrypt and save
            fernet = Fernet(self._get_encryption_key(password))
            encrypted_data = fernet.encrypt(json.dumps(stored_keys).encode())

            with open(self.keys_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.keys_file, 0o600)

            return True

        except Exception as e:
            self.logger.error(f"Failed to set keys for {exchange}: {e}")
            return False

    def get_exchange_keys(self, exchange: str, password: str) -> Optional[Dict[str, str]]:
        """
        Retrieve API keys for a specific exchange

        Args:
            exchange: Exchange name (lowercase)
            password: Encryption password

        Returns:
            Optional[Dict[str, str]]: Dictionary of API keys or None
        """
        try:
            stored_keys = self.get_all_keys(password)
            return stored_keys.get(exchange.lower()) if stored_keys else None
        except Exception as e:
            self.logger.error(f"Failed to get keys for {exchange}: {e}")
            return None

    def get_all_keys(self, password: str) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Retrieve all stored API keys

        Args:
            password: Encryption password

        Returns:
            Optional[Dict[str, Dict[str, str]]]: Dictionary of all stored keys or None
        """
        try:
            if not os.path.exists(self.keys_file):
                return {}

            with open(self.keys_file, 'rb') as f:
                encrypted_data = f.read()

            fernet = Fernet(self._get_encryption_key(password))
            decrypted_data = fernet.decrypt(encrypted_data)

            return json.loads(decrypted_data.decode())

        except Exception as e:
            self.logger.error(f"Failed to get all keys: {e}")
            return None

    def remove_exchange_keys(self, exchange: str, password: str) -> bool:
        """
        Remove API keys for a specific exchange

        Args:
            exchange: Exchange name (lowercase)
            password: Encryption password

        Returns:
            bool: Success status
        """
        try:
            stored_keys = self.get_all_keys(password)
            if not stored_keys or exchange.lower() not in stored_keys:
                return False

            del stored_keys[exchange.lower()]

            fernet = Fernet(self._get_encryption_key(password))
            encrypted_data = fernet.encrypt(json.dumps(stored_keys).encode())

            with open(self.keys_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.keys_file, 0o600)

            return True

        except Exception as e:
            self.logger.error(f"Failed to remove keys for {exchange}: {e}")
            return False

    def get_configured_exchanges(self, password: str) -> List[str]:
        """
        Get list of exchanges with configured API keys

        Args:
            password: Encryption password

        Returns:
            List[str]: List of configured exchange names
        """
        try:
            stored_keys = self.get_all_keys(password)
            return list(stored_keys.keys()) if stored_keys else []
        except Exception as e:
            self.logger.error(f"Failed to get configured exchanges: {e}")
            return []

    def validate_keys(self, exchange: str, keys: Dict[str, str]) -> bool:
        """
        Validate API keys for an exchange

        Args:
            exchange: Exchange name (lowercase)
            keys: Dictionary of API keys

        Returns:
            bool: Validation status
        """
        try:
            exchange = exchange.lower()
            if exchange not in self.supported_exchanges:
                return False

            required_keys = self.supported_exchanges[exchange]['required_keys']
            return all(k in keys and bool(keys[k]) for k in required_keys)

        except Exception as e:
            self.logger.error(f"Failed to validate keys for {exchange}: {e}")
            return False

    def get_exchange_requirements(self, exchange: str) -> Optional[Dict[str, List[str]]]:
        """
        Get API key requirements for an exchange

        Args:
            exchange: Exchange name (lowercase)

        Returns:
            Optional[Dict[str, List[str]]]: Dictionary of required keys or None
        """
        try:
            exchange = exchange.lower()
            return self.supported_exchanges.get(exchange)
        except Exception as e:
            self.logger.error(f"Failed to get requirements for {exchange}: {e}")
            return None

"""
API Key Management Routes
"""
from flask import Blueprint, request, jsonify, render_template
from src.core.key_manager import KeyManager
import logging

api_keys = Blueprint('api_keys', __name__)
key_manager = KeyManager()
logger = logging.getLogger(__name__)

@api_keys.route('/keys')
def api_keys_page():
    """Render API keys management page"""
    return render_template('api_keys.html')

@api_keys.route('/api/keys', methods=['GET'])
def get_configured_exchanges():
    """Get list of configured exchanges"""
    try:
        password = request.headers.get('X-Encryption-Password')
        if not password:
            return jsonify({'error': 'Encryption password required'}), 400

        exchanges = key_manager.get_configured_exchanges(password)
        return jsonify({exchange: True for exchange in exchanges})

    except Exception as e:
        logger.error(f"Failed to get configured exchanges: {e}")
        return jsonify({'error': 'Failed to get configured exchanges'}), 500

@api_keys.route('/api/keys', methods=['POST'])
def save_exchange_keys():
    """Save API keys for an exchange"""
    try:
        password = request.headers.get('X-Encryption-Password')
        if not password:
            return jsonify({'error': 'Encryption password required'}), 400

        data = request.get_json()
        if not data or 'exchange' not in data or 'keys' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        exchange = data['exchange']
        keys = data['keys']

        if not key_manager.validate_keys(exchange, keys):
            return jsonify({'error': 'Invalid API keys'}), 400

        success = key_manager.set_exchange_keys(exchange, keys, password)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Failed to save API keys'}), 500

    except Exception as e:
        logger.error(f"Failed to save exchange keys: {e}")
        return jsonify({'error': 'Failed to save API keys'}), 500

@api_keys.route('/api/keys/<exchange>', methods=['DELETE'])
def remove_exchange_keys(exchange):
    """Remove API keys for an exchange"""
    try:
        password = request.headers.get('X-Encryption-Password')
        if not password:
            return jsonify({'error': 'Encryption password required'}), 400

        success = key_manager.remove_exchange_keys(exchange, password)
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Failed to remove API keys'}), 500

    except Exception as e:
        logger.error(f"Failed to remove exchange keys: {e}")
        return jsonify({'error': 'Failed to remove exchange keys'}), 500

@api_keys.route('/api/keys/requirements/<exchange>', methods=['GET'])
def get_exchange_requirements(exchange):
    """Get API key requirements for an exchange"""
    try:
        requirements = key_manager.get_exchange_requirements(exchange)
        if requirements:
            return jsonify(requirements)
        else:
            return jsonify({'error': 'Exchange not supported'}), 404

    except Exception as e:
        logger.error(f"Failed to get exchange requirements: {e}")
        return jsonify({'error': 'Failed to get exchange requirements'}), 500

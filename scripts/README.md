# Migration Scripts

This directory contains utility scripts for the Trading Bot.

## API Key Migration

The `migrate_keys.py` script helps migrate API keys from environment variables to the new secure storage system.

### Usage

1. Make sure your `.env` file contains your existing API keys
2. Run the migration script:
   ```bash
   python3 scripts/migrate_keys.py
   ```
3. Enter and confirm your encryption password when prompted
4. The script will migrate all configured API keys to secure storage
5. After successful migration, you can remove the API keys from your .env file

### Security Notes

- Choose a strong encryption password
- Store your encryption password securely
- Don't share your encryption password
- Keep backups of your API keys
- Consider rotating your API keys after migration

For more information about API key management, see the [API Keys Guide](../docs/API_KEYS_GUIDE.md).

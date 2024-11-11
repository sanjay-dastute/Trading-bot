# Trading Bot Installation Guide

## System Requirements
- Python 3.12 or higher
- Node.js 18 or higher
- PostgreSQL 13 or higher
- Linux/Unix environment (recommended)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/trading-bot.git
cd trading-bot
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb trading_bot
```

### 4. Configuration
1. Copy example configuration:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your settings:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost/trading_bot

   # Web Interface
   PORT=8000
   HOST=localhost

   # Optional: Default Exchange API Keys
   BINANCE_API_KEY=your_key
   BINANCE_SECRET_KEY=your_secret

   # Repeat for other exchanges as needed
   ```

## Exchange Setup

### Supported Exchanges
The bot supports these major exchanges:
1. Binance
2. KuCoin
3. Gate.io
4. Bybit
5. MEXC
6. Bitget
7. OKX
8. Blofin
9. WOO
10. Coinbase

### API Key Setup
You can configure any number of exchanges. API keys are optional and can be added later through the web interface.

For each exchange:
1. Create API keys on the exchange website
2. Enable trading permissions
3. Add keys via web interface or `.env` file

See [API Keys Guide](API_KEYS_GUIDE.md) for detailed instructions.

## Running the Bot

### 1. Start Web Interface
```bash
python run.py
```

### 2. Access Dashboard
Open `http://localhost:8000` in your browser

### 3. Configure Exchanges
1. Navigate to API Key Management
2. Add exchange credentials
3. Set encryption password

## Development Setup

### 1. Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Run Tests
```bash
pytest tests/
```

### 3. Code Style
```bash
# Check style
flake8 src/

# Format code
black src/
```

## Docker Installation (Optional)

### Using Docker Compose
```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Manual Docker Setup
```bash
# Build image
docker build -t trading-bot .

# Run container
docker run -d \
  -p 8000:8000 \
  --name trading-bot \
  -v $(pwd)/.env:/app/.env \
  trading-bot
```

## Troubleshooting

### Common Issues

#### Database Connection
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Reset database
sudo -u postgres dropdb trading_bot
sudo -u postgres createdb trading_bot
```

#### Exchange Connection
- Verify API key permissions
- Check network connectivity
- Ensure correct API endpoints

#### Web Interface
- Check port availability
- Verify database connection
- Check log files

## Security Recommendations

### API Key Security
- Use read-only API keys when possible
- Enable IP restrictions
- Regular key rotation
- Secure password storage

### System Security
- Regular updates
- Firewall configuration
- SSL/TLS setup
- Access control

## Monitoring

### Log Files
- Application logs: `logs/app.log`
- Trading logs: `logs/trading.log`
- Error logs: `logs/error.log`

### Metrics
- System resources
- Trading performance
- Exchange connectivity
- Error rates

## Updating

### Regular Updates
```bash
# Update repository
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate
```

### Version Control
- Check release notes
- Backup configuration
- Test in staging
- Gradual rollout

## Support

### Getting Help
- Check documentation
- Review error logs
- Search issues
- Contact support

## Next Steps
1. Configure exchanges
2. Set trading parameters
3. Monitor performance
4. Review documentation

For detailed usage instructions, see [Trading Guide](TRADING_GUIDE.md).

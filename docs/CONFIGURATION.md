# 🔧 Configuration Guide

Complete configuration reference for the Crypto Trading Bot including API setup, environment variables, and network requirements.

## 📋 Table of Contents

1. [Environment Variables](#environment-variables)
2. [API Configuration](#api-configuration)
3. [Network Requirements](#network-requirements)
4. [Trading Modes](#trading-modes)
5. [Exchange Configuration](#exchange-configuration)
6. [Security Best Practices](#security-best-practices)

## Environment Variables

### Configuration File Setup

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your settings
code .env  # or nano .env

# Validate configuration
python validate_env.py
```

### Core Settings

```env
# Trading Mode
MODE="backtest"              # Safe testing mode
# MODE="trade"               # Live trading (requires API keys)

# Exchange Selection
EXCHANGE="BinanceBacktestClient"  # For backtesting
# EXCHANGE="Binance"              # For live trading
# EXCHANGE="KrakenBacktestClient" # Kraken backtesting
# EXCHANGE="TestExchange"         # Test mode with live data

# Strategy Configuration
STRATEGY="GridTradingStrategy"   # Primary strategy
TRADING_PAIR="BTC_USD"          # Default trading pair
```

### API Credentials (Live Trading Only)

```env
# Binance.US API Configuration
API_KEY="your_actual_api_key_here"
API_SECRET="your_actual_secret_key_here"

# Optional: API endpoint customization
API_BASE_URL="https://api.binance.us"
```

## API Configuration

### Binance.US Account Setup

1. **Create Account**: Sign up at [Binance.US](https://www.binance.us/)
2. **Enable 2FA**: Set up two-factor authentication for security
3. **Complete Verification**: Complete identity verification for API access
4. **Create API Keys**: Follow [Binance.US API Documentation](https://support.binance.us/en/articles/9842800-how-to-create-an-api-key-on-binance-us)

### API Key Permissions

**Recommended permissions for trading bot:**
- ✅ **Enable Reading** - Required for market data
- ✅ **Enable Spot & Margin Trading** - Required for placing orders
- ❌ **Enable Withdrawals** - NOT recommended for security
- ❌ **Enable Internal Transfer** - NOT recommended for security

### API Security Settings

```env
# Restrict API access by IP (recommended)
API_IP_RESTRICTION="your.server.ip.address"

# Use testnet for development (if available)
USE_TESTNET="true"  # Development only
```

## Network Requirements

### IPv4 Connectivity

Binance.US API requires IPv4 connectivity. IPv6 is not supported.

#### Connectivity Test

**MacOS/Linux:**
```bash
# Test IPv4 connectivity to Binance.US
curl -4 -I https://api.binance.us/api/v3/ping

# Expected response: HTTP/1.1 200 OK
```

**Windows:**
```cmd
# Test connectivity
curl -4 -I https://api.binance.us/api/v3/ping
```

#### IPv4 Issues Troubleshooting

**MacOS - Disable IPv6:**
```bash
# Temporary disable (requires admin password)
sudo networksetup -setv6off Wi-Fi
sudo networksetup -setv6off Ethernet

# Re-enable later
sudo networksetup -setv6automatic Wi-Fi
sudo networksetup -setv6automatic Ethernet
```

**Windows - Prioritize IPv4:**
```cmd
# Run as Administrator
netsh interface ipv6 set global randomizeidentifiers=disabled
netsh interface ipv6 set privacy state=disabled
```

**Linux - Prefer IPv4:**
```bash
# Add to /etc/gai.conf
echo "precedence ::ffff:0:0/96 100" | sudo tee -a /etc/gai.conf
```

### Firewall Configuration

Ensure outbound HTTPS (port 443) access to:
- `api.binance.us`
- `stream.binance.us` (for WebSocket data)

## Trading Modes

### Backtest Mode
```env
MODE="backtest"
EXCHANGE="BinanceBacktestClient"
```

**Features:**
- Uses historical data from `Test/HistoricalData/`
- No real money involved
- Perfect for strategy testing
- Generates performance reports

**Data Requirements:**
- Historical CSV files in `Test/HistoricalData/`
- Format: timestamp, open, high, low, close, volume

### Live Trading Mode
```env
MODE="trade"
EXCHANGE="Binance"
API_KEY="your_key"
API_SECRET="your_secret"
```

**Features:**
- Real-time market data
- Actual order placement
- Real money at risk
- Live performance tracking

**Safety Checks:**
- Start with small amounts
- Test strategies in backtest mode first
- Monitor positions actively
- Set appropriate stop-losses

### Test Mode
```env
MODE="test"
EXCHANGE="TestExchange"
```

**Features:**
- Live market data
- Simulated order execution
- No real money involved
- Real-time testing environment

## Exchange Configuration

### Binance.US Configuration
```env
EXCHANGE="Binance"
API_BASE_URL="https://api.binance.us"
WEBSOCKET_URL="wss://stream.binance.us:9443"

# Rate limiting
API_RATE_LIMIT="1200"  # Requests per minute
ORDER_RATE_LIMIT="100" # Orders per 10 seconds
```

### Kraken Configuration (Future)
```env
EXCHANGE="Kraken"
API_BASE_URL="https://api.kraken.com"
# Additional Kraken-specific settings
```

### Custom Exchange Settings
```env
# Timeouts
API_TIMEOUT="30"        # API request timeout in seconds
WEBSOCKET_TIMEOUT="10"  # WebSocket timeout in seconds

# Retry settings
MAX_RETRIES="3"         # Maximum API retry attempts
RETRY_DELAY="1"         # Delay between retries in seconds
```

## Security Best Practices

### API Key Security
- **Never commit** API keys to version control
- **Use environment variables** or `.env` files (add `.env` to `.gitignore`)
- **Restrict IP access** in your exchange account settings
- **Disable withdrawals** for API keys used by trading bots
- **Rotate keys regularly** and monitor for unauthorized access

### Environment File Security
```bash
# Set proper permissions on .env file
chmod 600 .env

# Verify .env is in .gitignore
grep -q "\.env" .gitignore && echo "✅ .env ignored" || echo "❌ Add .env to .gitignore"
```

### Production Deployment
```env
# Use separate API keys for production
PRODUCTION_API_KEY="prod_key_here"
PRODUCTION_API_SECRET="prod_secret_here"

# Enable additional logging for production
LOG_LEVEL="INFO"
LOG_API_CALLS="true"
ENABLE_MONITORING="true"
```

### Backup and Recovery
- **Backup configuration**: Keep secure copies of working configurations
- **Document changes**: Track configuration changes in version control
- **Test recovery**: Regularly test backup restoration procedures
- **Monitor alerts**: Set up monitoring for configuration issues

## Advanced Configuration

### Strategy Parameters
```env
# Grid Trading Strategy
GRID_SIZE="10"           # Number of grid levels
GRID_SPACING="0.01"      # Spacing between grid levels (1%)
POSITION_SIZE="100"      # Base position size in USD
MAX_POSITIONS="5"        # Maximum concurrent positions

# Risk Management
STOP_LOSS_PERCENT="0.05" # Stop loss at 5%
TAKE_PROFIT_PERCENT="0.02" # Take profit at 2%
MAX_DRAWDOWN="0.10"      # Maximum portfolio drawdown (10%)
```

### Performance Tuning
```env
# Data refresh rates
PRICE_UPDATE_INTERVAL="1"    # Price updates per second
ORDER_CHECK_INTERVAL="5"     # Order status check interval (seconds)
METRICS_UPDATE_INTERVAL="10" # Metrics collection interval (seconds)

# Memory management
MAX_HISTORY_RECORDS="10000"  # Maximum historical data records
CLEANUP_INTERVAL="3600"      # Cleanup old data every hour
```

### Logging Configuration
```env
# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL="INFO"

# Log destinations
LOG_TO_FILE="true"
LOG_TO_CONSOLE="true"
LOG_FILE_PATH="logs/trading_bot.log"

# Log rotation
LOG_MAX_SIZE="10MB"
LOG_BACKUP_COUNT="5"
```

## Validation and Testing

### Configuration Validation
```bash
# Validate configuration
python validate_env.py

# Test API connectivity
python -c "from Exchanges.Live.Binance import Binance; b = Binance(); print('API connection: OK')"

# Test strategy initialization
python -c "from Strategies.GridTradingStrategy import GridTradingStrategy; s = GridTradingStrategy(); print('Strategy init: OK')"
```

### Environment Testing
```bash
# Check all environment variables
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required_vars = ['MODE', 'EXCHANGE', 'STRATEGY']
for var in required_vars:
    value = os.getenv(var)
    print(f'{var}: {value if value else \"❌ MISSING\"}')
"
```

---

🔒 **Security Note**: Always prioritize security when configuring live trading. Start with small amounts and test thoroughly before scaling up.
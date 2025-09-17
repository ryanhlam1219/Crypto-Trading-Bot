# Crypto Trading Bot

Advanced crypto trading bot written in Python 3.13+ with comprehensive performance tracking and metrics collection. The bot supports multiple trading strategies and provides detailed analytics for both backtesting and live trading scenarios.

## ✨ Features

- **Multi-Exchange Support**: Built-in support for Binance.US with extensible architecture
- **Strategy Framework**: Modular strategy system with Grid Trading implementation
- **Comprehensive Metrics**: Advanced performance tracking with trade analytics
- **Backtesting Engine**: Historical data testing with detailed performance reports
- **Live Trading**: Real-time trading with API monitoring and error handling
- **Professional Reporting**: Detailed P&L analysis, win rates, and performance metrics

## 📊 Metrics & Analytics

The bot includes a sophisticated `MetricsCollector` system that provides:
- Trade entry/exit tracking with unique identifiers
- Real-time P&L calculations and profit percentage analysis
- API performance monitoring (response times, error rates)
- Win rate statistics and trading performance analytics
- Comprehensive performance reports for session analysis

For detailed metrics documentation, see [METRICS_README.md](METRICS_README.md)

## 🌐 Network Requirements

In order for this bot to establish a connection to the Binance.US API, you must establish a network connection using IPv4 and not IPv6 as IPv6 is not supported. ([read more here](https://dev.binance.vision/t/ipv6-support-for-trading/17876))

### IPv4 Connectivity Check

To confirm a connection to Binance.US API exists, run:
```bash
curl -I https://api.binance.us
```

#### MacOS Users

Open Terminal (Cmd + Space, type Terminal, press Enter). 

**Check Wi-Fi connection:**
```bash
ipconfig getifaddr en0
```

**Check Ethernet connection:**
```bash
ipconfig getifaddr en1
```

If an IPv4 address appears (e.g., 192.168.x.x), you are connected to IPv4. If no IPv4 address appears, proceed to disable IPv6.

#### Windows Users

Open Command Prompt (Win + R, type cmd, press Enter):
```cmd
ipconfig
```

Look for "IPv4 Address" under your active network. If no IPv4 address appears, proceed to enable IPv4.

### IPv6 Disable Instructions

#### MacOS - Disable IPv6

**For Wi-Fi:**
```bash
networksetup -setv6off Wi-Fi
```

**For Ethernet:**
```bash
networksetup -setv6off Ethernet
```

**For both networks:**
```bash
networksetup -setv6off Ethernet && networksetup -setv6off Wi-Fi
```

**To re-enable IPv6:**
```bash
networksetup -setv6automatic Wi-Fi && networksetup -setv6automatic Ethernet
```

#### Windows - Enable IPv4

1. Open Control Panel → Network and Sharing Center
2. Click "Change adapter settings" on the left
3. Right-click your active network (Wi-Fi or Ethernet) → Properties
4. Find "Internet Protocol Version 4 (TCP/IPv4)"
5. If unchecked, check the box and click OK

If IPv4 is enabled but still not working, try:
```cmd
ipconfig /release
ipconfig /renew
```

## 🚀 Getting Started

### Prerequisites

### Prerequisites

#### 1. Binance.US Account Setup
You will need a Binance.US account to utilize the trading bot. Follow the [Binance.US API Documentation](https://support.binance.us/en/articles/9842800-how-to-create-an-api-key-on-binance-us) to create your API keys.

**Important:** Save your Secret Key and API Key securely! You will only be able to view your secret key once.

#### 2. Python Environment
- Python 3.13+ required
- pip package manager

#### 3. Git (Optional)
For easy repository management, install [GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/ryanhlam1219/Crypto-Trading-Bot.git
cd Crypto-Trading-Bot
```

#### 2. Install Dependencies
```bash
# For macOS/Linux
python3 -m pip install --no-cache-dir -r requirements.txt

# For Windows
python -m pip install --no-cache-dir -r requirements.txt
```

#### 3. Configure Environment

**Option A: Automated Setup (Recommended)**
```bash
./setup.sh
```
This interactive script will:
- Copy `.env.example` to `.env`
- Prompt for your API credentials
- Help you choose the right trading mode
- Install dependencies automatically

**Validate Your Configuration:**
```bash
python3 validate_env.py
```
This script checks your `.env` file for common issues and validates your configuration.

**Option B: Manual Setup**

**Step 1: Copy the example environment file**
```bash
cp .env.example .env
```

**Step 2: Edit the .env file with your API credentials**
```bash
# Open .env in your favorite text editor
nano .env
# or
code .env
```

**Step 3: Replace placeholder values**
Update these fields in your `.env` file:
```env
# Replace with your actual Binance.US API credentials
API_KEY="your_actual_api_key_here"
API_SECRET="your_actual_secret_key_here"

# Choose your trading mode
MODE="backtest"  # Safe for testing
# MODE="trade"   # For live trading

# Choose your exchange
EXCHANGE="Binance"  # For live trading
# EXCHANGE="BinanceBacktestClient"  # For backtesting
# EXCHANGE="KrakenBacktestClient"   # For Kraken backtesting
```

**Available Exchanges:**
- **Live Trading**: `Binance` (requires real API keys)
- **Backtesting**: `BinanceBacktestClient`, `KrakenBacktestClient`
- **Test Mode**: `TestExchange` (live data, simulated trades)

**⚠️ Security Best Practices:**
- Never commit your `.env` file with real API keys to version control
- Use API keys with limited permissions (trading only, no withdrawals)
- Start with small amounts when live trading
- Keep your `.env` file secure and private

## 💡 Usage

### Basic Trading
Run with a specific trading pair:
```bash
python3 main.py BTC_USD
```

### Trading Modes
Configure your trading mode in the `.env` file:

**Test Mode (Backtesting):**
```env
TRADING_MODE="test"
```
- Runs backtests using historical data
- No real money involved
- Perfect for strategy testing and validation

**Live Trading Mode:**
```env
TRADING_MODE="real"
```
- Connects to live Binance.US API
- Uses real funds
- **Use with caution!**

### Performance Reports
After each trading session, the bot generates comprehensive performance reports including:
- Total trades executed and P&L analysis
- Win rate percentages and average profit per trade
- API performance metrics and response times
- Detailed trade history with entry/exit prices

## 🏗️ Project Structure

```
Crypto-Trading-Bot/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── .env                      # Environment configuration (create from .env.example)
├── .env.example              # Example environment configuration
├── setup.sh                  # Automated setup script
├── validate_env.py           # Configuration validation script
├── Utils/
│   └── MetricsCollector.py   # Performance tracking system
├── Exchanges/
│   ├── exchange.py           # Base exchange interface
│   ├── Live/
│   │   └── Binance.py       # Live Binance.US implementation
│   └── Test/
│       ├── BinanceBacktestClient.py  # Binance backtesting client
│       ├── KrakenBacktestClient.py   # Kraken backtesting client
│       └── testExchange.py           # Test exchange client
├── Strategies/
│   ├── Strategy.py          # Base strategy interface
│   └── GridTradingStrategy.py   # Grid trading implementation
└── Test/
    ├── StrategyWrapper.py   # Testing utilities
    └── DataFetchException.py   # Exception handling
```

## 📈 Supported Strategies

### Grid Trading Strategy
- Automated buy/sell orders at predetermined price levels
- Profits from market volatility within defined ranges
- Configurable grid spacing and position sizing
- Risk management with stop-loss capabilities

## 🔧 Configuration Options

Key configuration parameters in `.env`:
- `TRADING_MODE`: "test" or "real"
- `STRATEGY`: Trading strategy selection
- `EXCHANGE_NAME`: Exchange selection
- `INTERVAL`: Price update intervals

## 📋 Requirements

See `requirements.txt` for complete dependency list. Key packages include:
- `requests`: HTTP API communication
- `python-decouple`: Environment configuration
- `threading`: Concurrent operations
- Custom exchange and strategy modules

## ⚠️ Important Notes

- **Risk Warning**: Cryptocurrency trading involves significant financial risk
- **API Security**: Never commit your `.env` file with real API keys
- **Testing First**: Always test strategies thoroughly before live trading
- **IPv4 Required**: Ensure IPv4 connectivity for Binance.US API access
- **Monitoring**: Monitor bot performance and market conditions regularly

## 📚 Documentation

- [Metrics Documentation](METRICS_README.md) - Detailed performance tracking guide
- [Binance.US API Docs](https://docs.binance.us/) - Official API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚡ Quick Start

1. **Setup**: Create Binance.US account and generate API keys
2. **Install**: Clone repo and install dependencies
3. **Configure**: Update `.env` with your API keys
4. **Test**: Run in test mode first: `TRADING_MODE="test"`
5. **Trade**: When ready, switch to `TRADING_MODE="real"`

**Remember**: Start with small amounts and always understand the risks involved in cryptocurrency trading!

# Crypto Trading Bot

Advanced crypto trading bot written in Python with multi-exchange support, comprehensive testing framework, and real-time performance analytics.

## ✨ Key Features

- **Multi-Exchange Support**: Binance.US with extensible architecture
- **Grid Trading Strategy**: Automated buy/sell orders with profit optimization
- **Comprehensive Testing**: 85% test coverage with automated build system
- **Performance Analytics**: Real-time P&L tracking and trade analysis
- **Dual Modes**: Backtesting with historical data and live trading

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/ryanhlam1219/Crypto-Trading-Bot.git
cd Crypto-Trading-Bot

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Look for (.venv) in your prompt

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure
```bash
# Copy and edit configuration
cp .env.example .env
code .env  # Add your API keys for live trading

# Validate setup
python validate_env.py
```

### 3. Run
```bash
# Backtesting (safe, no real money)
python main.py BTC_USD

# Run tests
python -m pytest Tests/ -v

# Generate coverage reports
python build.py --coverage
```

## 💡 Basic Usage

### Virtual Environment
Always activate your virtual environment before working:
```bash
source .venv/bin/activate  # You should see (.venv) in your prompt
```

### Trading Modes
- **Backtest Mode**: Uses historical data, no real money involved
- **Live Trading**: Connects to real exchange APIs (requires API keys)

Configure in your `.env` file:
```env
MODE="backtest"  # Safe for testing
# MODE="trade"   # Live trading (use caution!)
```

### Development
```bash
# Run strategy tests
python -m pytest Tests/unit/strategies/ -v

# Check code coverage
python build.py --coverage

# Run all tests
python -m pytest Tests/ -v
```

## 📚 Comprehensive Documentation

**For detailed setup, configuration, and advanced usage:**

- 📖 **[Complete Documentation Hub](docs/README.md)** - Start here for full guides
- 🛠️ **[Detailed Setup Guide](docs/SETUP_GUIDE.md)** - Comprehensive setup with troubleshooting
- 🧪 **[Testing Framework](docs/TESTING.md)** - Testing best practices and coverage details
- 📊 **[Performance Metrics](docs/METRICS.md)** - Analytics and monitoring features
- 🔧 **[Build System](docs/BUILD_README.md)** - Automation and coverage tools

## 🎯 Project Status

- ✅ **GridTradingStrategy**: 85% test coverage (29 comprehensive tests)
- ✅ **Build System**: Automated testing and coverage reporting
- ✅ **Dependencies**: Consolidated requirements with virtual environment support
- ✅ **Documentation**: Organized guides in `docs/` folder

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite: `python -m pytest Tests/ -v`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## ⚠️ Disclaimer

This software is for educational and research purposes. Live trading involves real financial risk. Always:
- Test thoroughly with backtesting first
- Start with small amounts
- Use proper risk management
- Never invest more than you can afford to lose

---

📚 **Need help?** Check the [Documentation Hub](docs/README.md) for detailed guides and troubleshooting.
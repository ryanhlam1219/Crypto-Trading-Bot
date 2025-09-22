# Crypto Trading Bot

Advanced crypto trading bot written in Python with multi-exchange support, comprehensive testing framework, and real-time performance analytics.

## ✨ Key Features

- **Multi-Exchange Support**: Binance.US with extensible architecture and intelligent order validation
- **Multiple Trading Strategies**: Grid Trading and Simple Moving Average strategies
- **Smart Order Management**: Automatic price/quantity validation with exchange-specific filter compliance
- **Graceful Shutdown**: Ctrl+C signal handling for safe strategy termination
- **Comprehensive Testing**: 94%+ test coverage with automated build system
- **Performance Analytics**: Real-time P&L tracking and trade analysis with optimized MetricsCollector
- **Dual Modes**: TestExchange with live data + simulated trades, and full live trading
- **Extensible Architecture**: Abstract base classes for creating custom strategies

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
# Test Mode (recommended) - Live data with simulated trades
python main.py  # Uses TestExchange with real market data

# Backtesting (safe, historical data)
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

#### TestExchange Mode (Recommended for Development)
- **Real market data** from Binance API for accurate price feeds
- **Simulated trades** using Binance's test endpoint (no real money)
- **Full validation** including exchange filters and order requirements
- **Live price discovery** with actual market conditions

```env
MODE="trade"
TRADING_MODE="test"  # Uses TestExchange
ASSET="DOGE"         # Recommended for testing (lower price volatility)
CURRENCY="USD"
```

#### Backtest Mode
- Uses historical data, no real money involved
- Good for strategy validation with past market conditions

```env
MODE="backtest"
```

#### Live Trading Mode
- Connects to real exchange APIs with real money (use extreme caution!)

```env
MODE="trade"
TRADING_MODE="real"  # Real trading - requires valid API keys
```

### Available Strategies

#### 1. GridTradingStrategy (Default)
Automated grid trading with intelligent order management:

```env
STRATEGY="GridTradingStrategy"
ASSET="DOGE"           # Recommended - better filter compatibility than BTC
CURRENCY="USD"
```

**Key Features:**
- **Smart Grid Calculation**: Uses current market prices to avoid exchange filter rejections
- **Automatic Validation**: Price precision and minimum notional requirements handled automatically
- **Exchange Filter Compliance**: Supports PERCENT_PRICE_BY_SIDE, PRICE_FILTER, MIN_NOTIONAL filters
- **Asset-Specific Optimization**: Different tick sizes and minimums for BTC vs DOGE vs others
- **Comprehensive Logging**: Detailed order validation and adjustment reporting

**Supported Assets:**
- **DOGE/USD**: Recommended for testing (tick size: 0.00001, min notional: $10)
- **BTC/USD**: Higher value (tick size: 0.01, min notional: $10) 
- **Others**: Default validation (tick size: 0.0001, min notional: $10)

**Grid Strategy Notes:**
- Classical grid trading requires specific exchange filter compatibility
- Binance has strict price deviation limits that may conflict with traditional grid approaches
- TestExchange mode recommended for development and validation

#### 2. SimpleMovingAverageStrategy
Classic moving average crossover strategy for trend following:
```env
STRATEGY="SimpleMovingAverageStrategy"

# Optional SMA configuration (defaults shown)
SMA_SHORT_WINDOW=10     # Short moving average periods
SMA_LONG_WINDOW=20      # Long moving average periods  
SMA_MIN_CANDLES=50      # Minimum data before trading
SMA_TRADE_QUANTITY=1.0  # Trade size per order
```

**SMA Strategy Logic:**
- **Buy Signal**: Short MA crosses above Long MA (bullish crossover)
- **Sell Signal**: Short MA crosses below Long MA (bearish crossover)
- **Position Management**: Automatically closes opposing positions
- **Risk Management**: Built-in stop-loss and profit targets

### Creating Custom Strategies

The `SimpleMovingAverageStrategy` serves as an excellent reference for building your own strategies. Key implementation points:

```python
from Strategies.Strategy import Strategy

class MyCustomStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector, **kwargs):
        # Initialize base class (automatic signal handling setup)
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        # Add your custom parameters
    
    # Required abstract methods
    def execute_trade(self, price, direction): pass
    def close_trade(self, price): pass  
    def check_trades(self, price): pass
    def run_strategy(self, trade_interval): pass
    
    # Optional customization
    def on_shutdown_signal(self, signum, frame): pass
    def perform_graceful_shutdown(self): pass
```

**Benefits of inheriting from Strategy base class:**
- ✅ Automatic Ctrl+C signal handling
- ✅ Graceful shutdown with cleanup
- ✅ Consistent interface across all strategies
- ✅ Built-in metrics integration
- ✅ Thread-safe shutdown coordination

**Reference Implementation:** See `Strategies/SimpleMovingAverageStrategy.py` for a complete, production-ready example with:
- Parameter validation and error handling
- Comprehensive logging and status reporting
- Position management and trade execution
- Signal handling integration
- Full test coverage (28 unit tests)

### Graceful Shutdown
The trading strategy supports graceful shutdown via signal handling:

```bash
# Start the strategy
python main.py BTC_USD

# Press Ctrl+C for graceful shutdown
# The strategy will:
# 1. Stop accepting new trades
# 2. Display performance summary
# 3. Exit cleanly without data loss
```

**Signal Support:**
- `Ctrl+C` (SIGINT) - Graceful shutdown
- `SIGTERM` - Graceful shutdown (Linux/Unix)
- Automatic cleanup of resources and trade tracking

**Architecture:**
- Signal handling is managed by the trading strategy itself
- `main.py` no longer blocks or handles signals directly
- Clean separation of concerns between launcher and strategy

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
- 🎯 **[Strategy Development Guide](docs/SIGNAL_HANDLING_ARCHITECTURE.md)** - Creating custom strategies with signal handling

## 🎯 Project Status

- ✅ **GridTradingStrategy**: Enhanced with exchange filter compliance and smart order validation
- ✅ **SimpleMovingAverageStrategy**: 100% test coverage (28 tests) - Reference implementation
- ✅ **MetricsCollector**: Optimized with O(1) performance and bounded memory usage
- ✅ **Exchange Integration**: Smart validation for Binance price filters and order requirements
- ✅ **TestExchange**: Real market data with simulated trades for safe development
- ✅ **Abstract Strategy Architecture**: Signal handling and graceful shutdown for all strategies
- ✅ **Build System**: Automated testing and coverage reporting
- ✅ **Dependencies**: Consolidated requirements with virtual environment support
- ✅ **Documentation**: Organized guides in `docs/` folder with strategy development guide

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
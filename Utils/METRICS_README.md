# MetricsCollector

A centralized metrics collection system for the Crypto Trading Bot that provides comprehensive tracking of trading performance, exchange API metrics, and strategy analytics.

## Overview

The `MetricsCollector` is designed to centralize all metrics collection and reporting in one place, removing the need for individual strategies and exchanges to handle their own profit tracking and performance metrics. This creates a clean separation of concerns and provides a single source of truth for all trading metrics.

## Features

### 🎯 Trade Tracking
- **Unique Trade IDs**: Automatically generates unique identifiers for each trade
- **Entry/Exit Tracking**: Records precise entry and exit prices with timestamps
- **Profit/Loss Calculation**: Automatic P&L calculation for both BUY and SELL trades
- **Stop-Loss & Profit Targets**: Tracks stop-loss and profit target prices for each trade
- **Trade Status Management**: Manages trade lifecycle (active, closed, cancelled)

### 📊 Performance Analytics
- **Net Profit Percentage**: Calculates overall portfolio performance
- **Win Rate**: Tracks percentage of profitable trades
- **Average Profit Per Trade**: Measures average profit across all trades
- **Total P&L**: Sum of all realized profits and losses
- **Session Tracking**: Monitors trading session duration and activity

### 🌐 API Performance Monitoring
- **Response Time Tracking**: Measures API call latencies
- **Success Rate Monitoring**: Tracks API call success vs failure rates
- **Error Logging**: Records detailed error information for failed API calls
- **Endpoint Analytics**: Performance metrics per API endpoint

### 📈 Strategy Analytics
- **Signal Recording**: Tracks strategy signal generation and confidence levels
- **Strategy Performance**: Per-strategy performance metrics
- **Signal Metadata**: Extensible metadata tracking for strategy signals

## Architecture

### Core Components

```
MetricsCollector
├── Trade Tracking
│   ├── active_trades[]
│   ├── closed_trades[]
│   └── cancelled_trades[]
├── API Metrics
│   ├── api_calls[]
│   └── api_errors[]
├── Strategy Metrics
│   └── strategy_signals[]
└── Session Tracking
    ├── session_start_time
    └── total_trades_executed
```

### Integration Points

The MetricsCollector integrates with:

1. **Exchange Classes**: Tracks API performance and order execution
2. **Strategy Classes**: Records trade entries/exits and strategy signals
3. **Main Application**: Provides centralized initialization and reporting

## Usage

### Basic Setup

```python
from MetricsCollector import MetricsCollector

# Create a metrics collector instance
metrics = MetricsCollector()

# Inject into exchange and strategy
exchange = BinanceClient(api_key, api_secret, currency, asset, metrics)
strategy = GridTradingStrategy(exchange, interval, stop_loss, metrics)
```

### Recording Trades

```python
# Record trade entry
trade = metrics.record_trade_entry(
    trade_id="trade_001",
    symbol="BTCUSD",
    direction="BUY",
    entry_price=50000.0,
    quantity=1.0,
    stop_loss=49000.0,
    profit_target=51000.0,
    strategy_name="GridTradingStrategy"
)

# Record trade exit
closed_trade = metrics.record_trade_exit(
    trade_id="trade_001",
    exit_price=51000.0,
    reason="profit_target"
)
```

### API Performance Tracking

```python
# Record successful API call
metrics.record_api_call(
    endpoint="/api/v3/order",
    method="POST",
    response_time=0.125,
    status_code=200,
    success=True
)

# Record failed API call
metrics.record_api_call(
    endpoint="/api/v3/order",
    method="POST",
    response_time=2.5,
    status_code=500,
    success=False,
    error_message="Internal server error"
)
```

### Strategy Signal Recording

```python
# Record strategy signal
metrics.record_strategy_signal(
    strategy_name="GridTradingStrategy",
    signal_type="BUY",
    symbol="BTCUSD",
    price=50000.0,
    confidence=0.85,
    metadata={"grid_level": 2, "trend": "bullish"}
)
```

### Generating Reports

```python
# Get comprehensive performance report
report = metrics.generate_performance_report()
print(report)

# Get specific metrics
profit_percentage = metrics.calculate_net_profit_percentage()
win_rate = metrics.calculate_win_rate()
api_stats = metrics.get_api_performance_stats()
```

## API Reference

### Trade Management

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `record_trade_entry()` | Records a new trade entry | trade_id, symbol, direction, entry_price, quantity, stop_loss, profit_target, strategy_name | Dict containing trade record |
| `record_trade_exit()` | Records trade exit and calculates P&L | trade_id, exit_price, reason | Dict containing closed trade record |
| `close_all_active_trades()` | Closes all active trades at specified price | exit_price, reason | None |

### Performance Calculations

| Method | Description | Returns |
|--------|-------------|---------|
| `calculate_total_profit_loss()` | Sum of all realized P&L | float |
| `calculate_net_profit_percentage()` | Net profit as percentage of capital deployed | float |
| `calculate_win_rate()` | Percentage of profitable trades | float |
| `calculate_average_profit_per_trade()` | Average profit per closed trade | float |

### API Monitoring

| Method | Description | Parameters |
|--------|-------------|------------|
| `record_api_call()` | Records API call metrics | endpoint, method, response_time, status_code, success, error_message |
| `get_api_performance_stats()` | Returns API performance summary | None |

### Reporting

| Method | Description | Returns |
|--------|-------------|---------|
| `generate_performance_report()` | Creates comprehensive performance report | Formatted string report |

## Sample Output

### Performance Report Example

```
============================================================
🚀 TRADING BOT PERFORMANCE REPORT
============================================================
Session Duration: 2:34:15.123456
Total Trades Executed: 24

📊 TRADING PERFORMANCE:
  • Active Trades: 2
  • Closed Trades: 22
  • Total P&L: $1,247.83
  • Net Profit %: 12.48%
  • Win Rate: 68.18%
  • Avg Profit/Trade: $56.72

🌐 API PERFORMANCE:
  • Total API Calls: 156
  • Success Rate: 98.72%
  • Avg Response Time: 0.142s
  • Total Errors: 2

💼 RECENT CLOSED TRADES:
  Trade ID | Symbol | Direction | Entry $ | Exit $ | P&L $ | P&L %
  abc12345 | BTCUSD | BUY | $49500.00 | $50250.00 | $750.00 | 1.52%
  def67890 | BTCUSD | SELL | $50800.00 | $50200.00 | $600.00 | 1.18%
  ghi11111 | BTCUSD | BUY | $49800.00 | $49200.00 | -$600.00 | -1.20%
============================================================
```

## Integration with Existing Codebase

### Before (GridTradingStrategy)
```python
class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage):
        self.active_trades = []  # Manual tracking
        self.closed_trades = []  # Manual tracking
    
    def calculate_net_profit(self):
        # Manual profit calculation
        return sum(trade["profit"] for trade in self.closed_trades)
```

### After (GridTradingStrategy with MetricsCollector)
```python
class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector):
        self.metrics_collector = metrics_collector  # Centralized tracking
    
    # No manual profit calculation needed
    # All metrics handled by MetricsCollector
```

## Error Handling

The MetricsCollector includes robust error handling:

- **Trade Not Found**: Returns `None` if attempting to close non-existent trade
- **Invalid Parameters**: Validates input parameters and provides clear error messages
- **API Errors**: Gracefully handles and logs API failures without disrupting trading
- **Data Consistency**: Ensures trade state consistency across operations

## Thread Safety

⚠️ **Note**: The current implementation is not thread-safe. If using in a multi-threaded environment, consider adding appropriate locking mechanisms.

## Future Enhancements

### Planned Features
- [ ] **Database Integration**: Persistent storage for metrics
- [ ] **Real-time Dashboards**: Web-based performance monitoring
- [ ] **Risk Metrics**: Drawdown, Sharpe ratio, and other risk indicators
- [ ] **Portfolio Analytics**: Multi-asset portfolio performance tracking
- [ ] **Alert System**: Configurable performance alerts and notifications
- [ ] **Export Functions**: CSV/JSON export for external analysis

### Extensibility

The MetricsCollector is designed for extensibility:

```python
# Custom metadata for trades
metadata = {
    "market_condition": "volatile",
    "rsi_level": 65.4,
    "volume_spike": True
}

metrics.record_trade_entry(..., metadata=metadata)
```

## Contributing

When extending the MetricsCollector:

1. **Maintain Separation of Concerns**: Keep metrics collection separate from trading logic
2. **Follow Naming Conventions**: Use descriptive method and variable names
3. **Add Documentation**: Document all new methods and parameters
4. **Include Error Handling**: Ensure robust error handling for new features
5. **Test Thoroughly**: Test new features with various scenarios

## Dependencies

- `datetime`: For timestamp management
- `typing`: For type hints and better code documentation
- `enum`: For trade status and direction enums

## License

This MetricsCollector is part of the Crypto Trading Bot project and follows the same license terms.
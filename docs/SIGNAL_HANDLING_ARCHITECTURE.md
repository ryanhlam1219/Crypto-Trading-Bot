# Signal Handling Architecture

This document describes the abstract signal handling system implemented in the Crypto Trading Bot, providing graceful shutdown capabilities across all trading strategies.

## Overview

The signal handling architecture provides:
- **Consistent Ctrl+C (SIGINT) handling** across all strategy implementations
- **Graceful shutdown** with proper resource cleanup
- **Abstract base class design** ensuring all strategies have signal handling
- **Strategy-specific customization** while maintaining consistent behavior
- **Comprehensive test coverage** for reliability

## Architecture Components

### 1. Abstract Strategy Base Class (`Strategies/Strategy.py`)

The `Strategy` abstract base class provides the foundation for all trading strategies:

```python
from abc import ABC, abstractmethod
import signal

class Strategy(ABC):
    """Abstract base class for all trading strategies with signal handling."""
    
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector):
        # Common initialization
        self.client = client
        self.interval = interval
        self.stop_loss_percentage = stop_loss_percentage
        self.metrics_collector = metrics_collector
        
        # Signal handling setup
        self.shutdown_requested = False
        self._setup_signal_handlers()
```

#### Key Features:

- **Automatic signal handling setup** during initialization
- **Thread-safe shutdown flag** (`shutdown_requested`)
- **Consistent signal processing** for SIGINT and SIGTERM
- **Abstract methods** enforcing implementation requirements

#### Required Abstract Methods:

All strategy implementations must provide:

```python
@abstractmethod
def execute_trade(self, price, direction):
    """Execute a trade at the given price and direction."""
    pass

@abstractmethod
def close_trade(self, price):
    """Close the current position."""
    pass

@abstractmethod
def check_trades(self, price):
    """Check current price and execute trades based on strategy logic."""
    pass

@abstractmethod
def run_strategy(self, trade_interval):
    """Run the strategy main loop."""
    pass
```

#### Optional Override Methods:

Strategies can customize these behaviors:

```python
def on_shutdown_signal(self, signum, frame):
    """Strategy-specific signal handling logic."""
    pass

def perform_graceful_shutdown(self):
    """Strategy-specific shutdown operations."""
    pass
```

### 2. GridTradingStrategy Implementation (`Strategies/GridTradingStrategy.py`)

The grid trading strategy demonstrates how to use the abstract base class:

```python
class GridTradingStrategy(Strategy):
    """Grid trading strategy with inherited signal handling."""
    
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector, 
                 grid_size, num_grids, grid_spacing_percentage):
        # Initialize base class (sets up signal handling)
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        
        # Strategy-specific initialization
        self.grid_size = grid_size
        self.num_grids = num_grids
        self.grid_spacing_percentage = grid_spacing_percentage
        # ... other initialization
```

#### Key Implementation Details:

- **Inherits signal handling** from base class automatically
- **Uses `is_shutdown_requested()`** in main loop for graceful exit
- **Overrides shutdown methods** for strategy-specific cleanup
- **Maintains backward compatibility** with existing code

### 3. Signal Handling Flow

```
1. Strategy Initialization
   ├── Base class __init__() called
   ├── Signal handlers registered (SIGINT, SIGTERM)
   └── shutdown_requested flag initialized

2. Strategy Execution
   ├── run_strategy() starts main loop
   ├── Loop checks is_shutdown_requested() each iteration
   └── Continues until shutdown requested

3. Signal Reception (Ctrl+C)
   ├── Signal handler (_signal_handler) called
   ├── shutdown_requested flag set to True
   ├── on_shutdown_signal() called for strategy customization
   └── Loop exits on next iteration

4. Graceful Shutdown
   ├── perform_graceful_shutdown() called
   ├── Strategy-specific cleanup performed
   ├── Base class cleanup performed
   └── Program exits cleanly
```

## Usage Examples

### Creating a New Strategy

```python
from Strategies.Strategy import Strategy
from Strategies.ExchangeModels import TradeDirection, OrderType

class MyCustomStrategy(Strategy):
    """Custom strategy with automatic signal handling."""
    
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector, custom_param):
        # Initialize base class (sets up signal handling)
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        self.custom_param = custom_param
    
    def execute_trade(self, price, direction):
        """Implement trade execution logic."""
        # Your trade logic here
        pass
    
    def close_trade(self, price):
        """Implement position closing logic."""
        # Your close logic here
        pass
    
    def check_trades(self, price):
        """Implement strategy logic."""
        # Your strategy logic here
        pass
    
    def run_strategy(self, trade_interval):
        """Main strategy loop with signal handling."""
        try:
            print("Starting custom strategy...")
            
            # Main loop with shutdown check
            while not self.is_shutdown_requested():
                # Your strategy logic here
                current_price = self.client.get_current_price()
                self.check_trades(current_price)
                
                time.sleep(trade_interval)
            
            # Graceful shutdown
            self.perform_graceful_shutdown()
            
        except Exception as e:
            print(f"Error in strategy: {e}")
            self.perform_graceful_shutdown()
    
    def on_shutdown_signal(self, signum, frame):
        """Custom shutdown signal handling."""
        print("Custom strategy received shutdown signal")
        # Close any open positions, save state, etc.
    
    def perform_graceful_shutdown(self):
        """Custom graceful shutdown operations."""
        print("Performing custom strategy shutdown...")
        
        # Custom cleanup logic here
        
        # Call parent class shutdown
        super().perform_graceful_shutdown()
```

### Using the Strategy

```python
from MyCustomStrategy import MyCustomStrategy
from Exchanges.Live.Binance import Binance
from Utils.MetricsCollector import MetricsCollector

# Create client and metrics collector
client = Binance()
metrics_collector = MetricsCollector()

# Create strategy (signal handling automatically set up)
strategy = MyCustomStrategy(
    client=client,
    interval=60,
    stop_loss_percentage=3,
    metrics_collector=metrics_collector,
    custom_param="example"
)

# Run strategy (will handle Ctrl+C gracefully)
strategy.run_strategy(trade_interval=30)
```

## Testing

The signal handling system includes comprehensive test coverage:

### Test Files:
- `Tests/unit/strategies/test_grid_trading_strategy_signals.py`

### Test Coverage:
- **Abstract base class functionality** - Ensures proper interface enforcement
- **Signal handler registration** - Verifies SIGINT/SIGTERM handling
- **Shutdown flag management** - Tests programmatic and signal-based shutdown
- **Inheritance behavior** - Confirms derived classes inherit signal handling
- **Override functionality** - Tests custom signal handling implementations
- **Integration testing** - Verifies base and derived class cooperation

### Running Tests:

```bash
# Run all signal handling tests
python -m pytest Tests/unit/strategies/test_grid_trading_strategy_signals.py -v

# Run with coverage
python -m pytest Tests/unit/strategies/test_grid_trading_strategy_signals.py --cov=Strategies --cov-report=html
```

## Benefits

### 1. Consistency
- All strategies have identical signal handling behavior
- Uniform user experience across different strategy types
- Consistent shutdown procedures and messaging

### 2. Reliability
- Comprehensive test coverage ensures robustness
- Graceful shutdown prevents data loss or corruption
- Proper resource cleanup prevents memory leaks

### 3. Maintainability
- Abstract base class enforces consistent interfaces
- Signal handling logic centralized in one location
- Easy to extend with new strategy types

### 4. Developer Experience
- Simple inheritance model - just extend Strategy class
- Automatic signal handling setup - no manual configuration
- Clear override points for customization

## Migration Guide

### From GridTradingStrategy without Signal Handling

**Before:**
```python
class GridTradingStrategy:
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector):
        self.client = client
        # ... other initialization
    
    def run_strategy(self, trade_interval):
        while True:  # Infinite loop
            # Strategy logic
            time.sleep(trade_interval)
```

**After:**
```python
class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector):
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        # ... other initialization
    
    def run_strategy(self, trade_interval):
        while not self.is_shutdown_requested():  # Check shutdown flag
            # Strategy logic
            time.sleep(trade_interval)
        
        self.perform_graceful_shutdown()  # Clean shutdown
```

### From main.py with Signal Handling

**Before:**
```python
import signal
import threading

def signal_handler(signum, frame):
    print("Shutting down...")
    shutdown_event.set()

shutdown_event = threading.Event()
signal.signal(signal.SIGINT, signal_handler)

strategy = GridTradingStrategy(...)
strategy.run_strategy(30)

shutdown_event.wait()  # Wait for signal
```

**After:**
```python
# No signal handling needed in main.py
strategy = GridTradingStrategy(...)
strategy.run_strategy(30)  # Handles signals internally
```

## Future Enhancements

### Planned Features:
1. **Configuration-based timeouts** for shutdown operations
2. **Signal handling metrics** and monitoring
3. **Strategy state persistence** during shutdown
4. **Multi-strategy orchestration** with coordinated shutdown
5. **Health check integration** with signal handling

### Extensibility:
- Additional signal types (SIGUSR1, SIGUSR2) for runtime configuration
- Remote shutdown via API endpoints
- Strategy pause/resume functionality
- Dynamic strategy parameter updates

## Conclusion

The abstract signal handling architecture provides a robust, consistent, and maintainable foundation for all trading strategies in the Crypto Trading Bot. By centralizing signal handling in the abstract base class, we ensure that:

- All strategies behave consistently when receiving shutdown signals
- Developers can focus on strategy logic rather than infrastructure concerns
- The system remains reliable and testable
- Future enhancements can be applied across all strategies simultaneously

This architecture supports the project's goals of reliability, maintainability, and developer productivity while providing users with a consistent and predictable experience.
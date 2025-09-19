#!/usr/bin/python3
import sys
import threading
import importlib
import os
from decouple import config

# Add current directory and utils to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'utils'))

# Local imports
import Exchanges
from Tests.utils import StrategyWrapper
from Utils.MetricsCollector import MetricsCollector

# Constants for configuration keys
EXCHANGE_NAME = "exchange_name"
AVAILABLE_EXCHANGES = "available_exchanges"
MODE = "mode"
STRATEGY = "strategy"
TRADING_MODE = "trading_mode"
INTERVAL = "interval"
CURRENCY = "currency"
ASSET = "asset"
API_KEY = "key"
API_SECRET = "secret"
TRADE_INTERVAL = "trade_interval"
TEST_DATA_DIRECTORY = "Tests/data"

def load_configuration():
    """Loads configuration from environment variables."""
    return {
        EXCHANGE_NAME: config('EXCHANGE'),
        AVAILABLE_EXCHANGES: config('AVAILABLE_EXCHANGES').split(','),
        MODE: config('MODE'),
        STRATEGY: config('STRATEGY'),
        TRADING_MODE: config('TRADING_MODE'),
        INTERVAL: int(config('CANDLE_INTERVAL')),
        CURRENCY: config('CURRENCY'),
        ASSET: config('ASSET'),
        API_KEY: config('API_KEY'),
        API_SECRET: config('API_SECRET'),
        TRADE_INTERVAL: config('TRADE_INTERVAL')
    }

def handle_cli_arguments(currency, asset):
    """Handles CLI arguments for currency/asset pair."""
    if len(sys.argv) > 1:
        currencies = sys.argv[1].split('_')
        if len(currencies) > 1:
            print(f'Using Currency and Asset: [{currencies[0]}, {currencies[1]}]')
            return currencies[0], currencies[1]
        else:
            raise ValueError(f"Invalid keyboard input when executing bot: '{sys.argv[1]}'")
    else:
        print(f"No system arguments used: defaulting to config currency={currency}, asset={asset}")
        return currency, asset

def initialize_exchange_client(exchange_name, key, secret, currency, asset, metrics_collector):
    """Dynamically imports and initializes the exchange client."""
    if exchange_name.endswith("BacktestClient"):
        # Backtest clients
        exchange_module = importlib.import_module(f"Exchanges.Test.{exchange_name}")
    elif exchange_name == "TestExchange":
        # Test exchange - file name is TestExchange.py and class is TestExchange
        exchange_module = importlib.import_module("Exchanges.Test.TestExchange")
    else:
        # Live clients
        exchange_module = importlib.import_module(f"Exchanges.Live.{exchange_name}")
    exchange_class = getattr(exchange_module, exchange_name)
    return exchange_class(key, secret, currency, asset, metrics_collector)

def initialize_strategy(strategy_name, client, interval, metrics_collector):
    """Dynamically imports and initializes the strategy."""
    print(f"Using {strategy_name} to determine trades")
    strategy_module = importlib.import_module(f"Strategies.{strategy_name}")
    strategy_class = getattr(strategy_module, strategy_name)
    
    # Initialize strategy with appropriate parameters based on strategy type
    if strategy_name == "SimpleMovingAverageStrategy":
        # SMA strategy with default parameters (can be customized via environment variables)
        short_window = int(config('SMA_SHORT_WINDOW', default=10))
        long_window = int(config('SMA_LONG_WINDOW', default=20))
        min_candles = int(config('SMA_MIN_CANDLES', default=50))
        trade_quantity = float(config('SMA_TRADE_QUANTITY', default=1.0))
        
        return strategy_class(
            client=client, 
            interval=interval, 
            stop_loss_percentage=5, 
            metrics_collector=metrics_collector,
            short_window=short_window,
            long_window=long_window,
            min_candles=min_candles,
            trade_quantity=trade_quantity
        )
    else:
        # Default initialization for other strategies (e.g., GridTradingStrategy)
        return strategy_class(client, interval, 5, metrics_collector)

def run_trading_mode(config):
    """Runs the bot in real trading mode."""
    # Create metrics collector
    metrics_collector = MetricsCollector()
    
    # Handle CLI arguments
    currency, asset = handle_cli_arguments(config["currency"], config["asset"])
    if config[TRADING_MODE] == "real": 
        print("*** Caution: Real trading mode activated ***")
        print(f"Connecting to {config['exchange_name']} exchange...")
        # Initialize Exchange Client
        client = initialize_exchange_client(config["exchange_name"], config["key"], config["secret"], currency, asset, metrics_collector)
    elif config[TRADING_MODE] == "test":
        print("*** Live Testing Mode Enabled ***")
        print("Using Test Binance Client for strategy testing...")
        client = Exchanges.TestExchange(config[API_KEY], config[API_SECRET], currency, asset, metrics_collector)

    # Initialize and run the strategy
    strategy_instance = initialize_strategy(config[STRATEGY], client, config[INTERVAL], metrics_collector)
    
    print("🚀 Starting trading strategy...")
    print("   Strategy will handle its own execution loop and signal management")
    strategy_instance.run_strategy(int(config[TRADE_INTERVAL]))
    
    print("✅ Trading strategy completed execution")

def run_test_mode(config):
    """Runs the bot in test mode."""
    # Create metrics collector
    metrics_collector = MetricsCollector()

    # Connect to Test Client
    print("BackTest mode enabled...")
    print(f"Using {config[EXCHANGE_NAME]} for collecting data...")
    currency, asset = handle_cli_arguments(config[CURRENCY], config[ASSET])
    TestClient = initialize_exchange_client(config[EXCHANGE_NAME], config[API_KEY], config[API_SECRET], currency, asset, metrics_collector)

    # Collect Historical Data
    yearsPast = 1
    print(f"Writing Historical Data for past {yearsPast} year(s) with interval of {config[INTERVAL]} minutes")
    historicalData = TestClient.get_historical_candle_stick_data(config[INTERVAL], yearsPast)
    TestClient.write_candlestick_to_csv(historicalData, f"{TEST_DATA_DIRECTORY}/past-{yearsPast}-years-historical-data-{currency}{asset}.csv")
    
    # Initialize Strategy and Strategy Wrapper
    strategy_instance = initialize_strategy(config[STRATEGY], TestClient, config[INTERVAL], metrics_collector)
    strategy_wrapper = StrategyWrapper(strategy_instance)

    # Execute the Backtest
    strategy_wrapper.run_strategy()


if __name__ == "__main__":
    # Load configuration
    config_data = load_configuration()

    print("🤖 Crypto Trading Bot Starting...")
    print("📝 Note: Signal handling is now managed by the trading strategy")
    print("   Press Ctrl+C during strategy execution for graceful shutdown")
    print()

    if config_data[MODE] == "backtest":
        run_test_mode(config_data)
    elif config_data[MODE] == "trade":
        run_trading_mode(config_data)
    else:
        raise ValueError(f'Incorrect Mode value provided in .env: {config_data[MODE]}')
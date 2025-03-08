#!/usr/bin/python3
import signal
import sys
import threading
import importlib
from decouple import config

# Local imports
import Exchanges
import Test

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
TEST_DATA_DIRECTORY = "Test/HistoricalData"

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

def signal_handler(signal, frame):
    """Handles termination signals like Ctrl+C."""
    print("\nStopping client...")
    sys.exit(0)

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

def initialize_exchange_client(exchange_name, key, secret, currency, asset):
    """Dynamically imports and initializes the exchange client."""
    exchange_module = importlib.import_module(f"Exchanges.{exchange_name}")
    exchange_class = getattr(exchange_module, exchange_name)
    return exchange_class(key, secret, currency, asset)

def initialize_strategy(strategy_name, client, interval):
    """Dynamically imports and initializes the strategy."""
    strategy_module = importlib.import_module(f"Strategies.{strategy_name}")
    strategy_class = getattr(strategy_module, strategy_name)
    return strategy_class(client, interval, 5)

def run_trading_mode(config):
    """Runs the bot in real trading mode."""
    # Handle CLI arguments
    currency, asset = handle_cli_arguments(config["currency"], config["asset"])
    if config[TRADING_MODE] == "real": 
        print("*** Caution: Real trading mode activated ***")
        print(f"Connecting to {config['exchange_name']} exchange...")
        # Initialize Exchange Client
        client = initialize_exchange_client(config["exchange_name"], config["key"], config["secret"], currency, asset)
    elif config[TRADING_MODE] == "test":
        print("*** Live Testing Mode Enabled ***")
        print("Using Test Binance Client for strategy testing...")
        client = Exchanges.TestExchange(config[API_KEY], config[API_SECRET], currency, asset)

    # Initialize and run the strategy
    strategy_instance = initialize_strategy(config[STRATEGY], client, config[INTERVAL])
    strategy_instance.run_strategy(int(config[TRADE_INTERVAL]))

    # Keep script running
    threading.Event().wait()

def run_test_mode(config):
    """Runs the bot in test mode."""

    # Connect to Test Client
    print("BackTest mode enabled...")
    print(f"Using {config[EXCHANGE_NAME]}BacktestClient for collecting data...")
    currency, asset = handle_cli_arguments(config[CURRENCY], config[ASSET])
    TestClient = initialize_exchange_client(f"{config[EXCHANGE_NAME]}BacktestClient", config[API_KEY], config[API_SECRET], currency, asset)

    # Collect Historical Data
    yearsPast = 1
    print(f"Writing Historical Data for past {yearsPast} year(s) with interval of {config[INTERVAL]} minutes")
    historicalData = TestClient.get_historical_candle_stick_data(config[INTERVAL], yearsPast)
    TestClient.write_candlestick_to_csv(historicalData, f"{TEST_DATA_DIRECTORY}/past-{yearsPast}-years-historical-data-{currency}{asset}.csv")
    
    # Initialize Strategy and Strategy Wrapper
    strategy_instance = initialize_strategy(config[STRATEGY], TestClient, config[INTERVAL])
    strategy_wrapper = Test.StrategyWrapper(strategy_instance)

    # Execute the Backtest
    strategy_wrapper.run_strategy()


if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Load configuration
    config_data = load_configuration()

    if config_data[MODE] == "backtest":
        run_test_mode(config_data)
    elif config_data[MODE] == "trade":
        run_trading_mode(config_data)
    else:
        raise ValueError(f'Incorrect Mode value provided in .env: {config_data[MODE]}')
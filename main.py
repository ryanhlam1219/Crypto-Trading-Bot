#!/usr/bin/python3
import signal
import sys
import threading
import importlib

# Local imports
import Strategies
import Exchanges
import BackTest.ExecuteDataCleaning as testScript  # TODO: Remove for cleaner code

from decouple import config

# Load configuration
exchange_name = config('EXCHANGE')
available_exchanges = config('AVAILABLE_EXCHANGES').split(',')
mode: str = config('MODE')
strategy: str = config('STRATEGY')
trading_mode: str = config('TRADING_MODE')
interval: int = int(config('CANDLE_INTERVAL'))
currency: str = config('CURRENCY')
asset: str = config('ASSET')
key: str = config('BINANCE_API_KEY')
secret: str = config('BINANCE_API_SECRET')

def signal_handler(signal, frame):
    """Handles termination signals like Ctrl+C."""
    print("\nStopping client...")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

if trading_mode == 'real':
    try:
        print("*** Caution: Real trading mode activated ***")

        # Load exchange
        exchange = exchange_name.capitalize()
        print(f"Connecting to {exchange} exchange...")

        # Handle CLI arguments for currency/asset pair
        if len(sys.argv) > 1:
            currencies = sys.argv[1].split('_')
            if len(currencies) > 1:
                currency, asset = currencies
            else:
                raise ValueError(f"Invalid keyboard input when executing bot: '{sys.argv[1]}'")
        else:
            print(f"No system arguments used: defaulting to config currency={currency}, asset={asset}")

        # Create Client for connecting to Exchange APIs
        exchange_module = importlib.import_module(f"Exchanges.{exchange}")
        exchange_class = getattr(exchange_module, exchange)
        client = exchange_class(key, secret, currency, asset)

        # Connect Strategy with Exchange Client
        strategy_module = importlib.import_module(f"Strategies.{strategy}")
        strategy_class = getattr(strategy_module, strategy)

        # Instantiate and run the strategy
        strategy_instance = strategy_class(client, interval, 5)
        strategy_instance.run_strategy()

        # Keep script running
        threading.Event().wait()

    except (ModuleNotFoundError, AttributeError) as e:
        print(f"Error: Strategy '{strategy}' not found. Check configuration and imports.")
        sys.exit(1)
    
    except ValueError as e:
        print(f"Value Error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

# Test Trading Mode
else:
    print("Test mode enabled...")
    testScript.executeScript()

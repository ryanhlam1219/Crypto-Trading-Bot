#!/usr/bin/python3
import signal
import sys
import threading
import importlib

# local imports
import Strategies
import Exchanges
# TODO:remove this import for cleaner code
import BackTest.ExecuteDataCleaning as testScript

from decouple import config

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

if trading_mode == 'real':
    print("*** Caution: Real trading mode activated ***")
    # Load exchange
    exchange = (exchange_name[0].upper() + exchange_name[1:])
    print(f"Connecting to {exchange} exchange...")

    if len(sys.argv) > 1:
        currencies = sys.argv[1].split('_')
        if len(currencies) > 1:
            currency = currencies[0]
            asset = currencies[1]
        else: 
            raise ValueError(f"invalid keyboard inputs when executing bot '{sys.argv[1]}'")

    else:
        print(f"No System Arguments used: defaulting to Config currency: {currency} and asset: {asset}")    

    ## Connect to Exchange
    exchange_module = importlib.import_module(f"Exchanges.{exchange}")
    exchange_class = getattr(exchange_module, exchange)
    client = exchange_class(key, secret, currency, asset)

    ### Execute Trading Strategy
    # Dynamically load the correct strategy
    try:
        strategy_module = importlib.import_module(f"Strategies.{strategy}")
        strategy_class = getattr(strategy_module, strategy)
    except (ModuleNotFoundError, AttributeError) as e:
        raise ValueError(f"Strategy {strategy} not found. Check configuration and imports.") from e

    # Instantiate and run the strategy
    strategy_instance = strategy_class()
    strategy_instance.run_strategy(client)

    def signal_handler(signal, frame):
            print('\nstopping client...')
            sys.exit(0)

    # Listen for keyboard interrupt event
    signal.signal(signal.SIGINT, signal_handler)
    forever = threading.Event()
    forever.wait()
    sys.exit(0)

#Test Trading Mode
else:
    print("Test mode enabled...")
    testScript.executeScript()

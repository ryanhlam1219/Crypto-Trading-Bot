#!/usr/bin/python3

#import importlib
import signal
import sys
import threading

#TODO:remove this import for cleaner code
import Exchanges.Binance as Client
import BackTest.ExecuteDataGathering as testScript

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
else:
    print("Test mode")
    testScript.executeScript()

if len(sys.argv) > 1:
    currencies = sys.argv[1].split('_')
    if len(currencies) > 1:
        currency = currencies[0]
        asset = currencies[1]

# Load exchange
print("Connecting to {} exchange...".format(exchange_name[0].upper() + exchange_name[1:]))
client = Client.Binance(key,secret)
if(client.getConnectivityStatus()):
    print("Connected.")
else:
    print("Could not establish connection to {} exchange...".format(exchange_name[0].upper() + exchange_name[1:]))

client.getAccountStatus()
client.getCandleStickData('BTCUSD')

def signal_handler(signal, frame):
        print('\nstopping client...')
        sys.exit(0)

# Listen for keyboard interrupt event
signal.signal(signal.SIGINT, signal_handler)
forever = threading.Event()
forever.wait()
sys.exit(0)

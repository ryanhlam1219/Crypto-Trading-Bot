# Base Exchange Class
from .exchange import Exchange

# Live Exchange Implementations
from .Live.Binance import Binance

# Test/Backtest Exchange Implementations
from .Test.BinanceBacktestClient import BinanceBacktestClient
from .Test.KrakenBacktestClient import KrakenBackTestClient
from .Test.testExchange import TestExchange

# If you add more exchanges
#from .Live.OtherExchange import OtherExchange
#from .Test.OtherBacktestClient import OtherBacktestClient
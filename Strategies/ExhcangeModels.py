from enum import Enum

class OrderType(Enum):
    """Enum representing different order types supported by Binance API."""
    MARKET_ORDER = "MARKET_ORDER"
    LIMIT_ORDER = "LIMIT_ORDER"
    STOP_LIMIT_ORDER = "STOP_LOSS_LIMIT"
    TAKE_PROFIT_LIMIT_ORDER = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER_ORDER = "LIMIT_MAKER"

class TradeDirection(Enum):
    """Enum representing possible trade directions."""
    BUY = "BUY"
    SELL = "SELL"

from typing import List

from typing import List  # Importing List for type hinting

class CandleStickData:
    def __init__(
        self,
        open_time: int,  # Timestamp when the candlestick opens
        open_price: float,  # Price at which the candlestick opens
        high_price: float,  # Highest price during the candlestick period
        low_price: float,  # Lowest price during the candlestick period
        close_price: float,  # Price at which the candlestick closes
        volume: float,  # Amount of asset traded during the candlestick period
        close_time: int,  # Timestamp when the candlestick closes
        quote_asset_volume: float,  # Volume in quote asset
        num_trades: int,  # Number of trades executed during the candlestick period
        taker_buy_base_asset_volume: float,  # Volume of the asset bought by takers
        taker_buy_quote_asset_volume: float  # Quote asset volume bought by takers
    ):
        # Initializing instance variables
        self.open_time = open_time
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.close_time = close_time
        self.quote_asset_volume = quote_asset_volume
        self.num_trades = num_trades
        self.taker_buy_base_asset_volume = taker_buy_base_asset_volume
        self.taker_buy_quote_asset_volume = taker_buy_quote_asset_volume
    
    @classmethod
    def from_list(cls, data: List):  # Accepts a list of data and converts it into an instance
        return cls(
            open_time=data[0],
            open_price=float(data[1]),
            high_price=float(data[2]),
            low_price=float(data[3]),
            close_price=float(data[4]),
            volume=float(data[5]),
            close_time=data[6],
            quote_asset_volume=float(data[7]),
            num_trades=int(data[8]),
            taker_buy_base_asset_volume=float(data[9]),
            taker_buy_quote_asset_volume=float(data[10])
        )
    
    def __repr__(self):  # Returns a string representation of the object for debugging
        return (
            f"BinanceCandle(open_time={self.open_time}, open_price={self.open_price}, high_price={self.high_price}, "
            f"low_price={self.low_price}, close_price={self.close_price}, volume={self.volume}, close_time={self.close_time}, "
            f"quote_asset_volume={self.quote_asset_volume}, num_trades={self.num_trades}, "
            f"taker_buy_base_asset_volume={self.taker_buy_base_asset_volume}, taker_buy_quote_asset_volume={self.taker_buy_quote_asset_volume})"
        )
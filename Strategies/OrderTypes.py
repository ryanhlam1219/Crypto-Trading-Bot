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

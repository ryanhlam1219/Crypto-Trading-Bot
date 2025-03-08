import datetime
from abc import ABC, abstractmethod
from twisted.internet import reactor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Strategies.OrderTypes import TradeDirection, OrderType  # Only for type hints

class Exchange(ABC):
    api_url: str

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        self.apiKey = key
        self.apiSecret = secret
        self.currency = currency
        self.asset = asset
        self.currency_asset = currency + asset

    # Abstract methods

    @abstractmethod
    def get_connectivity_status(self):
        pass

    @abstractmethod
    def get_candle_stick_data(self) -> list[list]:
        pass

    @abstractmethod
    def get_account_status(self):
        pass

    @abstractmethod
    def create_new_order(self, direction: "TradeDirection", order_type: "OrderType", quantity: int):
        pass

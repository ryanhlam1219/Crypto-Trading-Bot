import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
    from Utils.MetricsCollector import MetricsCollector

class Exchange(ABC):
    api_url: str

    def __init__(self, key: str, secret: str, currency: str, asset: str, metrics_collector: "MetricsCollector"):
        self.apiKey = key
        self.apiSecret = secret
        self.currency = currency
        self.asset = asset
        self.currency_asset = asset + currency  # Standard trading pair format: BTCUSD (asset+currency)
        self.metrics_collector = metrics_collector

    # Abstract methods

    @abstractmethod
    def get_connectivity_status(self):
        pass

    @abstractmethod
    def get_candle_stick_data(self, interval:int) -> "CandleStickData":
        pass

    @abstractmethod
    def get_account_status(self):
        pass

    @abstractmethod
    def create_new_order(self, direction: "TradeDirection", order_type: "OrderType", quantity: int, price: float = None):
        pass

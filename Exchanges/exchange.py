import datetime
from abc import ABC, abstractmethod
from twisted.internet import reactor


class Exchange(ABC):
    api_url: str

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        self.apiKey = key
        self.apiSecret = secret
        self.currency = currency
        self.asset = asset
        self.currency_asset = currency + asset

    # abstract methods

    @abstractmethod
    def get_connectivity_status():
        pass

    @abstractmethod
    def get_candle_stick_data() -> list[list]:
        pass

    @abstractmethod
    def get_account_status():
        pass

    @abstractmethod
    def create_new_order():
        pass
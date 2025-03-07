import datetime
from abc import ABC, abstractmethod
from twisted.internet import reactor


class Exchange(ABC):
    api_url: str

    def __init__(self, key: str, secret: str, currency: str, asset: str):
        self.apiKey = key
        self.apiSecret = secret
        self.name = None
        self.currency = currency
        self.asset = asset

    # abstract methods

    @abstractmethod
    def getConnectivityStatus():
        pass

    @abstractmethod
    def getCandleStickData(currency:str, asset:str):
        pass

    @abstractmethod
    def getAccountStatus():
        pass
import datetime
from abc import ABC, abstractmethod
from twisted.internet import reactor


class Exchange(ABC):
    api_url: str

    def __init__(self, key: str, secret: str):
        self.apiKey = key
        self.apiSecret = secret
        self.name = None

    # abstract methods

    @abstractmethod
    def getConnectivityStatus():
        pass

    @abstractmethod
    def getCandleStickData(symbol: str):
        pass
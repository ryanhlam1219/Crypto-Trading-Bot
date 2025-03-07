from abc import ABC, abstractmethod
from Exchanges import Exchange
from enum import Enum

class TradeDirection(Enum):
    BUY = "BUY"
    SELL = "SELL"

class Strategy(ABC):
    def __init__(self, client:Exchange, interval:int, stop_loss_percentage:int):
        self.client = client
        self.interval = interval
        self.current_level = None
        self.current_trade = None
        self.current_direction = TradeDirection.BUY
        self.current_profit_level = None
        self.stop_loss_percentage = stop_loss_percentage

    @abstractmethod
    def execute_trade(self, price, direction):
        pass

    @abstractmethod
    def close_trade(self, price):
        pass

    @abstractmethod
    def check_trades(self, price):
        pass

    @abstractmethod
    def run_strategy(self):
        pass

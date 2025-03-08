from abc import ABC, abstractmethod
from Exchanges.exchange import Exchange
from Strategies.OrderTypes import TradeDirection


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
    def calculate_net_profit():
        pass
    
    @abstractmethod
    def run_strategy(self, trade_interval):
        pass

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from Exchanges.exchange import Exchange
from Strategies.ExhcangeModels import TradeDirection

if TYPE_CHECKING:
    from Utils.MetricsCollector import MetricsCollector


class Strategy(ABC):
    def __init__(self, client: Exchange, interval: int, stop_loss_percentage: int, metrics_collector: "MetricsCollector"):
        self.client = client
        self.interval = interval
        self.current_level = None
        self.current_trade = None
        self.current_direction = TradeDirection.BUY
        self.current_profit_level = None
        self.stop_loss_percentage = stop_loss_percentage
        self.metrics_collector = metrics_collector

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
    def run_strategy(self, trade_interval):
        pass

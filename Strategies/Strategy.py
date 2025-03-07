from abc import ABC, abstractmethod

class Strategy(ABC):
    def __init__(self, grid_size=10):
        self.grid_size = grid_size
        self.current_level = None
        self.current_trade = None
        self.current_direction = "buy"
        self.current_profit_level = None

    @abstractmethod
    def execute_trade(self, price, direction):
        pass

    @abstractmethod
    def close_trade(self, price):
        pass

    @abstractmethod
    def check_trade(self, price):
        pass

    @abstractmethod
    def run_strategy(self):
        pass

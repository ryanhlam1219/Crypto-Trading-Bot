from Strategies.Strategy import Strategy
from Exchanges.exchange import Exchange
from Strategies.OrderTypes import TradeDirection
from Test.DataFetchException import DataFetchException
import sys
import traceback

class StrategyWrapper:
    def __init__(self, strategy: Strategy):
        """
        Initializes the StrategyWrapper with a specific trading strategy.

        :param strategy: An instance of a class that inherits from Strategy.
        """
        if not isinstance(strategy, Strategy):
            raise TypeError("Provided strategy must be an instance of a subclass of Strategy.")
        self.strategy = strategy

    def run_strategy(self):
        """Runs the trading strategy."""
        try:
            self.strategy.run_strategy(0.000001)
        except DataFetchException as e:
            print("Backtest complete, stopping client")
            self.strategy.calculate_net_profit()
            sys.exit(0)
            
        except Exception as e:
            print(f"An Error occured when executing Strategy: {e}")
            traceback.print_exc()

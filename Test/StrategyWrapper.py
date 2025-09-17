from Strategies.Strategy import Strategy
from Test.DataFetchException import DataFetchException
from Exchanges.BinanceBacktestClient import BinanceBacktestClient
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
        """Runs the trading strategy with progress bar for backtesting."""
        try:
            # Initialize progress bar if using BinanceBacktestClient
            if isinstance(self.strategy.client, BinanceBacktestClient):
                self.strategy.client.initialize_strategy_progress_bar()
            
            self.strategy.run_strategy(0.000001)
        except DataFetchException as e:
            # Close progress bar if it was initialized
            if isinstance(self.strategy.client, BinanceBacktestClient):
                self.strategy.client.close_strategy_progress_bar()
            
            print("\nBacktest complete, stopping client")
            
            # Use MetricsCollector for final profit calculation if available
            if self.strategy.metrics_collector:
                # Close any remaining active trades at current price
                if self.strategy.metrics_collector.active_trades:
                    # Get the last known price (we'll use the strategy's last data point)
                    try:
                        last_price = self.strategy.candlestick_data[-1].close_price if self.strategy.candlestick_data else 0
                        self.strategy.metrics_collector.close_all_active_trades(last_price, "backtest_end")
                    except:
                        pass  # If no data available, skip closing trades
                
                # Generate performance report
                report = self.strategy.metrics_collector.generate_performance_report()
                print(report)
                
                # Print legacy-style metrics for compatibility
                net_profit_percentage = self.strategy.metrics_collector.calculate_net_profit_percentage()
                total_profit = self.strategy.metrics_collector.calculate_total_profit_loss()
                print(f"Net Profit Percentage: {net_profit_percentage:.2f}%")
                print(f"Total Profit: ${round(total_profit, 2)}")
            else:
                print("Warning: No metrics collector available for profit calculation")
            
            sys.exit(0)
            
        except Exception as e:
            # Close progress bar if it was initialized
            if isinstance(self.strategy.client, BinanceBacktestClient):
                self.strategy.client.close_strategy_progress_bar()
            
            print(f"An Error occured when executing Strategy: {e}")
            traceback.print_exc()

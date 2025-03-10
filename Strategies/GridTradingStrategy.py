import time
import traceback
from Strategies.Strategy import Strategy
from Strategies.ExhcangeModels import CandleStickData, OrderType, TradeDirection
from Test.DataFetchException import DataFetchException

class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage, grid_percentage=1, num_levels=3, min_candles=10):
        super().__init__(client, interval, stop_loss_percentage)
        self.grid_percentage = grid_percentage  # Grid size as a percentage of market price
        self.num_levels = num_levels
        self.min_candles = min_candles  # Minimum number of candlesticks required before trading
        self.active_trades = []
        self.closed_trades = []
        self.candlestick_data = []  # Store collected candlestick data
        print(f"Initialized GridTradingStrategy with grid percentage: {self.grid_percentage}, levels: {self.num_levels}, stop-loss: {self.stop_loss_percentage}%, and min candles: {self.min_candles}")

    def execute_trade(self, price: float, direction: TradeDirection, grid_size: float):
        try:
            if price <= 0:
                raise ValueError("Invalid price. Price must be a positive number.")

            stop_loss = price - (grid_size * (self.stop_loss_percentage / 100)) if direction == TradeDirection.BUY \
                        else price + (grid_size * (self.stop_loss_percentage / 100))
            profit_target = price + grid_size if direction == TradeDirection.BUY else price - grid_size

            trade = {"entry": price, "direction": direction.value, "profit_target": profit_target, "stop_loss": stop_loss}
            self.active_trades.append(trade)

            # Using create_new_order method with correct args
            self.client.create_new_order(direction, OrderType.LIMIT_ORDER, 1, price)
            print(f"Executed {direction.value} order at {price}. Profit target: {profit_target}, Stop-loss: {stop_loss}")
        except Exception as e:
            print(f"Error executing trade: {e}")
            traceback.print_exc()

    def close_trade(self, trade: dict, price: float):
        try:
            if trade in self.active_trades:
                self.active_trades.remove(trade)
                profit = (price - trade["entry"]) if trade["direction"] == TradeDirection.BUY.value else (trade["entry"] - price)
                trade["exit"] = price
                trade["profit"] = profit
                self.closed_trades.append(trade)
                print(f"Closed {trade['direction']} order at {price}. Profit: ${round(profit,2)}")
        except Exception as e:
            print(f"Error closing trade: {e}")
            traceback.print_exc()

    def calculate_net_profit(self) -> float:
        try:
            total_profit = sum(trade["profit"] for trade in self.closed_trades)
            total_entry_amount = sum(trade["entry"] for trade in self.closed_trades)
            
            if total_entry_amount == 0:
                return 0.0

            net_profit_percentage = (total_profit / total_entry_amount) * 100
            print(f"Net Profit Percentage: {net_profit_percentage:.2f}%")
            print(f"Total Profit: ${round(total_profit,2)}")
            return net_profit_percentage
        except Exception as e:
            print(f"Error calculating net profit: {e}")
            traceback.print_exc()
            return 0.0

    def check_trades(self, price: float):
        for trade in self.active_trades[:]:
            if (trade["direction"] == TradeDirection.BUY.value and price >= trade["profit_target"]) or \
               (trade["direction"] == TradeDirection.SELL.value and price <= trade["profit_target"]):
                self.close_trade(trade, price)
            elif (trade["direction"] == TradeDirection.BUY.value and price <= trade["stop_loss"]) or \
                 (trade["direction"] == TradeDirection.SELL.value and price >= trade["stop_loss"]):
                self.close_trade(trade, price)

    def run_strategy(self, trade_interval: int):
        try:
            if not self.client.get_connectivity_status():
                print("Could not establish connection to exchange. Exiting strategy.")
                return

            self.client.get_account_status()
            
            while len(self.candlestick_data) < self.min_candles:
                new_data = self.client.get_candle_stick_data(self.interval)
                if isinstance(new_data, CandleStickData):
                    self.candlestick_data.append(new_data)
                print("Not enough candlestick data collected. Waiting...")
                time.sleep(trade_interval)
            
            base_price = self.__extract_latest_price(self.candlestick_data)
            if base_price is None:
                print("Failed to retrieve initial price. Exiting strategy.")
                return

            self.__initialize_grid(base_price)

            while True:
                new_data = self.client.get_candle_stick_data(self.interval)
                if isinstance(new_data, CandleStickData):
                    self.candlestick_data.append(new_data)
                    self.candlestick_data = self.candlestick_data[-self.min_candles:]
                    current_price = self.__extract_latest_price(self.candlestick_data)
                    if current_price is not None:
                        self.check_trades(current_price)
                time.sleep(trade_interval)
        except DataFetchException as e:
            raise DataFetchException(e)
        except Exception as e:
            print(f"Error in strategy execution: {e}")
            traceback.print_exc()

    def __extract_latest_price(self, candlestick_data: list) -> float:
        try:
            latest_candle = candlestick_data[-1]
            return latest_candle.close_price 
        except Exception as e:
            print(f"Error extracting latest price: {e}")
            traceback.print_exc()
            return None

    def __initialize_grid(self, base_price: float):
        try:
            grid_size = base_price * self.grid_percentage
            for i in range(1, self.num_levels + 1):
                self.execute_trade(base_price - (i * grid_size), TradeDirection.BUY, grid_size)
                self.execute_trade(base_price + (i * grid_size), TradeDirection.SELL, grid_size)
        except Exception as e:
            print(f"Error initializing grid: {e}")
            traceback.print_exc()
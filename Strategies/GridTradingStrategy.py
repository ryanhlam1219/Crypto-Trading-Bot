import time
import traceback
from Strategies.Strategy import Strategy
from Strategies.OrderTypes import OrderType, TradeDirection
from Test.DataFetchException import DataFetchException

class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage, grid_size=10, num_levels=3):
        super().__init__(client, interval, stop_loss_percentage)
        self.grid_size = grid_size
        self.num_levels = num_levels
        self.active_trades = []
        self.closed_trades = []  # Stores completed trades for profit calculations
        print(f"Initialized GridTradingStrategy with grid size: {self.grid_size}, levels: {self.num_levels}, and stop-loss: {self.stop_loss_percentage}%")

    def execute_trade(self, price, direction):
        try:
            if not isinstance(price, (int, float)) or price <= 0:
                raise ValueError("Invalid price. Price must be a positive number.")

            if direction not in (TradeDirection.BUY, TradeDirection.SELL):
                raise ValueError("Invalid trade direction. Must be 'buy' or 'sell'.")

            stop_loss = price - (self.grid_size * (self.stop_loss_percentage / 100)) if direction == TradeDirection.BUY \
                        else price + (self.grid_size * (self.stop_loss_percentage / 100))
            profit_target = price + self.grid_size if direction == TradeDirection.BUY else price - self.grid_size

            trade = {"entry": price, "direction": direction.value, "profit_target": profit_target, "stop_loss": stop_loss}
            self.active_trades.append(trade)

            self.client.create_new_order(direction.value, OrderType.LIMIT_ORDER, 1, price=price)
            print(f"Executed {direction.value} order at {price}. Profit target: {profit_target}, Stop-loss: {stop_loss}")
        except Exception as e:
            print(f"Error executing trade: {e}")
            traceback.print_exc()

    def close_trade(self, trade, price):
        try:
            if trade in self.active_trades:
                self.active_trades.remove(trade)
                profit = (price - trade["entry"]) if trade["direction"] == TradeDirection.BUY.value else (trade["entry"] - price)
                trade["exit"] = price
                trade["profit"] = profit
                self.closed_trades.append(trade)
                print(f"Closed {trade['direction']} order at {price}. Profit: {profit}")
        except Exception as e:
            print(f"Error closing trade: {e}")
            traceback.print_exc()

    def calculate_net_profit(self):
        try:
            total_profit = sum(trade["profit"] for trade in self.closed_trades)
            total_entry_amount = sum(trade["entry"] for trade in self.closed_trades)
            
            if total_entry_amount == 0:
                return 0.0

            net_profit_percentage = (total_profit / total_entry_amount) * 100
            print(f"Net Profit Percentage: {net_profit_percentage:.2f}%")
            return net_profit_percentage
        except Exception as e:
            print(f"Error calculating net profit: {e}")
            traceback.print_exc()
            return 0.0

    def check_trades(self, price):
        for trade in self.active_trades[:]:
            if (trade["direction"] == TradeDirection.BUY.value and price >= trade["profit_target"]) or \
               (trade["direction"] == TradeDirection.SELL.value and price <= trade["profit_target"]):
                self.close_trade(trade, price)
            elif (trade["direction"] == TradeDirection.BUY.value and price <= trade["stop_loss"]) or \
                 (trade["direction"] == TradeDirection.SELL.value and price >= trade["stop_loss"]):
                self.close_trade(trade, price)

    def run_strategy(self, trade_interval):
        try:
            if not self.client.get_connectivity_status():
                print("Could not establish connection to exchange. Exiting strategy.")
                return

            self.client.get_account_status()
            candlestick_data = self.client.get_candle_stick_data(self.interval)

            if not isinstance(candlestick_data, list) or len(candlestick_data) == 0:
                raise ValueError("Received invalid candlestick data.")

            base_price = self.__extract_latest_price(candlestick_data)
            if base_price is None:
                print("Failed to retrieve initial price. Exiting strategy.")
                return

            self.__initialize_grid(base_price)

            while True:
                candlestick_data = self.client.get_candle_stick_data(self.interval)
                if isinstance(candlestick_data, list) and candlestick_data:
                    current_price = self.__extract_latest_price(candlestick_data)
                    if current_price is not None:
                        self.check_trades(current_price)
                time.sleep(trade_interval)
        except DataFetchException as e:
            raise DataFetchException(e)
        except Exception as e:
            print(f"Error in strategy execution: {e}")
            traceback.print_exc()

    def __extract_latest_price(self, candlestick_data):
        try:
            latest_candle = candlestick_data[-1]
            return float(latest_candle[4])
        except Exception as e:
            print(f"Error extracting latest price: {e}")
            traceback.print_exc()
            return None

    def __initialize_grid(self, base_price):
        try:
            for i in range(1, self.num_levels + 1):
                self.execute_trade(base_price - (i * self.grid_size), TradeDirection.BUY)
                self.execute_trade(base_price + (i * self.grid_size), TradeDirection.SELL)
        except Exception as e:
            print(f"Error initializing grid: {e}")
            traceback.print_exc()
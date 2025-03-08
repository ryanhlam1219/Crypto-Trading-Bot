import time
import traceback
from Strategies.Strategy import Strategy
from Strategies.OrderTypes import OrderType, TradeDirection
from Test.DataFetchException import DataFetchException


class GridTradingStrategy(Strategy):
    """
    A strategy that places buy and sell orders at predefined price levels (grid trading).
    """
    def __init__(self, client, interval, stop_loss_percentage, grid_size=10, num_levels=3):
        """
        Initializes the grid trading strategy.

        :param client: API client for interacting with the exchange.
        :param interval: Time interval (in minutes) for fetching candlestick data.
        :param stop_loss_percentage: Percentage below/above entry price to set stop-loss.
        :param grid_size: Price difference between grid levels.
        :param num_levels: Number of grid levels for buy/sell trades.
        """
        super().__init__(client, interval, stop_loss_percentage)
        self.grid_size = grid_size
        self.num_levels = num_levels
        self.active_trades = []  # List to store active trades
        print(f"Initialized GridTradingStrategy with grid size: {self.grid_size}, levels: {self.num_levels}, and stop-loss: {self.stop_loss_percentage}%")

    def execute_trade(self, price, direction):
        """
        Executes a buy or sell trade and sets stop-loss and profit targets.

        :param price: The price at which the trade is executed (must be a positive number).
        :param direction: "buy" or "sell" (must be a valid TradeDirection enum).
        """
        try:
            # Validate price
            if not isinstance(price, (int, float)) or price <= 0:
                raise ValueError("Invalid price. Price must be a positive number.")

            # Validate direction
            if direction not in (TradeDirection.BUY, TradeDirection.SELL):
                raise ValueError("Invalid trade direction. Must be 'buy' or 'sell'.")

            # Validate essential attributes
            if not hasattr(self, "grid_size") or not hasattr(self, "stop_loss_percentage"):
                raise AttributeError("Missing required trade attributes (grid_size or stop_loss_percentage).")

            if not hasattr(self, "client") or not hasattr(self.client, "create_new_order"):
                raise AttributeError("Trading client is not properly initialized.")

            # Calculate stop-loss based on direction
            stop_loss = price - (self.grid_size * (self.stop_loss_percentage / 100)) if direction == TradeDirection.BUY \
                        else price + (self.grid_size * (self.stop_loss_percentage / 100))

            # Set profit target at a fixed grid level
            profit_target = price + self.grid_size if direction == TradeDirection.BUY else price - self.grid_size

            # Store trade details
            trade = {
                "entry": price,
                "direction": direction.value,
                "profit_target": profit_target,
                "stop_loss": stop_loss
            }

            if not hasattr(self, "active_trades"):
                self.active_trades = []  # Ensure the list exists

            self.active_trades.append(trade)

            # Execute order
            self.client.create_new_order(direction.value, OrderType.LIMIT_ORDER, 1, price=price)

            print(f"Executed {direction.value} order at {price}. Profit target: {profit_target}, Stop-loss: {stop_loss}")

        except ValueError as ve:
            print(f"ValueError: {ve}")
            traceback.print_exc
        except AttributeError as ae:
            print(f"AttributeError: {ae}")
            traceback.print_exc
        except Exception as e:
            print(f"Unexpected error during trade execution: {e}")
            traceback.print_exc


    def close_trade(self, trade, price):
        """
        Closes an active trade and calculates profit.

        :param trade: The trade dictionary containing trade details.
        :param price: The price at which the trade is closed (must be a positive number).
        """
        try:
            # Validate trade object
            if not isinstance(trade, dict):
                raise ValueError("Invalid trade. Trade must be a dictionary.")

            required_keys = {"entry", "direction"}
            if not required_keys.issubset(trade):
                raise KeyError("Trade dictionary is missing required keys: 'entry' or 'direction'.")

            # Validate price
            if not isinstance(price, (int, float)) or price <= 0:
                raise ValueError("Invalid price. Price must be a positive number.")

            # Validate trade direction
            if trade["direction"] not in (TradeDirection.BUY.value, TradeDirection.SELL.value):
                raise ValueError("Invalid trade direction in trade dictionary.")

            # Ensure active_trades list exists
            if not hasattr(self, "active_trades") or not isinstance(self.active_trades, list):
                raise AttributeError("Missing or invalid 'active_trades' list.")

            # Calculate profit
            profit = (price - trade["entry"]) if trade["direction"] == TradeDirection.BUY.value else (trade["entry"] - price)

            # Attempt to remove trade
            if trade in self.active_trades:
                self.active_trades.remove(trade)
            else:
                raise ValueError("Trade not found in active_trades list.")

            print(f"Closed {trade['direction']} order at {price}. Profit: {profit}")

        except ValueError as ve:
            print(f"ValueError: {ve}")
            traceback.print_exc
        except KeyError as ke:
            print(f"KeyError: {ke}")
            traceback.print_exc
        except AttributeError as ae:
            print(f"AttributeError: {ae}")
        except Exception as e:
            print(f"Unexpected error during trade closure: {e}")
            traceback.print_exc



    def check_trades(self, price):
        """
        Checks whether any active trades have hit their profit target or stop-loss.

        :param price: The current market price (must be a positive number).
        """
        try:
            # Validate price
            if not isinstance(price, (int, float)) or price <= 0:
                raise ValueError("Invalid price. Price must be a positive number.")

            # Ensure active_trades list exists
            if not hasattr(self, "active_trades") or not isinstance(self.active_trades, list):
                raise AttributeError("Missing or invalid 'active_trades' list.")

            # Check trades for profit target or stop-loss
            for trade in self.active_trades[:]:  # Iterate over a copy to allow safe modification
                # Validate trade dictionary
                if not isinstance(trade, dict):
                    print("Skipping invalid trade entry (not a dictionary).")
                    continue

                required_keys = {"entry", "direction", "profit_target", "stop_loss"}
                if not required_keys.issubset(trade):
                    print("Skipping trade with missing keys:", trade)
                    continue

                # Validate trade direction
                if trade["direction"] not in (TradeDirection.BUY.value, TradeDirection.SELL.value):
                    print(f"Skipping trade with invalid direction: {trade}")
                    continue

                # Check if profit target or stop-loss is reached
                if (trade["direction"] == TradeDirection.BUY.value and price >= trade["profit_target"]) or \
                (trade["direction"] == TradeDirection.SELL.value and price <= trade["profit_target"]):
                    print(f"Profit target reached for {trade['direction']} trade at {price}. Closing trade.")
                    self.close_trade(trade, price)
                elif (trade["direction"] == TradeDirection.BUY.value and price <= trade["stop_loss"]) or \
                    (trade["direction"] == TradeDirection.SELL.value and price >= trade["stop_loss"]):
                    print(f"Stop-loss hit for {trade['direction']} trade at {price}. Closing trade.")
                    self.close_trade(trade, price)

        except ValueError as ve:
            print(f"ValueError: {ve}")
            traceback.print_exc
        except AttributeError as ae:
            print(f"AttributeError: {ae}")
            traceback.print_exc            
        except Exception as e:
            print(f"Unexpected error while checking trades: {e}")
            traceback.print_exc


    def __extract_latest_price(self, candlestick_data):
        """
        Extracts the latest closing price from candlestick data.

        :param candlestick_data: JSON response from Binance API (list of candlesticks).
        :return: The latest closing price as a float, or None if the data is invalid.
        """
        try:
            # Validate input
            if not isinstance(candlestick_data, list) or len(candlestick_data) == 0:
                raise ValueError("Invalid candlestick data: Expected a non-empty list.")

            # Validate latest candlestick entry
            latest_candle = candlestick_data[-1]
            if not isinstance(latest_candle, list) or len(latest_candle) < 5:
                raise ValueError("Invalid candlestick format: Expected a list with at least 5 elements.")

            # Extract and validate closing price
            closing_price = latest_candle[4]  # Closing price is at index 4
            if not isinstance(closing_price, (int, float, str)):
                raise TypeError("Closing price must be a number or string representation of a number.")

            latest_close_price = float(closing_price)
            print(f"Extracted latest closing price: {latest_close_price}")
            return latest_close_price

        except ValueError as ve:
            print(f"ValueError: {ve}")
            traceback.print_exc
        except TypeError as te:
            print(f"TypeError: {te}")
            traceback.print_exc
        except Exception as e:
            print(f"Unexpected error while extracting latest price: {e}")
            traceback.print_exc

        return None  # Return None if any error occurs


    def __initialize_grid(self, base_price):
        """
        Initializes grid trades at predefined levels above and below the base price.

        :param base_price: The current market price used as the grid center (must be a positive number).
        """
        try:
            # Validate base_price
            if not isinstance(base_price, (int, float)) or base_price <= 0:
                raise ValueError("Invalid base price. It must be a positive number.")

            # Ensure necessary attributes exist
            if not hasattr(self, "num_levels") or not isinstance(self.num_levels, int) or self.num_levels <= 0:
                raise AttributeError("Invalid or missing 'num_levels'. It must be a positive integer.")

            if not hasattr(self, "grid_size") or not isinstance(self.grid_size, (int, float)) or self.grid_size <= 0:
                raise AttributeError("Invalid or missing 'grid_size'. It must be a positive number.")

            if not hasattr(self, "execute_trade") or not callable(self.execute_trade):
                raise AttributeError("Missing or invalid 'execute_trade' method.")

            print("Initializing grid levels...")

            # Initialize grid trades
            for i in range(1, self.num_levels + 1):
                buy_price = base_price - (i * self.grid_size)
                sell_price = base_price + (i * self.grid_size)

                # Execute buy and sell trades with error handling
                try:
                    self.execute_trade(buy_price, TradeDirection.BUY)
                    self.execute_trade(sell_price, TradeDirection.SELL)
                except Exception as e:
                    print(f"Error executing trade at grid level {i}: {e}")
                    traceback.print_exc

        except ValueError as ve:
            print(f"ValueError: {ve}")
            traceback.print_exc
        except AttributeError as ae:
            print(f"AttributeError: {ae}")
            traceback.print_exc
        except Exception as e:
            print(f"Unexpected error while initializing grid: {e}")
            traceback.print_exc


    def run_strategy(self, trade_interval):
        """
        Runs the grid trading strategy in a loop.
        :param trade_interval: the interval in seconds to wait before fetching the updated market price
        """
        try:
            print("Starting grid trading strategy...")

            # Ensure client object exists and has necessary methods
            if not hasattr(self, "client"):
                raise AttributeError("Trading client is not initialized.")

            if not hasattr(self.client, "get_connectivity_status") or not callable(self.client.get_connectivity_status):
                raise AttributeError("Missing 'get_connectivity_status' method in trading client.")

            if not hasattr(self.client, "get_account_status") or not callable(self.client.get_account_status):
                raise AttributeError("Missing 'get_account_status' method in trading client.")

            if not hasattr(self.client, "get_candle_stick_data") or not callable(self.client.get_candle_stick_data):
                raise AttributeError("Missing 'get_candle_stick_data' method in trading client.")

            # Check exchange connectivity
            if not self.client.get_connectivity_status():
                print("Could not establish connection to exchange. Exiting strategy.")
                return

            print("Fetching account status...")
            self.client.get_account_status()

            # Fetch initial market price
            print("Fetching initial market price...")
            candlestick_data = self.client.get_candle_stick_data(self.interval)

            if not isinstance(candlestick_data, list) or len(candlestick_data) == 0:
                raise ValueError("Received invalid candlestick data.")

            base_price = self.__extract_latest_price(candlestick_data)
            if base_price is None:
                print("Failed to retrieve initial price. Exiting strategy.")
                return

            # Initialize grid trades
            self.__initialize_grid(base_price)

            # Start trading loop
            while True:
                print("Fetching latest market price...")
                candlestick_data = self.client.get_candle_stick_data(self.interval)

                if not isinstance(candlestick_data, list) or len(candlestick_data) == 0:
                    print("Warning: Received empty or invalid candlestick data. Skipping this iteration.")
                    continue

                current_price = self.__extract_latest_price(candlestick_data)
                if current_price is not None:
                    print(f"Current market price: {current_price}")
                    self.check_trades(current_price)
                else:
                    print("Failed to extract latest price. Skipping this iteration.")

                print(f"Waiting for {trade_interval} seconds before initiating next trade")
                time.sleep(trade_interval)
        except ValueError as ve:
            print(f"ValueError: {ve}")
            traceback.print_exc
        except AttributeError as ae:
            print(f"AttributeError: {ae}")
            traceback.print_exc

import time
from Strategies.Strategy import Strategy

class GridTradingStrategy(Strategy):
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

        :param price: The price at which the trade is executed.
        :param direction: "buy" or "sell".
        """
        # Calculate stop-loss based on direction
        stop_loss = price - (self.grid_size * (self.stop_loss_percentage / 100)) if direction == "buy" \
                    else price + (self.grid_size * (self.stop_loss_percentage / 100))

        # Set profit target at a fixed grid level
        profit_target = price + self.grid_size if direction == "buy" else price - self.grid_size

        # Store trade details
        trade = {
            "entry": price,
            "direction": direction,
            "profit_target": profit_target,
            "stop_loss": stop_loss
        }

        self.active_trades.append(trade)
        print(f"Executed {direction} order at {price}. Profit target: {profit_target}, Stop-loss: {stop_loss}")

    def close_trade(self, trade, price):
        """
        Closes an active trade and calculates profit.

        :param trade: The trade dictionary containing trade details.
        :param price: The price at which the trade is closed.
        """
        # Calculate profit or loss based on direction
        profit = (price - trade["entry"]) if trade["direction"] == "buy" else (trade["entry"] - price)
        print(f"Closed {trade['direction']} order at {price}. Profit: {profit}")

        # Remove the closed trade from active trades
        self.active_trades.remove(trade)

    def check_trades(self, price):
        """
        Checks whether any active trades have hit their profit target or stop-loss.

        :param price: The current market price.
        """
        for trade in self.active_trades[:]:  # Iterate over a copy to allow modification
            # Check if profit target is reached
            if (trade["direction"] == "buy" and price >= trade["profit_target"]) or \
               (trade["direction"] == "sell" and price <= trade["profit_target"]):
                print("Profit target reached. Closing trade.")
                self.close_trade(trade, price)

            # Check if stop-loss is triggered
            elif (trade["direction"] == "buy" and price <= trade["stop_loss"]) or \
                 (trade["direction"] == "sell" and price >= trade["stop_loss"]):
                print("Stop-loss hit. Closing trade.")
                self.close_trade(trade, price)

    def extract_latest_price(self, candlestick_data):
        """
        Extracts the latest closing price from candlestick data.

        :param candlestick_data: JSON response from Binance API (list of candlesticks).
        :return: The latest closing price as a float, or None if the data is invalid.
        """
        if candlestick_data and isinstance(candlestick_data, list) and len(candlestick_data) > 0:
            latest_close_price = float(candlestick_data[-1][4])  # Extract closing price (index 4)
            print(f"Extracted latest closing price: {latest_close_price}")
            return latest_close_price
        else:
            print("Error: Invalid or empty candlestick data received.")
            return None

    def initialize_grid(self, base_price):
        """
        Initializes grid trades at predefined levels above and below the base price.

        :param base_price: The current market price used as the grid center.
        """
        print("Initializing grid levels...")
        for i in range(self.num_levels):
            # Set buy orders below the base price
            buy_price = base_price - (i * self.grid_size)
            self.execute_trade(buy_price, "buy")

            # Set sell orders above the base price
            sell_price = base_price + (i * self.grid_size)
            self.execute_trade(sell_price, "sell")

    def run_strategy(self):
        """
        Runs the grid trading strategy in a loop.
        """
        print("Starting grid trading strategy...")

        # Ensure connection to the exchange is established
        if not self.client.getConnectivityStatus():
            print("Could not establish connection to exchange...")
            return

        print("Fetching account status...")
        self.client.getAccountStatus()

        # Fetch the initial market price to set up the grid
        print("Fetching initial market price...")
        candlestick_data = self.client.getCandleStickData(self.interval)
        if not isinstance(candlestick_data, list) or len(candlestick_data) == 0:
            raise ValueError("Received invalid candlestick data")

        base_price = self.extract_latest_price(candlestick_data)
        if base_price is None:
            print("Failed to retrieve initial price. Exiting strategy.")
            raise ValueError("Failed to retrieve initial price. Exiting strategy.")

        # Set up the initial grid trades
        self.initialize_grid(base_price)

        # Infinite loop to monitor price movements and manage trades
        while True:
            print("Fetching latest market price...")
            candlestick_data = self.client.getCandleStickData(self.interval)
            current_price = self.extract_latest_price(candlestick_data)

            if current_price is not None:
                print(f"Current market price: {current_price}")
                self.check_trades(current_price)  # Check for trades to close

            # Wait before fetching the next price update
            print(f"Waiting for {self.interval} minute(s) before next price update...")
            time.sleep(self.interval * 60)
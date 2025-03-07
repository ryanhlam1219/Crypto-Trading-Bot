import time
from Strategies.Strategy import Strategy

class GridTradingStrategy(Strategy):
    def execute_trade(self, price, direction):
        self.current_trade = price
        self.current_direction = direction
        self.current_profit_level = price + self.grid_size if direction == "buy" else price - self.grid_size
        print(f"Executed {direction} order at price {price}. Profit level: {self.current_profit_level}")

    def close_trade(self, price):
        if self.current_trade is None:
            return
        profit = (price - self.current_trade) if self.current_direction == "buy" else (self.current_trade - price)
        print(f"Closed {self.current_direction} order at price {price}. Profit: {profit}")
        self.current_trade = self.current_direction = self.current_profit_level = None

    def check_trade(self, price):
        if self.current_trade and self.current_profit_level and (
            (self.current_direction == "buy" and price >= self.current_profit_level) or
            (self.current_direction == "sell" and price <= self.current_profit_level)
        ):
            self.close_trade(price)

    def run_strategy(self, client):
        if(client.getConnectivityStatus()):
            print("Connected.")
        else:
            print("Could not establish connection to exchange...")
        client.getAccountStatus()
        client.getCandleStickData()


        while True:
            current_price = 100  # Replace with actual price retrieval
            time.sleep(60)  # Adjust for candle interval
            self.check_trade(current_price)

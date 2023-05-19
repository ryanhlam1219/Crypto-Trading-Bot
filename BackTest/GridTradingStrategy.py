import time

# Define the grid size in pips
grid_size = 10

# Define the current level of the grid
current_level = None

# Define the current trade
current_trade = None

# Define the current direction of the trade
current_direction = "buy"

# Define the current profit level
current_profit_level = None

# Define the function to execute a trade at the given price
def execute_trade(price, direction):
    global current_trade, current_direction, current_profit_level
    current_trade = price
    current_direction = direction
    
    #TODO: setup with live data and allow function to execute live trades
    if direction == "buy":
        current_profit_level = price + grid_size
    else:
        current_profit_level = price - grid_size
    
    print("Executed {} order at price {}. Current profit level: {}".format(direction, price, current_profit_level))

# Define the function to close the current trade at the given price
def close_trade(price):
    global current_trade, current_direction, current_profit_level
    profit = 0

    #TODO: setup with live data and allow function to execute live trades
    if current_direction == "buy":
        profit = price - current_trade
    else:
        profit = current_trade - price
    
    print("Closed {} order at price {}. Profit: {}".format(current_direction, price, profit))
    current_trade = None
    current_direction = None
    current_profit_level = None

# Define the function to check if the current trade should be closed
def check_trade(price):
    global current_trade, current_profit_level
    if current_direction == "buy" and price >= current_profit_level:
        close_trade(price)
    elif current_direction == "sell" and price <= current_profit_level:
        close_trade(price)

# Define the main function that runs the grid trading strategy
def run_strategy():
    global current_level, current_trade, current_direction, current_profit_level
    while True:
        # Get the current price

        # TODO: Replace this with your code to get the actual price
        current_price = 100  

        # Wait for a new candle to be established
        time.sleep(60)  # Replace 60 with the number of seconds in your candle interval

        # Check if a new grid level has been reached
        new_level = int(current_price / grid_size)
        if current_level is None:
            current_level = new_level
        elif new_level > current_level:
            # Sell the order that takes profit from the previous grid level
            if current_direction == "buy":
                execute_trade(current_profit_level, "sell")
            elif current_direction == "sell":
                execute_trade(current_profit_level - grid_size, "sell")
            current_level = new_level
        elif new_level < current_level:
            # Sell the order that takes profit from the previous grid level
            if current_direction == "buy":
                execute_trade(current_profit_level + grid_size, "buy")
            elif current_direction == "sell":
                execute_trade(current_profit_level, "buy")
            current_level = new_level

        # Check if the current trade should be closed
        if current_trade is not None:
            check_trade(current_price)

        # Sell open trades at positive of one grid level of either level
        if current_trade is not None and (current_price >= (current_trade + grid_size) or current_price <= (current_trade - grid_size)):
            if current_direction == "buy":
                close_trade(current_trade + grid_size)
            elif current_direction == "sell":
                close_trade(current_trade - grid_size)

run_strategy()

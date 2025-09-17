import time
import traceback
import uuid
from Strategies.Strategy import Strategy
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from Test.DataFetchException import DataFetchException

class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector, grid_percentage=1, num_levels=3, min_candles=10):
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        self.grid_percentage = grid_percentage  # Grid size as a percentage of market price
        self.num_levels = num_levels
        self.min_candles = min_candles  # Minimum number of candlesticks required before trading
        self.candlestick_data = []  # Store collected candlestick data
        # Trade tracking is now handled by MetricsCollector
        print(f"Initialized GridTradingStrategy with grid percentage: {self.grid_percentage}, levels: {self.num_levels}, stop-loss: {self.stop_loss_percentage}%, and min candles: {self.min_candles}")

    def execute_trade(self, price: float, direction: TradeDirection, grid_size: float):
        try:
            if price <= 0:
                raise ValueError("Invalid price. Price must be a positive number.")

            stop_loss = price - (grid_size * (self.stop_loss_percentage / 100)) if direction == TradeDirection.BUY \
                        else price + (grid_size * (self.stop_loss_percentage / 100))
            profit_target = price + grid_size if direction == TradeDirection.BUY else price - grid_size

            # Generate unique trade ID
            trade_id = str(uuid.uuid4())[:8]
            
            # Record trade entry with MetricsCollector
            if self.metrics_collector:
                self.metrics_collector.record_trade_entry(
                    trade_id=trade_id,
                    symbol=self.client.currency_asset,
                    direction=direction.value,
                    entry_price=price,
                    quantity=1,
                    stop_loss=stop_loss,
                    profit_target=profit_target,
                    strategy_name="GridTradingStrategy"
                )

            # Using create_new_order method with correct args
            self.client.create_new_order(direction, OrderType.LIMIT_ORDER, 1, price)
            
            # Legacy print for compatibility
            print(f"Executed {direction.value} order at {price}. Profit target: {profit_target}, Stop-loss: {stop_loss}")
        except Exception as e:
            print(f"Error executing trade: {e}")
            traceback.print_exc()

    def close_trade(self, trade_id: str, price: float, reason: str = "strategy_signal"):
        """
        Close a trade using the MetricsCollector.
        
        Args:
            trade_id: ID of the trade to close
            price: Exit price
            reason: Reason for closing ('profit_target', 'stop_loss', 'manual')
        """
        try:
            if self.metrics_collector:
                closed_trade = self.metrics_collector.record_trade_exit(trade_id, price, reason)
                if closed_trade:
                    # Legacy print for compatibility
                    print(f"Closed {closed_trade['direction']} order at {price}. Profit: ${round(closed_trade['profit_loss'], 2)}")
                else:
                    print(f"Warning: Could not find trade {trade_id} to close")
        except Exception as e:
            print(f"Error closing trade: {e}")
            traceback.print_exc()

    def check_trades(self, price: float):
        """
        Check active trades for profit targets or stop losses.
        Now uses MetricsCollector to track active trades.
        """
        if not self.metrics_collector:
            return []
        # Get active trades from MetricsCollector
        active_trades = self.metrics_collector.active_trades.copy()
        
        for trade in active_trades:
            trade_id = trade['trade_id']
            direction = trade['direction']
            profit_target = trade['profit_target']
            stop_loss = trade['stop_loss']
            
            # Check for profit target hit
            if ((direction == TradeDirection.BUY.value and price >= profit_target) or 
                (direction == TradeDirection.SELL.value and price <= profit_target)):
                self.close_trade(trade_id, price, "profit_target")
            
            # Check for stop loss hit
            elif ((direction == TradeDirection.BUY.value and price <= stop_loss) or 
                  (direction == TradeDirection.SELL.value and price >= stop_loss)):
                self.close_trade(trade_id, price, "stop_loss")

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
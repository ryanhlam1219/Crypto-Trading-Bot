import time
import traceback
import uuid
from Strategies.Strategy import Strategy
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from Tests.utils import DataFetchException

class GridTradingStrategy(Strategy):
    def __init__(self, client, interval, stop_loss_percentage=None, metrics_collector=None, 
                 grid_percentage=1, num_levels=3, min_candles=10, threshold=None):
        # Handle backward compatibility and set defaults
        if stop_loss_percentage is None:
            stop_loss_percentage = 5  # Default stop loss percentage
        if threshold is None:
            threshold = 0.01  # Default threshold value
        
        # Ensure metrics_collector is provided (required by base class)
        if metrics_collector is None:
            raise ValueError("metrics_collector is required for GridTradingStrategy")
            
        # Initialize base class (which sets up signal handling)
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        
        # Grid-specific parameters
        self.grid_percentage = grid_percentage  # Grid size as a percentage of market price
        self.num_levels = num_levels
        self.min_candles = min_candles  # Minimum number of candlesticks required before trading
        self.threshold = threshold  # Store threshold as separate parameter
        self.candlestick_data = []  # Store collected candlestick data
        # Trade tracking is now handled by MetricsCollector
        
        print(f"Initialized GridTradingStrategy with grid percentage: {self.grid_percentage}, levels: {self.num_levels}, stop-loss: {self.stop_loss_percentage}%, and min candles: {self.min_candles}")

    def on_shutdown_signal(self, signum, frame):
        """Grid-specific shutdown signal handling."""
        print("GridTradingStrategy received shutdown signal - stopping grid operations...")
        # Could add grid-specific cleanup here if needed

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

            # Round price to appropriate tick size for the asset
            if "DOGE" in self.client.currency_asset:
                # DOGE tick size is typically 0.00001 (5 decimal places)
                tick_size = 0.00001
                rounded_price = round(price / tick_size) * tick_size
                rounded_price = round(rounded_price, 5)
            elif "BTC" in self.client.currency_asset:
                # BTC tick size is typically 0.01 (2 decimal places)
                tick_size = 0.01
                rounded_price = round(price / tick_size) * tick_size
                rounded_price = round(rounded_price, 2)
            else:
                # Default tick size 0.0001 (4 decimal places)
                tick_size = 0.0001
                rounded_price = round(price / tick_size) * tick_size
                rounded_price = round(rounded_price, 4)
            
            # Using limit orders (proper grid trading methodology)
            self.client.create_new_order(direction, OrderType.LIMIT_ORDER, 1, rounded_price)
            
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
            
            # Initial data collection phase with shutdown check
            while len(self.candlestick_data) < self.min_candles and not self.is_shutdown_requested():
                try:
                    new_data = self.client.get_candle_stick_data(self.interval)
                    if isinstance(new_data, CandleStickData):
                        self.candlestick_data.append(new_data)
                    print(f"Collecting initial data... ({len(self.candlestick_data)}/{self.min_candles} candles)")
                    time.sleep(trade_interval)
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt during data collection. Shutting down...")
                    return
            
            if self.is_shutdown_requested():
                print("Shutdown requested during initial data collection. Exiting...")
                return
            
            base_price = self.__extract_latest_price(self.candlestick_data)
            if base_price is None:
                print("Failed to retrieve initial price. Exiting strategy.")
                return

            self.__initialize_grid(base_price)
            print(f"Grid initialized with base price: {base_price}. Starting trading loop...")

            # Main trading loop with shutdown check
            while not self.is_shutdown_requested():
                try:
                    new_data = self.client.get_candle_stick_data(self.interval)
                    if isinstance(new_data, CandleStickData):
                        self.candlestick_data.append(new_data)
                        self.candlestick_data = self.candlestick_data[-self.min_candles:]
                        current_price = self.__extract_latest_price(self.candlestick_data)
                        if current_price is not None:
                            self.check_trades(current_price)
                    time.sleep(trade_interval)
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt in trading loop. Shutting down...")
                    break
                    
            # Graceful shutdown using base class method
            self.perform_graceful_shutdown()
            
        except DataFetchException as e:
            print(f"Data fetch error: {e}")
            self.perform_graceful_shutdown()
            raise DataFetchException(e)
        except Exception as e:
            print(f"Error in strategy execution: {e}")
            traceback.print_exc()
            self.perform_graceful_shutdown()

    def perform_graceful_shutdown(self):
        """Grid-specific graceful shutdown operations."""
        print("\n" + "="*50)
        print("GRID TRADING STRATEGY - GRACEFUL SHUTDOWN")
        print("="*50)
        
        try:
            # Grid-specific reporting
            print(f"Grid Configuration:")
            print(f"  • Grid Percentage: {self.grid_percentage}%")
            print(f"  • Grid Levels: {self.num_levels}")
            print(f"  • Candles Collected: {len(self.candlestick_data)}")
            
            # Call parent class shutdown for common functionality
            super().perform_graceful_shutdown()
            
        except Exception as e:
            print(f"Error during GridTradingStrategy shutdown: {e}")
            import traceback
            traceback.print_exc()
        
        print("GridTradingStrategy shutdown completed.")

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
            # Get current market price to avoid PERCENT_PRICE_BY_SIDE errors
            try:
                current_data = self.client.get_candle_stick_data(self.interval)
                current_price = float(current_data.close_price)
                print(f"Using current market price: ${current_price:.2f} (vs historical: ${base_price:.2f})")
                base_price = current_price
            except Exception as e:
                print(f"Could not get current price, using historical: {e}")
            
            # Convert percentage to decimal and use very small grid to avoid filter errors
            safe_percentage = min(self.grid_percentage, 0.01)  # Cap at 0.01% (much smaller)
            grid_size = base_price * (safe_percentage / 100.0)
            print(f"Grid initialized with base price: {base_price}, grid size: {grid_size} ({safe_percentage}%)")
            
            for i in range(1, self.num_levels + 1):
                buy_price = base_price - (i * grid_size)
                sell_price = base_price + (i * grid_size)
                
                print(f"Level {i}: BUY at ${buy_price:.2f}, SELL at ${sell_price:.2f}")
                
                # Only execute trades with positive prices
                if buy_price > 0:
                    self.execute_trade(buy_price, TradeDirection.BUY, grid_size)
                else:
                    print(f"⚠️ Skipping BUY order at level {i} - price would be ${buy_price:.2f}")
                    
                self.execute_trade(sell_price, TradeDirection.SELL, grid_size)
        except Exception as e:
            print(f"Error initializing grid: {e}")
            traceback.print_exc()

    def should_enter_trade(self, price: float) -> bool:
        """
        Determine if the strategy should enter a trade at the given price.
        
        Args:
            price: Current market price
            
        Returns:
            bool: True if should enter trade
        """
        try:
            # Check if we have enough candlestick data
            if len(self.candlestick_data) < self.min_candles:
                return False
                
            # Check if price change exceeds threshold
            if self.candlestick_data:
                last_price = self.candlestick_data[-1].close_price
                price_change = abs(price - last_price) / last_price
                return price_change >= self.threshold
                
            return False
        except Exception as e:
            print(f"Error in should_enter_trade: {e}")
            return False

    def should_exit_trade(self, price: float, trade_id: str = None) -> bool:
        """
        Determine if the strategy should exit a trade at the given price.
        
        Args:
            price: Current market price
            trade_id: Optional specific trade ID to check
            
        Returns:
            bool: True if should exit trade
        """
        try:
            # Check active trades for stop-loss or profit target conditions
            active_trades = self.metrics_collector.active_trades
            
            for trade in active_trades:
                if trade_id and trade['trade_id'] != trade_id:
                    continue
                    
                # Check stop-loss condition
                if 'stop_loss' in trade and trade['stop_loss']:
                    if trade['direction'] == 'BUY' and price <= trade['stop_loss']:
                        return True
                    elif trade['direction'] == 'SELL' and price >= trade['stop_loss']:
                        return True
                        
                # Check profit target condition  
                if 'profit_target' in trade and trade['profit_target']:
                    if trade['direction'] == 'BUY' and price >= trade['profit_target']:
                        return True
                    elif trade['direction'] == 'SELL' and price <= trade['profit_target']:
                        return True
                        
            return False
        except Exception as e:
            print(f"Error in should_exit_trade: {e}")
            return False
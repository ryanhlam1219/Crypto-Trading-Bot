"""
Simple Moving Average (SMA) Crossover Trading Strategy

This strategy implements a classic technical analysis approach using moving average
crossovers to generate buy and sell signals. It serves as both a functional trading
strategy and a reference implementation for creating custom strategies.

Strategy Logic:
- Buy when short MA crosses above long MA
- Sell when short MA crosses below long MA
- Uses market orders for execution
- Inherits signal handling from abstract Strategy base class

This implementation demonstrates:
- Proper inheritance from the abstract Strategy class
- Signal handling integration for graceful shutdown
- Trading logic with position management
- Error handling and logging
- Strategy-specific configuration parameters
"""

import time
import logging
from typing import Optional, List
from Strategies.Strategy import Strategy
from Strategies.ExchangeModels import TradeDirection, OrderType, CandleStickData
from Tests.utils import DataFetchException


class SimpleMovingAverageStrategy(Strategy):
    """
    Simple Moving Average crossover trading strategy.
    
    Generates buy/sell signals based on short and long moving average crossovers.
    Inherits graceful shutdown capabilities from the abstract Strategy base class.
    
    Args:
        client: Exchange client for trading operations
        interval: Time interval for candlestick data collection
        stop_loss_percentage: Stop loss percentage for risk management
        metrics_collector: Metrics collection for performance tracking
        short_window: Number of periods for short moving average (default: 10)
        long_window: Number of periods for long moving average (default: 20)
        min_candles: Minimum candles required before trading starts (default: 50)
        trade_quantity: Quantity to trade per order (default: 1)
        enable_logging: Enable detailed logging (default: True)
    """
    
    def __init__(self, client, interval, stop_loss_percentage, metrics_collector, 
                 short_window: int = 10, long_window: int = 20, min_candles: int = 50,
                 trade_quantity: float = 1.0, enable_logging: bool = True):
        # Initialize base class (sets up signal handling)
        super().__init__(client, interval, stop_loss_percentage, metrics_collector)
        
        # Strategy-specific parameters
        self.short_window = short_window
        self.long_window = long_window
        self.min_candles = max(min_candles, long_window)  # Ensure enough data
        self.trade_quantity = trade_quantity
        self.enable_logging = enable_logging
        
        # Strategy state
        self.candlestick_data: List[CandleStickData] = []
        self.position: Optional[str] = None  # 'long', 'short', or None
        self.last_signal: Optional[str] = None  # Track last signal to avoid duplicates
        
        # Setup logging
        if self.enable_logging:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(f"SMA_Strategy_{self.client.currency_asset}")
        else:
            self.logger = logging.getLogger()
            self.logger.disabled = True
        
        # Validate parameters
        self._validate_parameters()
        
        self.logger.info(f"Initialized SimpleMovingAverageStrategy:")
        self.logger.info(f"  Short MA Window: {self.short_window}")
        self.logger.info(f"  Long MA Window: {self.long_window}")
        self.logger.info(f"  Min Candles: {self.min_candles}")
        self.logger.info(f"  Trade Quantity: {self.trade_quantity}")
        self.logger.info(f"  Asset: {self.client.currency_asset}")

    def _validate_parameters(self):
        """Validate strategy parameters."""
        if self.short_window >= self.long_window:
            raise ValueError("Short window must be less than long window")
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("Moving average windows must be positive")
        if self.trade_quantity <= 0:
            raise ValueError("Trade quantity must be positive")
        if self.stop_loss_percentage <= 0:
            raise ValueError("Stop loss percentage must be positive")

    def execute_trade(self, price: float, direction: TradeDirection) -> bool:
        """
        Execute a trade at the given price and direction.
        
        Args:
            price: Current market price
            direction: Trade direction (BUY or SELL)
            
        Returns:
            bool: True if trade executed successfully, False otherwise
        """
        try:
            self.logger.info(f"Executing {direction.value} order at {price:.2f}")
            
            order_result = self.client.create_new_order(
                direction=direction,
                order_type=OrderType.MARKET_ORDER,
                quantity=self.trade_quantity,
                price=price
            )
            
            # Generate unique trade ID
            trade_id = f"sma_{direction.value.lower()}_{int(time.time())}"
            
            # Calculate stop loss and profit target
            if direction == TradeDirection.BUY:
                stop_loss = price * (1 - self.stop_loss_percentage / 100)
                profit_target = price * 1.02  # 2% profit target
                self.position = 'long'
            else:
                stop_loss = price * (1 + self.stop_loss_percentage / 100)
                profit_target = price * 0.98  # 2% profit target
                self.position = 'short'
            
            # Record trade with metrics collector
            self.metrics_collector.record_trade_entry(
                trade_id=trade_id,
                symbol=self.client.currency_asset,
                direction=direction.value,
                entry_price=price,
                quantity=self.trade_quantity,
                stop_loss=stop_loss,
                profit_target=profit_target
            )
            
            self.logger.info(f"Successfully executed {direction.value} order:")
            self.logger.info(f"  Price: {price:.2f}")
            self.logger.info(f"  Quantity: {self.trade_quantity}")
            self.logger.info(f"  Stop Loss: {stop_loss:.2f}")
            self.logger.info(f"  Profit Target: {profit_target:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing {direction.value} trade: {e}")
            return False

    def close_trade(self, price: float) -> bool:
        """
        Close the current position.
        
        Args:
            price: Current market price
            
        Returns:
            bool: True if position closed successfully, False otherwise
        """
        if not self.position:
            self.logger.warning("Attempted to close position when no position exists")
            return False
        
        try:
            # Determine close direction (opposite of current position)
            close_direction = TradeDirection.SELL if self.position == 'long' else TradeDirection.BUY
            
            self.logger.info(f"Closing {self.position} position at {price:.2f}")
            
            order_result = self.client.create_new_order(
                direction=close_direction,
                order_type=OrderType.MARKET_ORDER,
                quantity=self.trade_quantity,
                price=price
            )
            
            self.logger.info(f"Successfully closed {self.position} position at {price:.2f}")
            self.position = None
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing {self.position} position: {e}")
            return False

    def check_trades(self, price: float):
        """
        Check current price against moving averages and execute trades.
        
        Args:
            price: Current market price
        """
        if len(self.candlestick_data) < self.long_window:
            return
        
        # Calculate moving averages
        short_ma = self._calculate_moving_average(self.short_window)
        long_ma = self._calculate_moving_average(self.long_window)
        
        if short_ma is None or long_ma is None:
            self.logger.warning("Unable to calculate moving averages")
            return
        
        # Determine current signal
        current_signal = None
        if short_ma > long_ma:
            current_signal = 'bullish'
        elif short_ma < long_ma:
            current_signal = 'bearish'
        
        # Log moving average values periodically
        if len(self.candlestick_data) % 10 == 0:  # Every 10 candles
            self.logger.info(f"MA Status - Short: {short_ma:.2f}, Long: {long_ma:.2f}, Price: {price:.2f}")
        
        # Execute trades based on crossover signals
        if current_signal != self.last_signal and current_signal is not None:
            self.logger.info(f"Signal change detected: {self.last_signal} -> {current_signal}")
            
            if current_signal == 'bullish' and self.position != 'long':
                # Short MA crossed above long MA - bullish signal
                if self.position == 'short':
                    self.close_trade(price)
                self.execute_trade(price, TradeDirection.BUY)
                
            elif current_signal == 'bearish' and self.position != 'short':
                # Short MA crossed below long MA - bearish signal
                if self.position == 'long':
                    self.close_trade(price)
                self.execute_trade(price, TradeDirection.SELL)
            
            self.last_signal = current_signal

    def run_strategy(self, trade_interval: int):
        """
        Run the simple moving average strategy.
        
        Args:
            trade_interval: Time interval between strategy iterations (seconds)
        """
        try:
            # Check exchange connectivity
            if not self.client.get_connectivity_status():
                self.logger.error("Could not establish connection to exchange. Exiting strategy.")
                return

            # Verify account status
            self.client.get_account_status()
            self.logger.info("Starting Simple Moving Average Strategy...")
            self.logger.info(f"Trade interval: {trade_interval} seconds")
            
            # Initial data collection phase
            self.logger.info(f"Collecting initial data ({self.min_candles} candles)...")
            
            while len(self.candlestick_data) < self.min_candles and not self.is_shutdown_requested():
                try:
                    new_data = self.client.get_candle_stick_data(self.interval)
                    if isinstance(new_data, CandleStickData):
                        self.candlestick_data.append(new_data)
                        
                        if len(self.candlestick_data) % 10 == 0:
                            self.logger.info(f"Data collection progress: {len(self.candlestick_data)}/{self.min_candles} candles")
                    
                    time.sleep(trade_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt during data collection. Shutting down...")
                    return
                except Exception as e:
                    self.logger.error(f"Error collecting initial data: {e}")
                    time.sleep(trade_interval)
            
            if self.is_shutdown_requested():
                self.logger.info("Shutdown requested during data collection. Exiting...")
                return
            
            self.logger.info("Initial data collection completed. Starting trading loop...")
            
            # Main trading loop
            while not self.is_shutdown_requested():
                try:
                    # Get new market data
                    new_data = self.client.get_candle_stick_data(self.interval)
                    if isinstance(new_data, CandleStickData):
                        self.candlestick_data.append(new_data)
                        
                        # Maintain rolling window of data
                        if len(self.candlestick_data) > self.min_candles * 2:
                            self.candlestick_data = self.candlestick_data[-self.min_candles:]
                        
                        current_price = new_data.close_price
                        self.check_trades(current_price)
                    
                    time.sleep(trade_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt in trading loop. Shutting down...")
                    break
                except DataFetchException as e:
                    self.logger.error(f"Data fetch error: {e}")
                    time.sleep(trade_interval * 2)  # Longer wait on data errors
                except Exception as e:
                    self.logger.error(f"Unexpected error in trading loop: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(trade_interval)
            
            # Graceful shutdown
            self.perform_graceful_shutdown()
            
        except Exception as e:
            self.logger.error(f"Critical error in strategy execution: {e}")
            import traceback
            traceback.print_exc()
            self.perform_graceful_shutdown()
            raise

    def _calculate_moving_average(self, window: int) -> Optional[float]:
        """
        Calculate moving average for the given window.
        
        Args:
            window: Number of periods for moving average
            
        Returns:
            float: Moving average value, or None if insufficient data
        """
        if len(self.candlestick_data) < window:
            return None
        
        recent_prices = [candle.close_price for candle in self.candlestick_data[-window:]]
        return sum(recent_prices) / len(recent_prices)

    def get_strategy_status(self) -> dict:
        """
        Get current strategy status and metrics.
        
        Returns:
            dict: Strategy status information
        """
        status = {
            'strategy_name': 'SimpleMovingAverageStrategy',
            'asset': self.client.currency_asset,
            'position': self.position,
            'last_signal': self.last_signal,
            'candles_collected': len(self.candlestick_data),
            'min_candles_required': self.min_candles,
            'short_window': self.short_window,
            'long_window': self.long_window,
            'ready_to_trade': len(self.candlestick_data) >= self.long_window
        }
        
        # Add moving averages if available
        if len(self.candlestick_data) >= self.long_window:
            status['short_ma'] = self._calculate_moving_average(self.short_window)
            status['long_ma'] = self._calculate_moving_average(self.long_window)
            
            if self.candlestick_data:
                status['current_price'] = self.candlestick_data[-1].close_price
        
        return status

    def on_shutdown_signal(self, signum, frame):
        """Handle shutdown signal - strategy specific logic."""
        self.logger.info("SimpleMovingAverageStrategy received shutdown signal")
        
        # Close any open positions
        if self.position and self.candlestick_data:
            self.logger.info(f"Closing open {self.position} position due to shutdown...")
            try:
                latest_price = self.candlestick_data[-1].close_price
                self.close_trade(latest_price)
            except Exception as e:
                self.logger.error(f"Error closing position during shutdown: {e}")

    def perform_graceful_shutdown(self):
        """Simple moving average strategy specific shutdown operations."""
        self.logger.info("=" * 60)
        self.logger.info("SIMPLE MOVING AVERAGE STRATEGY - GRACEFUL SHUTDOWN")
        self.logger.info("=" * 60)
        
        try:
            # Get final strategy status
            status = self.get_strategy_status()
            
            self.logger.info("Final Strategy Status:")
            for key, value in status.items():
                self.logger.info(f"  • {key.replace('_', ' ').title()}: {value}")
            
            # Close any remaining positions
            if self.position:
                self.logger.warning(f"Open position detected: {self.position}")
                if self.candlestick_data:
                    try:
                        latest_price = self.candlestick_data[-1].close_price
                        self.close_trade(latest_price)
                        self.logger.info("Position closed during shutdown")
                    except Exception as e:
                        self.logger.error(f"Failed to close position during shutdown: {e}")
            
            # Call parent class shutdown for common functionality
            super().perform_graceful_shutdown()
            
        except Exception as e:
            self.logger.error(f"Error during SimpleMovingAverageStrategy shutdown: {e}")
            import traceback
            traceback.print_exc()
        
        self.logger.info("SimpleMovingAverageStrategy shutdown completed.")
        self.logger.info("=" * 60)
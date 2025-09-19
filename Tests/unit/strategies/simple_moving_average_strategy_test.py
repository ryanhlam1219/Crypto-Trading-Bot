"""
Comprehensive test suite for SimpleMovingAverageStrategy.

Tests cover:
- Strategy initialization and parameter validation
- Trading logic and moving average calculations
- Signal handling and graceful shutdown
- Position management and trade execution
- Error handling and edge cases
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import signal
import time
from Strategies.SimpleMovingAverageStrategy import SimpleMovingAverageStrategy
from Strategies.ExchangeModels import TradeDirection, OrderType, CandleStickData
from Tests.utils import DataFetchException
from Utils.MetricsCollector import MetricsCollector


class TestSimpleMovingAverageStrategy(unittest.TestCase):
    """Test cases for SimpleMovingAverageStrategy functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock client
        self.mock_client = Mock()
        self.mock_client.currency_asset = "BTCUSD"
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = None
        self.mock_client.create_new_order.return_value = {"status": "success"}
        
        # Create metrics collector
        self.metrics_collector = MetricsCollector()
        
        # Default strategy parameters
        self.default_params = {
            "client": self.mock_client,
            "interval": 60,
            "stop_loss_percentage": 3,
            "metrics_collector": self.metrics_collector,
            "short_window": 5,
            "long_window": 10,
            "min_candles": 15,
            "trade_quantity": 1.0,
            "enable_logging": False  # Disable logging for tests
        }
    
    def test_initialization_with_default_parameters(self):
        """Test strategy initialization with default parameters."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        
        self.assertEqual(strategy.short_window, 5)
        self.assertEqual(strategy.long_window, 10)
        self.assertEqual(strategy.min_candles, 15)
        self.assertEqual(strategy.trade_quantity, 1.0)
        self.assertIsNone(strategy.position)
        self.assertIsNone(strategy.last_signal)
        self.assertEqual(len(strategy.candlestick_data), 0)
        self.assertFalse(strategy.is_shutdown_requested())
    
    def test_initialization_with_custom_parameters(self):
        """Test strategy initialization with custom parameters."""
        custom_params = self.default_params.copy()
        custom_params.update({
            "short_window": 15,
            "long_window": 30,
            "min_candles": 100,
            "trade_quantity": 2.5
        })
        
        strategy = SimpleMovingAverageStrategy(**custom_params)
        
        self.assertEqual(strategy.short_window, 15)
        self.assertEqual(strategy.long_window, 30)
        self.assertEqual(strategy.min_candles, 100)
        self.assertEqual(strategy.trade_quantity, 2.5)
    
    def test_parameter_validation(self):
        """Test parameter validation during initialization."""
        # Test short_window >= long_window
        invalid_params = self.default_params.copy()
        invalid_params["short_window"] = 20
        invalid_params["long_window"] = 10
        
        with self.assertRaises(ValueError) as context:
            SimpleMovingAverageStrategy(**invalid_params)
        self.assertIn("Short window must be less than long window", str(context.exception))
        
        # Test negative windows
        invalid_params = self.default_params.copy()
        invalid_params["short_window"] = -5
        
        with self.assertRaises(ValueError) as context:
            SimpleMovingAverageStrategy(**invalid_params)
        self.assertIn("Moving average windows must be positive", str(context.exception))
        
        # Test negative trade quantity
        invalid_params = self.default_params.copy()
        invalid_params["trade_quantity"] = -1.0
        
        with self.assertRaises(ValueError) as context:
            SimpleMovingAverageStrategy(**invalid_params)
        self.assertIn("Trade quantity must be positive", str(context.exception))
        
        # Test negative stop loss
        invalid_params = self.default_params.copy()
        invalid_params["stop_loss_percentage"] = -3
        
        with self.assertRaises(ValueError) as context:
            SimpleMovingAverageStrategy(**invalid_params)
        self.assertIn("Stop loss percentage must be positive", str(context.exception))
    
    def test_min_candles_adjustment(self):
        """Test that min_candles is adjusted to be at least long_window."""
        params = self.default_params.copy()
        params["long_window"] = 50
        params["min_candles"] = 30  # Less than long_window
        
        strategy = SimpleMovingAverageStrategy(**params)
        
        # min_candles should be adjusted to match long_window
        self.assertEqual(strategy.min_candles, 50)
    
    def test_moving_average_calculation(self):
        """Test moving average calculation with various data scenarios."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        
        # Test with insufficient data
        self.assertIsNone(strategy._calculate_moving_average(5))
        
        # Add test data
        test_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        for i, price in enumerate(test_prices):
            candle = CandleStickData(
                open_time=i * 60000,
                open_price=price,
                high_price=price + 1,
                low_price=price - 1,
                close_price=price,
                volume=100,
                close_time=(i + 1) * 60000,
                quote_asset_volume=10000,
                num_trades=10,
                taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            strategy.candlestick_data.append(candle)
        
        # Test 5-period MA calculation
        ma_5 = strategy._calculate_moving_average(5)
        expected_ma_5 = sum(test_prices[-5:]) / 5  # Last 5 prices
        self.assertAlmostEqual(ma_5, expected_ma_5, places=2)
        
        # Test 10-period MA calculation
        ma_10 = strategy._calculate_moving_average(10)
        expected_ma_10 = sum(test_prices) / 10  # All prices
        self.assertAlmostEqual(ma_10, expected_ma_10, places=2)
    
    def test_execute_trade_buy_order(self):
        """Test execute_trade method for buy orders."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        
        # Mock metrics collector method
        strategy.metrics_collector.record_trade_entry = Mock()
        
        result = strategy.execute_trade(100.0, TradeDirection.BUY)
        
        self.assertTrue(result)
        self.assertEqual(strategy.position, 'long')
        
        # Verify order was placed correctly
        self.mock_client.create_new_order.assert_called_once_with(
            direction=TradeDirection.BUY,
            order_type=OrderType.MARKET_ORDER,
            quantity=1.0,
            price=100.0
        )
        
        # Verify metrics were recorded
        strategy.metrics_collector.record_trade_entry.assert_called_once()
    
    def test_execute_trade_sell_order(self):
        """Test execute_trade method for sell orders."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        
        # Mock metrics collector method
        strategy.metrics_collector.record_trade_entry = Mock()
        
        result = strategy.execute_trade(100.0, TradeDirection.SELL)
        
        self.assertTrue(result)
        self.assertEqual(strategy.position, 'short')
        
        # Verify order was placed correctly
        self.mock_client.create_new_order.assert_called_once_with(
            direction=TradeDirection.SELL,
            order_type=OrderType.MARKET_ORDER,
            quantity=1.0,
            price=100.0
        )
    
    def test_execute_trade_error_handling(self):
        """Test execute_trade error handling."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        
        # Mock order failure
        self.mock_client.create_new_order.side_effect = Exception("Order failed")
        
        result = strategy.execute_trade(100.0, TradeDirection.BUY)
        
        self.assertFalse(result)
        self.assertIsNone(strategy.position)  # Position should not change on error
    
    def test_close_trade_long_position(self):
        """Test close_trade method for long positions."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.position = 'long'
        
        result = strategy.close_trade(105.0)
        
        self.assertTrue(result)
        self.assertIsNone(strategy.position)
        
        # Verify sell order was placed to close long position
        self.mock_client.create_new_order.assert_called_once_with(
            direction=TradeDirection.SELL,
            order_type=OrderType.MARKET_ORDER,
            quantity=1.0,
            price=105.0
        )
    
    def test_close_trade_short_position(self):
        """Test close_trade method for short positions."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.position = 'short'
        
        result = strategy.close_trade(95.0)
        
        self.assertTrue(result)
        self.assertIsNone(strategy.position)
        
        # Verify buy order was placed to close short position
        self.mock_client.create_new_order.assert_called_once_with(
            direction=TradeDirection.BUY,
            order_type=OrderType.MARKET_ORDER,
            quantity=1.0,
            price=95.0
        )
    
    def test_close_trade_no_position(self):
        """Test close_trade when no position exists."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        
        result = strategy.close_trade(100.0)
        
        self.assertFalse(result)
        self.mock_client.create_new_order.assert_not_called()
    
    def test_close_trade_error_handling(self):
        """Test close_trade error handling."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.position = 'long'
        
        # Mock order failure
        self.mock_client.create_new_order.side_effect = Exception("Close failed")
        
        result = strategy.close_trade(105.0)
        
        self.assertFalse(result)
        self.assertEqual(strategy.position, 'long')  # Position should remain unchanged
    
    def test_check_trades_bullish_crossover(self):
        """Test check_trades method for bullish crossover signal."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.execute_trade = Mock(return_value=True)
        
        # Add data that creates bullish crossover (short MA > long MA)
        # Prices trend upward so short MA will be higher than long MA
        prices = [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]
        for i, price in enumerate(prices):
            candle = CandleStickData(
                open_time=i * 60000, open_price=price, high_price=price + 1,
                low_price=price - 1, close_price=price, volume=100,
                close_time=(i + 1) * 60000, quote_asset_volume=10000,
                num_trades=10, taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            strategy.candlestick_data.append(candle)
        
        strategy.check_trades(105.0)
        
        # Should execute buy trade due to bullish signal
        strategy.execute_trade.assert_called_once_with(105.0, TradeDirection.BUY)
        self.assertEqual(strategy.last_signal, 'bullish')
    
    def test_check_trades_bearish_crossover(self):
        """Test check_trades method for bearish crossover signal."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.execute_trade = Mock(return_value=True)
        
        # Add data that creates bearish crossover (short MA < long MA)
        # Prices trend downward so short MA will be lower than long MA
        prices = [105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95]
        for i, price in enumerate(prices):
            candle = CandleStickData(
                open_time=i * 60000, open_price=price, high_price=price + 1,
                low_price=price - 1, close_price=price, volume=100,
                close_time=(i + 1) * 60000, quote_asset_volume=10000,
                num_trades=10, taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            strategy.candlestick_data.append(candle)
        
        strategy.check_trades(95.0)
        
        # Should execute sell trade due to bearish signal
        strategy.execute_trade.assert_called_once_with(95.0, TradeDirection.SELL)
        self.assertEqual(strategy.last_signal, 'bearish')
    
    def test_check_trades_position_management(self):
        """Test check_trades position management (closing before opening new)."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.execute_trade = Mock(return_value=True)
        strategy.close_trade = Mock(return_value=True)
        strategy.position = 'short'  # Start with short position
        
        # Add bullish data
        prices = [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]
        for i, price in enumerate(prices):
            candle = CandleStickData(
                open_time=i * 60000, open_price=price, high_price=price + 1,
                low_price=price - 1, close_price=price, volume=100,
                close_time=(i + 1) * 60000, quote_asset_volume=10000,
                num_trades=10, taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            strategy.candlestick_data.append(candle)
        
        strategy.check_trades(105.0)
        
        # Should close short position first, then open long position
        strategy.close_trade.assert_called_once_with(105.0)
        strategy.execute_trade.assert_called_once_with(105.0, TradeDirection.BUY)
    
    def test_check_trades_no_duplicate_signals(self):
        """Test that duplicate signals don't trigger trades."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.execute_trade = Mock(return_value=True)
        strategy.last_signal = 'bullish'  # Already have bullish signal
        
        # Add bullish data (should maintain bullish signal)
        prices = [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105]
        for i, price in enumerate(prices):
            candle = CandleStickData(
                open_time=i * 60000, open_price=price, high_price=price + 1,
                low_price=price - 1, close_price=price, volume=100,
                close_time=(i + 1) * 60000, quote_asset_volume=10000,
                num_trades=10, taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            strategy.candlestick_data.append(candle)
        
        strategy.check_trades(105.0)
        
        # Should not execute trade since signal hasn't changed
        strategy.execute_trade.assert_not_called()
    
    def test_get_strategy_status(self):
        """Test get_strategy_status method."""
        strategy = SimpleMovingAverageStrategy(**self.default_params)
        strategy.position = 'long'
        strategy.last_signal = 'bullish'
        
        # Add some test data
        for i in range(15):
            candle = CandleStickData(
                open_time=i * 60000, open_price=100 + i, high_price=101 + i,
                low_price=99 + i, close_price=100 + i, volume=100,
                close_time=(i + 1) * 60000, quote_asset_volume=10000,
                num_trades=10, taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            strategy.candlestick_data.append(candle)
        
        status = strategy.get_strategy_status()
        
        self.assertEqual(status['strategy_name'], 'SimpleMovingAverageStrategy')
        self.assertEqual(status['asset'], 'BTCUSD')
        self.assertEqual(status['position'], 'long')
        self.assertEqual(status['last_signal'], 'bullish')
        self.assertEqual(status['candles_collected'], 15)
        self.assertEqual(status['min_candles_required'], 15)
        self.assertTrue(status['ready_to_trade'])
        self.assertIn('short_ma', status)
        self.assertIn('long_ma', status)
        self.assertIn('current_price', status)


class TestSimpleMovingAverageStrategySignalHandling(unittest.TestCase):
    """Test signal handling integration for SimpleMovingAverageStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.currency_asset = "BTCUSD"
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = None
        
        self.metrics_collector = MetricsCollector()
        
        self.strategy_params = {
            "client": self.mock_client,
            "interval": 60,
            "stop_loss_percentage": 3,
            "metrics_collector": self.metrics_collector,
            "short_window": 5,
            "long_window": 10,
            "min_candles": 15,
            "enable_logging": False
        }
    
    def test_inherits_signal_handling(self):
        """Test that SMA strategy inherits signal handling from base class."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        # Should inherit signal handling methods
        self.assertTrue(hasattr(strategy, 'is_shutdown_requested'))
        self.assertTrue(hasattr(strategy, 'request_shutdown'))
        self.assertTrue(hasattr(strategy, '_signal_handler'))
        self.assertTrue(hasattr(strategy, 'on_shutdown_signal'))
        self.assertTrue(hasattr(strategy, 'perform_graceful_shutdown'))
        
        # Initial state
        self.assertFalse(strategy.is_shutdown_requested())
    
    def test_programmatic_shutdown_request(self):
        """Test programmatic shutdown request."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        self.assertFalse(strategy.is_shutdown_requested())
        
        strategy.request_shutdown()
        
        self.assertTrue(strategy.is_shutdown_requested())
    
    @patch('signal.signal')
    def test_signal_handler_registration(self, mock_signal):
        """Test that signal handlers are registered during initialization."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        # Verify signal handlers were registered
        self.assertEqual(mock_signal.call_count, 2)
        mock_signal.assert_any_call(signal.SIGINT, strategy._signal_handler)
        mock_signal.assert_any_call(signal.SIGTERM, strategy._signal_handler)
    
    def test_on_shutdown_signal_closes_position(self):
        """Test that on_shutdown_signal closes open positions."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        strategy.close_trade = Mock(return_value=True)
        strategy.position = 'long'
        
        # Add test data
        candle = CandleStickData(
            open_time=0, open_price=100, high_price=101,
            low_price=99, close_price=100, volume=100,
            close_time=60000, quote_asset_volume=10000,
            num_trades=10, taker_buy_base_asset_volume=50,
            taker_buy_quote_asset_volume=5000
        )
        strategy.candlestick_data.append(candle)
        
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # Should attempt to close position
        strategy.close_trade.assert_called_once_with(100)
    
    def test_on_shutdown_signal_no_position(self):
        """Test on_shutdown_signal when no position exists."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        strategy.close_trade = Mock()
        strategy.position = None
        
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # Should not attempt to close position
        strategy.close_trade.assert_not_called()
    
    def test_perform_graceful_shutdown(self):
        """Test perform_graceful_shutdown method."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        strategy.close_trade = Mock(return_value=True)
        strategy.position = 'long'
        
        # Add test data
        candle = CandleStickData(
            open_time=0, open_price=100, high_price=101,
            low_price=99, close_price=100, volume=100,
            close_time=60000, quote_asset_volume=10000,
            num_trades=10, taker_buy_base_asset_volume=50,
            taker_buy_quote_asset_volume=5000
        )
        strategy.candlestick_data.append(candle)
        
        # Mock the parent class method
        with patch('Strategies.Strategy.Strategy.perform_graceful_shutdown') as mock_parent:
            strategy.perform_graceful_shutdown()
            
            # Should close position and call parent shutdown
            strategy.close_trade.assert_called_once_with(100)
            mock_parent.assert_called_once()


class TestSimpleMovingAverageStrategyRunStrategy(unittest.TestCase):
    """Test run_strategy method and integration scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.currency_asset = "BTCUSD"
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = None
        
        self.metrics_collector = MetricsCollector()
        
        self.strategy_params = {
            "client": self.mock_client,
            "interval": 60,
            "stop_loss_percentage": 3,
            "metrics_collector": self.metrics_collector,
            "short_window": 2,
            "long_window": 3,
            "min_candles": 5,  # Small numbers for faster testing
            "enable_logging": False
        }
    
    def test_run_strategy_connectivity_check(self):
        """Test run_strategy exits gracefully when no connectivity."""
        self.mock_client.get_connectivity_status.return_value = False
        
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        # Should return immediately without error
        strategy.run_strategy(1)
        
        # Should not have attempted to get account status
        self.mock_client.get_account_status.assert_not_called()
    
    @patch('time.sleep')
    def test_run_strategy_data_collection_phase(self, mock_sleep):
        """Test run_strategy data collection phase."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        # Mock data collection with a counter to prevent infinite loops
        candles = []
        for i in range(5):
            candle = CandleStickData(
                open_time=i * 60000, open_price=100 + i, high_price=101 + i,
                low_price=99 + i, close_price=100 + i, volume=100,
                close_time=(i + 1) * 60000, quote_asset_volume=10000,
                num_trades=10, taker_buy_base_asset_volume=50,
                taker_buy_quote_asset_volume=5000
            )
            candles.append(candle)
        
        # Create a call counter to control the loop
        call_count = 0
        def get_candle_side_effect(*args):
            nonlocal call_count
            if call_count < len(candles):
                result = candles[call_count]
                call_count += 1
                return result
            else:
                # After collecting required data, request shutdown to exit loop
                strategy.request_shutdown()
                return candles[-1]  # Return last candle
        
        self.mock_client.get_candle_stick_data.side_effect = get_candle_side_effect
        
        strategy.run_strategy(1)
        
        # Should have collected at least the required candles (may be +1 from trading loop)
        self.assertGreaterEqual(len(strategy.candlestick_data), 5)
        self.assertLessEqual(len(strategy.candlestick_data), 6)  # Should not exceed by much
        
        # Should have called sleep during data collection
        self.assertGreater(mock_sleep.call_count, 0)
    
    @patch('time.sleep')
    def test_run_strategy_shutdown_during_data_collection(self, mock_sleep):
        """Test run_strategy handles shutdown during data collection."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        # Request shutdown immediately
        strategy.request_shutdown()
        
        # Mock incomplete data
        candle = CandleStickData(
            open_time=0, open_price=100, high_price=101,
            low_price=99, close_price=100, volume=100,
            close_time=60000, quote_asset_volume=10000,
            num_trades=10, taker_buy_base_asset_volume=50,
            taker_buy_quote_asset_volume=5000
        )
        self.mock_client.get_candle_stick_data.return_value = candle
        
        strategy.run_strategy(1)
        
        # Should exit early without completing data collection
        self.assertLess(len(strategy.candlestick_data), strategy.min_candles)
    
    def test_run_strategy_exception_handling(self):
        """Test run_strategy handles exceptions gracefully."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        strategy.perform_graceful_shutdown = Mock()
        
        # Mock exception during connectivity check (before the try/except blocks)
        self.mock_client.get_connectivity_status.side_effect = Exception("Critical error")
        
        # Strategy should re-raise critical exceptions after graceful shutdown
        with self.assertRaises(Exception):
            strategy.run_strategy(1)
        
        # Should have called graceful shutdown
        strategy.perform_graceful_shutdown.assert_called_once()
    
    def test_run_strategy_data_fetch_exception_handling(self):
        """Test run_strategy handles DataFetchException during data collection."""
        strategy = SimpleMovingAverageStrategy(**self.strategy_params)
        
        call_count = 0
        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Allow a couple of calls before requesting shutdown
                raise DataFetchException("Data unavailable")
            else:
                # After a few failed attempts, request shutdown to exit gracefully
                strategy.request_shutdown()
                raise DataFetchException("Data unavailable")
        
        # Mock DataFetchException during data collection phase
        self.mock_client.get_candle_stick_data.side_effect = side_effect
        
        # Should not raise DataFetchException (handled gracefully)
        try:
            strategy.run_strategy(1)
        except DataFetchException:
            self.fail("Strategy should handle DataFetchException during data collection gracefully")
            
        # Strategy should have attempted data collection even with errors
        self.assertGreater(call_count, 0)


if __name__ == '__main__':
    unittest.main()
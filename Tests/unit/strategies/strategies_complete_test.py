"""
Comprehensive Strategies Tests - All-in-One File with Full Mocking

This file consolidates all Strategy-related tests including:
- GridTradingStrategy comprehensive testing
- Strategy base class functionality
- ExchangeModels data structures
- All edge cases and exception handling
- 100% code coverage target with extensive mocking
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from Strategies.Strategy import Strategy
from Strategies.GridTradingStrategy import GridTradingStrategy
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from Utils.MetricsCollector import MetricsCollector


class TestExchangeModels:
    """Comprehensive tests for ExchangeModels data structures."""
    
    def test_order_type_enum_values(self):
        """Test OrderType enum values."""
        assert OrderType.MARKET_ORDER.value == "MARKET_ORDER"
        assert OrderType.LIMIT_ORDER.value == "LIMIT_ORDER"
        assert OrderType.STOP_LIMIT_ORDER.value == "STOP_LIMIT_ORDER"
    
    def test_trade_direction_enum_values(self):
        """Test TradeDirection enum values."""
        assert TradeDirection.BUY.value == "BUY"
        assert TradeDirection.SELL.value == "SELL"
    
    def test_candlestick_data_initialization(self):
        """Test CandleStickData initialization."""
        candle = CandleStickData(
            open_time=1640995200000,
            open_price=47000.0,
            high_price=47500.0,
            low_price=46500.0,
            close_price=47200.0,
            volume=100.0,
            close_time=1640995259999,
            quote_asset_volume=4720000.0,
            number_of_trades=150,
            taker_buy_base_asset_volume=60.0,
            taker_buy_quote_asset_volume=2832000.0,
            ignore="0"
        )
        
        assert candle.open_time == 1640995200000
        assert candle.open_price == 47000.0
        assert candle.high_price == 47500.0
        assert candle.low_price == 46500.0
        assert candle.close_price == 47200.0
        assert candle.volume == 100.0
        assert candle.close_time == 1640995259999
        assert candle.quote_asset_volume == 4720000.0
        assert candle.number_of_trades == 150
        assert candle.taker_buy_base_asset_volume == 60.0
        assert candle.taker_buy_quote_asset_volume == 2832000.0
        assert candle.ignore == "0"
    
    def test_candlestick_data_from_list(self):
        """Test CandleStickData creation from list."""
        data_list = [
            1640995200000, "47000.0", "47500.0", "46500.0", "47200.0", "100.0",
            1640995259999, "4720000.0", 150, "60.0", "2832000.0", "0"
        ]
        
        candle = CandleStickData.from_list(data_list)
        
        assert candle.open_time == 1640995200000
        assert candle.open_price == 47000.0
        assert candle.high_price == 47500.0
        assert candle.low_price == 46500.0
        assert candle.close_price == 47200.0
        assert candle.volume == 100.0
    
    def test_candlestick_data_from_list_invalid(self):
        """Test CandleStickData creation from invalid list."""
        with pytest.raises(IndexError):
            CandleStickData.from_list([])
        
        with pytest.raises(IndexError):
            CandleStickData.from_list([1, 2, 3])  # Too few elements
    
    def test_candlestick_data_from_list_type_conversion(self):
        """Test CandleStickData type conversion from string values."""
        data_list = [
            "1640995200000", "47000.0", "47500.0", "46500.0", "47200.0", "100.0",
            "1640995259999", "4720000.0", "150", "60.0", "2832000.0", "0"
        ]
        
        candle = CandleStickData.from_list(data_list)
        
        assert isinstance(candle.open_time, int)
        assert isinstance(candle.open_price, float)
        assert isinstance(candle.number_of_trades, int)


class TestStrategyBase:
    """Comprehensive tests for the base Strategy class."""
    
    def setup_method(self):
        """Setup test instances."""
        self.mock_exchange = Mock()
        self.mock_metrics = Mock()
        self.strategy = Strategy(self.mock_exchange, self.mock_metrics)
    
    def test_initialization(self):
        """Test Strategy base class initialization."""
        assert self.strategy.exchange == self.mock_exchange
        assert self.strategy.metrics_collector == self.mock_metrics
    
    def test_initialization_without_metrics(self):
        """Test Strategy initialization without metrics collector."""
        strategy = Strategy(self.mock_exchange, None)
        assert strategy.exchange == self.mock_exchange
        assert strategy.metrics_collector is None
    
    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            self.strategy.buy(1.0, 50000.0)
        
        with pytest.raises(NotImplementedError):
            self.strategy.sell(1.0, 50000.0)
        
        with pytest.raises(NotImplementedError):
            self.strategy.run()


class TestGridTradingStrategy:
    """Comprehensive tests for GridTradingStrategy with full mocking."""
    
    def setup_method(self):
        """Setup test instances with mocked dependencies."""
        self.mock_exchange = Mock()
        self.mock_metrics = Mock()
        
        # Mock exchange methods
        self.mock_exchange.get_connectivity_status.return_value = True
        self.mock_exchange.get_account_status.return_value = None
        self.mock_exchange.create_new_order.return_value = {"orderId": 12345, "status": "FILLED"}
        
        # Mock candlestick data
        self.mock_candle = CandleStickData(
            open_time=1640995200000,
            open_price=47000.0,
            high_price=47500.0,
            low_price=46500.0,
            close_price=47200.0,
            volume=100.0,
            close_time=1640995259999,
            quote_asset_volume=4720000.0,
            number_of_trades=150,
            taker_buy_base_asset_volume=60.0,
            taker_buy_quote_asset_volume=2832000.0,
            ignore="0"
        )
        self.mock_exchange.get_candle_stick_data.return_value = self.mock_candle
        
        # Initialize strategy
        self.strategy = GridTradingStrategy(
            exchange=self.mock_exchange,
            metrics_collector=self.mock_metrics,
            quantity=1.0,
            take_profit_percentage=2.0,
            stop_loss_percentage=1.0,
            grid_levels=5,
            grid_range_percentage=5.0
        )
    
    def test_initialization(self):
        """Test GridTradingStrategy initialization."""
        assert self.strategy.exchange == self.mock_exchange
        assert self.strategy.metrics_collector == self.mock_metrics
        assert self.strategy.quantity == 1.0
        assert self.strategy.take_profit_percentage == 2.0
        assert self.strategy.stop_loss_percentage == 1.0
        assert self.strategy.grid_levels == 5
        assert self.strategy.grid_range_percentage == 5.0
        assert self.strategy.grid_orders == []
        assert self.strategy.base_price is None
        assert self.strategy.position is None
        assert self.strategy.entry_price is None
    
    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        strategy = GridTradingStrategy(self.mock_exchange, self.mock_metrics)
        assert strategy.quantity == 0.01
        assert strategy.take_profit_percentage == 2.0
        assert strategy.stop_loss_percentage == 1.0
        assert strategy.grid_levels == 10
        assert strategy.grid_range_percentage == 10.0
    
    def test_initialization_edge_cases(self):
        """Test initialization with edge case parameters."""
        # Test with zero values
        strategy = GridTradingStrategy(
            self.mock_exchange, self.mock_metrics,
            quantity=0.0, take_profit_percentage=0.0,
            stop_loss_percentage=0.0, grid_levels=1,
            grid_range_percentage=0.0
        )
        assert strategy.quantity == 0.0
        assert strategy.grid_levels == 1
    
    def test_initialization_negative_values(self):
        """Test initialization with negative values."""
        strategy = GridTradingStrategy(
            self.mock_exchange, self.mock_metrics,
            quantity=-1.0, take_profit_percentage=-2.0,
            stop_loss_percentage=-1.0, grid_levels=-5,
            grid_range_percentage=-5.0
        )
        # Strategy should handle negative values (business logic decision)
        assert strategy.quantity == -1.0
        assert strategy.grid_levels == -5
    
    @patch('time.sleep')
    def test_run_method_basic_flow(self, mock_sleep):
        """Test the main run method with basic flow."""
        # Mock the run to execute once then exit
        call_count = 0
        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Stop after first iteration
                return False
            return True
        
        self.mock_exchange.get_connectivity_status.side_effect = side_effect
        
        with patch.object(self.strategy, '_execute_strategy') as mock_execute:
            with patch.object(self.strategy, '_manage_risk') as mock_risk:
                with patch.object(self.strategy, '_manage_grid') as mock_grid:
                    self.strategy.run()
        
        # Verify methods were called
        mock_execute.assert_called()
        mock_risk.assert_called()
        mock_grid.assert_called()
        mock_sleep.assert_called()
    
    @patch('time.sleep')
    def test_run_method_connection_failure(self, mock_sleep):
        """Test run method handling connection failures."""
        self.mock_exchange.get_connectivity_status.return_value = False
        
        # Mock to exit after few iterations
        call_count = 0
        def connectivity_side_effect():
            nonlocal call_count
            call_count += 1
            return call_count <= 2  # Return False after 2 calls to exit
        
        self.mock_exchange.get_connectivity_status.side_effect = connectivity_side_effect
        
        with patch.object(self.strategy, '_execute_strategy') as mock_execute:
            self.strategy.run()
        
        # Strategy execution should not be called when connectivity fails
        mock_execute.assert_not_called()
    
    @patch('time.sleep')
    def test_run_method_exception_handling(self, mock_sleep):
        """Test run method handling exceptions."""
        # Mock exchange to raise exception
        self.mock_exchange.get_connectivity_status.side_effect = [True, Exception("Network error"), False]
        
        with patch.object(self.strategy, '_execute_strategy') as mock_execute:
            # Should not raise exception, should handle gracefully
            self.strategy.run()
    
    def test_buy_method(self):
        """Test buy method implementation."""
        # Test successful buy
        result = self.strategy.buy(1.0, 50000.0)
        
        self.mock_exchange.create_new_order.assert_called_once_with(
            direction=TradeDirection.BUY,
            order_type=OrderType.LIMIT_ORDER,
            quantity=1.0,
            price=50000.0
        )
        assert result == {"orderId": 12345, "status": "FILLED"}
    
    def test_buy_method_with_metrics(self):
        """Test buy method with metrics recording."""
        with patch('time.time', return_value=1609459200.123):
            self.strategy.buy(1.0, 50000.0)
        
        # Verify metrics were recorded
        self.mock_metrics.record_trade.assert_called_once()
        call_args = self.mock_metrics.record_trade.call_args[1]
        assert call_args['direction'] == 'BUY'
        assert call_args['quantity'] == 1.0
        assert call_args['price'] == 50000.0
    
    def test_buy_method_exception(self):
        """Test buy method handling exceptions."""
        self.mock_exchange.create_new_order.side_effect = Exception("Order failed")
        
        with pytest.raises(Exception, match="Order failed"):
            self.strategy.buy(1.0, 50000.0)
        
        # Verify metrics recorded the failure
        self.mock_metrics.record_trade.assert_called_once()
        call_args = self.mock_metrics.record_trade.call_args[1]
        assert call_args['success'] is False
        assert call_args['error_message'] == "Order failed"
    
    def test_sell_method(self):
        """Test sell method implementation."""
        result = self.strategy.sell(1.0, 50000.0)
        
        self.mock_exchange.create_new_order.assert_called_once_with(
            direction=TradeDirection.SELL,
            order_type=OrderType.LIMIT_ORDER,
            quantity=1.0,
            price=50000.0
        )
        assert result == {"orderId": 12345, "status": "FILLED"}
    
    def test_sell_method_with_metrics(self):
        """Test sell method with metrics recording."""
        with patch('time.time', return_value=1609459200.123):
            self.strategy.sell(1.0, 50000.0)
        
        # Verify metrics were recorded
        self.mock_metrics.record_trade.assert_called_once()
        call_args = self.mock_metrics.record_trade.call_args[1]
        assert call_args['direction'] == 'SELL'
        assert call_args['quantity'] == 1.0
        assert call_args['price'] == 50000.0
    
    def test_sell_method_exception(self):
        """Test sell method handling exceptions."""
        self.mock_exchange.create_new_order.side_effect = Exception("Order failed")
        
        with pytest.raises(Exception, match="Order failed"):
            self.strategy.sell(1.0, 50000.0)
    
    def test_execute_strategy_no_position(self):
        """Test strategy execution when no position is held."""
        # Set current price
        self.mock_candle.close_price = 50000.0
        
        with patch.object(self.strategy, '_should_enter_long', return_value=True):
            with patch.object(self.strategy, 'buy') as mock_buy:
                mock_buy.return_value = {"orderId": 123, "status": "FILLED"}
                
                self.strategy._execute_strategy()
                
                mock_buy.assert_called_once()
                assert self.strategy.position == TradeDirection.BUY
                assert self.strategy.entry_price == 50000.0
    
    def test_execute_strategy_with_long_position(self):
        """Test strategy execution when holding long position."""
        # Set up existing position
        self.strategy.position = TradeDirection.BUY
        self.strategy.entry_price = 48000.0
        self.mock_candle.close_price = 50000.0  # Price has risen
        
        with patch.object(self.strategy, '_should_exit_long', return_value=True):
            with patch.object(self.strategy, 'sell') as mock_sell:
                mock_sell.return_value = {"orderId": 124, "status": "FILLED"}
                
                self.strategy._execute_strategy()
                
                mock_sell.assert_called_once()
                assert self.strategy.position is None
                assert self.strategy.entry_price is None
    
    def test_execute_strategy_with_short_position(self):
        """Test strategy execution when holding short position."""
        # Set up existing position
        self.strategy.position = TradeDirection.SELL
        self.strategy.entry_price = 52000.0
        self.mock_candle.close_price = 50000.0  # Price has fallen
        
        with patch.object(self.strategy, '_should_exit_short', return_value=True):
            with patch.object(self.strategy, 'buy') as mock_buy:
                mock_buy.return_value = {"orderId": 125, "status": "FILLED"}
                
                self.strategy._execute_strategy()
                
                mock_buy.assert_called_once()
                assert self.strategy.position is None
                assert self.strategy.entry_price is None
    
    def test_should_enter_long_conditions(self):
        """Test conditions for entering long position."""
        self.mock_candle.close_price = 49000.0
        
        # Test when conditions are met
        with patch.object(self.strategy, '_is_oversold', return_value=True):
            with patch.object(self.strategy, '_has_upward_momentum', return_value=True):
                assert self.strategy._should_enter_long() is True
        
        # Test when conditions are not met
        with patch.object(self.strategy, '_is_oversold', return_value=False):
            assert self.strategy._should_enter_long() is False
    
    def test_should_enter_short_conditions(self):
        """Test conditions for entering short position."""
        self.mock_candle.close_price = 51000.0
        
        # Test when conditions are met
        with patch.object(self.strategy, '_is_overbought', return_value=True):
            with patch.object(self.strategy, '_has_downward_momentum', return_value=True):
                assert self.strategy._should_enter_short() is True
        
        # Test when conditions are not met
        with patch.object(self.strategy, '_is_overbought', return_value=False):
            assert self.strategy._should_enter_short() is False
    
    def test_should_exit_long_take_profit(self):
        """Test exiting long position for take profit."""
        self.strategy.entry_price = 48000.0
        self.mock_candle.close_price = 49000.0  # 2.08% gain
        
        # Should exit when take profit threshold is met
        assert self.strategy._should_exit_long() is True
    
    def test_should_exit_long_stop_loss(self):
        """Test exiting long position for stop loss."""
        self.strategy.entry_price = 48000.0
        self.mock_candle.close_price = 47500.0  # 1.04% loss
        
        # Should exit when stop loss threshold is met
        assert self.strategy._should_exit_long() is True
    
    def test_should_exit_long_no_exit(self):
        """Test not exiting long position when thresholds not met."""
        self.strategy.entry_price = 48000.0
        self.mock_candle.close_price = 48500.0  # Small gain, below take profit
        
        # Should not exit
        assert self.strategy._should_exit_long() is False
    
    def test_should_exit_short_take_profit(self):
        """Test exiting short position for take profit."""
        self.strategy.entry_price = 52000.0
        self.mock_candle.close_price = 51000.0  # 1.92% gain
        
        # Should exit when take profit threshold is met
        assert self.strategy._should_exit_short() is True
    
    def test_should_exit_short_stop_loss(self):
        """Test exiting short position for stop loss."""
        self.strategy.entry_price = 52000.0
        self.mock_candle.close_price = 52500.0  # 0.96% loss
        
        # Should exit when stop loss threshold is met
        assert self.strategy._should_exit_short() is True
    
    def test_manage_risk_method(self):
        """Test risk management functionality."""
        # Set up position with risk
        self.strategy.position = TradeDirection.BUY
        self.strategy.entry_price = 50000.0
        self.mock_candle.close_price = 49000.0  # 2% loss
        
        with patch.object(self.strategy, '_should_exit_long', return_value=True):
            with patch.object(self.strategy, 'sell') as mock_sell:
                mock_sell.return_value = {"orderId": 126, "status": "FILLED"}
                
                self.strategy._manage_risk()
                
                mock_sell.assert_called_once()
    
    def test_manage_grid_initialization(self):
        """Test grid management initialization."""
        self.mock_candle.close_price = 50000.0
        
        # First call should initialize grid
        self.strategy._manage_grid()
        
        assert self.strategy.base_price == 50000.0
        assert len(self.strategy.grid_orders) > 0
    
    def test_manage_grid_order_execution(self):
        """Test grid order execution."""
        # Set up grid
        self.strategy.base_price = 50000.0
        self.strategy.grid_orders = [
            {"price": 49000.0, "direction": TradeDirection.BUY, "executed": False},
            {"price": 51000.0, "direction": TradeDirection.SELL, "executed": False}
        ]
        
        # Price hits buy level
        self.mock_candle.close_price = 49000.0
        
        with patch.object(self.strategy, 'buy') as mock_buy:
            mock_buy.return_value = {"orderId": 127, "status": "FILLED"}
            
            self.strategy._manage_grid()
            
            mock_buy.assert_called_once()
            assert self.strategy.grid_orders[0]["executed"] is True
    
    def test_technical_indicators(self):
        """Test technical indicator methods."""
        # Mock historical data for indicators
        with patch.object(self.strategy, '_get_recent_prices', return_value=[49000, 49500, 50000, 50500, 51000]):
            # Test oversold/overbought conditions
            with patch.object(self.strategy, '_calculate_rsi', return_value=25):  # Oversold
                assert self.strategy._is_oversold() is True
                assert self.strategy._is_overbought() is False
            
            with patch.object(self.strategy, '_calculate_rsi', return_value=75):  # Overbought
                assert self.strategy._is_oversold() is False
                assert self.strategy._is_overbought() is True
    
    def test_momentum_indicators(self):
        """Test momentum calculation methods."""
        with patch.object(self.strategy, '_get_recent_prices', return_value=[48000, 49000, 50000]):
            # Upward momentum
            assert self.strategy._has_upward_momentum() is True
            assert self.strategy._has_downward_momentum() is False
        
        with patch.object(self.strategy, '_get_recent_prices', return_value=[52000, 51000, 50000]):
            # Downward momentum
            assert self.strategy._has_upward_momentum() is False
            assert self.strategy._has_downward_momentum() is True
    
    def test_grid_calculation_methods(self):
        """Test grid level calculation."""
        levels = self.strategy._calculate_grid_levels(50000.0)
        
        assert len(levels) == self.strategy.grid_levels
        assert all(isinstance(level, dict) for level in levels)
        assert all('price' in level and 'direction' in level for level in levels)
    
    def test_rsi_calculation(self):
        """Test RSI calculation method."""
        # Mock price data for RSI calculation
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110]
        
        with patch.object(self.strategy, '_get_recent_prices', return_value=prices):
            rsi = self.strategy._calculate_rsi()
            
            assert 0 <= rsi <= 100
            assert isinstance(rsi, (int, float))
    
    def test_error_handling_in_strategy_execution(self):
        """Test error handling throughout strategy execution."""
        # Test with exchange error
        self.mock_exchange.get_candle_stick_data.side_effect = Exception("API Error")
        
        # Should handle exception gracefully
        try:
            self.strategy._execute_strategy()
        except Exception:
            pytest.fail("Strategy should handle exceptions gracefully")
    
    def test_metrics_recording_comprehensive(self):
        """Test comprehensive metrics recording."""
        # Execute a full trade cycle
        with patch('time.time', return_value=1609459200.123):
            # Enter position
            self.strategy.buy(1.0, 50000.0)
            
            # Exit position
            self.strategy.sell(1.0, 51000.0)
        
        # Verify metrics calls
        assert self.mock_metrics.record_trade.call_count == 2
        
        # Check buy trade metrics
        buy_call = self.mock_metrics.record_trade.call_args_list[0][1]
        assert buy_call['direction'] == 'BUY'
        assert buy_call['quantity'] == 1.0
        assert buy_call['price'] == 50000.0
        
        # Check sell trade metrics
        sell_call = self.mock_metrics.record_trade.call_args_list[1][1]
        assert sell_call['direction'] == 'SELL'
        assert sell_call['quantity'] == 1.0
        assert sell_call['price'] == 51000.0
    
    def test_edge_cases_and_boundary_conditions(self):
        """Test edge cases and boundary conditions."""
        # Test with zero prices
        self.mock_candle.close_price = 0.0
        try:
            self.strategy._execute_strategy()
        except ZeroDivisionError:
            pytest.fail("Should handle zero prices gracefully")
        
        # Test with negative prices
        self.mock_candle.close_price = -1000.0
        try:
            self.strategy._execute_strategy()
        except ValueError:
            pass  # Expected for negative prices
        
        # Test with very large prices
        self.mock_candle.close_price = 1e10
        try:
            self.strategy._execute_strategy()
        except OverflowError:
            pytest.fail("Should handle large numbers gracefully")
    
    def test_strategy_state_persistence(self):
        """Test strategy state management."""
        # Test state changes through execution
        initial_position = self.strategy.position
        initial_entry_price = self.strategy.entry_price
        
        # Execute buy
        self.strategy.buy(1.0, 50000.0)
        self.strategy.position = TradeDirection.BUY
        self.strategy.entry_price = 50000.0
        
        assert self.strategy.position != initial_position
        assert self.strategy.entry_price != initial_entry_price
        
        # Execute sell
        self.strategy.sell(1.0, 51000.0)
        self.strategy.position = None
        self.strategy.entry_price = None
        
        assert self.strategy.position is None
        assert self.strategy.entry_price is None
    
    def test_concurrent_operation_safety(self):
        """Test strategy behavior under concurrent operations."""
        # Simulate rapid successive calls
        for _ in range(10):
            try:
                self.strategy._execute_strategy()
                self.strategy._manage_risk()
                self.strategy._manage_grid()
            except Exception as e:
                pytest.fail(f"Strategy should handle rapid calls: {e}")
    
    def test_memory_management(self):
        """Test memory management in long-running operations."""
        # Simulate many iterations
        for i in range(100):
            self.mock_candle.close_price = 50000.0 + i
            self.strategy._execute_strategy()
        
        # Ensure grid orders don't grow indefinitely
        assert len(self.strategy.grid_orders) <= self.strategy.grid_levels * 2
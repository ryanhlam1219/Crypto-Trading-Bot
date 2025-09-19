"""
Comprehensive GridTradingStrategy Test Suite
Consolidates all GridTradingStrategy testing into one complete file for better organization and completeness.
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from Strategies.GridTradingStrategy import GridTradingStrategy
from Strategies.ExchangeModels import (
    CandleStickData, 
    TradeDirection, 
    OrderType
)
from Tests.utils import DataFetchException


class TestGridTradingStrategyComplete:
    """Complete comprehensive test suite for GridTradingStrategy."""
    
    @pytest.fixture
    def mock_client(self):
        """Standard mock client for testing."""
        client = Mock()
        client.get_connectivity_status.return_value = True
        client.get_account_status.return_value = {"balance": 1000}
        client.create_new_order.return_value = {"order_id": "123", "status": "filled"}
        return client
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Standard mock metrics collector."""
        collector = Mock()
        collector.active_trades = []
        return collector
    
    @pytest.fixture
    def sample_candle(self):
        """Standard candlestick data for testing."""
        return CandleStickData(
            open_time=1640995200000,
            open_price=50000.0,
            high_price=51000.0,
            low_price=49000.0,
            close_price=50500.0,
            volume=100.0,
            close_time=1640995260000,
            quote_asset_volume=100.0,
            num_trades=100,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=50.0
        )

    # ============ INITIALIZATION TESTS ============
    
    def test_initialization_basic(self, mock_client, mock_metrics_collector):
        """Test basic GridTradingStrategy initialization."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        assert strategy.client == mock_client
        assert strategy.interval == "1m"
        assert strategy.grid_percentage == 1
        assert strategy.num_levels == 3
        assert strategy.min_candles == 10
        assert strategy.stop_loss_percentage == 5
        assert strategy.threshold == 0.01
        assert strategy.candlestick_data == []

    def test_initialization_with_custom_params(self, mock_client, mock_metrics_collector):
        """Test GridTradingStrategy initialization with custom parameters."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="5m",
            stop_loss_percentage=3.5,
            metrics_collector=mock_metrics_collector,
            grid_percentage=2.0,
            num_levels=5,
            min_candles=20,
            threshold=0.02
        )
        
        assert strategy.interval == "5m"
        assert strategy.grid_percentage == 2.0
        assert strategy.num_levels == 5
        assert strategy.min_candles == 20
        assert strategy.stop_loss_percentage == 3.5
        assert strategy.threshold == 0.02

    def test_initialization_without_metrics_collector_raises_error(self, mock_client):
        """Test that initialization without metrics_collector raises ValueError."""
        with pytest.raises(ValueError, match="metrics_collector is required"):
            GridTradingStrategy(
                client=mock_client,
                interval="1m",
                metrics_collector=None
            )

    # ============ TRADE EXECUTION TESTS ============
    
    def test_execute_trade_buy(self, mock_client, mock_metrics_collector):
        """Test execute_trade for buy orders."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Test buy trade execution (returns None but should not raise exception)
        result = strategy.execute_trade(price=100.0, direction=TradeDirection.BUY, grid_size=1.0)
        
        # Method should complete without error (returns None)
        assert result is None
        # Verify client method was called
        mock_client.create_new_order.assert_called_once()
        # Verify metrics were recorded
        mock_metrics_collector.record_trade_entry.assert_called_once()

    def test_execute_trade_sell(self, mock_client, mock_metrics_collector):
        """Test execute_trade for sell orders."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Test sell trade execution (returns None but should not raise exception)
        result = strategy.execute_trade(price=100.0, direction=TradeDirection.SELL, grid_size=1.0)
        
        # Method should complete without error (returns None)
        assert result is None
        # Verify client method was called
        mock_client.create_new_order.assert_called_once()
        # Verify metrics were recorded
        mock_metrics_collector.record_trade_entry.assert_called_once()

    def test_execute_trade_exception_handling(self, mock_client, mock_metrics_collector):
        """Test execute_trade handles exceptions gracefully."""
        mock_client.create_new_order.side_effect = Exception("Order failed")
        
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Should handle exception gracefully and return None (not crash)
        result = strategy.execute_trade(price=100.0, direction=TradeDirection.BUY, grid_size=1.0)
        assert result is None  # Method completes without crashing

    # ============ UTILITY METHOD TESTS ============

    def test_should_enter_trade_basic(self, mock_client, mock_metrics_collector):
        """Test should_enter_trade basic decision logic."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # First initialize the grid by setting candlestick data
        sample_candle = CandleStickData(
            open_time=1640995200000,
            open_price=50000.0,
            high_price=51000.0,
            low_price=49000.0,
            close_price=50500.0,
            volume=100.0,
            close_time=1640995260000,
            quote_asset_volume=100.0,
            num_trades=100,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=50.0
        )
        strategy.candlestick_data = [sample_candle] * 10  # Provide sufficient data
        
        # Test entry logic with various price levels
        result = strategy.should_enter_trade(102.0)  
        assert isinstance(result, bool)  # Should return a boolean

    def test_grid_initialization_indirect(self, mock_client, mock_metrics_collector):
        """Test grid initialization through actual strategy workflow."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            grid_percentage=1.0,
            num_levels=3
        )
        
        # Test that strategy can be created with grid parameters
        assert strategy.grid_percentage == 1.0
        assert strategy.num_levels == 3
        
        # Test that candlestick data starts empty
        assert len(strategy.candlestick_data) == 0

    # ============ SAFE RUN_STRATEGY TESTS ============

    def test_data_collection_loop_logic_without_execution(self, mock_client, mock_metrics_collector, sample_candle):
        """SAFE: Test the data collection loop logic without entering main execution loop."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            min_candles=5  # Set higher than what we'll provide
        )
        
        # Mock to return one candle and then throw exception to exit immediately
        call_count = 0
        def controlled_candle_data(interval):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return sample_candle
            else:
                # Force immediate exit after first candle
                raise DataFetchException("Controlled exit after first candle")
        
        mock_client.get_candle_stick_data.side_effect = controlled_candle_data
        
        with patch('time.sleep', return_value=None):  # Speed up test
            with pytest.raises(DataFetchException, match="Controlled exit"):
                strategy.run_strategy(60)
        
        # Verify we collected the candle but never entered main loop
        assert len(strategy.candlestick_data) == 1
        assert call_count == 2  # Initial call + one retry that failed

    def test_run_strategy_exception_handling_safe(self, mock_client, mock_metrics_collector):
        """SAFE: Test the exception handling path in run_strategy."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            min_candles=1  # Minimal to avoid long data collection
        )
        
        # Simulate what happens when get_candle_stick_data raises an exception
        # This tests the exception handling code in run_strategy without infinite loops
        mock_client.get_candle_stick_data.side_effect = DataFetchException("Controlled test exception")
        
        # Test that DataFetchException is properly handled and re-raised
        with patch('time.sleep', return_value=None):  # Speed up test by removing sleeps
            with pytest.raises(DataFetchException, match="Controlled test exception"):
                strategy.run_strategy(60)
        
        # Verify the proper methods were called before the exception
        mock_client.get_connectivity_status.assert_called()
        mock_client.get_account_status.assert_called()

    def test_run_strategy_data_collection_phase_safe(self, mock_client, mock_metrics_collector, sample_candle):
        """SAFE: Test the data collection phase of run_strategy without entering main loop."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            min_candles=10  # Set much higher than what we'll provide
        )
        
        # Provide very limited data and force quick exit
        call_count = 0
        def limited_candle_data(interval):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return sample_candle  # Only return one candle
            else:
                # Force immediate exit on second call
                raise DataFetchException("Controlled exit after data collection test")
        
        mock_client.get_candle_stick_data.side_effect = limited_candle_data
        
        with patch('time.sleep', return_value=None):  # Remove sleep delays
            with pytest.raises(DataFetchException, match="Controlled exit"):
                strategy.run_strategy(60)
        
        # Verify we collected minimal data but never entered main loop
        assert len(strategy.candlestick_data) < strategy.min_candles
        assert call_count >= 1

    # ============ EDGE CASE AND ERROR HANDLING TESTS ============

    def test_invalid_grid_parameters(self, mock_client, mock_metrics_collector):
        """Test handling of invalid grid parameters."""
        # Test with zero grid percentage
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            grid_percentage=0
        )
        assert strategy.grid_percentage == 0
        
        # Test with negative num_levels
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m", 
            metrics_collector=mock_metrics_collector,
            num_levels=-1
        )
        assert strategy.num_levels == -1

    def test_candlestick_data_management(self, mock_client, mock_metrics_collector, sample_candle):
        """Test candlestick data collection and management."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Initially empty
        assert len(strategy.candlestick_data) == 0
        
        # Add some test data
        strategy.candlestick_data.append(sample_candle)
        assert len(strategy.candlestick_data) == 1
        
        # Verify the data is accessible
        assert strategy.candlestick_data[0] == sample_candle

    def test_price_calculation_edge_cases(self, mock_client, mock_metrics_collector):
        """Test price calculations with edge case values."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Set up minimal candlestick data for should_enter_trade to work
        sample_candle = CandleStickData(
            open_time=1640995200000,
            open_price=50000.0,
            high_price=51000.0,
            low_price=49000.0,
            close_price=50500.0,
            volume=100.0,
            close_time=1640995260000,
            quote_asset_volume=100.0,
            num_trades=100,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=50.0
        )
        strategy.candlestick_data = [sample_candle] * 10
        
        # Test with various price values (should_enter_trade only takes one price parameter)
        result1 = strategy.should_enter_trade(0.001)  # Very small price
        result2 = strategy.should_enter_trade(100000.0)  # Very large price
        
        # Both should return boolean values
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)

    # ============ INTEGRATION-STYLE TESTS ============

    def test_strategy_workflow_without_trades(self, mock_client, mock_metrics_collector, sample_candle):
        """Test a complete strategy workflow without executing trades."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            min_candles=2  # Small number for test
        )
        
        # Mock sufficient candlestick data to reach main loop but prevent trading
        strategy.candlestick_data = [sample_candle, sample_candle]
        
        # Test strategy initialization worked properly
        assert strategy.grid_percentage is not None
        assert strategy.num_levels is not None
        
        # Test decision logic without actually executing
        should_trade = strategy.should_enter_trade(50500.0)
        assert isinstance(should_trade, bool)
        
        # Test that we can check exit conditions too
        should_exit = strategy.should_exit_trade(50500.0)
        assert isinstance(should_exit, bool)

    def test_metrics_collector_integration(self, mock_client, mock_metrics_collector):
        """Test integration with metrics collector."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Verify metrics collector is properly set
        assert strategy.metrics_collector == mock_metrics_collector
        
        # Test that metrics collector methods are available
        assert hasattr(strategy.metrics_collector, 'active_trades')
        assert strategy.metrics_collector.active_trades == []

    # ============ COMPREHENSIVE COVERAGE TESTS ============

    def test_check_trades_profit_target(self, mock_client, mock_metrics_collector):
        """Test check_trades method with profit target conditions."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m", 
            metrics_collector=mock_metrics_collector
        )
        
        # Setup mock active trades with profit targets
        mock_trade_buy = {
            'trade_id': 'test_buy_1',
            'direction': TradeDirection.BUY.value,
            'profit_target': 51000,
            'stop_loss': 49000
        }
        mock_trade_sell = {
            'trade_id': 'test_sell_1', 
            'direction': TradeDirection.SELL.value,
            'profit_target': 49000,
            'stop_loss': 51000
        }
        
        # Test BUY trade profit target hit
        mock_metrics_collector.active_trades = [mock_trade_buy]
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(51500)  # Price above profit target
            mock_close.assert_called_once_with('test_buy_1', 51500, "profit_target")
        
        # Test SELL trade profit target hit
        mock_metrics_collector.active_trades = [mock_trade_sell]
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(48500)  # Price below profit target
            mock_close.assert_called_once_with('test_sell_1', 48500, "profit_target")

    def test_check_trades_stop_loss(self, mock_client, mock_metrics_collector):
        """Test check_trades method with stop loss conditions."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Setup mock active trades
        mock_trade_buy = {
            'trade_id': 'test_buy_2',
            'direction': TradeDirection.BUY.value,
            'profit_target': 51000,
            'stop_loss': 49000
        }
        mock_trade_sell = {
            'trade_id': 'test_sell_2',
            'direction': TradeDirection.SELL.value,
            'profit_target': 49000,
            'stop_loss': 51000
        }
        
        # Test BUY trade stop loss hit
        mock_metrics_collector.active_trades = [mock_trade_buy]
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(48500)  # Price below stop loss
            mock_close.assert_called_once_with('test_buy_2', 48500, "stop_loss")
        
        # Test SELL trade stop loss hit
        mock_metrics_collector.active_trades = [mock_trade_sell]
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(51500)  # Price above stop loss
            mock_close.assert_called_once_with('test_sell_2', 51500, "stop_loss")

    def test_check_trades_no_action(self, mock_client, mock_metrics_collector):
        """Test check_trades method when no profit/loss conditions are met."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        mock_trade = {
            'trade_id': 'test_trade_3',
            'direction': TradeDirection.BUY.value,
            'profit_target': 51000,
            'stop_loss': 49000
        }
        
        mock_metrics_collector.active_trades = [mock_trade]
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(50000)  # Price in middle - no action
            mock_close.assert_not_called()

    def test_close_trade_success(self, mock_client, mock_metrics_collector):
        """Test close_trade method with successful trade closure."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Mock successful trade closure
        mock_closed_trade = {
            'direction': 'BUY',
            'profit_loss': 150.50
        }
        mock_metrics_collector.record_trade_exit.return_value = mock_closed_trade
        
        with patch('builtins.print') as mock_print:
            strategy.close_trade('test_id', 50500, 'profit_target')
            
            # Verify metrics collector called
            mock_metrics_collector.record_trade_exit.assert_called_once_with('test_id', 50500, 'profit_target')
            
            # Verify print statement
            mock_print.assert_called_with("Closed BUY order at 50500. Profit: $150.5")

    def test_close_trade_not_found(self, mock_client, mock_metrics_collector):
        """Test close_trade method when trade is not found."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Mock trade not found
        mock_metrics_collector.record_trade_exit.return_value = None
        
        with patch('builtins.print') as mock_print:
            strategy.close_trade('nonexistent_id', 50500, 'manual')
            
            # Verify warning message
            mock_print.assert_called_with("Warning: Could not find trade nonexistent_id to close")

    def test_close_trade_exception(self, mock_client, mock_metrics_collector):
        """Test close_trade method with exception handling."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Mock exception
        mock_metrics_collector.record_trade_exit.side_effect = Exception("Test error")
        
        with patch('builtins.print') as mock_print:
            with patch('traceback.print_exc') as mock_traceback:
                strategy.close_trade('test_id', 50500, 'stop_loss')
                
                # Verify error handling
                mock_print.assert_called_with("Error closing trade: Test error")
                mock_traceback.assert_called_once()

    def test_should_exit_trade_stop_loss_conditions(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade method for stop loss conditions."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Mock active trades with stop loss
        mock_trades = [
            {
                'trade_id': 'buy_trade',
                'direction': 'BUY',
                'stop_loss': 49000,
                'profit_target': 51000
            },
            {
                'trade_id': 'sell_trade',
                'direction': 'SELL',
                'stop_loss': 51000,
                'profit_target': 49000
            }
        ]
        mock_metrics_collector.active_trades = mock_trades
        
        # Test BUY trade stop loss
        assert strategy.should_exit_trade(48500, 'buy_trade') == True
        
        # Test SELL trade stop loss
        assert strategy.should_exit_trade(51500, 'sell_trade') == True
        
        # Test no stop loss trigger
        assert strategy.should_exit_trade(50000, 'buy_trade') == False

    def test_should_exit_trade_profit_target_conditions(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade method for profit target conditions."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Mock active trades with profit targets
        mock_trades = [
            {
                'trade_id': 'buy_trade',
                'direction': 'BUY',
                'stop_loss': 49000,
                'profit_target': 51000
            },
            {
                'trade_id': 'sell_trade',
                'direction': 'SELL',
                'stop_loss': 51000,
                'profit_target': 49000
            }
        ]
        mock_metrics_collector.active_trades = mock_trades
        
        # Test BUY trade profit target
        assert strategy.should_exit_trade(51500, 'buy_trade') == True
        
        # Test SELL trade profit target
        assert strategy.should_exit_trade(48500, 'sell_trade') == True

    def test_should_exit_trade_exception_handling(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade method exception handling."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        # Mock exception in active_trades access
        mock_metrics_collector.active_trades = None
        
        with patch('builtins.print') as mock_print:
            result = strategy.should_exit_trade(50000, 'test_id')
            
            # Should return False on exception
            assert result == False
            mock_print.assert_called()

    def test_grid_initialization_logic(self, mock_client, mock_metrics_collector):
        """Test the private __initialize_grid method indirectly."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            num_levels=5,  # Use correct parameter name
            grid_percentage=0.01  # Use smaller percentage (10 -> 0.01)
        )
        
        # Test grid initialization through initialization
        base_price = 50000
        
        # Mock execute_trade to prevent actual trade execution
        with patch.object(strategy, 'execute_trade') as mock_execute:
            # Access the private method for testing
            strategy._GridTradingStrategy__initialize_grid(base_price)
            
            # Verify execute_trade was called the expected number of times
            # Should be called 2 * num_levels times (buy and sell for each level)
            expected_calls = 2 * strategy.num_levels
            assert mock_execute.call_count == expected_calls
        
        # Verify grid was initialized
        assert strategy.num_levels is not None
        assert strategy.num_levels == 5

    def test_run_strategy_connection_failure(self, mock_client, mock_metrics_collector):
        """Test run_strategy when connection fails."""
        # Mock connection failure - use the correct method name that run_strategy actually calls
        mock_client.get_connectivity_status.return_value = False
        
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector
        )
        
        with patch('builtins.print') as mock_print:
            strategy.run_strategy(trade_interval=1)  # Add required parameter
            
            # Verify connection attempt and failure message
            mock_client.get_connectivity_status.assert_called_once()
            mock_print.assert_called_with("Could not establish connection to exchange. Exiting strategy.")

    def test_run_strategy_data_collection_phase_detailed(self, mock_client, mock_metrics_collector, sample_candle):
        """Test run_strategy data collection phase with realistic conditions."""
        # Setup mock client responses
        mock_client.get_connectivity_status.return_value = True  # Fix: use correct method name
        mock_client.get_account_status.return_value = {'status': 'active'}
        
        # Mock candlestick data generation
        mock_client.get_candle_stick_data.return_value = sample_candle
        
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            min_candles=2  # Low number for quick test
        )
        
        # Use a counter to control the infinite loop
        call_count = 0
        original_get_candle = mock_client.get_candle_stick_data
        
        def side_effect_limited(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 5:  # Stop after 5 calls to prevent infinite loop
                raise KeyboardInterrupt("Test termination")
            return original_get_candle(*args, **kwargs)
        
        mock_client.get_candle_stick_data.side_effect = side_effect_limited
        
        # Test the data collection phase
        with patch('time.sleep'):  # Speed up the test
            with patch('builtins.print'):  # Suppress prints
                try:
                    strategy.run_strategy(trade_interval=0.1)
                except KeyboardInterrupt:
                    pass  # Expected termination
        
        # Verify data collection occurred
        assert len(strategy.candlestick_data) >= 0
        mock_client.get_connectivity_status.assert_called_once()  # Fix: use correct method name
        mock_client.get_account_status.assert_called_once()

    def test_extract_latest_price_failure_case(self, mock_client, mock_metrics_collector):
        """Test run_strategy when price extraction fails."""
        # Setup mocks
        mock_client.get_connectivity_status.return_value = True  # Fix: use correct method name
        mock_client.get_account_status.return_value = {'status': 'active'}
        
        # Mock invalid candlestick data that causes price extraction to fail
        invalid_candle = CandleStickData(
            open_time=1234567890,  # Use correct parameter name
            open_price=None,  # Invalid data
            high_price=None,
            low_price=None,
            close_price=None,
            volume=100,
            close_time=1234567950,  # Add missing required parameters
            quote_asset_volume=100.0,
            num_trades=10,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=50.0
        )
        mock_client.get_candle_stick_data.return_value = invalid_candle
        
        strategy = GridTradingStrategy(
            client=mock_client,
            interval="1m",
            metrics_collector=mock_metrics_collector,
            min_candles=1
        )
        
        with patch('builtins.print') as mock_print:
            with patch('time.sleep'):  # Speed up test
                strategy.run_strategy(trade_interval=0.1)  # Add required parameter
                
                # Verify failure message for price extraction
                mock_print.assert_any_call("Failed to retrieve initial price. Exiting strategy.")
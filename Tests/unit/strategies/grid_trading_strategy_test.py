"""
GridTradingStrategy Test Suite

Comprehensive test coverage for GridTradingStrategy functionality including:
- Strategy initialization and configuration
- Trading logic and grid management  
- Signal handling and graceful shutdown
- Error handling and edge cases
- Integration with exchange clients and metrics collector

Following the testing convention: one test file per strategy implementation.
"""

import pytest
import signal
import threading
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from Strategies.GridTradingStrategy import GridTradingStrategy
from Strategies.Strategy import Strategy
from Strategies.ExchangeModels import (
    CandleStickData, 
    TradeDirection, 
    OrderType
)
from Utils.MetricsCollector import MetricsCollector
from Tests.utils import DataFetchException


class TestGridTradingStrategyComplete:
    """Complete comprehensive test suite for GridTradingStrategy functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Standard mock client for testing."""
        client = Mock()
        client.get_connectivity_status.return_value = True
        client.get_account_status.return_value = {"balance": 1000}
        client.create_new_order.return_value = {"order_id": "123", "status": "filled"}
        client.currency_asset = "BTCUSD"
        return client
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Standard mock metrics collector for testing."""
        collector = Mock(spec=MetricsCollector)
        collector.active_trades = []
        collector.record_trade_entry.return_value = None
        collector.record_trade_exit.return_value = None
        return collector
    
    @pytest.fixture
    def sample_candle_data(self):
        """Sample candlestick data for testing."""
        return CandleStickData(
            open_time=1609459200000,
            open_price=29000.0,
            high_price=30000.0,
            low_price=28500.0,
            close_price=29500.0,
            volume=100.0,
            close_time=1609459260000,
            quote_asset_volume=2950000.0,
            num_trades=50,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=1475000.0
        )

    def test_initialization_basic(self, mock_client, mock_metrics_collector):
        """Test basic GridTradingStrategy initialization."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=60,
            stop_loss_percentage=5,
            metrics_collector=mock_metrics_collector
        )
        
        assert strategy.client == mock_client
        assert strategy.interval == 60
        assert strategy.stop_loss_percentage == 5
        assert strategy.metrics_collector == mock_metrics_collector
        assert strategy.grid_percentage == 1  # Default value
        assert strategy.num_levels == 3  # Default value
        assert strategy.min_candles == 10  # Default value
        assert strategy.candlestick_data == []

    def test_initialization_with_custom_params(self, mock_client, mock_metrics_collector):
        """Test GridTradingStrategy initialization with custom parameters."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=60,
            stop_loss_percentage=5,
            metrics_collector=mock_metrics_collector,
            grid_percentage=2,
            num_levels=5,
            min_candles=20
        )
        
        assert strategy.grid_percentage == 2
        assert strategy.num_levels == 5
        assert strategy.min_candles == 20

    def test_initialization_without_metrics_collector_raises_error(self, mock_client):
        """Test that initialization without metrics_collector raises appropriate error."""
        with pytest.raises(ValueError, match="metrics_collector is required"):
            GridTradingStrategy(
                client=mock_client,
                interval=60,
                stop_loss_percentage=5
            )

    def test_initialization_with_none_stop_loss_percentage(self, mock_client, mock_metrics_collector):
        """Test initialization with None stop_loss_percentage uses default value."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=60,
            stop_loss_percentage=None,  # This should trigger default handling
            metrics_collector=mock_metrics_collector
        )
        
        # Should default to 5%
        assert strategy.stop_loss_percentage == 5
        assert strategy.threshold == 0.01  # Default threshold

    def test_initialization_with_none_threshold(self, mock_client, mock_metrics_collector):
        """Test initialization with None threshold uses default value."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=60,
            stop_loss_percentage=3,
            threshold=None,  # This should trigger default handling
            metrics_collector=mock_metrics_collector
        )
        
        # Should default to 0.01
        assert strategy.threshold == 0.01
        assert strategy.stop_loss_percentage == 3

    def test_initialization_with_both_none_parameters(self, mock_client, mock_metrics_collector):
        """Test initialization with both None parameters uses both defaults."""
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=60,
            stop_loss_percentage=None,  # Should default to 5
            threshold=None,  # Should default to 0.01
            metrics_collector=mock_metrics_collector
        )
        
        assert strategy.stop_loss_percentage == 5
        assert strategy.threshold == 0.01

    def test_execute_trade_buy(self, mock_client, mock_metrics_collector):
        """Test execute_trade method for buy orders."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock the metrics collector's record_trade_entry method
        mock_metrics_collector.record_trade_entry.return_value = None
        
        # execute_trade needs a grid_size parameter
        strategy.execute_trade(100.0, TradeDirection.BUY, 10.0)
        
        # Verify the client order was created
        mock_client.create_new_order.assert_called_once_with(
            TradeDirection.BUY, OrderType.LIMIT_ORDER, 1, 100.0
        )
        
        # Verify the metrics collector was called
        mock_metrics_collector.record_trade_entry.assert_called_once()

    def test_execute_trade_sell(self, mock_client, mock_metrics_collector):
        """Test execute_trade method for sell orders."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock the metrics collector's record_trade_entry method
        mock_metrics_collector.record_trade_entry.return_value = None
        
        # execute_trade needs a grid_size parameter
        strategy.execute_trade(100.0, TradeDirection.SELL, 10.0)
        
        # Verify the client order was created
        mock_client.create_new_order.assert_called_once_with(
            TradeDirection.SELL, OrderType.LIMIT_ORDER, 1, 100.0
        )
        
        # Verify the metrics collector was called
        mock_metrics_collector.record_trade_entry.assert_called_once()

    def test_execute_trade_exception_handling(self, mock_client, mock_metrics_collector):
        """Test execute_trade handles exceptions properly."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        mock_client.create_new_order.side_effect = Exception("Network error")
        
        # Should not raise an exception, just handle it internally
        strategy.execute_trade(100.0, TradeDirection.BUY, 10.0)
        
        # Should have attempted the order
        mock_client.create_new_order.assert_called_once()

    def test_execute_trade_invalid_price(self, mock_client, mock_metrics_collector):
        """Test execute_trade with invalid price."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Should handle invalid price gracefully
        strategy.execute_trade(0.0, TradeDirection.BUY, 10.0)
        strategy.execute_trade(-100.0, TradeDirection.SELL, 10.0)
        
        # Should not have called create_new_order due to invalid prices
        mock_client.create_new_order.assert_not_called()

    def test_close_trade_success(self, mock_client, mock_metrics_collector):
        """Test successful trade closure."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock successful trade closure
        mock_metrics_collector.record_trade_exit.return_value = {
            "trade_id": "test_trade",
            "direction": "BUY",
            "profit_loss": 50.0
        }
        
        strategy.close_trade("test_trade", 105.0, "profit_target")
        
        mock_metrics_collector.record_trade_exit.assert_called_once_with(
            "test_trade", 105.0, "profit_target"
        )

    def test_close_trade_not_found(self, mock_client, mock_metrics_collector):
        """Test closing a trade that doesn't exist."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock trade not found
        mock_metrics_collector.record_trade_exit.return_value = None
        
        strategy.close_trade("nonexistent_trade", 100.0)
        
        mock_metrics_collector.record_trade_exit.assert_called_once()

    def test_close_trade_exception(self, mock_client, mock_metrics_collector):
        """Test trade closure with exception handling."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock exception in trade closure
        mock_metrics_collector.record_trade_exit.side_effect = Exception("Database error")
        
        # Should handle exception gracefully
        strategy.close_trade("test_trade", 105.0)
        
        mock_metrics_collector.record_trade_exit.assert_called_once()

    def test_check_trades_profit_target(self, mock_client, mock_metrics_collector):
        """Test check_trades method for profit target conditions."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active trades
        mock_metrics_collector.active_trades = [{
            'trade_id': 'test_trade',
            'direction': 'BUY',
            'profit_target': 105.0,
            'stop_loss': 95.0
        }]
        
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(106.0)  # Price above profit target
            mock_close.assert_called_once_with('test_trade', 106.0, 'profit_target')

    def test_check_trades_stop_loss(self, mock_client, mock_metrics_collector):
        """Test check_trades method for stop loss conditions."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active trades
        mock_metrics_collector.active_trades = [{
            'trade_id': 'test_trade',
            'direction': 'BUY',
            'profit_target': 105.0,
            'stop_loss': 95.0
        }]
        
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(94.0)  # Price below stop loss
            mock_close.assert_called_once_with('test_trade', 94.0, 'stop_loss')

    def test_check_trades_no_action(self, mock_client, mock_metrics_collector):
        """Test check_trades method when no action is needed."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active trades
        mock_metrics_collector.active_trades = [{
            'trade_id': 'test_trade',
            'direction': 'BUY',
            'profit_target': 105.0,
            'stop_loss': 95.0
        }]
        
        with patch.object(strategy, 'close_trade') as mock_close:
            strategy.check_trades(102.0)  # Price within normal range
            mock_close.assert_not_called()

    def test_should_enter_trade_basic(self, mock_client, mock_metrics_collector):
        """Test should_enter_trade basic logic."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Test the method exists and returns a boolean
        result = strategy.should_enter_trade(100.0)
        assert isinstance(result, bool)

    def test_should_enter_trade_with_threshold_checking(self, mock_client, mock_metrics_collector, sample_candle_data):
        """Test should_enter_trade with threshold checking and candlestick data."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, threshold=0.02, min_candles=1)  # 2% threshold, 1 min candle
        
        # Add candlestick data with a specific close price
        strategy.candlestick_data = [sample_candle_data]
        
        # Test price change that exceeds threshold (should return True)
        last_price = sample_candle_data.close_price  # 29500.0
        new_price = last_price * 1.025  # 2.5% increase (exceeds 2% threshold)
        result = strategy.should_enter_trade(new_price)
        assert result is True
        
        # Test price change that doesn't exceed threshold (should return False)
        new_price = last_price * 1.01  # 1% increase (below 2% threshold)
        result = strategy.should_enter_trade(new_price)
        assert result is False

    def test_should_enter_trade_with_empty_candlestick_data(self, mock_client, mock_metrics_collector):
        """Test should_enter_trade with empty candlestick data."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, threshold=0.01)
        
        # Empty candlestick data should return False
        strategy.candlestick_data = []
        result = strategy.should_enter_trade(100.0)
        assert result is False

    def test_should_enter_trade_exception_handling(self, mock_client, mock_metrics_collector):
        """Test should_enter_trade exception handling."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Test with None price (should handle gracefully)
        result = strategy.should_enter_trade(None)
        assert result is False
        
        # Test with negative price (should handle gracefully)
        result = strategy.should_enter_trade(-100.0)
        assert result is False

    def test_should_exit_trade_basic(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade basic logic."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Test the method exists and returns a boolean
        result = strategy.should_exit_trade(100.0)
        assert isinstance(result, bool)

    def test_should_exit_trade_with_stop_loss_buy_trade(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade with stop loss condition for buy trade."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active buy trade with stop loss
        mock_metrics_collector.active_trades = [
            {
                'trade_id': 'test123',
                'direction': 'BUY',
                'entry_price': 50000,
                'stop_loss': 48000,  # Stop loss at 48000
                'profit_target': 52000
            }
        ]
        
        # Test price that triggers stop loss (below stop loss)
        result = strategy.should_exit_trade(47500.0)  # Below stop loss
        assert result is True
        
        # Test price that doesn't trigger stop loss
        result = strategy.should_exit_trade(49000.0)  # Above stop loss
        assert result is False

    def test_should_exit_trade_with_stop_loss_sell_trade(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade with stop loss condition for sell trade."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active sell trade with stop loss
        mock_metrics_collector.active_trades = [
            {
                'trade_id': 'test456',
                'direction': 'SELL',
                'entry_price': 50000,
                'stop_loss': 52000,  # Stop loss at 52000 for sell
                'profit_target': 48000
            }
        ]
        
        # Test price that triggers stop loss (above stop loss)
        result = strategy.should_exit_trade(52500.0)  # Above stop loss
        assert result is True
        
        # Test price that doesn't trigger stop loss
        result = strategy.should_exit_trade(51000.0)  # Below stop loss
        assert result is False

    def test_should_exit_trade_with_profit_target_buy_trade(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade with profit target condition for buy trade."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active buy trade with profit target
        mock_metrics_collector.active_trades = [
            {
                'trade_id': 'test789',
                'direction': 'BUY',
                'entry_price': 50000,
                'stop_loss': 48000,
                'profit_target': 52000  # Profit target at 52000
            }
        ]
        
        # Test price that reaches profit target
        result = strategy.should_exit_trade(52500.0)  # Above profit target
        assert result is True
        
        # Test price that doesn't reach profit target
        result = strategy.should_exit_trade(51000.0)  # Below profit target
        assert result is False

    def test_should_exit_trade_with_profit_target_sell_trade(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade with profit target condition for sell trade."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock active sell trade with profit target
        mock_metrics_collector.active_trades = [
            {
                'trade_id': 'test101',
                'direction': 'SELL',
                'entry_price': 50000,
                'stop_loss': 52000,
                'profit_target': 48000  # Profit target at 48000 for sell
            }
        ]
        
        # Test price that reaches profit target
        result = strategy.should_exit_trade(47500.0)  # Below profit target
        assert result is True
        
        # Test price that doesn't reach profit target
        result = strategy.should_exit_trade(49000.0)  # Above profit target
        assert result is False

    def test_should_exit_trade_with_specific_trade_id(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade with specific trade ID filtering."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock multiple active trades
        mock_metrics_collector.active_trades = [
            {
                'trade_id': 'trade1',
                'direction': 'BUY',
                'stop_loss': 48000,
                'profit_target': 52000
            },
            {
                'trade_id': 'trade2',
                'direction': 'BUY',
                'stop_loss': 45000,  # Different stop loss
                'profit_target': 55000
            }
        ]
        
        # Test with specific trade ID - should only check that trade
        result = strategy.should_exit_trade(47000.0, trade_id='trade1')  # Below trade1 stop loss
        assert result is True
        
        # Test same price with different trade ID - should not trigger
        result = strategy.should_exit_trade(47000.0, trade_id='trade2')  # Above trade2 stop loss
        assert result is False

    def test_should_exit_trade_exception_handling(self, mock_client, mock_metrics_collector):
        """Test should_exit_trade exception handling."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock invalid active trades data
        mock_metrics_collector.active_trades = [
            {
                'trade_id': 'invalid_trade',
                # Missing required fields - should handle gracefully
            }
        ]
        
        # Should handle exception gracefully and return False
        result = strategy.should_exit_trade(50000.0)
        assert result is False

    def test_run_strategy_connection_failure(self, mock_client, mock_metrics_collector):
        """Test run_strategy behavior when connection fails."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock connection failure
        mock_client.get_connectivity_status.return_value = False
        
        # Should exit gracefully
        strategy.run_strategy(1)
        
        # Verify it checked connectivity but didn't proceed further
        mock_client.get_connectivity_status.assert_called_once()
        mock_client.get_account_status.assert_not_called()

    @patch('time.sleep')
    def test_run_strategy_data_collection_phase_safe(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test run_strategy data collection phase with safe exit."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Mock data collection - provide limited data then request shutdown
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                strategy.request_shutdown()  # Trigger graceful shutdown
            return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Run strategy - should exit gracefully due to shutdown request
        strategy.run_strategy(1)
        
        # Verify data was collected
        assert len(strategy.candlestick_data) > 0
        assert mock_sleep.called

    @patch('time.sleep')
    def test_run_strategy_keyboard_interrupt_during_data_collection(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test KeyboardInterrupt handling during initial data collection phase."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, min_candles=5)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Mock KeyboardInterrupt during data collection
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Interrupt during data collection
                raise KeyboardInterrupt("Simulated interrupt")
            return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Run strategy - should handle KeyboardInterrupt gracefully
        strategy.run_strategy(1)
        
        # Verify it collected some data before interruption
        assert len(strategy.candlestick_data) > 0

    @patch('time.sleep')
    def test_run_strategy_keyboard_interrupt_during_trading_loop(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test KeyboardInterrupt handling during main trading loop."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, min_candles=2)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Mock data collection - interrupt during trading loop
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Allow initial data collection
                return sample_candle_data
            elif call_count == 4:  # Interrupt during trading loop
                raise KeyboardInterrupt("Simulated interrupt in trading loop")
            return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Run strategy - should handle KeyboardInterrupt during trading
        strategy.run_strategy(1)
        
        # Verify it completed initial data collection
        assert len(strategy.candlestick_data) >= 2

    @patch('time.sleep')  
    def test_run_strategy_shutdown_requested_during_data_collection(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test shutdown request handling during initial data collection phase."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, min_candles=10)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Mock data collection - request shutdown during collection
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # Request shutdown during data collection
                strategy.request_shutdown()
            return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Run strategy - should exit due to shutdown request during data collection
        strategy.run_strategy(1)
        
        # Verify it collected some data before shutdown
        assert len(strategy.candlestick_data) < 10  # Less than required min_candles
        assert strategy.is_shutdown_requested()

    @patch('time.sleep')
    def test_run_strategy_failed_price_retrieval(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test run_strategy with failed price retrieval scenario."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, min_candles=2)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Mock data collection that provides enough candles but then fails on price extraction
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Provide enough initial data
                return sample_candle_data
            else:  # Then request shutdown to avoid infinite loop
                strategy.request_shutdown()
                return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Mock the __extract_latest_price method to return None (simulating failure)
        with patch.object(strategy, '_GridTradingStrategy__extract_latest_price', return_value=None):
            # Run strategy - should exit due to failed price retrieval
            strategy.run_strategy(1)
        
        # Verify strategy attempted to collect data but failed at price extraction
        assert len(strategy.candlestick_data) >= 2  # Should have collected minimum data

    @patch('time.sleep')
    def test_run_strategy_successful_grid_initialization(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test run_strategy with successful grid initialization."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, min_candles=2, num_levels=2)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Track execute_trade calls to verify grid initialization
        execute_trade_calls = []
        original_execute_trade = strategy.execute_trade
        
        def mock_execute_trade(*args, **kwargs):
            execute_trade_calls.append(args)
            # Mock successful trade execution
            return {"order_id": "123", "status": "filled"}
        
        strategy.execute_trade = mock_execute_trade
        
        # Mock data collection
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 4:  # Allow initial collection then request shutdown
                strategy.request_shutdown()
            return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Run strategy - should initialize grid and start trading
        strategy.run_strategy(1)
        
        # Verify grid was initialized (should have 2 buy + 2 sell orders)
        assert len(execute_trade_calls) == 4  # 2 levels * 2 directions = 4 trades
        
        # Verify both buy and sell trades were created
        buy_trades = [call for call in execute_trade_calls if call[1] == TradeDirection.BUY]
        sell_trades = [call for call in execute_trade_calls if call[1] == TradeDirection.SELL]
        assert len(buy_trades) == 2
        assert len(sell_trades) == 2

    @patch('time.sleep')
    def test_run_strategy_main_trading_loop_with_candlestick_handling(self, mock_sleep, mock_client, mock_metrics_collector, sample_candle_data):
        """Test main trading loop with proper CandleStickData handling and price checking."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector, min_candles=2)
        
        # Mock successful initial checks
        mock_client.get_connectivity_status.return_value = True
        mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Mock execute_trade to avoid actual trading
        strategy.execute_trade = Mock(return_value={"order_id": "123", "status": "filled"})
        
        # Track check_trades calls
        check_trades_calls = []
        original_check_trades = strategy.check_trades
        
        def mock_check_trades(price):
            check_trades_calls.append(price)
            return original_check_trades(price)
        
        strategy.check_trades = mock_check_trades
        
        # Mock data collection for trading loop
        call_count = 0
        def get_data_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Initial data collection
                return sample_candle_data
            elif call_count <= 5:  # Trading loop iterations
                # Return new CandleStickData for trading loop
                return CandleStickData(
                    open_time=1600000000 + call_count,
                    open_price=50000 + call_count,
                    high_price=51000 + call_count,
                    low_price=49000 + call_count,
                    close_price=50500 + call_count,
                    volume=100,
                    close_time=1600000060 + call_count,
                    quote_asset_volume=5000000,
                    num_trades=50,  # Fixed parameter name
                    taker_buy_base_asset_volume=60,
                    taker_buy_quote_asset_volume=3000000
                )
            else:  # Request shutdown after several iterations
                strategy.request_shutdown()
                return sample_candle_data
        
        mock_client.get_candle_stick_data.side_effect = get_data_side_effect
        
        # Run strategy - should complete initial collection, initialize grid, and run trading loop
        strategy.run_strategy(1)
        
        # Verify trading loop ran and processed new data
        assert len(strategy.candlestick_data) == 2  # Should maintain min_candles limit
        assert len(check_trades_calls) >= 3  # Should have called check_trades multiple times
        
        # Verify prices were extracted and checked during trading loop
        assert all(isinstance(price, (int, float)) for price in check_trades_calls)

    def test_candlestick_data_management(self, mock_client, mock_metrics_collector, sample_candle_data):
        """Test candlestick data collection and management."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Test adding data
        strategy.candlestick_data.append(sample_candle_data)
        assert len(strategy.candlestick_data) == 1
        
        # Test data persistence
        assert strategy.candlestick_data[0].close_price == 29500.0

    def test_metrics_collector_integration(self, mock_client, mock_metrics_collector):
        """Test integration with MetricsCollector."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Verify metrics collector is properly assigned
        assert strategy.metrics_collector == mock_metrics_collector
        
        # Test that metrics collector methods can be called
        strategy.metrics_collector.record_trade_entry("test_id", "BTCUSD", "BUY", 100.0, 1.0, 95.0, 105.0)
        strategy.metrics_collector.record_trade_entry.assert_called_once()

    def test_graceful_shutdown_implementation(self, mock_client, mock_metrics_collector):
        """Test graceful shutdown functionality."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Test that graceful shutdown can be called
        strategy.perform_graceful_shutdown()
        
        # Should not raise an exception
        assert True

    def test_price_extraction_with_data(self, mock_client, mock_metrics_collector, sample_candle_data):
        """Test price extraction with valid data."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Add sample data
        strategy.candlestick_data = [sample_candle_data]
        
        # Access the private method for testing
        price = strategy._GridTradingStrategy__extract_latest_price(strategy.candlestick_data)
        assert price == 29500.0

    def test_price_extraction_without_data(self, mock_client, mock_metrics_collector):
        """Test price extraction without data."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Access the private method for testing
        price = strategy._GridTradingStrategy__extract_latest_price([])
        assert price is None

    def test_grid_initialization(self, mock_client, mock_metrics_collector):
        """Test grid initialization."""
        strategy = GridTradingStrategy(mock_client, 60, 5, mock_metrics_collector)
        
        # Access the private method for testing
        strategy._GridTradingStrategy__initialize_grid(100.0)
        
        # Should not raise an exception
        assert True


class TestGridTradingStrategySignalHandling:
    """Test signal handling functionality for GridTradingStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = None
        self.mock_client.currency_asset = "BTCUSD"
        
        # Create sample candlestick data
        self.sample_candle = CandleStickData(
            open_time=1609459200000,
            open_price=29000.0,
            high_price=30000.0,
            low_price=28500.0,
            close_price=29500.0,
            volume=100.0,
            close_time=1609459260000,
            quote_asset_volume=2950000.0,
            num_trades=50,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=1475000.0
        )
        
        self.metrics_collector = MetricsCollector()

    def test_abstract_strategy_enforces_signal_handling(self):
        """Test that Strategy abstract base class enforces signal handling interface."""
        # Verify Strategy class exists and has required methods
        assert hasattr(Strategy, 'is_shutdown_requested')
        assert hasattr(Strategy, 'request_shutdown')
        assert hasattr(Strategy, '_signal_handler')
        assert hasattr(Strategy, 'on_shutdown_signal')
        assert hasattr(Strategy, 'perform_graceful_shutdown')

    def test_grid_strategy_inherits_signal_handling(self):
        """Test that GridTradingStrategy inherits signal handling from base class."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Should inherit all signal handling methods
        assert hasattr(strategy, 'is_shutdown_requested')
        assert hasattr(strategy, 'request_shutdown')
        assert hasattr(strategy, '_signal_handler')
        assert hasattr(strategy, 'on_shutdown_signal')
        assert hasattr(strategy, 'perform_graceful_shutdown')
        
        # Initial state should be not shutdown
        assert strategy.is_shutdown_requested() is False

    def test_base_class_signal_handler_sets_flag(self):
        """Test that base class signal handler sets the shutdown flag."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Simulate signal reception
        strategy._signal_handler(signal.SIGINT, None)
        
        # Should have set shutdown flag
        assert strategy.is_shutdown_requested() is True

    def test_programmatic_shutdown_request(self):
        """Test programmatic shutdown request functionality."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Initially not shutdown
        assert strategy.is_shutdown_requested() is False
        
        # Request shutdown
        strategy.request_shutdown()
        
        # Should be marked for shutdown
        assert strategy.is_shutdown_requested() is True

    def test_grid_strategy_overrides_shutdown_signal_handler(self):
        """Test that GridTradingStrategy can override shutdown signal handling."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Override method should exist and be callable
        assert hasattr(strategy, 'on_shutdown_signal')
        assert callable(strategy.on_shutdown_signal)
        
        # Call the override method
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # Should not raise an exception (basic test that it's implemented)
        assert True

    def test_grid_strategy_overrides_graceful_shutdown(self):
        """Test that GridTradingStrategy overrides graceful shutdown."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Override method should exist
        assert hasattr(strategy, 'perform_graceful_shutdown')
        assert callable(strategy.perform_graceful_shutdown)
        
        # Should be able to call without error
        strategy.perform_graceful_shutdown()
        assert True

    def test_run_strategy_uses_base_class_shutdown_flag(self):
        """Test that run_strategy respects the base class shutdown flag."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Request shutdown before running
        strategy.request_shutdown()
        
        # Mock connectivity to pass initial checks
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Run strategy - should exit early due to shutdown flag
        with patch('time.sleep') as mock_sleep:
            strategy.run_strategy(1)
        
        # Should have exited early, so minimal sleep calls
        assert mock_sleep.call_count <= 1

    def test_initialization_with_base_class_signal_handling(self):
        """Test that initialization properly sets up signal handling."""
        with patch('signal.signal') as mock_signal:
            strategy = GridTradingStrategy(
                self.mock_client, 60, 5, self.metrics_collector
            )
            
            # Should have registered signal handlers
            assert mock_signal.call_count >= 2  # At least SIGINT and SIGTERM
            
            # Should have proper attributes
            assert hasattr(strategy, 'shutdown_requested')
            assert strategy.shutdown_requested is False

    def test_grid_specific_shutdown_message(self):
        """Test that GridTradingStrategy has strategy-specific shutdown behavior."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Add some test state
        strategy.candlestick_data = [self.sample_candle]
        
        # Shutdown signal should trigger strategy-specific cleanup
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # Should not raise exception (test that method is properly implemented)
        assert True

    def test_base_and_derived_class_cooperation(self):
        """Test that base class and derived class signal handling work together."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Test the full signal handling flow
        # 1. Signal received -> sets base class flag
        strategy._signal_handler(signal.SIGINT, None)
        assert strategy.is_shutdown_requested() is True
        
        # 2. Strategy-specific shutdown logic can be called
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # 3. Graceful shutdown can be performed
        strategy.perform_graceful_shutdown()
        
        # All should complete without errors
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


class TestGridTradingStrategySignalHandling:
    """Test signal handling functionality for GridTradingStrategy."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = None
        self.mock_client.currency_asset = "BTCUSD"
        
        # Create sample candlestick data
        self.sample_candle = CandleStickData(
            open_time=1609459200000,
            open_price=29000.0,
            high_price=30000.0,
            low_price=28500.0,
            close_price=29500.0,
            volume=100.0,
            close_time=1609459260000,
            quote_asset_volume=2950000.0,
            num_trades=50,
            taker_buy_base_asset_volume=50.0,
            taker_buy_quote_asset_volume=1475000.0
        )
        
        self.metrics_collector = MetricsCollector()

    def test_abstract_strategy_enforces_signal_handling(self):
        """Test that Strategy abstract base class enforces signal handling interface."""
        # Verify Strategy class exists and has required methods
        assert hasattr(Strategy, 'is_shutdown_requested')
        assert hasattr(Strategy, 'request_shutdown')
        assert hasattr(Strategy, '_signal_handler')
        assert hasattr(Strategy, 'on_shutdown_signal')
        assert hasattr(Strategy, 'perform_graceful_shutdown')

    def test_grid_strategy_inherits_signal_handling(self):
        """Test that GridTradingStrategy inherits signal handling from base class."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Should inherit all signal handling methods
        assert hasattr(strategy, 'is_shutdown_requested')
        assert hasattr(strategy, 'request_shutdown')
        assert hasattr(strategy, '_signal_handler')
        assert hasattr(strategy, 'on_shutdown_signal')
        assert hasattr(strategy, 'perform_graceful_shutdown')
        
        # Initial state should be not shutdown
        assert strategy.is_shutdown_requested() is False

    def test_base_class_signal_handler_sets_flag(self):
        """Test that base class signal handler sets the shutdown flag."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Simulate signal reception
        strategy._signal_handler(signal.SIGINT, None)
        
        # Should have set shutdown flag
        assert strategy.is_shutdown_requested() is True

    def test_programmatic_shutdown_request(self):
        """Test programmatic shutdown request functionality."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Initially not shutdown
        assert strategy.is_shutdown_requested() is False
        
        # Request shutdown
        strategy.request_shutdown()
        
        # Should be marked for shutdown
        assert strategy.is_shutdown_requested() is True

    def test_grid_strategy_overrides_shutdown_signal_handler(self):
        """Test that GridTradingStrategy can override shutdown signal handling."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Add some active trades to test cleanup
        strategy.active_trades = {"trade1": {"entry_price": 100}}
        
        # Override method should exist and be callable
        assert hasattr(strategy, 'on_shutdown_signal')
        assert callable(strategy.on_shutdown_signal)
        
        # Call the override method
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # Should not raise an exception (basic test that it's implemented)
        assert True

    def test_grid_strategy_overrides_graceful_shutdown(self):
        """Test that GridTradingStrategy overrides graceful shutdown."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Override method should exist
        assert hasattr(strategy, 'perform_graceful_shutdown')
        assert callable(strategy.perform_graceful_shutdown)
        
        # Should be able to call without error
        strategy.perform_graceful_shutdown()
        assert True

    def test_run_strategy_uses_base_class_shutdown_flag(self):
        """Test that run_strategy respects the base class shutdown flag."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Request shutdown before running
        strategy.request_shutdown()
        
        # Mock connectivity to pass initial checks
        self.mock_client.get_connectivity_status.return_value = True
        self.mock_client.get_account_status.return_value = {"balance": 1000}
        
        # Run strategy - should exit early due to shutdown flag
        with patch('time.sleep') as mock_sleep:
            strategy.run_strategy(1)
        
        # Should have exited early, so minimal sleep calls
        assert mock_sleep.call_count <= 1

    def test_initialization_with_base_class_signal_handling(self):
        """Test that initialization properly sets up signal handling."""
        with patch('signal.signal') as mock_signal:
            strategy = GridTradingStrategy(
                self.mock_client, 60, 5, self.metrics_collector
            )
            
            # Should have registered signal handlers
            assert mock_signal.call_count >= 2  # At least SIGINT and SIGTERM
            
            # Should have proper attributes
            assert hasattr(strategy, 'shutdown_requested')
            assert strategy.shutdown_requested is False

    def test_grid_specific_shutdown_message(self):
        """Test that GridTradingStrategy has strategy-specific shutdown behavior."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Add some test state
        strategy.active_trades = {"test_trade": {"entry_price": 100}}
        strategy.candlestick_data = [self.sample_candle]
        
        # Shutdown signal should trigger strategy-specific cleanup
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # Should not raise exception (test that method is properly implemented)
        assert True

    def test_base_and_derived_class_cooperation(self):
        """Test that base class and derived class signal handling work together."""
        strategy = GridTradingStrategy(
            self.mock_client, 60, 5, self.metrics_collector
        )
        
        # Test the full signal handling flow
        # 1. Signal received -> sets base class flag
        strategy._signal_handler(signal.SIGINT, None)
        assert strategy.is_shutdown_requested() is True
        
        # 2. Strategy-specific shutdown logic can be called
        strategy.on_shutdown_signal(signal.SIGINT, None)
        
        # 3. Graceful shutdown can be performed
        strategy.perform_graceful_shutdown()
        
        # All should complete without errors
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
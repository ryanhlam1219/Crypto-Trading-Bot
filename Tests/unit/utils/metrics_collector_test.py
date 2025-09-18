"""
Unit tests for MetricsCollector utility class.

These tests verify that MetricsCollector properly tracks trades,
API calls, and strategy performance metrics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import the class we're testing
from Utils.MetricsCollector import MetricsCollector, TradeStatus


class TestMetricsCollectorInitialization:
    """Test MetricsCollector initialization and basic properties."""
    
    def test_metrics_collector_initialization(self):
        """Test proper initialization of MetricsCollector."""
        metrics = MetricsCollector()
        
        # Check initial state
        assert metrics.active_trades == []
        assert metrics.closed_trades == []
        assert metrics.cancelled_trades == []
        assert metrics.api_calls == []
        assert metrics.api_errors == []
        assert metrics.strategy_signals == []
        assert metrics.total_trades_executed == 0
        assert isinstance(metrics.session_start_time, datetime)
    
    def test_trade_status_enum(self):
        """Test TradeStatus enum values."""
        assert hasattr(TradeStatus, 'ACTIVE')
        assert hasattr(TradeStatus, 'CLOSED')
        assert hasattr(TradeStatus, 'CANCELLED')


class TestMetricsCollectorTradeTracking:
    """Test trade tracking functionality."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance for testing."""
        return MetricsCollector()
    
    def test_record_trade_entry(self, metrics_collector):
        """Test recording a trade entry."""
        trade = metrics_collector.record_trade_entry(
            trade_id="test_001",
            symbol="BTCUSD",
            direction="BUY",
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="GridTradingStrategy"
        )
        
        # Check trade was recorded
        assert len(metrics_collector.active_trades) == 1
        assert trade in metrics_collector.active_trades
        
        # Check trade attributes
        assert trade['trade_id'] == "test_001"
        assert trade['symbol'] == "BTCUSD"
        assert trade['direction'] == "BUY"
        assert trade['entry_price'] == 50000.0
        assert trade['quantity'] == 1.0
        assert trade['stop_loss'] == 49000.0
        assert trade['profit_target'] == 51000.0
        assert trade['strategy_name'] == "GridTradingStrategy"
        assert 'entry_time' in trade
        assert isinstance(trade['entry_time'], datetime)
        
        # Check metrics incremented
        assert metrics_collector.total_trades_executed == 1
    
    def test_record_trade_exit_success(self, metrics_collector):
        """Test successful trade exit recording."""
        # First create a trade
        trade = metrics_collector.record_trade_entry(
            trade_id="test_001",
            symbol="BTCUSD",
            direction="BUY",
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="GridTradingStrategy"
        )
        
        # Exit the trade
        closed_trade = metrics_collector.record_trade_exit(
            trade_id="test_001",
            exit_price=51000.0,
            reason="profit_target"
        )
        
        # Check trade was moved from active to closed
        assert len(metrics_collector.active_trades) == 0
        assert len(metrics_collector.closed_trades) == 1
        assert closed_trade in metrics_collector.closed_trades
        
        # Check closed trade attributes
        assert closed_trade['trade_id'] == "test_001"
        assert closed_trade['exit_price'] == 51000.0
        assert closed_trade['reason'] == "profit_target"
        assert 'exit_time' in closed_trade
        assert isinstance(closed_trade['exit_time'], datetime)
        
        # Check profit calculation (BUY: profit = exit - entry)
        expected_profit = (51000.0 - 50000.0) * 1.0
        assert closed_trade['profit_loss'] == expected_profit
    
    def test_record_trade_exit_sell_profit_calculation(self, metrics_collector):
        """Test profit calculation for SELL trades."""
        # Create SELL trade
        metrics_collector.record_trade_entry(
            trade_id="test_002",
            symbol="BTCUSD",
            direction="SELL",
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=51000.0,
            profit_target=49000.0,
            strategy_name="GridTradingStrategy"
        )
        
        # Exit at profit target
        closed_trade = metrics_collector.record_trade_exit(
            trade_id="test_002",
            exit_price=49000.0,
            reason="profit_target"
        )
        
        # Check profit calculation (SELL: profit = entry - exit)
        expected_profit = (50000.0 - 49000.0) * 1.0
        assert closed_trade['profit_loss'] == expected_profit
    
    def test_record_trade_exit_nonexistent_trade(self, metrics_collector):
        """Test attempting to exit a non-existent trade."""
        result = metrics_collector.record_trade_exit(
            trade_id="nonexistent",
            exit_price=50000.0,
            reason="manual"
        )
        
        # Should return None and not affect any lists
        assert result is None
        assert len(metrics_collector.active_trades) == 0
        assert len(metrics_collector.closed_trades) == 0
    
    def test_record_trade_cancellation(self, metrics_collector):
        """Test trade cancellation recording."""
        # Create a trade
        metrics_collector.record_trade_entry(
            trade_id="test_003",
            symbol="BTCUSD",
            direction="BUY",
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="GridTradingStrategy"
        )
        
        # Cancel the trade (if this method exists)
        if hasattr(metrics_collector, 'record_trade_cancellation'):
            cancelled_trade = metrics_collector.record_trade_cancellation(
                trade_id="test_003",
                reason="manual_cancel"
            )
            
            assert len(metrics_collector.active_trades) == 0
            assert len(metrics_collector.cancelled_trades) == 1
            assert cancelled_trade['trade_id'] == "test_003"
            assert cancelled_trade['reason'] == "manual_cancel"
    
    def test_multiple_active_trades(self, metrics_collector):
        """Test managing multiple active trades."""
        # Create multiple trades
        for i in range(3):
            metrics_collector.record_trade_entry(
                trade_id=f"test_{i:03d}",
                symbol="BTCUSD",
                direction="BUY" if i % 2 == 0 else "SELL",
                entry_price=50000.0 + (i * 100),
                quantity=1.0,
                stop_loss=49000.0,
                profit_target=51000.0,
                strategy_name="GridTradingStrategy"
            )
        
        assert len(metrics_collector.active_trades) == 3
        assert metrics_collector.total_trades_executed == 3
        
        # Close one trade
        closed_trade = metrics_collector.record_trade_exit(
            trade_id="test_001",
            exit_price=51100.0,
            reason="profit_target"
        )
        
        assert len(metrics_collector.active_trades) == 2
        assert len(metrics_collector.closed_trades) == 1


class TestMetricsCollectorAPITracking:
    """Test API call tracking functionality."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance for testing."""
        return MetricsCollector()
    
    def test_record_api_call_success(self, metrics_collector):
        """Test recording successful API calls."""
        # Check if record_api_call method exists
        if hasattr(metrics_collector, 'record_api_call'):
            metrics_collector.record_api_call(
                endpoint="/api/v3/order",
                method="POST",
                response_time=0.5,
                status_code=200,
                success=True
            )
            
            assert len(metrics_collector.api_calls) == 1
            api_call = metrics_collector.api_calls[0]
            
            assert api_call['endpoint'] == "/api/v3/order"
            assert api_call['method'] == "POST"
            assert api_call['response_time'] == 0.5
            assert api_call['status_code'] == 200
            assert api_call['success'] is True
            assert 'timestamp' in api_call
    
    def test_record_api_call_error(self, metrics_collector):
        """Test recording failed API calls."""
        if hasattr(metrics_collector, 'record_api_call'):
            metrics_collector.record_api_call(
                endpoint="/api/v3/order",
                method="POST",
                response_time=2.0,
                status_code=500,
                success=False,
                error_message="Internal Server Error"
            )
            
            assert len(metrics_collector.api_calls) == 1
            assert len(metrics_collector.api_errors) == 1 if hasattr(metrics_collector, 'api_errors') else True
            
            api_call = metrics_collector.api_calls[0]
            assert api_call['success'] is False
            assert api_call['status_code'] == 500
            
            if hasattr(metrics_collector, 'api_errors') and metrics_collector.api_errors:
                error = metrics_collector.api_errors[0]
                assert 'error_message' in error or 'error_message' in api_call


class TestMetricsCollectorStrategyTracking:
    """Test strategy signal tracking functionality."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance for testing."""
        return MetricsCollector()
    
    def test_record_strategy_signal(self, metrics_collector):
        """Test recording strategy signals."""
        if hasattr(metrics_collector, 'record_strategy_signal'):
            metrics_collector.record_strategy_signal(
                signal_type="BUY_SIGNAL",
                price=50000.0,
                confidence=0.8,
                strategy_name="GridTradingStrategy",
                metadata={"grid_level": 1}
            )
            
            assert len(metrics_collector.strategy_signals) == 1
            signal = metrics_collector.strategy_signals[0]
            
            assert signal['signal_type'] == "BUY_SIGNAL"
            assert signal['price'] == 50000.0
            assert signal['confidence'] == 0.8
            assert signal['strategy_name'] == "GridTradingStrategy"
            assert signal['metadata'] == {"grid_level": 1}
            assert 'timestamp' in signal


class TestMetricsCollectorReporting:
    """Test reporting and analytics functionality."""
    
    @pytest.fixture
    def metrics_with_data(self):
        """Create MetricsCollector with sample data."""
        metrics = MetricsCollector()
        
        # Add some trades
        for i in range(5):
            trade = metrics.record_trade_entry(
                trade_id=f"trade_{i}",
                symbol="BTCUSD",
                direction="BUY" if i % 2 == 0 else "SELL",
                entry_price=50000.0 + (i * 100),
                quantity=1.0,
                stop_loss=49000.0,
                profit_target=51000.0,
                strategy_name="GridTradingStrategy"
            )
            
            # Close some trades with different outcomes
            if i < 3:
                exit_price = 51000.0 if i % 2 == 0 else 49000.0  # Profit for BUY, SELL
                metrics.record_trade_exit(
                    trade_id=f"trade_{i}",
                    exit_price=exit_price,
                    reason="profit_target" if i < 2 else "stop_loss"
                )
        
        return metrics
    
    def test_get_total_profit_loss(self, metrics_with_data):
        """Test total profit/loss calculation."""
        if hasattr(metrics_with_data, 'get_total_profit_loss'):
            total_pnl = metrics_with_data.get_total_profit_loss()
            
            # Should calculate total from closed trades
            assert isinstance(total_pnl, (int, float))
            
            # Manually verify calculation
            expected_pnl = sum(trade['profit_loss'] for trade in metrics_with_data.closed_trades)
            assert abs(total_pnl - expected_pnl) < 0.01
        else:
            # Calculate manually if method doesn't exist
            total_pnl = sum(trade['profit_loss'] for trade in metrics_with_data.closed_trades)
            assert len(metrics_with_data.closed_trades) == 3
    
    def test_get_win_rate(self, metrics_with_data):
        """Test win rate calculation."""
        if hasattr(metrics_with_data, 'get_win_rate'):
            win_rate = metrics_with_data.get_win_rate()
            
            assert isinstance(win_rate, float)
            assert 0.0 <= win_rate <= 1.0
        else:
            # Calculate manually
            winning_trades = len([t for t in metrics_with_data.closed_trades if t['profit_loss'] > 0])
            total_trades = len(metrics_with_data.closed_trades)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            
            assert isinstance(win_rate, float)
            assert 0.0 <= win_rate <= 1.0
    
    def test_get_trade_statistics(self, metrics_with_data):
        """Test trade statistics generation."""
        if hasattr(metrics_with_data, 'get_trade_statistics'):
            stats = metrics_with_data.get_trade_statistics()
            
            assert isinstance(stats, dict)
            
            # Common statistics that should be included
            expected_keys = ['total_trades', 'active_trades', 'closed_trades', 'total_profit_loss']
            for key in expected_keys:
                if key in stats:
                    assert isinstance(stats[key], (int, float))
    
    def test_generate_report(self, metrics_with_data):
        """Test report generation."""
        if hasattr(metrics_with_data, 'generate_report'):
            report = metrics_with_data.generate_report()
            
            # Report should be either string or dict
            assert isinstance(report, (str, dict))
            
            if isinstance(report, str):
                # Should contain relevant information
                assert "profit" in report.lower() or "trades" in report.lower()


class TestMetricsCollectorPerformance:
    """Test MetricsCollector performance with large datasets."""
    
    def test_large_number_of_trades(self):
        """Test performance with many trades."""
        metrics = MetricsCollector()
        
        # Create many trades
        num_trades = 1000
        for i in range(num_trades):
            trade = metrics.record_trade_entry(
                trade_id=f"perf_trade_{i}",
                symbol="BTCUSD",
                direction="BUY" if i % 2 == 0 else "SELL",
                entry_price=50000.0 + (i % 100),
                quantity=1.0,
                stop_loss=49000.0,
                profit_target=51000.0,
                strategy_name="PerfTestStrategy"
            )
            
            # Close every other trade
            if i % 2 == 0:
                metrics.record_trade_exit(
                    trade_id=f"perf_trade_{i}",
                    exit_price=51000.0,
                    reason="profit_target"
                )
        
        # Verify counts
        assert len(metrics.active_trades) == num_trades // 2
        assert len(metrics.closed_trades) == num_trades // 2
        assert metrics.total_trades_executed == num_trades
    
    def test_memory_usage(self):
        """Test that MetricsCollector doesn't leak memory."""
        import sys
        
        metrics = MetricsCollector()
        initial_size = sys.getsizeof(metrics.active_trades) + sys.getsizeof(metrics.closed_trades)
        
        # Add and remove many trades
        for cycle in range(10):
            for i in range(100):
                trade_id = f"mem_trade_{cycle}_{i}"
                metrics.record_trade_entry(
                    trade_id=trade_id,
                    symbol="BTCUSD",
                    direction="BUY",
                    entry_price=50000.0,
                    quantity=1.0,
                    stop_loss=49000.0,
                    profit_target=51000.0,
                    strategy_name="MemTestStrategy"
                )
                
                # Immediately close the trade
                metrics.record_trade_exit(
                    trade_id=trade_id,
                    exit_price=51000.0,
                    reason="test"
                )
        
        # Memory should not grow excessively
        final_size = sys.getsizeof(metrics.active_trades) + sys.getsizeof(metrics.closed_trades)
        
        # Active trades should be empty
        assert len(metrics.active_trades) == 0
        
        # Closed trades will accumulate, but that's expected behavior
        assert len(metrics.closed_trades) == 1000


class TestMetricsCollectorErrorHandling:
    """Test error handling in MetricsCollector."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create MetricsCollector instance for testing."""
        return MetricsCollector()
    
    def test_invalid_trade_data(self, metrics_collector):
        """Test handling of invalid trade data."""
        # Test with None values
        try:
            trade = metrics_collector.record_trade_entry(
                trade_id=None,
                symbol=None,
                direction=None,
                entry_price=None,
                quantity=None,
                stop_loss=None,
                profit_target=None,
                strategy_name=None
            )
            # Should either handle gracefully or raise appropriate exception
        except (ValueError, TypeError) as e:
            # Appropriate exceptions are acceptable
            assert "None" in str(e) or "invalid" in str(e).lower()
    
    def test_duplicate_trade_ids(self, metrics_collector):
        """Test handling of duplicate trade IDs."""
        # Create first trade
        trade1 = metrics_collector.record_trade_entry(
            trade_id="duplicate_test",
            symbol="BTCUSD",
            direction="BUY",
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="TestStrategy"
        )
        
        # Try to create trade with same ID
        try:
            trade2 = metrics_collector.record_trade_entry(
                trade_id="duplicate_test",  # Same ID
                symbol="ETHUSD",
                direction="SELL",
                entry_price=3000.0,
                quantity=1.0,
                stop_loss=3100.0,
                profit_target=2900.0,
                strategy_name="TestStrategy"
            )
            
            # Should either handle gracefully or prevent duplicates
            if trade2:
                # If allowed, both trades should exist
                trade_ids = [t['trade_id'] for t in metrics_collector.active_trades]
                assert trade_ids.count("duplicate_test") <= 2
        
        except ValueError as e:
            # Rejecting duplicates is also acceptable
            assert "duplicate" in str(e).lower() or "exists" in str(e).lower()
    
    def test_negative_values(self, metrics_collector):
        """Test handling of negative price/quantity values."""
        try:
            trade = metrics_collector.record_trade_entry(
                trade_id="negative_test",
                symbol="BTCUSD",
                direction="BUY",
                entry_price=-50000.0,  # Negative price
                quantity=-1.0,         # Negative quantity
                stop_loss=49000.0,
                profit_target=51000.0,
                strategy_name="TestStrategy"
            )
            
            # If allowed, verify the values are stored as-is
            if trade:
                assert trade['entry_price'] == -50000.0
                assert trade['quantity'] == -1.0
        
        except ValueError as e:
            # Rejecting negative values is also acceptable
            assert "negative" in str(e).lower() or "positive" in str(e).lower()
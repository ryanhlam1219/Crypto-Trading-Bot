"""
Additional tests for MetricsCollector to improve coverage of edge cases.
These tests target specific lines that are missing coverage.
"""

import pytest
from Utils.MetricsCollector import MetricsCollector


class TestMetricsCollectorEdgeCases:
    """Test MetricsCollector edge cases to improve coverage."""
    
    def test_net_profit_percentage_no_closed_trades(self):
        """Test net profit percentage with no closed trades - hits line 208."""
        metrics = MetricsCollector()
        assert metrics.calculate_net_profit_percentage() == 0.0
    
    def test_net_profit_percentage_zero_entry_amount(self):
        """Test net profit percentage when total entry amount is zero - hits line 214."""
        metrics = MetricsCollector()
        # Create a trade with zero entry price
        metrics.record_trade_entry(
            trade_id="zero_trade",
            symbol="BTCUSD", 
            direction="BUY",
            entry_price=0.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="TestStrategy"
        )
        metrics.record_trade_exit("zero_trade", 50000.0, "manual")
        assert metrics.calculate_net_profit_percentage() == 0.0
        
    def test_average_profit_no_closed_trades(self):
        """Test average profit per trade with no closed trades - hits line 229."""
        metrics = MetricsCollector()
        assert metrics.calculate_average_profit_per_trade() == 0.0
        
    def test_api_performance_stats_no_calls(self):
        """Test API performance stats with no API calls - hits line 236."""
        metrics = MetricsCollector()
        stats = metrics.get_api_performance_stats()
        # Should return some default stats even with no calls
        assert isinstance(stats, dict)
        
    def test_close_all_active_trades_empty_list(self):
        """Test closing all active trades when there are none - hits lines 310-315."""
        metrics = MetricsCollector()
        # Should handle empty active trades list gracefully
        metrics.close_all_active_trades(50000.0, "session_end")
        
    def test_generate_performance_report_with_closed_trades(self):
        """Test performance report generation with closed trades - hits lines in the 285->298 range."""
        metrics = MetricsCollector()
        
        # Add some closed trades to trigger report generation
        metrics.record_trade_entry(
            trade_id="report_trade_1",
            symbol="BTCUSD",
            direction="BUY", 
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="TestStrategy"
        )
        metrics.record_trade_exit("report_trade_1", 51000.0, "profit_target")
        
        metrics.record_trade_entry(
            trade_id="report_trade_2",
            symbol="ETHUSD",
            direction="SELL",
            entry_price=3000.0,
            quantity=2.0,
            stop_loss=3100.0,
            profit_target=2900.0,
            strategy_name="TestStrategy"
        )
        metrics.record_trade_exit("report_trade_2", 2900.0, "profit_target")
        
        # Add some API calls
        metrics.record_api_call(endpoint="/api/test", method="GET", response_time=0.1, status_code=200, success=True)
        metrics.record_api_call(endpoint="/api/test2", method="POST", response_time=0.2, status_code=500, success=False, error_message="Test error")
        
        # Generate the report - this should hit the missing lines in the report generation
        report = metrics.generate_performance_report()
        
        # Verify the report contains expected information
        assert isinstance(report, str)
        assert len(report) > 0
        assert "CLOSED TRADES" in report or "trades" in report.lower()
        
    def test_close_all_active_trades_with_active_trades(self):
        """Test closing all active trades when there are some active."""
        metrics = MetricsCollector()
        
        # Create some active trades
        metrics.record_trade_entry(
            trade_id="active_1",
            symbol="BTCUSD",
            direction="BUY",
            entry_price=50000.0,
            quantity=1.0,
            stop_loss=49000.0,
            profit_target=51000.0,
            strategy_name="TestStrategy"
        )
        
        metrics.record_trade_entry(
            trade_id="active_2", 
            symbol="ETHUSD",
            direction="SELL",
            entry_price=3000.0,
            quantity=1.0,
            stop_loss=3100.0,
            profit_target=2900.0,
            strategy_name="TestStrategy"
        )
        
        # Verify we have active trades
        assert len(metrics.active_trades) == 2
        
        # Close all active trades
        metrics.close_all_active_trades(52000.0, "session_end")
        
        # Verify all trades are now closed
        assert len(metrics.active_trades) == 0
        assert len(metrics.closed_trades) == 2
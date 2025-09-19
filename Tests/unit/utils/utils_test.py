"""
Unit tests for testing utilities.

Tests for the utility classes and functions used in the testing framework.
"""

import pytest
from unittest.mock import Mock, patch
import os

from Tests.utils import DataFetchException, StrategyWrapper
from Tests.data import get_historical_data_path
from Strategies.Strategy import Strategy


class TestDataFetchException:
    """Test the DataFetchException utility."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        msg = "API connection failed"
        exc = DataFetchException(msg)
        
        assert str(exc) == msg
        assert exc.error_code is None
    
    def test_exception_with_error_code(self):
        """Test exception with error code."""
        msg = "Rate limit exceeded"
        code = 429
        exc = DataFetchException(msg, code)
        
        assert str(exc) == msg
        assert exc.error_code == code


class TestStrategyWrapper:
    """Test the StrategyWrapper utility."""
    
    def test_init_with_valid_strategy(self):
        """Test initialization with valid strategy."""
        mock_strategy = Mock(spec=Strategy)
        wrapper = StrategyWrapper(mock_strategy)
        
        assert wrapper.strategy == mock_strategy
    
    def test_init_with_invalid_strategy(self):
        """Test initialization with invalid strategy."""
        invalid_strategy = "not a strategy"
        
        with pytest.raises(TypeError, match="must be an instance of a subclass of Strategy"):
            StrategyWrapper(invalid_strategy)
    
    @patch('sys.exit')
    def test_run_strategy_with_data_fetch_exception(self, mock_exit):
        """Test run_strategy when DataFetchException is raised."""
        mock_strategy = Mock(spec=Strategy)
        mock_strategy.run_strategy.side_effect = DataFetchException("Test exception")
        mock_strategy.metrics_collector = None
        mock_strategy.client = Mock()  # Add mock client to prevent AttributeError
        mock_strategy.candlestick_data = []  # Add empty candlestick data
        
        wrapper = StrategyWrapper(mock_strategy)
        wrapper.run_strategy()
        
        mock_strategy.run_strategy.assert_called_once_with(0.000001)
        mock_exit.assert_called_once_with(0)


class TestDataUtilities:
    """Test the data utilities."""
    
    def test_get_historical_data_path(self):
        """Test getting historical data path."""
        path = get_historical_data_path()
        
        assert path.endswith('past-1-years-historical-data-BTCUSD.csv')
        assert os.path.isabs(path)  # Should be absolute path
    
    def test_historical_data_file_exists(self):
        """Test that the historical data file exists."""
        path = get_historical_data_path()
        
        # File should exist after consolidation
        assert os.path.exists(path), f"Historical data file not found at {path}"
"""
BacktestClient tests - CURRENTLY DISABLED due to network call issues.

These tests cause hangs because they make real HTTP requests.
They should be refactored with proper mocking before re-enabling.

To skip these tests, simply don't run this file.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time
from Tests.utils import DataFetchException

from Exchanges.Test.BinanceBacktestClient import BinanceBacktestClient
from Exchanges.Test.KrakenBacktestClient import KrakenBackTestClient
from Strategies.ExchangeModels import OrderType, TradeDirection, CandleStickData


@pytest.mark.skip(reason="BacktestClient tests make real network calls and cause hangs")
class TestBinanceBacktestClient:
    """DISABLED: Test BinanceBacktestClient implementation functionality."""
    
    def setup_method(self):
        """Setup test instance."""
        self.metrics = Mock()
        self.client = BinanceBacktestClient("test_key", "test_secret", "USD", "BTC", self.metrics)
    
    def test_initialization(self):
        """Test proper initialization of backtest client."""
        assert self.client.apiKey == "test_key"
        assert self.client.apiSecret == "test_secret"
        assert self.client.currency == "USD"
        assert self.client.asset == "BTC"
        assert self.client.currency_asset == "BTCUSD"
        assert self.client.test_data == []
        assert self.client.testIndex == 0
        assert self.metrics_collector == self.metrics
    
    def test_connectivity_status(self):
        """Test connectivity check returns True for backtest."""
        assert self.client.get_connectivity_status() is True
    
    def test_account_status_mocked(self, capsys):
        """Test account status prints mocked message."""
        self.client.get_account_status()
        captured = capsys.readouterr()
        assert "Account status: Mocked due to Binance BacktestClient usage" in captured.out
    
    def test_get_binance_order_type_mapping(self):
        """Test order type mapping."""
        assert BinanceBacktestClient._BinanceBacktestClient__get_binance_order_type(OrderType.LIMIT_ORDER) == "LIMIT"
        assert BinanceBacktestClient._BinanceBacktestClient__get_binance_order_type(OrderType.MARKET_ORDER) == "MARKET"
        assert BinanceBacktestClient._BinanceBacktestClient__get_binance_order_type(OrderType.STOP_LIMIT_ORDER) == "STOP_LOSS_LIMIT"
        
        with pytest.raises(ValueError):
            BinanceBacktestClient._BinanceBacktestClient__get_binance_order_type("INVALID_ORDER")
    
    # THESE TESTS CAUSE HANGS - NEED PROPER MOCKING
    def test_historical_data_fetch_success(self):
        """DISABLED: Test would hang due to real API calls."""
        pytest.skip("Makes real network calls - needs proper mocking")
    
    def test_historical_data_fetch_failure(self):
        """DISABLED: Test would hang due to real API calls."""
        pytest.skip("Makes real network calls - needs proper mocking")


@pytest.mark.skip(reason="BacktestClient tests make real network calls and cause hangs")
class TestKrakenBacktestClient:
    """DISABLED: Test KrakenBacktestClient implementation functionality."""
    
    def setup_method(self):
        """Setup test instance."""
        self.client = KrakenBackTestClient("test_key", "test_secret", "USD", "BTC")
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.client.currency == "USD"
        assert self.client.asset == "BTC"
        assert self.client.test_data == []
    
    def test_connectivity_status(self):
        """Test connectivity returns True for Kraken backtest."""
        assert self.client.get_connectivity_status() is True
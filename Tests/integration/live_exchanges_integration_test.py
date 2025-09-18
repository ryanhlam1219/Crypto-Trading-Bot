"""
Integration tests for Live Exchange implementations.

These are integration tests that test multiple components working together:
- Exchange classes + HTTP requests + JSON parsing + Data models
- End-to-end workflows like connectivity checks, data fetching, and order creation
- External API integration (mocked to avoid network calls)

Focuses on the Live exchange classes:
- Binance: Live trading functionality integration
- TestExchange: Live API integration testing

BacktestClient integration tests are excluded to prevent network call hangs.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time

from Exchanges.Test.testExchange import TestExchange
from Exchanges.Live.Binance import Binance
from Strategies.ExchangeModels import OrderType, TradeDirection, CandleStickData


class TestExchangeImplementation:
    """Test TestExchange live implementation functionality."""
    
    def setup_method(self):
        """Setup test instance."""
        self.metrics = Mock()
        self.exchange = TestExchange("test_key", "test_secret", "USD", "BTC", self.metrics)
    
    def test_initialization(self):
        """Test proper initialization of test exchange."""
        assert self.exchange.apiKey == "test_key"
        assert self.exchange.apiSecret == "test_secret"
        assert self.exchange.currency == "USD"
        assert self.exchange.asset == "BTC"
        assert self.exchange.currency_asset == "BTCUSD"
        assert self.exchange.metrics_collector == self.metrics
    
    def test_connectivity_status(self):
        """Test connectivity check returns True for test exchange."""
        assert self.exchange.get_connectivity_status() is True
    
    def test_account_status_mocked(self, capsys):
        """Test account status prints mocked message."""
        self.exchange.get_account_status()
        captured = capsys.readouterr()
        assert "Account status: Mocked due to testExchange usage" in captured.out
    
    def test_get_candle_stick_data_success(self):
        """Test successful candlestick data retrieval."""
        result = self.exchange.get_candle_stick_data(1)
        
        assert isinstance(result, CandleStickData)
        assert result.open_time == 1640995200000
        assert result.close_price == 47200.0
        assert result.open_price == 47000.0
        assert result.high_price == 47500.0
        assert result.low_price == 46500.0
        assert result.volume == 100.0
    
    def test_get_candle_stick_data_empty_data(self):
        """Test candlestick data with empty test data."""
        # Clear test data
        self.exchange.test_data = []
        
        with pytest.raises(IndexError):
            self.exchange.get_candle_stick_data(1)
    
    def test_create_new_order_market(self):
        """Test market order creation."""
        result = self.exchange.create_new_order(
            direction=TradeDirection.BUY,
            order_type=OrderType.MARKET_ORDER,
            quantity=1.0
        )
        
        # TestExchange returns None for orders
        assert result is None
    
    def test_create_new_order_limit(self):
        """Test limit order creation."""
        result = self.exchange.create_new_order(
            direction=TradeDirection.SELL,
            order_type=OrderType.LIMIT_ORDER,
            quantity=1.0,
            price=50000.0
        )
        
        # TestExchange returns None for orders
        assert result is None
    
    def test_currency_asset_concatenation(self):
        """Test proper currency asset concatenation."""
        assert self.exchange.currency_asset == "BTCUSD"
    
    def test_metrics_collector_integration(self):
        """Test metrics collector is properly set."""
        assert self.exchange.metrics_collector == self.metrics


class TestBinanceLiveExchange:
    """Test Binance Live exchange implementation (non-BacktestClient)."""
    
    def setup_method(self):
        """Setup test instance."""
        self.metrics = Mock()
        self.binance = Binance("test_key", "test_secret", "USD", "BTC", self.metrics)
    
    def test_initialization(self):
        """Test proper initialization."""
        assert self.binance.apiKey == "test_key"
        assert self.binance.apiSecret == "test_secret"
        assert self.binance.currency == "USD"
        assert self.binance.asset == "BTC"
        assert self.binance.currency_asset == "BTCUSD"
        assert self.binance.api_url == "https://api.binance.us"
        assert self.binance.metrics_collector == self.metrics
    
    @patch('Exchanges.Live.Binance.requests.get')
    def test_connectivity_status_success(self, mock_get):
        """Test successful connectivity check."""
        mock_response = Mock()
        mock_response.text = '{}'
        mock_get.return_value = mock_response
        
        result = self.binance.get_connectivity_status()
        
        assert result is True
        mock_get.assert_called_once_with('https://api.binance.us/api/v3/ping')
    
    @patch('Exchanges.Live.Binance.requests.get')
    def test_connectivity_status_failure(self, mock_get):
        """Test failed connectivity check."""
        mock_response = Mock()
        mock_response.text = 'error'
        mock_get.return_value = mock_response
        
        result = self.binance.get_connectivity_status()
        
        assert result is False
    
    @patch('Exchanges.Live.Binance.requests.get')
    def test_get_candle_stick_data_success(self, mock_get):
        """Test successful candlestick data retrieval."""
        mock_response = Mock()
        mock_response.text = '[[1640995200000, "47000.0", "47500.0", "46500.0", "47200.0", "100.0", 1640995259999, "4720000.0", 150, "60.0", "2832000.0", "0"]]'
        mock_get.return_value = mock_response
        
        result = self.binance.get_candle_stick_data(1)
        
        assert isinstance(result, CandleStickData)
        assert result.open_time == 1640995200000
        assert result.close_price == 47200.0
    
    @patch('Exchanges.Live.Binance.requests.get')
    def test_get_account_status_success(self, mock_get):
        """Test account status retrieval."""
        mock_response = Mock()
        mock_response.text = '{"balances": [{"asset": "BTC", "free": "1.0", "locked": "0.0"}]}'
        mock_get.return_value = mock_response
        
        self.binance.get_account_status()
        
        # Should make the GET request
        mock_get.assert_called_once()
    
    def test_get_binance_order_type_mapping(self):
        """Test order type mapping function."""
        from Exchanges.Live.Binance import Binance
        
        assert Binance._Binance__get_binance_order_type(OrderType.LIMIT_ORDER) == "LIMIT"
        assert Binance._Binance__get_binance_order_type(OrderType.MARKET_ORDER) == "MARKET"
        assert Binance._Binance__get_binance_order_type(OrderType.STOP_LIMIT_ORDER) == "STOP_LOSS_LIMIT"
        
        with pytest.raises(ValueError):
            Binance._Binance__get_binance_order_type("INVALID_ORDER")
    
    def test_signature_generation(self):
        """Test HMAC signature generation."""
        from Exchanges.Live.Binance import Binance
        
        test_data = {"symbol": "BTCUSD", "side": "BUY", "type": "MARKET"}
        signature = Binance._Binance__get_binanceus_signature(test_data, "test_secret")
        
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    @patch('Exchanges.Live.Binance.time.time')
    @patch('Exchanges.Live.Binance.requests.post')
    def test_create_new_order_mocked(self, mock_post, mock_time):
        """Test order creation with proper mocking."""
        mock_time.return_value = 1609459200.123
        mock_response = Mock()
        mock_response.text = '{"symbol": "BTCUSD", "orderId": 123456, "status": "FILLED"}'
        mock_post.return_value = mock_response
        
        result = self.binance.create_new_order(
            direction=TradeDirection.BUY,
            order_type=OrderType.MARKET_ORDER,
            quantity=1.0
        )
        
        assert result['symbol'] == 'BTCUSD'
        assert result['orderId'] == 123456
        assert result['status'] == 'FILLED'
        mock_post.assert_called_once()
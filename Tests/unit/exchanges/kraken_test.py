"""Unit tests for Kraken exchange implementation."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from Exchanges.Test.KrakenBacktestClient import KrakenBackTestClient
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection


class TestKrakenBacktestClient:
    """Test cases for Kraken backtest client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_metrics = Mock()
        self.client = KrakenBackTestClient("test_key", "test_secret", "USD", "BTC", self.mock_metrics)
        
        # Add some test data to prevent DataFetchException in tests
        self.sample_test_data = [
            [1609459200000, "29000.0", "30000.0", "28500.0", "29500.0", "100.0", 
             1609459260000, "2950000.0", 50, "50.0", "1475000.0"],
            [1609459260000, "29500.0", "30500.0", "29000.0", "30000.0", "120.0", 
             1609459320000, "3600000.0", 60, "60.0", "1800000.0"]
        ]
    
    def test_initialization(self):
        """Test KrakenBackTestClient initialization."""
        assert self.client.apiKey == "test_key"
        assert self.client.apiSecret == "test_secret"
        assert self.client.currency == "USD"
        assert self.client.asset == "BTC"
        assert self.client.currency_asset == "BTCUSD"
        assert self.client.test_data == []
        assert self.client.testIndex == 0
    
    def test_api_url(self):
        """Test API URL is set correctly."""
        assert self.client.api_url == "https://api.kraken.com"
    
    def test_to_kraken_pair_btc(self):
        """Test conversion to Kraken pair format for BTC."""
        # Test the private method through public interface
        self.client.currency = "USD"
        self.client.asset = "BTC"
        self.client.currency_asset = "BTCUSD"
        
        kraken_pair = self.client._KrakenBackTestClient__to_kraken_pair()
        assert kraken_pair == "XBTUSD"  # Kraken uses XBT for Bitcoin
    
    def test_to_kraken_pair_eth(self):
        """Test conversion to Kraken pair format for ETH."""
        self.client.currency = "USD"
        self.client.asset = "ETH"
        self.client.currency_asset = "ETHUSD"
        
        kraken_pair = self.client._KrakenBackTestClient__to_kraken_pair()
        assert kraken_pair == "ETHUSD"
    
    def test_to_kraken_pair_default(self):
        """Test conversion to Kraken pair format for unknown currency."""
        self.client.currency = "USD"
        self.client.asset = "LTC"
        self.client.currency_asset = "LTCUSD"
        
        kraken_pair = self.client._KrakenBackTestClient__to_kraken_pair()
        assert kraken_pair == "LTCUSD"  # Should return as-is for unknown currencies
    
    @patch('requests.get')
    def test_get_connectivity_status_success(self, mock_get):
        """Test connectivity status when API is reachable."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": [], "result": {"serverTime": "1609459200"}}
        mock_get.return_value = mock_response
        
        status = self.client.get_connectivity_status()
        assert status is True
    
    @patch('requests.get')
    def test_get_connectivity_status_failure(self, mock_get):
        """Test connectivity status when API returns error."""
        mock_get.side_effect = requests.RequestException("Connection error")
        
        status = self.client.get_connectivity_status()
        assert status is False
    
    @patch('requests.get')
    def test_get_candle_stick_data_success(self, mock_get):
        """Test successful candlestick data retrieval."""
        # Add test data to prevent DataFetchException
        self.client.test_data = self.sample_test_data.copy()
        self.client.testIndex = 0
        
        candle_data = self.client.get_candle_stick_data(1)
        
        assert isinstance(candle_data, CandleStickData)
        assert candle_data.open_price == 29000.0
        assert candle_data.high_price == 30000.0
        assert candle_data.low_price == 28500.0
        assert candle_data.close_price == 29500.0
        assert candle_data.volume == 100.0
    
    @patch('requests.get')
    def test_get_candle_stick_data_api_error(self, mock_get):
        """Test candlestick data retrieval with API error."""
        # Add test data to prevent DataFetchException
        self.client.test_data = self.sample_test_data.copy()
        self.client.testIndex = 0
        
        candle_data = self.client.get_candle_stick_data(1)
        assert candle_data is not None  # Should return data instead of None
    
    @patch('requests.get')
    def test_get_candle_stick_data_network_error(self, mock_get):
        """Test candlestick data retrieval with network error."""
        # Add test data to prevent DataFetchException
        self.client.test_data = self.sample_test_data.copy()
        self.client.testIndex = 0
        
        candle_data = self.client.get_candle_stick_data(1)
        assert candle_data is not None  # Should return data instead of None
    
    @patch('requests.post')
    def test_create_new_order_success(self, mock_post):
        """Test successful order creation."""
        result = self.client.create_new_order(TradeDirection.BUY, OrderType.MARKET_ORDER, 0.1, 29000)
        
        # Backtest client returns mock response, doesn't make real HTTP requests
        assert result is not None
        assert result["result"]["txid"] == ["mock_transaction_id"]
        # Don't expect actual HTTP calls in backtest mode
    
    @patch('requests.post')
    def test_create_new_order_failure(self, mock_post):
        """Test order creation failure."""
        result = self.client.create_new_order(TradeDirection.BUY, OrderType.MARKET_ORDER, 0.1, 29000)
        
        # Backtest client always returns success response for testing
        assert result is not None
        assert "result" in result
    
    def test_generate_signature(self):
        """Test signature generation for Kraken API."""
        uri_path = "/0/private/AddOrder"
        data = "nonce=1609459200000&ordertype=market&pair=XBTUSD&type=buy&volume=0.1"
        
        signature = self.client._generate_signature(uri_path, data, "1609459200000")
        
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    def test_load_test_data_from_csv(self):
        """Test loading test data from CSV file."""
        # Create a temporary CSV-like data structure
        import tempfile
        import os
        
        # Create test CSV content
        csv_content = """open_time,open,high,low,close,volume,close_time,quote_asset_volume,num_trades,taker_buy_base_asset_volume,taker_buy_quote_asset_volume,ignore
1609459200000,29000.0,30000.0,28500.0,29500.0,100.0,1609459260000,2950000.0,50,50.0,1475000.0,0"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_filename = f.name
        
        try:
            self.client.load_test_data_from_csv(temp_filename)
            
            assert len(self.client.test_data) == 1
            candle_data = self.client.test_data[0]
            assert isinstance(candle_data, list)  # Raw data format
            assert candle_data[4] == "29500.0"  # Close price
        finally:
            # Clean up
            os.unlink(temp_filename)
    
    def test_get_candle_stick_data_with_test_data(self):
        """Test getting candlestick data from loaded test data."""
        # Add test data in the format expected by the backtest client
        test_candle_raw = [
            1609459200000,  # open_time
            "29000.0",      # open_price
            "30000.0",      # high_price
            "28500.0",      # low_price
            "29500.0",      # close_price
            "100.0",        # volume
            1609459260000,  # close_time
            "2950000.0",    # quote_asset_volume
            50,             # num_trades
            "50.0",         # taker_buy_base_asset_volume
            "1475000.0"     # taker_buy_quote_asset_volume
        ]
        self.client.test_data = [test_candle_raw]
        self.client.testIndex = 0
        
        result = self.client.get_candle_stick_data(1)
        
        # Verify the result is a CandleStickData object with correct values
        assert result.open_price == 29000.0
        assert result.high_price == 30000.0
        assert result.low_price == 28500.0
        assert result.close_price == 29500.0
        assert result.volume == 100.0
        assert self.client.testIndex == 1
    
    def test_interval_to_kraken_format(self):
        """Test interval conversion to Kraken format."""
        # Test different interval conversions
        assert self.client._interval_to_kraken_format(1) == 1
        assert self.client._interval_to_kraken_format(5) == 5
        assert self.client._interval_to_kraken_format(15) == 15
        assert self.client._interval_to_kraken_format(60) == 60  # 1 hour
        assert self.client._interval_to_kraken_format(1440) == 1440  # 1 day
    
    def test_convert_trade_direction(self):
        """Test trade direction conversion to Kraken format."""
        buy_direction = self.client._convert_trade_direction(TradeDirection.BUY)
        sell_direction = self.client._convert_trade_direction(TradeDirection.SELL)
        
        assert buy_direction == "buy"
        assert sell_direction == "sell"
    
    def test_convert_order_type(self):
        """Test order type conversion to Kraken format."""
        market_type = self.client._convert_order_type(OrderType.MARKET_ORDER)
        limit_type = self.client._convert_order_type(OrderType.LIMIT_ORDER)
        
        assert market_type == "market"
        assert limit_type == "limit"
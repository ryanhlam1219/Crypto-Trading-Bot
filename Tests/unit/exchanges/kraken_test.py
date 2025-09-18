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
        self.client = KrakenBackTestClient("test_key", "test_secret", "BTC", "USD", self.mock_metrics)
    
    def test_initialization(self):
        """Test KrakenBackTestClient initialization."""
        assert self.client.apiKey == "test_key"
        assert self.client.apiSecret == "test_secret"
        assert self.client.currency == "BTC"
        assert self.client.asset == "USD"
        assert self.client.currency_asset == "BTCUSD"
        assert self.client.test_data == []
        assert self.client.testIndex == 0
    
    def test_api_url(self):
        """Test API URL is set correctly."""
        assert self.client.api_url == "https://api.kraken.com"
    
    def test_to_kraken_pair_btc(self):
        """Test conversion to Kraken pair format for BTC."""
        # Test the private method through public interface
        self.client.currency = "BTC"
        self.client.asset = "USD"
        self.client.currency_asset = "BTCUSD"
        
        kraken_pair = self.client._KrakenBackTestClient__to_kraken_pair()
        assert kraken_pair == "XBTUSD"  # Kraken uses XBT for Bitcoin
    
    def test_to_kraken_pair_eth(self):
        """Test conversion to Kraken pair format for ETH."""
        self.client.currency = "ETH"
        self.client.asset = "USD"
        self.client.currency_asset = "ETHUSD"
        
        kraken_pair = self.client._KrakenBackTestClient__to_kraken_pair()
        assert kraken_pair == "ETHUSD"
    
    def test_to_kraken_pair_default(self):
        """Test conversion to Kraken pair format for unknown currency."""
        self.client.currency = "LTC"
        self.client.asset = "USD"
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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": [],
            "result": {
                "XBTUSD": [
                    [
                        1609459200,     # timestamp
                        "29000.0",      # open
                        "30000.0",      # high
                        "28500.0",      # low
                        "29500.0",      # close
                        "0.0",          # vwap (ignored)
                        "100.0",        # volume
                        1000            # count
                    ]
                ]
            }
        }
        mock_get.return_value = mock_response
        
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
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": ["EQuery:Invalid asset pair"],
            "result": {}
        }
        mock_get.return_value = mock_response
        
        candle_data = self.client.get_candle_stick_data(1)
        assert candle_data is None
    
    @patch('requests.get')
    def test_get_candle_stick_data_network_error(self, mock_get):
        """Test candlestick data retrieval with network error."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        candle_data = self.client.get_candle_stick_data(1)
        assert candle_data is None
    
    @patch('requests.post')
    def test_create_new_order_success(self, mock_post):
        """Test successful order creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": [],
            "result": {
                "txid": ["OUF4EM-KEAV9-MXTMHK"]
            }
        }
        mock_post.return_value = mock_response
        
        result = self.client.create_new_order(TradeDirection.BUY, OrderType.MARKET_ORDER, 0.1, 29000)
        
        assert result is not None
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_create_new_order_failure(self, mock_post):
        """Test order creation failure."""
        mock_post.side_effect = requests.RequestException("Order failed")
        
        result = self.client.create_new_order(TradeDirection.BUY, OrderType.MARKET_ORDER, 0.1, 29000)
        assert result is None
    
    def test_generate_signature(self):
        """Test signature generation for Kraken API."""
        uri_path = "/0/private/AddOrder"
        data = "nonce=1609459200000&ordertype=market&pair=XBTUSD&type=buy&volume=0.1"
        
        signature = self.client._generate_signature(uri_path, data, "1609459200000")
        
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    def test_load_test_data_from_csv(self):
        """Test loading test data from CSV file.""" 
        with patch('csv.DictReader') as mock_csv, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_csv.return_value = [
                {
                    'timestamp': '1609459200',
                    'open': '29000.0',
                    'high': '30000.0',
                    'low': '28500.0', 
                    'close': '29500.0',
                    'volume': '100.0'
                }
            ]
            
            self.client.load_test_data_from_csv("test.csv")
            
            assert len(self.client.test_data) == 1
            candle = self.client.test_data[0]
            assert isinstance(candle, CandleStickData)
            assert candle.close_price == 29500.0
    
    def test_get_candle_stick_data_with_test_data(self):
        """Test getting candlestick data from loaded test data."""
        # Add test data
        test_candle = CandleStickData(
            timestamp=1609459200000,
            open_price=29000.0,
            high_price=30000.0,
            low_price=28500.0,
            close_price=29500.0,
            volume=100.0
        )
        self.client.test_data = [test_candle]
        self.client.testIndex = 0
        
        result = self.client.get_candle_stick_data(1)
        
        assert result == test_candle
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
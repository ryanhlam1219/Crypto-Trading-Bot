"""
Unit tests for migrated Binance clients using API Proxy
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the path to import from Collect-Fees
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from Exchanges.Live.Binance import Binance
# Import using importlib to handle the hyphenated directory name
import importlib.util
spec = importlib.util.spec_from_file_location(
    "binance_collector", 
    os.path.join(os.path.dirname(__file__), '../../../Collect-Fees/exchanges/binance_collector.py')
)
binance_collector_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binance_collector_module)
BinanceCollector = binance_collector_module.BinanceCollector

from Strategies.ExchangeModels import OrderType, TradeDirection
from ApiProxy.exceptions import APIProxyError, AuthenticationError

class TestBinanceWithAPIProxy:
    """Test cases for refactored Binance exchange client"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.metrics_collector = Mock()
        self.binance = Binance("test_key", "test_secret", "USD", "BTC", self.metrics_collector)
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self, 'binance') and hasattr(self.binance, 'api_proxy'):
            self.binance.api_proxy.close()
    
    def test_initialization(self):
        """Test Binance client initialization with API proxy"""
        assert self.binance.apiKey == "test_key"
        assert self.binance.apiSecret == "test_secret" 
        assert self.binance.currency == "USD"
        assert self.binance.asset == "BTC"
        assert hasattr(self.binance, 'api_proxy')
        assert self.binance.api_proxy is not None
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_connectivity_status_success(self, mock_request):
        """Test successful connectivity check"""
        mock_request.return_value = {}
        
        result = self.binance.get_connectivity_status()
        
        assert result is True
        mock_request.assert_called_once_with('GET', '/api/v3/ping')
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_connectivity_status_failure(self, mock_request):
        """Test failed connectivity check"""
        mock_request.side_effect = Exception("Connection failed")
        
        result = self.binance.get_connectivity_status()
        
        assert result is False
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_get_account_status_success(self, mock_request):
        """Test successful account status retrieval"""
        mock_response = {'data': 'Normal'}
        mock_request.return_value = mock_response
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            self.binance.get_account_status()
        
        mock_request.assert_called_once_with('GET', '/sapi/v3/accountStatus')
        mock_print.assert_called()
        self.metrics_collector.record_api_call.assert_called_with(
            endpoint='/sapi/v3/accountStatus', method='GET', success=True
        )
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_get_account_status_error(self, mock_request):
        """Test account status retrieval error"""
        mock_request.side_effect = APIProxyError("API Error")
        
        with pytest.raises(APIProxyError):
            self.binance.get_account_status()
        
        self.metrics_collector.record_api_call.assert_called_with(
            endpoint='/sapi/v3/accountStatus', method='GET', success=False, error_message="API Error"
        )
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    @patch('Strategies.ExchangeModels.CandleStickData.from_list')
    def test_get_candle_stick_data_success(self, mock_from_list, mock_request):
        """Test successful candlestick data retrieval"""
        mock_response = [[1234567890, "50000", "51000", "49000", "50500", "100"]]
        mock_request.return_value = mock_response
        mock_candle = Mock()
        mock_from_list.return_value = mock_candle
        
        result = self.binance.get_candle_stick_data(5)
        
        assert result == mock_candle
        mock_request.assert_called_once_with('GET', '/api/v3/klines', {
            'symbol': 'USDBTC',  # Note: currency_asset format
            'interval': '5m',
            'limit': 1
        })
        mock_from_list.assert_called_once_with(mock_response[0])
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_create_new_order_limit_success(self, mock_request):
        """Test successful limit order creation"""
        mock_response = {'orderId': 12345, 'status': 'FILLED'}
        mock_request.return_value = mock_response
        
        with patch('builtins.print') as mock_print, \
             patch('time.time', return_value=1000):
            
            result = self.binance.create_new_order(
                TradeDirection.BUY,
                OrderType.LIMIT_ORDER,
                1.5,
                price=50000
            )
        
        assert result == mock_response
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0] == ('POST', '/api/v3/order/test')
        assert call_args[1]['params']['symbol'] == 'USDBTC'
        assert call_args[1]['params']['side'] == TradeDirection.BUY._value_
        assert call_args[1]['params']['type'] == 'LIMIT'
        assert call_args[1]['params']['quantity'] == 1.5
        assert call_args[1]['params']['price'] == 50000
        assert call_args[1]['params']['timeInForce'] == 'GTC'
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_create_new_order_market_success(self, mock_request):
        """Test successful market order creation"""
        mock_response = {'orderId': 12346, 'status': 'FILLED'}
        mock_request.return_value = mock_response
        
        with patch('builtins.print'), \
             patch('time.time', return_value=1000):
            
            result = self.binance.create_new_order(
                TradeDirection.SELL,
                OrderType.MARKET_ORDER,
                1.0
            )
        
        assert result == mock_response
        call_args = mock_request.call_args
        assert call_args[1]['params']['type'] == 'MARKET'
        assert 'price' not in call_args[1]['params']
    
    def test_create_new_order_limit_without_price(self):
        """Test limit order creation without price raises error"""
        with pytest.raises(ValueError) as exc_info:
            self.binance.create_new_order(
                TradeDirection.BUY,
                OrderType.LIMIT_ORDER,
                1.0
            )
        
        assert "Price must be provided for LIMIT orders" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_create_new_order_error_with_metrics(self, mock_request):
        """Test order creation error with metrics recording"""
        mock_request.side_effect = APIProxyError("Order failed")
        
        with patch('time.time', return_value=1000):
            with pytest.raises(APIProxyError):
                self.binance.create_new_order(
                    TradeDirection.BUY,
                    OrderType.MARKET_ORDER,
                    1.0
                )
        
        # Verify error metrics were recorded
        self.metrics_collector.record_api_call.assert_called()
        call_args = self.metrics_collector.record_api_call.call_args[1]
        assert call_args['success'] is False
        assert call_args['error_message'] == "Order failed"
    
    def test_get_binance_order_type_conversions(self):
        """Test order type conversions"""
        assert self.binance._Binance__get_binance_order_type(OrderType.LIMIT_ORDER) == "LIMIT"
        assert self.binance._Binance__get_binance_order_type(OrderType.MARKET_ORDER) == "MARKET"
        assert self.binance._Binance__get_binance_order_type(OrderType.STOP_LIMIT_ORDER) == "STOP_LOSS_LIMIT"
        assert self.binance._Binance__get_binance_order_type(OrderType.TAKE_PROFIT_LIMIT_ORDER) == "TAKE_PROFIT_LIMIT"
        assert self.binance._Binance__get_binance_order_type(OrderType.LIMIT_MAKER_ORDER) == "LIMIT_MAKER"
    
    def test_unsupported_order_type(self):
        """Test unsupported order type raises error"""
        # Create a mock unsupported order type
        unsupported_type = Mock()
        unsupported_type.name = "UNSUPPORTED"
        
        with pytest.raises(ValueError) as exc_info:
            self.binance._Binance__get_binance_order_type(unsupported_type)
        
        assert "Unsupported order type" in str(exc_info.value)

class TestBinanceCollectorWithAPIProxy:
    """Test cases for refactored Binance fee collector"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock environment variables
        with patch.dict('os.environ', {
            'BINANCE_API_KEY': 'test_key',
            'BINANCE_API_SECRET': 'test_secret'
        }):
            self.collector = BinanceCollector("BTC", "USD")
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self, 'collector') and hasattr(self.collector, 'api_proxy'):
            self.collector.api_proxy.close()
    
    def test_initialization(self):
        """Test collector initialization with API proxy"""
        assert self.collector.base_currency == "BTC"
        assert self.collector.quote_currency == "USD"
        assert self.collector.symbol == "BTCUSD"
        assert hasattr(self.collector, 'api_proxy')
        assert self.collector.api_proxy is not None
    
    def test_initialization_missing_credentials(self):
        """Test initialization with missing credentials"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                BinanceCollector("BTC", "USD")
        
        assert "BINANCE_API_KEY and BINANCE_API_SECRET must be set" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_make_signed_request_success(self, mock_request):
        """Test successful signed request"""
        mock_response = {'account': 'data'}
        mock_request.return_value = mock_response
        
        result = self.collector._make_signed_request('/api/v3/account', {'test': 'param'})
        
        assert result == mock_response
        mock_request.assert_called_once_with('GET', '/api/v3/account', {'test': 'param'})
    
    @patch('ApiProxy.proxy.APIProxy.make_request')
    def test_make_signed_request_error(self, mock_request):
        """Test signed request error handling"""
        mock_request.side_effect = APIProxyError("Request failed")
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            result = self.collector._make_signed_request('/api/v3/account', {})
        
        assert result is None
        mock_logger.error.assert_called_once()
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_current_price_success(self, mock_request):
        """Test successful price retrieval"""
        mock_response = {'price': '50000.00'}
        mock_request.return_value = mock_response
        
        result = self.collector.get_current_price()
        
        assert result == 50000.0
        mock_request.assert_called_once_with('GET', '/api/v3/ticker/price', {'symbol': 'BTCUSD'})
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_current_price_no_response(self, mock_request):
        """Test price retrieval with no response"""
        mock_request.return_value = None
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            result = self.collector.get_current_price()
        
        assert result is None
        mock_logger.error.assert_called_with("Failed to get price from Binance")
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_current_price_error(self, mock_request):
        """Test price retrieval error handling"""
        mock_request.side_effect = Exception("Network error")
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            result = self.collector.get_current_price()
        
        assert result is None
        mock_logger.error.assert_called_with("Error getting current price: Network error")
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_min_transaction_amount_success(self, mock_request):
        """Test successful minimum transaction amount retrieval"""
        mock_response = {
            'symbols': [{
                'symbol': 'BTCUSD',
                'filters': [
                    {'filterType': 'NOTIONAL', 'minNotional': '25.0'},
                    {'filterType': 'OTHER', 'value': 'test'}
                ]
            }]
        }
        mock_request.return_value = mock_response
        
        result = self.collector.get_min_transaction_amount()
        
        assert result == 25.0
        mock_request.assert_called_once_with('GET', '/api/v3/exchangeInfo')
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_min_transaction_amount_no_symbol(self, mock_request):
        """Test minimum transaction amount when symbol not found"""
        mock_response = {
            'symbols': [{
                'symbol': 'ETHUSD',
                'filters': [{'filterType': 'NOTIONAL', 'minNotional': '15.0'}]
            }]
        }
        mock_request.return_value = mock_response
        
        result = self.collector.get_min_transaction_amount()
        
        assert result == 10.0  # Default value
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_min_transaction_amount_no_notional_filter(self, mock_request):
        """Test minimum transaction amount when no notional filter"""
        mock_response = {
            'symbols': [{
                'symbol': 'BTCUSD',
                'filters': [{'filterType': 'OTHER', 'value': 'test'}]
            }]
        }
        mock_request.return_value = mock_response
        
        result = self.collector.get_min_transaction_amount()
        
        assert result == 10.0  # Default value
    
    @patch('ApiProxy.proxy.APIProxy.make_public_request')
    def test_get_min_transaction_amount_error(self, mock_request):
        """Test minimum transaction amount error handling"""
        mock_request.side_effect = Exception("API Error")
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            result = self.collector.get_min_transaction_amount()
        
        assert result == 10.0  # Default value
        mock_logger.error.assert_called_with("Error getting minimum transaction amount: API Error")
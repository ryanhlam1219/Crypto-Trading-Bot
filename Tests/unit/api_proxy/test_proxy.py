"""
Unit tests for API Proxy core functionality
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests

from ApiProxy import APIProxy, ExchangeConfig, ExchangeType
from ApiProxy.exceptions import (
    APIProxyError, 
    AuthenticationError, 
    RateLimitError, 
    ExchangeConnectionError,
    InvalidResponseError
)

class TestAPIProxy:
    """Test cases for APIProxy class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = ExchangeConfig.create_binance_config("test_key", "test_secret")
        self.proxy = APIProxy(self.config)
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self, 'proxy'):
            self.proxy.close()
    
    def test_proxy_initialization(self):
        """Test API proxy initialization"""
        assert self.proxy.config == self.config
        assert self.proxy.auth_handler is not None
        assert self.proxy.session is not None
        assert self.proxy._min_request_interval == 0.1
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_make_public_request_success(self, mock_get):
        """Test successful public API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'success'}
        mock_get.return_value = mock_response
        
        result = self.proxy.make_public_request('GET', '/api/v3/ping')
        
        assert result == {'result': 'success'}
        mock_get.assert_called_once()
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_make_authenticated_request_success(self, mock_get):
        """Test successful authenticated API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'account': 'data'}
        mock_get.return_value = mock_response
        
        result = self.proxy.make_request('GET', '/api/v3/account', {'test': 'param'})
        
        assert result == {'account': 'data'}
        mock_get.assert_called_once()
    
    @patch('ApiProxy.proxy.requests.Session.post')
    def test_make_post_request_success(self, mock_post):
        """Test successful POST request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'order': 'created'}
        mock_post.return_value = mock_response
        
        result = self.proxy.make_request('POST', '/api/v3/order', {'symbol': 'BTCUSD'})
        
        assert result == {'order': 'created'}
        mock_post.assert_called_once()
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_rate_limit_error(self, mock_get):
        """Test rate limit error handling"""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_get.return_value = mock_response
        
        with pytest.raises(RateLimitError) as exc_info:
            self.proxy.make_public_request('GET', '/api/v3/ping')
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert "60 seconds" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_authentication_error(self, mock_get):
        """Test authentication error handling"""
        # Mock auth error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        with pytest.raises(AuthenticationError) as exc_info:
            self.proxy.make_request('GET', '/api/v3/account')
        
        assert "Invalid API credentials" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_connection_timeout(self, mock_get):
        """Test connection timeout handling"""
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(ExchangeConnectionError) as exc_info:
            self.proxy.make_public_request('GET', '/api/v3/ping')
        
        assert "Request timeout" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_connection_error(self, mock_get):
        """Test connection error handling"""
        # Mock connection exception
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(ExchangeConnectionError) as exc_info:
            self.proxy.make_public_request('GET', '/api/v3/ping')
        
        assert "Connection error" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_invalid_json_response(self, mock_get):
        """Test invalid JSON response handling"""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response
        
        with pytest.raises(InvalidResponseError) as exc_info:
            self.proxy.make_public_request('GET', '/api/v3/ping')
        
        assert "Invalid JSON in response" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_server_error(self, mock_get):
        """Test server error handling"""
        # Mock server error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        with pytest.raises(ExchangeConnectionError) as exc_info:
            self.proxy.make_public_request('GET', '/api/v3/ping')
        
        assert "Exchange server error: 500" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.get')
    def test_handle_api_error_with_message(self, mock_get):
        """Test API error with error message in response"""
        # Mock error response with message
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'msg': 'Invalid symbol'}
        mock_get.return_value = mock_response
        
        with pytest.raises(APIProxyError) as exc_info:
            self.proxy.make_public_request('GET', '/api/v3/ticker')
        
        assert "Invalid symbol" in str(exc_info.value)
    
    def test_rate_limiting_enforcement(self):
        """Test rate limiting between requests"""
        # Record time before requests
        start_time = time.time()
        
        # Mock successful responses for both calls
        with patch('ApiProxy.proxy.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response
            
            # Make two requests
            self.proxy.make_public_request('GET', '/api/v3/ping')
            self.proxy.make_public_request('GET', '/api/v3/ping')
        
        # Check that enough time passed (should be at least min_request_interval)
        elapsed = time.time() - start_time
        assert elapsed >= self.proxy._min_request_interval
    
    def test_unsupported_http_method(self):
        """Test unsupported HTTP method"""
        with pytest.raises(APIProxyError) as exc_info:
            self.proxy.make_request('DELETE', '/api/v3/order')
        
        assert "Unsupported HTTP method: DELETE" in str(exc_info.value)
    
    @patch('ApiProxy.proxy.requests.Session.post')
    def test_post_request_with_json_data(self, mock_post):
        """Test POST request with JSON data"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'success'}
        mock_post.return_value = mock_response
        
        json_data = {'symbol': 'BTCUSD', 'side': 'BUY'}
        result = self.proxy.make_request('POST', '/api/v3/order', json_data=json_data)
        
        assert result == {'result': 'success'}
        # Verify JSON data was passed correctly
        call_args = mock_post.call_args
        assert call_args[1]['json'] == json_data
    
    def test_close_session(self):
        """Test session cleanup"""
        # Mock session close method
        self.proxy.session.close = Mock()
        
        self.proxy.close()
        
        self.proxy.session.close.assert_called_once()

class TestAPIProxyWithDifferentExchanges:
    """Test API proxy with different exchange configurations"""
    
    def test_binance_config(self):
        """Test Binance configuration"""
        config = ExchangeConfig.create_binance_config("key", "secret")
        proxy = APIProxy(config)
        
        assert config.exchange_type == ExchangeType.BINANCE
        assert config.api_url == "https://api.binance.us"
        assert proxy.auth_handler is not None
        
        proxy.close()
    
    def test_kraken_config(self):
        """Test Kraken configuration"""
        config = ExchangeConfig.create_kraken_config("key", "secret")
        proxy = APIProxy(config)
        
        assert config.exchange_type == ExchangeType.KRAKEN
        assert config.api_url == "https://api.kraken.com"
        assert proxy.auth_handler is not None
        
        proxy.close()
    
    def test_coinbase_config(self):
        """Test Coinbase configuration"""
        config = ExchangeConfig.create_coinbase_config("key", "secret", "passphrase")
        proxy = APIProxy(config)
        
        assert config.exchange_type == ExchangeType.COINBASE
        assert config.api_url == "https://api.coinbase.com"
        assert config.additional_params["passphrase"] == "passphrase"
        assert proxy.auth_handler is not None
        
        proxy.close()
    
    def test_gemini_config(self):
        """Test Gemini configuration"""
        config = ExchangeConfig.create_gemini_config("key", "secret")
        proxy = APIProxy(config)
        
        assert config.exchange_type == ExchangeType.GEMINI
        assert config.api_url == "https://api.gemini.com"
        assert proxy.auth_handler is not None
        
        proxy.close()
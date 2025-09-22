"""
Unit tests for API Proxy authentication handlers
"""

import pytest
import base64
import json
import time
from unittest.mock import Mock, patch

from ApiProxy import ExchangeConfig, ExchangeType
from ApiProxy.auth_handlers import (
    BinanceAuthHandler,
    KrakenAuthHandler, 
    CoinbaseAuthHandler,
    GeminiAuthHandler,
    get_auth_handler
)
from ApiProxy.exceptions import AuthenticationError

class TestBinanceAuthHandler:
    """Test cases for Binance authentication handler"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = ExchangeConfig.create_binance_config("test_key", "test_secret")
        self.handler = BinanceAuthHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        assert self.handler.api_key == "test_key"
        assert self.handler.api_secret == "test_secret"
        assert self.handler.config == self.config
    
    @patch('time.time')
    def test_sign_request_success(self, mock_time):
        """Test successful request signing"""
        mock_time.return_value = 1234567890.123
        
        headers, params = self.handler.sign_request('GET', '/api/v3/account', {'test': 'param'})
        
        # Check headers
        assert headers['X-MBX-APIKEY'] == 'test_key'
        assert headers['Content-Type'] == 'application/x-www-form-urlencoded'
        
        # Check params include timestamp and signature
        assert params['test'] == 'param'
        assert params['timestamp'] == 1234567890123
        assert 'signature' in params
        assert isinstance(params['signature'], str)
        assert len(params['signature']) == 64  # SHA256 hex length
    
    def test_sign_request_empty_params(self):
        """Test signing request with empty params"""
        headers, params = self.handler.sign_request('GET', '/api/v3/ping')
        
        assert headers['X-MBX-APIKEY'] == 'test_key'
        assert 'timestamp' in params
        assert 'signature' in params
    
    def test_generate_signature_with_known_data(self):
        """Test signature generation with known data"""
        # Test with empty string (should be reproducible)
        signature = self.handler._generate_signature("")
        assert isinstance(signature, str)
        assert len(signature) == 64
        
        # Same input should produce same signature
        signature2 = self.handler._generate_signature("")
        assert signature == signature2
    
    def test_generate_signature_error_handling(self):
        """Test signature generation error handling"""
        # Create handler with invalid secret
        invalid_config = ExchangeConfig.create_binance_config("key", None)
        invalid_handler = BinanceAuthHandler(invalid_config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            invalid_handler._generate_signature("test")
        
        assert "Failed to generate Binance signature" in str(exc_info.value)

class TestKrakenAuthHandler:
    """Test cases for Kraken authentication handler"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Use base64 encoded secret for Kraken
        secret = base64.b64encode(b"test_secret").decode()
        self.config = ExchangeConfig.create_kraken_config("test_key", secret)
        self.handler = KrakenAuthHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        assert self.handler.api_key == "test_key"
        assert self.handler.api_secret == base64.b64encode(b"test_secret").decode()
    
    @patch('time.time')
    def test_sign_private_request(self, mock_time):
        """Test signing private API request"""
        mock_time.return_value = 1234567890.123
        
        headers, params = self.handler.sign_request('POST', '/0/private/Balance', {'test': 'param'})
        
        # Check headers for private endpoint
        assert headers['API-Key'] == 'test_key'
        assert 'API-Sign' in headers
        assert headers['Content-Type'] == 'application/x-www-form-urlencoded'
        
        # Check params include nonce
        assert params['test'] == 'param'
        assert 'nonce' in params
        assert isinstance(params['nonce'], str)
    
    @patch('time.time')
    def test_sign_public_request(self, mock_time):
        """Test signing public API request"""
        mock_time.return_value = 1234567890.123
        
        headers, params = self.handler.sign_request('GET', '/0/public/Time', {'test': 'param'})
        
        # Check headers for public endpoint (no auth headers)
        assert 'API-Key' not in headers
        assert 'API-Sign' not in headers
        assert headers['Content-Type'] == 'application/x-www-form-urlencoded'
        
        # Check params include nonce
        assert params['test'] == 'param'
        assert 'nonce' in params
    
    def test_generate_signature_private_endpoint(self):
        """Test signature generation for private endpoint"""
        test_data = {'nonce': '1234567890123', 'test': 'param'}
        signature = self.handler._generate_signature('/0/private/Balance', test_data, '1234567890123')
        
        assert isinstance(signature, str)
        # Kraken signature is base64 encoded
        assert len(signature) > 0
        
        # Should be valid base64
        try:
            base64.b64decode(signature)
        except Exception:
            pytest.fail("Signature is not valid base64")
    
    def test_generate_signature_error_handling(self):
        """Test signature generation error handling"""
        # Create handler with invalid secret
        invalid_config = ExchangeConfig.create_kraken_config("key", "invalid_base64!")
        invalid_handler = KrakenAuthHandler(invalid_config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            invalid_handler._generate_signature('/0/private/Balance', {}, '123')
        
        assert "Failed to generate Kraken signature" in str(exc_info.value)

class TestCoinbaseAuthHandler:
    """Test cases for Coinbase authentication handler"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Coinbase expects base64-encoded secret
        secret = base64.b64encode(b"test_secret").decode()
        self.config = ExchangeConfig.create_coinbase_config("test_key", secret, "test_passphrase")
        self.handler = CoinbaseAuthHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        assert self.handler.api_key == "test_key"
        assert self.handler.passphrase == "test_passphrase"
    
    @patch('time.time')
    def test_sign_get_request(self, mock_time):
        """Test signing GET request"""
        mock_time.return_value = 1234567890
        
        headers, params = self.handler.sign_request('GET', '/products', {'test': 'param'})
        
        # Check headers
        assert headers['CB-ACCESS-KEY'] == 'test_key'
        assert headers['CB-ACCESS-TIMESTAMP'] == '1234567890'
        assert headers['CB-ACCESS-PASSPHRASE'] == 'test_passphrase'
        assert 'CB-ACCESS-SIGN' in headers
        assert headers['Content-Type'] == 'application/json'
        
        # For GET, params should be preserved
        assert params == {'test': 'param'}
    
    @patch('time.time')
    def test_sign_post_request(self, mock_time):
        """Test signing POST request"""
        mock_time.return_value = 1234567890
        
        headers, params = self.handler.sign_request('POST', '/orders', {'symbol': 'BTC-USD'})
        
        # Check headers
        assert headers['CB-ACCESS-KEY'] == 'test_key'
        assert headers['CB-ACCESS-TIMESTAMP'] == '1234567890'
        assert 'CB-ACCESS-SIGN' in headers
        
        # For POST, params should be None (moved to body)
        assert params is None
    
    def test_generate_signature(self):
        """Test signature generation"""
        signature = self.handler._generate_signature('1234567890', 'GET', '/products', '')
        
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Should be valid base64
        try:
            base64.b64decode(signature)
        except Exception:
            pytest.fail("Signature is not valid base64")
    
    def test_generate_signature_error_handling(self):
        """Test signature generation error handling"""
        # Create handler with invalid secret
        invalid_config = ExchangeConfig.create_coinbase_config("key", "invalid_base64!", "pass")
        invalid_handler = CoinbaseAuthHandler(invalid_config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            invalid_handler._generate_signature('123', 'GET', '/products', '')
        
        assert "Failed to generate Coinbase signature" in str(exc_info.value)

class TestGeminiAuthHandler:
    """Test cases for Gemini authentication handler"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = ExchangeConfig.create_gemini_config("test_key", "test_secret")
        self.handler = GeminiAuthHandler(self.config)
    
    def test_initialization(self):
        """Test handler initialization"""
        assert self.handler.api_key == "test_key"
        assert self.handler.api_secret == "test_secret"
    
    @patch('time.time')
    def test_sign_request(self, mock_time):
        """Test signing request"""
        mock_time.return_value = 1234567890.123
        
        headers, params = self.handler.sign_request('POST', '/v1/order/new', {'test': 'param'})
        
        # Check headers
        assert headers['X-GEMINI-APIKEY'] == 'test_key'
        assert 'X-GEMINI-PAYLOAD' in headers
        assert 'X-GEMINI-SIGNATURE' in headers
        assert headers['Content-Type'] == 'text/plain'
        assert headers['Content-Length'] == '0'
        assert headers['Cache-Control'] == 'no-cache'
        
        # For Gemini, params should be empty (moved to headers)
        assert params == {}
        
        # Verify payload is valid base64
        try:
            payload_data = base64.b64decode(headers['X-GEMINI-PAYLOAD'])
            payload_json = json.loads(payload_data)
            assert payload_json['test'] == 'param'
            assert payload_json['request'] == '/v1/order/new'
            assert 'nonce' in payload_json
        except Exception:
            pytest.fail("Payload is not valid base64 JSON")
    
    def test_generate_signature(self):
        """Test signature generation"""
        test_payload = {'test': 'data', 'nonce': '123'}
        signature = self.handler._generate_signature(test_payload)
        
        assert isinstance(signature, str)
        assert len(signature) == 96  # SHA384 hex length
    
    def test_generate_signature_error_handling(self):
        """Test signature generation error handling"""
        # Create handler with invalid secret (None)
        invalid_config = ExchangeConfig.create_gemini_config("key", None)
        invalid_handler = GeminiAuthHandler(invalid_config)
        
        with pytest.raises(AuthenticationError) as exc_info:
            invalid_handler._generate_signature({'test': 'data'})
        
        assert "Failed to generate Gemini signature" in str(exc_info.value)

class TestAuthHandlerFactory:
    """Test cases for auth handler factory function"""
    
    def test_get_binance_handler(self):
        """Test getting Binance auth handler"""
        config = ExchangeConfig.create_binance_config("key", "secret")
        handler = get_auth_handler(config)
        
        assert isinstance(handler, BinanceAuthHandler)
        assert handler.api_key == "key"
    
    def test_get_kraken_handler(self):
        """Test getting Kraken auth handler"""
        config = ExchangeConfig.create_kraken_config("key", "secret")
        handler = get_auth_handler(config)
        
        assert isinstance(handler, KrakenAuthHandler)
        assert handler.api_key == "key"
    
    def test_get_coinbase_handler(self):
        """Test getting Coinbase auth handler"""
        config = ExchangeConfig.create_coinbase_config("key", "secret", "pass")
        handler = get_auth_handler(config)
        
        assert isinstance(handler, CoinbaseAuthHandler)
        assert handler.api_key == "key"
        assert handler.passphrase == "pass"
    
    def test_get_gemini_handler(self):
        """Test getting Gemini auth handler"""
        config = ExchangeConfig.create_gemini_config("key", "secret")
        handler = get_auth_handler(config)
        
        assert isinstance(handler, GeminiAuthHandler)
        assert handler.api_key == "key"
    
    def test_unsupported_exchange_type(self):
        """Test error for unsupported exchange type"""
        # Create config with unsupported type
        config = ExchangeConfig(
            exchange_type=ExchangeType.TEST,
            api_url="test.com",
            api_key="key",
            api_secret="secret"
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            get_auth_handler(config)
        
        assert "No auth handler for exchange type" in str(exc_info.value)
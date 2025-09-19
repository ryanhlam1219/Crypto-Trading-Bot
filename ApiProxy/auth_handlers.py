"""
Authentication Handlers

Exchange-specific authentication handlers for API requests.
"""

import hashlib
import hmac
import base64
import urllib.parse
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any, Optional

from .config import ExchangeConfig, ExchangeType
from .exceptions import AuthenticationError

class BaseAuthHandler(ABC):
    """Base authentication handler"""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.api_key = config.api_key
        self.api_secret = config.api_secret
        
    @abstractmethod
    def sign_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """
        Sign a request for the specific exchange
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Request parameters
            
        Returns:
            Tuple of (headers, signed_params)
        """
        pass

class BinanceAuthHandler(BaseAuthHandler):
    """Binance API authentication handler"""
    
    def sign_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Sign Binance request with HMAC SHA256"""
        if not params:
            params = {}
            
        # Add timestamp
        params['timestamp'] = int(time.time() * 1000)
        
        # Create signature
        query_string = urllib.parse.urlencode(params)
        signature = self._generate_signature(query_string)
        params['signature'] = signature
        
        # Headers
        headers = {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        return headers, params
    
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC SHA256 signature"""
        try:
            message = data.encode('utf-8')
            byte_key = bytes(self.api_secret, 'UTF-8')
            mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
            return mac
        except Exception as e:
            raise AuthenticationError(f"Failed to generate Binance signature: {e}")

class KrakenAuthHandler(BaseAuthHandler):
    """Kraken API authentication handler"""
    
    def sign_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Sign Kraken request with HMAC SHA512"""
        if not params:
            params = {}
            
        # Add nonce
        nonce = str(int(time.time() * 1000))
        params['nonce'] = nonce
        
        # Create signature for private endpoints
        if endpoint.startswith('/0/private/'):
            signature = self._generate_signature(endpoint, params, nonce)
            headers = {
                'API-Key': self.api_key,
                'API-Sign': signature,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        else:
            # Public endpoint
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            
        return headers, params
    
    def _generate_signature(self, uri_path: str, data: Dict[str, Any], nonce: str) -> str:
        """Generate HMAC SHA512 signature for Kraken"""
        try:
            postdata = urllib.parse.urlencode(data)
            encoded = (nonce + postdata).encode()
            message = uri_path.encode() + hashlib.sha256(encoded).digest()
            
            mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
            return base64.b64encode(mac.digest()).decode()
        except Exception as e:
            raise AuthenticationError(f"Failed to generate Kraken signature: {e}")

class CoinbaseAuthHandler(BaseAuthHandler):
    """Coinbase Advanced Trade authentication handler"""
    
    def __init__(self, config: ExchangeConfig):
        super().__init__(config)
        self.passphrase = config.additional_params.get('passphrase', '') if config.additional_params else ''
        
    def sign_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Sign Coinbase request with HMAC SHA256"""
        timestamp = str(int(time.time()))
        body = ''
        
        if method == 'POST' and params:
            body = json.dumps(params)
            params = None  # For POST, params go in body
        elif method == 'GET' and params:
            # For GET, params become query string
            pass
            
        signature = self._generate_signature(timestamp, method, endpoint, body)
        
        headers = {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        return headers, params
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """Generate HMAC SHA256 signature for Coinbase"""
        try:
            message = timestamp + method + request_path + body
            hmac_key = base64.b64decode(self.api_secret)
            signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
            return base64.b64encode(signature.digest()).decode()
        except Exception as e:
            raise AuthenticationError(f"Failed to generate Coinbase signature: {e}")

class GeminiAuthHandler(BaseAuthHandler):
    """Gemini API authentication handler"""
    
    def sign_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Sign Gemini request with HMAC SHA384"""
        if not params:
            params = {}
            
        # Add nonce and request
        nonce = str(int(time.time() * 1000))
        params['nonce'] = nonce
        params['request'] = endpoint
        
        signature = self._generate_signature(params)
        
        headers = {
            'X-GEMINI-APIKEY': self.api_key,
            'X-GEMINI-PAYLOAD': base64.b64encode(json.dumps(params).encode()).decode(),
            'X-GEMINI-SIGNATURE': signature,
            'Content-Type': 'text/plain',
            'Content-Length': '0',
            'Cache-Control': 'no-cache'
        }
        
        return headers, {}  # Gemini puts params in headers
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate HMAC SHA384 signature for Gemini"""
        try:
            encoded_payload = base64.b64encode(json.dumps(payload).encode())
            signature = hmac.new(self.api_secret.encode(), encoded_payload, hashlib.sha384).hexdigest()
            return signature
        except Exception as e:
            raise AuthenticationError(f"Failed to generate Gemini signature: {e}")

def get_auth_handler(config: ExchangeConfig) -> BaseAuthHandler:
    """Factory function to get appropriate auth handler"""
    handlers = {
        ExchangeType.BINANCE: BinanceAuthHandler,
        ExchangeType.KRAKEN: KrakenAuthHandler,
        ExchangeType.COINBASE: CoinbaseAuthHandler,
        ExchangeType.GEMINI: GeminiAuthHandler,
    }
    
    handler_class = handlers.get(config.exchange_type)
    if not handler_class:
        raise AuthenticationError(f"No auth handler for exchange type: {config.exchange_type}")
        
    return handler_class(config)
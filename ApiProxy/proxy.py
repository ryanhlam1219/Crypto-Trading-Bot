"""
API Proxy Core

Centralized API proxy for crypto exchange integrations.
"""

import requests
import time
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

from .config import ExchangeConfig
from .auth_handlers import get_auth_handler, BaseAuthHandler
from .exceptions import (
    APIProxyError, 
    AuthenticationError, 
    RateLimitError, 
    ExchangeConnectionError,
    InvalidResponseError
)

logger = logging.getLogger(__name__)

class APIProxy:
    """Centralized API proxy for crypto exchanges"""
    
    def __init__(self, config: ExchangeConfig):
        """
        Initialize API proxy with exchange configuration
        
        Args:
            config: Exchange configuration object
        """
        self.config = config
        self.auth_handler = get_auth_handler(config)
        self.session = requests.Session()
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
    def make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        auth_required: bool = True,
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated or public API request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters for GET or form data for POST
            json_data: JSON data for POST requests
            auth_required: Whether authentication is required
            timeout: Request timeout in seconds
            
        Returns:
            Parsed JSON response or None on error
            
        Raises:
            APIProxyError: For various API-related errors
        """
        try:
            # Rate limiting
            self._enforce_rate_limit()
            
            # Prepare URL
            url = urljoin(self.config.api_url, endpoint)
            
            # Authentication
            headers = {}
            if auth_required:
                auth_headers, auth_params = self.auth_handler.sign_request(method, endpoint, params)
                headers.update(auth_headers)
                if auth_params:
                    params = auth_params
            
            # Make request
            logger.debug(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                if json_data:
                    response = self.session.post(url, json=json_data, headers=headers, timeout=timeout)
                else:
                    response = self.session.post(url, data=params, headers=headers, timeout=timeout)
            else:
                raise APIProxyError(f"Unsupported HTTP method: {method}")
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            raise ExchangeConnectionError(f"Request timeout to {self.config.exchange_type.value}")
        except requests.exceptions.ConnectionError:
            raise ExchangeConnectionError(f"Connection error to {self.config.exchange_type.value}")
        except AuthenticationError:
            raise  # Re-raise auth errors
        except (RateLimitError, InvalidResponseError, ExchangeConnectionError, APIProxyError):
            raise  # Re-raise our custom exceptions
        except Exception as e:
            raise APIProxyError(f"Unexpected error in API request: {e}")
    
    def make_public_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Make public (non-authenticated) API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Parsed JSON response or None on error
        """
        return self.make_request(method, endpoint, params, auth_required=False, timeout=timeout)
    
    def _handle_response(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """
        Handle and validate API response
        
        Args:
            response: Raw HTTP response
            
        Returns:
            Parsed JSON data or None
            
        Raises:
            RateLimitError: If rate limited
            InvalidResponseError: If response is invalid
            APIProxyError: For other API errors
        """
        try:
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")
            
            # Check for successful response
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Successful response: {response.status_code}")
                    return data
                except ValueError as e:
                    raise InvalidResponseError(f"Invalid JSON in response: {e}")
            
            # Handle various error codes
            elif response.status_code == 401:
                raise AuthenticationError("Invalid API credentials")
            elif response.status_code == 403:
                raise AuthenticationError("API access forbidden")
            elif response.status_code == 404:
                raise APIProxyError("API endpoint not found")
            elif response.status_code >= 500:
                raise ExchangeConnectionError(f"Exchange server error: {response.status_code}")
            else:
                # Try to get error message from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('msg', error_data.get('error', 'Unknown error'))
                except:
                    error_msg = f"HTTP {response.status_code}"
                raise APIProxyError(f"API request failed: {error_msg}")
                
        except (RateLimitError, AuthenticationError, InvalidResponseError, APIProxyError):
            raise  # Re-raise our custom exceptions
        except Exception as e:
            raise APIProxyError(f"Error handling response: {e}")
    
    def _enforce_rate_limit(self):
        """Enforce minimum time between requests"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def close(self):
        """Close the session"""
        self.session.close()
"""
API Proxy Exceptions

Custom exception classes for API proxy operations.
"""

class APIProxyError(Exception):
    """Base exception for API proxy operations"""
    pass

class AuthenticationError(APIProxyError):
    """Raised when authentication fails"""
    pass

class RateLimitError(APIProxyError):
    """Raised when rate limits are exceeded"""
    pass

class ExchangeConnectionError(APIProxyError):
    """Raised when exchange connection fails"""
    pass

class InvalidResponseError(APIProxyError):
    """Raised when response format is invalid"""
    pass
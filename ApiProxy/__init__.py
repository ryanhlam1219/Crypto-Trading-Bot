"""
API Proxy Package

Centralized API proxy for crypto exchange integrations.
Provides unified interface for different exchange APIs while handling
authentication, rate limiting, and response formatting.
"""

from .proxy import APIProxy
from .auth_handlers import (
    BaseAuthHandler,
    BinanceAuthHandler,
    KrakenAuthHandler,
    CoinbaseAuthHandler,
    GeminiAuthHandler
)
from .config import ExchangeConfig, ExchangeType
from .exceptions import APIProxyError, AuthenticationError, RateLimitError

__all__ = [
    'APIProxy',
    'BaseAuthHandler',
    'BinanceAuthHandler', 
    'KrakenAuthHandler',
    'CoinbaseAuthHandler',
    'GeminiAuthHandler',
    'ExchangeConfig',
    'ExchangeType',
    'APIProxyError',
    'AuthenticationError', 
    'RateLimitError'
]

__version__ = '1.0.0'
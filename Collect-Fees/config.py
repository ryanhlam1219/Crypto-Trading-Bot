#!/usr/bin/env python3
"""
Configuration Management

Centralized configuration for the fee collection system.
Allows easy switching between different exchanges and trading pairs.
"""

from decouple import config
from typing import List, Dict

class Config:
    """Configuration management"""
    
    # Trading pair settings
    BASE_CURRENCY = config('BASE_CURRENCY', default='BTC')
    QUOTE_CURRENCY = config('QUOTE_CURRENCY', default='USD')
    
    # Collection settings
    COLLECTION_INTERVAL_SECONDS = int(config('COLLECTION_INTERVAL_SECONDS', default=300))
    
    # Exchange API credentials
    BINANCE_API_KEY = config('BINANCE_API_KEY', default='')
    BINANCE_API_SECRET = config('BINANCE_API_SECRET', default='')
    
    KRAKEN_API_KEY = config('KRAKEN_API_KEY', default='')
    KRAKEN_API_SECRET = config('KRAKEN_API_SECRET', default='')
    
    COINBASE_API_KEY = config('COINBASE_API_KEY', default='')
    COINBASE_SECRET_KEY = config('COINBASE_SECRET_KEY', default='')
    COINBASE_PASSPHRASE = config('COINBASE_PASSPHRASE', default='')
    
    GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
    GEMINI_API_SECRET = config('GEMINI_API_SECRET', default='')
    GEMINI_SANDBOX = config('GEMINI_SANDBOX', default='false')
    
    # Logging
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')
    
    @classmethod
    def get_enabled_exchanges(cls) -> List[str]:
        """Get list of exchanges with configured API keys"""
        enabled = []
        
        if cls.BINANCE_API_KEY and cls.BINANCE_API_SECRET:
            enabled.append('binance')
            
        if cls.KRAKEN_API_KEY and cls.KRAKEN_API_SECRET:
            enabled.append('kraken')
            
        if cls.COINBASE_API_KEY and cls.COINBASE_SECRET_KEY:
            enabled.append('coinbase')
            
        if cls.GEMINI_API_KEY and cls.GEMINI_API_SECRET:
            enabled.append('gemini')
            
        return enabled
    
    @classmethod
    def get_trading_pair(cls) -> str:
        """Get formatted trading pair"""
        return f"{cls.BASE_CURRENCY}/{cls.QUOTE_CURRENCY}"
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration and return status"""
        enabled = cls.get_enabled_exchanges()
        
        return {
            'has_exchanges': len(enabled) > 0,
            'enabled_exchanges': enabled,
            'trading_pair': cls.get_trading_pair(),
            'collection_interval': cls.COLLECTION_INTERVAL_SECONDS,
            'log_level': cls.LOG_LEVEL
        }
"""
Exchange Configuration

Configuration classes for different exchange APIs.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    KRAKEN = "kraken"
    COINBASE = "coinbase"
    GEMINI = "gemini"
    TEST = "test"

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    exchange_type: ExchangeType
    api_url: str
    api_key: str
    api_secret: str
    additional_params: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create_binance_config(cls, api_key: str, api_secret: str, sandbox: bool = False):
        """Create Binance configuration"""
        url = "https://api.binance.us" if not sandbox else "https://testnet.binance.vision"
        return cls(
            exchange_type=ExchangeType.BINANCE,
            api_url=url,
            api_key=api_key,
            api_secret=api_secret
        )
    
    @classmethod 
    def create_kraken_config(cls, api_key: str, api_secret: str):
        """Create Kraken configuration"""
        return cls(
            exchange_type=ExchangeType.KRAKEN,
            api_url="https://api.kraken.com",
            api_key=api_key,
            api_secret=api_secret
        )
    
    @classmethod
    def create_coinbase_config(cls, api_key: str, api_secret: str, passphrase: str):
        """Create Coinbase configuration"""
        return cls(
            exchange_type=ExchangeType.COINBASE,
            api_url="https://api.coinbase.com",
            api_key=api_key,
            api_secret=api_secret,
            additional_params={"passphrase": passphrase}
        )
    
    @classmethod
    def create_gemini_config(cls, api_key: str, api_secret: str, sandbox: bool = False):
        """Create Gemini configuration"""
        url = "https://api.gemini.com" if not sandbox else "https://api.sandbox.gemini.com"
        return cls(
            exchange_type=ExchangeType.GEMINI,
            api_url=url,
            api_key=api_key,
            api_secret=api_secret
        )
        
    @classmethod
    def create_test_config(cls):
        """Create test exchange configuration"""
        return cls(
            exchange_type=ExchangeType.TEST,
            api_url="https://test.example.com",
            api_key="test_key",
            api_secret="test_secret"
        )
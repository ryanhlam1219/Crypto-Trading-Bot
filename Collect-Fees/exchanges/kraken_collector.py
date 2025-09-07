#!/usr/bin/env python3
"""
Kraken Fee Collector

Collects trading fee data from Kraken API
"""

import urllib.parse
import hashlib
import hmac
import base64
import requests
import time
import json
import logging
from typing import Optional, Dict, Any
from decouple import config
from .base_collector import BaseExchangeCollector

# Use exchange-specific logger
logger = logging.getLogger('exchange.kraken')

class KrakenCollector(BaseExchangeCollector):
    """Kraken fee collector"""
    
    def __init__(self, base_currency: str, quote_currency: str):
        super().__init__(base_currency, quote_currency)
        self.api_url = "https://api.kraken.com"
        self.api_key = config('KRAKEN_API_KEY', default='')
        self.api_secret = config('KRAKEN_API_SECRET', default='')
        
        # Kraken uses different symbol format (XBTUSD for BTCUSD)
        self.symbol = self._get_kraken_symbol(base_currency, quote_currency)
        
    def _get_kraken_symbol(self, base: str, quote: str) -> str:
        """Convert standard symbols to Kraken format"""
        # Kraken uses specific symbol formats
        base_upper = base.upper()
        quote_upper = quote.upper()
        
        # Common Kraken trading pairs (actual API symbols)
        symbol_mapping = {
            ('BTC', 'USD'): 'XXBTZUSD',
            ('ETH', 'USD'): 'XETHZUSD',
            ('BTC', 'EUR'): 'XXBTZEUR',
            ('ETH', 'EUR'): 'XETHZEUR',
        }
        
        # Check direct mapping first
        if (base_upper, quote_upper) in symbol_mapping:
            return symbol_mapping[(base_upper, quote_upper)]
        
        # Fallback to standard Kraken format
        symbol_map = {
            'BTC': 'XBT',
            'USD': 'USD',
            'ETH': 'ETH',
            'EUR': 'EUR'
        }
        
        kraken_base = symbol_map.get(base_upper, base_upper)
        kraken_quote = symbol_map.get(quote_upper, quote_upper)
        
        return f"{kraken_base}{kraken_quote}"
    
    def _get_signature(self, uri_path: str, data: dict) -> str:
        """Generate signature for Kraken API"""
        try:
            postdata = urllib.parse.urlencode(data)
            encoded = (str(data['nonce']) + postdata).encode()
            message = uri_path.encode() + hashlib.sha256(encoded).digest()
            
            mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
            sigdigest = base64.b64encode(mac.digest())
            return sigdigest.decode()
        except Exception as e:
            logger.error(f"Kraken signature error: {e}")
            return ""
    
    def _make_signed_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a signed request to Kraken API"""
        if not self.api_key or not self.api_secret:
            logger.error("Kraken API credentials not configured")
            return None
            
        try:
            if params is None:
                params = {}
                
            params['nonce'] = str(int(1000 * time.time()))
            
            headers = {
                'API-Key': self.api_key,
                'API-Sign': self._get_signature(endpoint, params)
            }
            
            response = requests.post(
                f"{self.api_url}{endpoint}",
                headers=headers,
                data=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('error'):
                    logger.error(f"Kraken API error: {data['error']}")
                    return None
                return data.get('result')
            else:
                logger.error(f"Kraken HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Kraken request error: {e}")
            return None
    
    def _make_public_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a public request to Kraken API"""
        try:
            response = requests.get(
                f"{self.api_url}{endpoint}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('error'):
                    logger.error(f"Kraken API error: {data['error']}")
                    return None
                return data.get('result')
            else:
                logger.error(f"Kraken HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Kraken public request error: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price from Kraken"""
        try:
            result = self._make_public_request(
                '/0/public/Ticker',
                {'pair': self.symbol}
            )
            
            if result and self.symbol in result:
                ticker = result[self.symbol]
                return float(ticker['c'][0])  # Last trade price
            
            return None
            
        except Exception as e:
            logger.error(f"Kraken price error: {e}")
            return None
    
    def get_trading_fee(self, transaction_amount: float) -> Optional[float]:
        """Get trading fee for a specific transaction amount"""
        try:
            # Get current price
            current_price = self.get_current_price()
            if not current_price:
                return None
            
            # Calculate quantity from USD amount
            quantity = self.calculate_quantity_from_amount(transaction_amount, current_price)
            
            # Get trading fee info for this pair
            result = self._make_signed_request('/0/private/TradeVolume')
            
            if not result:
                # Fallback to default fee structure
                return self._calculate_fee_from_default_structure(transaction_amount, quantity, current_price)
            
            # Get fee percentage for this pair
            fees_maker = result.get('fees_maker', {}) if result else {}
            fee_rate = 0.0026  # Default Kraken fee
            
            if fees_maker and self.symbol in fees_maker:
                fee_rate = float(fees_maker[self.symbol]['fee']) / 100
            elif result and 'fees' in result and result['fees'] and self.symbol in result['fees']:
                fee_rate = float(result['fees'][self.symbol]['fee']) / 100
            
            # Calculate fee in quote currency
            fee_in_base = quantity * fee_rate
            fee_in_quote = fee_in_base * current_price
            
            return fee_in_quote
            
        except Exception as e:
            logger.error(f"Kraken fee calculation error: {e}")
            return None
    
    def _calculate_fee_from_default_structure(self, amount: float, quantity: float, price: float) -> float:
        """Calculate fee using Kraken's default fee structure"""
        # Kraken default fee tiers (volume in USD over 30 days)
        fee_tiers = [
            (0, 0.0026),      # 0-50k: 0.26%
            (50000, 0.0024),  # 50k-100k: 0.24%
            (100000, 0.0022), # 100k-250k: 0.22%
            (250000, 0.0020), # 250k-500k: 0.20%
            (500000, 0.0018), # 500k-1M: 0.18%
            (1000000, 0.0016) # 1M+: 0.16%
        ]
        
        # Use maker fee (typically better)
        fee_rate = 0.0026  # Default
        
        for tier_volume, tier_fee in reversed(fee_tiers):
            if amount >= tier_volume:
                fee_rate = tier_fee
                break
        
        # Calculate fee in quote currency
        fee_in_base = quantity * fee_rate
        return fee_in_base * price
    
    def get_fee_structure(self) -> Dict[str, Any]:
        """Get Kraken fee structure"""
        try:
            result = self._make_signed_request('/0/private/TradeVolume')
            
            if result:
                return {
                    'exchange': 'Kraken',
                    'symbol': self.symbol,
                    'volume_30d': result.get('volume', 0),
                    'fees': result.get('fees', {}),
                    'fees_maker': result.get('fees_maker', {})
                }
            
            return {
                'exchange': 'Kraken',
                'symbol': self.symbol,
                'default_fee_rate': 0.0026,
                'fee_structure': 'Tiered based on 30-day volume'
            }
            
        except Exception as e:
            logger.error(f"Kraken fee structure error: {e}")
            return {}
    
    def get_min_transaction_amount(self) -> float:
        """Get minimum transaction amount for Kraken"""
        try:
            result = self._make_public_request('/0/public/AssetPairs', {'pair': self.symbol})
            
            if result and self.symbol in result:
                pair_info = result[self.symbol]
                # ordermin is minimum order size in base currency
                min_order = float(pair_info.get('ordermin', 0))
                
                if min_order > 0:
                    current_price = self.get_current_price()
                    if current_price:
                        return min_order * current_price
            
            return 10.0  # Default fallback
            
        except Exception as e:
            logger.error(f"Kraken min amount error: {e}")
            return 10.0
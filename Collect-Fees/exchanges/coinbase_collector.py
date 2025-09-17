#!/usr/bin/env python3
"""
Coinbase Fee Collector

Collects trading fee data from Coinbase Advanced Trade API
"""

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

logger = logging.getLogger(__name__)

class CoinbaseCollector(BaseExchangeCollector):
    """Coinbase Advanced Trade fee collector"""
    
    def __init__(self, base_currency: str, quote_currency: str):
        super().__init__(base_currency, quote_currency)
        self.api_url = "https://api.coinbase.com"
        self.api_key = config('COINBASE_API_KEY', default='')
        self.api_secret = config('COINBASE_API_SECRET', default='')
        self.passphrase = config('COINBASE_PASSPHRASE', default='')
        
        # Coinbase uses dash format (BTC-USD)
        self.symbol = f"{base_currency.upper()}-{quote_currency.upper()}"
        
    def _get_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """Generate signature for Coinbase API"""
        try:
            message = timestamp + method + request_path + body
            hmac_key = base64.b64decode(self.api_secret)
            signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
            signature_b64 = base64.b64encode(signature.digest()).decode()
            return signature_b64
        except Exception as e:
            logger.error(f"Coinbase signature error: {e}")
            return ""
    
    def _make_signed_request(self, method: str, endpoint: str, params: dict = None, json_data: dict = None) -> Optional[dict]:
        """Make a signed request to Coinbase API"""
        if not all([self.api_key, self.api_secret, self.passphrase]):
            logger.error("Coinbase API credentials not fully configured")
            return None
            
        try:
            timestamp = str(time.time())
            body = ''
            
            if method == 'GET' and params:
                endpoint += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
            elif method == 'POST' and json_data:
                body = json.dumps(json_data)
            
            signature = self._get_signature(timestamp, method, endpoint, body)
            
            headers = {
                'CB-ACCESS-KEY': self.api_key,
                'CB-ACCESS-SIGN': signature,
                'CB-ACCESS-TIMESTAMP': timestamp,
                'CB-ACCESS-PASSPHRASE': self.passphrase,
                'Content-Type': 'application/json'
            }
            
            if method == 'GET':
                response = requests.get(f"{self.api_url}{endpoint}", headers=headers, timeout=10)
            else:
                response = requests.post(f"{self.api_url}{endpoint}", headers=headers, json=json_data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Coinbase API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Coinbase request error: {e}")
            return None
    
    def _make_public_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a public request to Coinbase API"""
        try:
            response = requests.get(
                f"{self.api_url}{endpoint}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Coinbase public API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Coinbase public request error: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price from Coinbase"""
        try:
            result = self._make_public_request(f'/v2/exchange-rates?currency={self.base_currency}')
            
            if result and 'data' in result and 'rates' in result['data']:
                rates = result['data']['rates']
                if self.quote_currency in rates:
                    return float(rates[self.quote_currency])
            
            # Fallback to products endpoint
            result = self._make_public_request(f'/v2/prices/{self.symbol}/spot')
            
            if result and 'data' in result and 'amount' in result['data']:
                return float(result['data']['amount'])
            
            return None
            
        except Exception as e:
            logger.error(f"Coinbase price error: {e}")
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
            
            # Get account trading fee info (requires authentication)
            if self.api_key and self.api_secret and self.passphrase:
                result = self._make_signed_request('GET', '/v2/accounts')
                
                if result:
                    # Coinbase Advanced Trade has different fee structure
                    return self._calculate_advanced_trade_fee(transaction_amount, quantity, current_price)
            
            # Fallback to default fee structure
            return self._calculate_fee_from_default_structure(transaction_amount, quantity, current_price)
            
        except Exception as e:
            logger.error(f"Coinbase fee calculation error: {e}")
            return None
    
    def _calculate_advanced_trade_fee(self, amount: float, quantity: float, price: float) -> float:
        """Calculate fee using Coinbase Advanced Trade fee structure"""
        # Coinbase Advanced Trade fee tiers (30-day volume in USD)
        fee_tiers = [
            (0, 0.006, 0.008),        # 0-10k: 0.60% maker, 0.80% taker
            (10000, 0.004, 0.006),    # 10k-50k: 0.40% maker, 0.60% taker
            (50000, 0.0025, 0.004),   # 50k-100k: 0.25% maker, 0.40% taker
            (100000, 0.0015, 0.0025), # 100k-1M: 0.15% maker, 0.25% taker
            (1000000, 0.001, 0.0015), # 1M-15M: 0.10% maker, 0.15% taker
            (15000000, 0.0005, 0.001) # 15M+: 0.05% maker, 0.10% taker
        ]
        
        # Use taker fee (more conservative)
        maker_fee, taker_fee = 0.006, 0.008  # Default
        
        for tier_volume, tier_maker, tier_taker in reversed(fee_tiers):
            if amount >= tier_volume:
                maker_fee, taker_fee = tier_maker, tier_taker
                break
        
        # Use maker fee (better rate)
        fee_rate = maker_fee
        
        # Calculate fee in quote currency
        return amount * fee_rate
    
    def _calculate_fee_from_default_structure(self, amount: float, quantity: float, price: float) -> float:
        """Calculate fee using Coinbase's default fee structure"""
        # Standard Coinbase fee (simplified)
        base_fee = 0.005  # 0.5%
        
        # Volume-based discount
        if amount > 100000:
            base_fee = 0.003
        elif amount > 10000:
            base_fee = 0.004
        
        return amount * base_fee
    
    def get_fee_structure(self) -> Dict[str, Any]:
        """Get Coinbase fee structure"""
        try:
            if self.api_key and self.api_secret and self.passphrase:
                # Try to get actual fee info
                result = self._make_signed_request('GET', '/v2/user')
                
                if result:
                    return {
                        'exchange': 'Coinbase',
                        'symbol': self.symbol,
                        'fee_structure': 'Volume-based tiers',
                        'user_data': result.get('data', {})
                    }
            
            return {
                'exchange': 'Coinbase',
                'symbol': self.symbol,
                'fee_structure': 'Advanced Trade - Volume-based tiers',
                'maker_fee_range': '0.05% - 0.60%',
                'taker_fee_range': '0.10% - 0.80%'
            }
            
        except Exception as e:
            logger.error(f"Coinbase fee structure error: {e}")
            return {}
    
    def get_min_transaction_amount(self) -> float:
        """Get minimum transaction amount for Coinbase"""
        try:
            # Coinbase typically has $1 minimum for most pairs
            return 1.0
            
        except Exception as e:
            logger.error(f"Coinbase min amount error: {e}")
            return 1.0
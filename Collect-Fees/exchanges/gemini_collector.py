#!/usr/bin/env python3
"""
Gemini Fee Collector

Collects trading fee data from Gemini API
"""

import time
import json
import logging
from typing import Optional, Dict, Any
from decouple import config
from .base_collector import BaseExchangeCollector

# Import APIProxy
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from ApiProxy import APIProxy, ExchangeConfig

# Use exchange-specific logger
logger = logging.getLogger('exchange.gemini')

class GeminiCollector(BaseExchangeCollector):
    """Gemini fee collector"""
    
    def __init__(self, base_currency: str, quote_currency: str):
        super().__init__(base_currency, quote_currency)
        self.api_url = "https://api.gemini.com"
        self.sandbox_url = "https://api.sandbox.gemini.com"
        self.api_key = config('GEMINI_API_KEY', default='')
        self.api_secret = config('GEMINI_API_SECRET', default='')
        self.use_sandbox = config('GEMINI_SANDBOX', default='false').lower() == 'true'
        
        # Use sandbox if configured
        if self.use_sandbox:
            self.api_url = self.sandbox_url
            
        # Initialize API Proxy with Gemini configuration
        self.api_proxy = APIProxy(ExchangeConfig.gemini(self.api_key, self.api_secret, self.use_sandbox))
        
        # Gemini uses lowercase format (btcusd)
        self.symbol = f"{base_currency.lower()}{quote_currency.lower()}"
        
    def _make_signed_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a signed request to Gemini API"""
        if not self.api_key or not self.api_secret:
            logger.debug("Gemini API credentials not configured")
            return None
            
        try:
            if params is None:
                params = {}
                
            response = self.api_proxy.make_request('POST', endpoint, data=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.debug(f"Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.debug(f"Gemini request error: {e}")
            return None
    
    def _make_public_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a public request to Gemini API"""
        try:
            response = self.api_proxy.make_public_request('GET', endpoint, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Gemini public API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Gemini public request error: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price from Gemini"""
        try:
            result = self._make_public_request(f'/v1/pubticker/{self.symbol}')
            
            if result and 'last' in result:
                return float(result['last'])
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini price error: {e}")
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
            
            # Try to get account trading fee info if API keys are configured
            if self.api_key and self.api_secret:
                try:
                    # Get trading volume to determine fee tier
                    volume_result = self._make_signed_request('/v1/tradevolume')
                    if volume_result and isinstance(volume_result, list):
                        volume_30d = 0
                        for volume_data in volume_result:
                            if volume_data.get('symbol', '').lower() == self.symbol:
                                volume_30d = float(volume_data.get('base_volume', 0))
                                break
                        
                        return self._calculate_fee_from_volume(transaction_amount, volume_30d, current_price)
                except Exception as e:
                    logger.debug(f"Gemini authenticated request failed: {e}")
                    # Fall through to default calculation
            
            # Fallback to default fee structure (no authentication required)
            return self._calculate_fee_from_default_structure(transaction_amount, quantity, current_price)
            
        except Exception as e:
            logger.error(f"Gemini fee calculation error: {e}")
            return None
    
    def _calculate_fee_from_volume(self, amount: float, volume_30d: float, price: float) -> float:
        """Calculate fee based on 30-day volume"""
        # Gemini fee tiers (30-day volume in USD)
        fee_tiers = [
            (0, 0.0035, 0.0035),        # 0-500k: 0.35% maker/taker
            (500000, 0.0025, 0.0035),   # 500k-1M: 0.25% maker, 0.35% taker
            (1000000, 0.002, 0.0030),   # 1M-2.5M: 0.20% maker, 0.30% taker
            (2500000, 0.0015, 0.0025),  # 2.5M-5M: 0.15% maker, 0.25% taker
            (5000000, 0.001, 0.002),    # 5M-15M: 0.10% maker, 0.20% taker
            (15000000, 0.001, 0.0015),  # 15M-25M: 0.10% maker, 0.15% taker
            (25000000, 0.001, 0.001)    # 25M+: 0.10% maker/taker
        ]
        
        # Use maker fee (typically better)
        maker_fee, taker_fee = 0.0035, 0.0035  # Default
        
        volume_usd = volume_30d * price  # Convert volume to USD
        
        for tier_volume, tier_maker, tier_taker in reversed(fee_tiers):
            if volume_usd >= tier_volume:
                maker_fee, taker_fee = tier_maker, tier_taker
                break
        
        # Use maker fee
        return amount * maker_fee
    
    def _calculate_fee_from_default_structure(self, amount: float, quantity: float, price: float) -> float:
        """Calculate fee using Gemini's default fee structure"""
        # Default Gemini fees
        default_fee = 0.0035  # 0.35% for both maker and taker
        
        return amount * default_fee
    
    def get_fee_structure(self) -> Dict[str, Any]:
        """Get Gemini fee structure"""
        try:
            if self.api_key and self.api_secret:
                # Try to get account info
                account_result = self._make_signed_request('/v1/account')
                volume_result = self._make_signed_request('/v1/tradevolume')
                
                if account_result:
                    return {
                        'exchange': 'Gemini',
                        'symbol': self.symbol,
                        'account_info': account_result,
                        'trade_volume': volume_result,
                        'fee_structure': 'Volume-based tiers'
                    }
            
            return {
                'exchange': 'Gemini',
                'symbol': self.symbol,
                'fee_structure': 'Volume-based tiers',
                'default_fee': '0.35%',
                'fee_range': '0.10% - 0.35%'
            }
            
        except Exception as e:
            logger.error(f"Gemini fee structure error: {e}")
            return {}
    
    def get_min_transaction_amount(self) -> float:
        """Get minimum transaction amount for Gemini"""
        try:
            result = self._make_public_request(f'/v1/symbols/details/{self.symbol}')
            
            if result and 'min_order_size' in result:
                min_order = float(result['min_order_size'])
                current_price = self.get_current_price()
                if current_price:
                    return min_order * current_price
            
            return 5.0  # Default minimum
            
        except Exception as e:
            logger.error(f"Gemini min amount error: {e}")
            return 5.0
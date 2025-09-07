#!/usr/bin/env python3
"""
Binance Fee Collector

Collects trading fee data from Binance US API
"""

import urllib.parse
import hashlib
import hmac
import requests
import time
import json
import logging
from typing import Optional, Dict, Any
from decouple import config
from .base_collector import BaseExchangeCollector

# Use exchange-specific logger
logger = logging.getLogger('exchange.binance')

class BinanceCollector(BaseExchangeCollector):
    """Binance US fee collector"""
    
    def __init__(self, base_currency: str, quote_currency: str):
        super().__init__(base_currency, quote_currency)
        self.api_url = "https://api.binance.us"
        self.api_key = config('BINANCE_API_KEY')
        self.api_secret = config('BINANCE_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set")
            
        # Binance uses different symbol format
        self.symbol = f"{base_currency.upper()}{quote_currency.upper()}"
        
    def _get_signature(self, data: dict) -> str:
        """Generate HMAC SHA256 signature for Binance API"""
        postdata = urllib.parse.urlencode(data)
        message = postdata.encode()
        byte_key = bytes(self.api_secret, 'UTF-8')
        mac = hmac.new(byte_key, message, hashlib.sha256).hexdigest()
        return mac
    
    def _make_signed_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make a signed request to Binance API"""
        try:
            headers = {'X-MBX-APIKEY': self.api_key}
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._get_signature(params)
            
            response = requests.get(
                f"{self.api_url}{endpoint}",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Binance API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Binance request error: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price from Binance"""
        try:
            response = requests.get(
                f"{self.api_url}/api/v3/ticker/price",
                params={'symbol': self.symbol},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            else:
                logger.error(f"Binance price error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Binance price request error: {e}")
            return None
    
    def get_trading_fee(self, transaction_amount: float) -> Optional[float]:
        """
        Get trading fee for a specific transaction amount
        Uses account info endpoint or falls back to default fees
        """
        try:
            # Get current price first
            current_price = self.get_current_price()
            if not current_price:
                return None
            
            # Calculate quantity from USD amount
            quantity = self.calculate_quantity_from_amount(transaction_amount, current_price)
            
            # Try to get account info for VIP level
            try:
                account_data = self._make_signed_request('/api/v3/account', {})
                if account_data:
                    # Use maker fee rate from account (in basis points)
                    maker_fee_rate = float(account_data.get('makerCommission', 10))  # Default 10 bps
                    taker_fee_rate = float(account_data.get('takerCommission', 10))
                else:
                    # Fallback to default Binance US fees
                    maker_fee_rate = 10  # 0.1% = 10 basis points
                    taker_fee_rate = 10
            except:
                # Use default Binance US fees if account endpoint fails
                maker_fee_rate = 10  # 0.1% = 10 basis points
                taker_fee_rate = 10
            
            # Use maker fee (better rate)
            fee_rate_decimal = maker_fee_rate / 10000  # Convert basis points to decimal
            
            # Calculate fee in quote currency (USD)
            fee_in_base = quantity * fee_rate_decimal
            fee_in_quote = fee_in_base * current_price
            
            logger.debug(f"Binance fee: ${transaction_amount:.0f} -> {fee_rate_decimal:.4%} -> ${fee_in_quote:.4f}")
            
            return fee_in_quote
            
        except Exception as e:
            logger.error(f"Binance fee calculation error: {e}")
            return None
    
    def get_fee_structure(self) -> Dict[str, Any]:
        """Get Binance fee structure"""
        try:
            fee_data = self._make_signed_request('/sapi/v1/asset/tradeFee', {})
            
            if not fee_data:
                return {}
            
            # Find our symbol
            for fee_info in fee_data:
                if fee_info['symbol'] == self.symbol:
                    return {
                        'exchange': 'Binance',
                        'symbol': self.symbol,
                        'maker_fee_bps': float(fee_info['makerCommission']),
                        'taker_fee_bps': float(fee_info['takerCommission']),
                        'maker_fee_rate': float(fee_info['makerCommission']) / 10000,
                        'taker_fee_rate': float(fee_info['takerCommission']) / 10000
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"Binance fee structure error: {e}")
            return {}
    
    def get_min_transaction_amount(self) -> float:
        """Get minimum transaction amount for Binance"""
        try:
            response = requests.get(
                f"{self.api_url}/api/v3/exchangeInfo",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Find our symbol info
                for symbol_info in data['symbols']:
                    if symbol_info['symbol'] == self.symbol:
                        # Look for minimum notional filter
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'MIN_NOTIONAL':
                                return float(filter_info['minNotional'])
                        
                        # Look for minimum quantity filter
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'LOT_SIZE':
                                min_qty = float(filter_info['minQty'])
                                current_price = self.get_current_price()
                                if current_price:
                                    return min_qty * current_price
            
            return 10.0  # Default fallback
            
        except Exception as e:
            logger.error(f"Binance min amount error: {e}")
            return 10.0
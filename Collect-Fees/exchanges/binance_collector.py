#!/usr/bin/env python3
"""
Binance Fee Collector

Collects trading fee data from Binance US API
"""

import time
import json
import logging
from typing import Optional, Dict, Any
from decouple import config
from .base_collector import BaseExchangeCollector
from ApiProxy import APIProxy, ExchangeConfig

# Use exchange-specific logger
logger = logging.getLogger('exchange.binance')

class BinanceCollector(BaseExchangeCollector):
    """Binance US fee collector"""
    
    def __init__(self, base_currency: str, quote_currency: str):
        super().__init__(base_currency, quote_currency)
        self.api_key = config('BINANCE_API_KEY')
        self.api_secret = config('BINANCE_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET must be set")
            
        # Initialize API Proxy
        exchange_config = ExchangeConfig.create_binance_config(self.api_key, self.api_secret)
        self.api_proxy = APIProxy(exchange_config)
            
        # Binance uses different symbol format
        self.symbol = f"{base_currency.upper()}{quote_currency.upper()}"
        
    def _make_signed_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make a signed request to Binance API"""
        try:
            response = self.api_proxy.make_request('GET', endpoint, params)
            return response
        except Exception as e:
            logger.error(f"Error making signed request to {endpoint}: {e}")
            return None
    
    def get_current_price(self) -> Optional[float]:
        """Get current market price from Binance"""
        try:
            response = self.api_proxy.make_public_request('GET', '/api/v3/ticker/price', {'symbol': self.symbol})
            
            if response:
                return float(response['price'])
            else:
                logger.error("Failed to get price from Binance")
                return None
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
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
            response = self.api_proxy.make_public_request('GET', '/api/v3/exchangeInfo')
            
            if response:
                # Find our symbol info
                for symbol_info in response['symbols']:
                    if symbol_info['symbol'] == self.symbol:
                        # Look for minimum notional filter
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'NOTIONAL':
                                return float(filter_info.get('minNotional', 10.0))
                        return 10.0  # Default minimum
                return 10.0
            else:
                logger.error("Failed to get exchange info from Binance")
                return 10.0
        except Exception as e:
            logger.error(f"Error getting minimum transaction amount: {e}")
            return 10.0

    def __del__(self):
        """Clean up API proxy when object is destroyed"""
        if hasattr(self, 'api_proxy'):
            self.api_proxy.close()
#!/usr/bin/env python3
"""
Base Exchange Fee Collector Interface

Abstract base class for all exchange fee collectors.
Defines the standard interface for collecting fee data.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseExchangeCollector(ABC):
    """Base class for exchange fee collectors"""
    
    def __init__(self, base_currency: str, quote_currency: str):
        self.base_currency = base_currency.upper()
        self.quote_currency = quote_currency.upper()
        self.symbol = f"{base_currency}{quote_currency}".upper()
        self.name = self.__class__.__name__.replace('Collector', '')
        
    @abstractmethod
    def get_current_price(self) -> Optional[float]:
        """
        Get current market price for the trading pair
        
        Returns:
            float: Current price in quote currency, or None if error
        """
        pass
    
    @abstractmethod
    def get_trading_fee(self, transaction_amount: float) -> Optional[float]:
        """
        Get trading fee for a specific transaction amount
        
        Args:
            transaction_amount: Transaction size in quote currency (USD)
            
        Returns:
            float: Trading fee in quote currency, or None if error
        """
        pass
    
    @abstractmethod
    def get_fee_structure(self) -> Dict[str, Any]:
        """
        Get the exchange's fee structure/tiers
        
        Returns:
            Dict containing fee structure information
        """
        pass
    
    def calculate_quantity_from_amount(self, amount_usd: float, price: float) -> float:
        """
        Calculate base currency quantity from USD amount
        
        Args:
            amount_usd: Amount in USD
            price: Current price per unit
            
        Returns:
            float: Quantity in base currency
        """
        return amount_usd / price
    
    def validate_connection(self) -> bool:
        """
        Test connection to exchange API
        
        Returns:
            bool: True if connected successfully
        """
        try:
            price = self.get_current_price()
            return price is not None
        except Exception as e:
            logger.error(f"{self.name} connection validation failed: {e}")
            return False
    
    def get_min_transaction_amount(self) -> float:
        """
        Get minimum transaction amount for this exchange
        
        Returns:
            float: Minimum transaction amount in quote currency
        """
        return 10.0  # Default $10 minimum
    
    def get_max_transaction_amount(self) -> float:
        """
        Get maximum transaction amount for this exchange
        
        Returns:
            float: Maximum transaction amount in quote currency
        """
        return 1_000_000.0  # Default $1M maximum
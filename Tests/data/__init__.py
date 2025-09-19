"""
Test data utilities and historical data access.

This module provides access to historical market data used for backtesting
and testing purposes.
"""

import os
import re

def sanitize_filename(filename):
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): The filename to sanitize
        
    Returns:
        str: A sanitized filename safe for filesystem use
    """
    # Remove quotes, control characters, and comments
    sanitized = re.sub(r'["\']', '', filename)  # Remove quotes
    sanitized = re.sub(r'#.*$', '', sanitized, flags=re.MULTILINE)  # Remove comments
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)  # Remove control chars
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)  # Replace invalid chars with underscore
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscore
    sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
    return sanitized

def get_historical_data_path():
    """Get the path to the historical BTCUSD data file."""
    return os.path.join(os.path.dirname(__file__), 'past-1-years-historical-data-BTCUSD.csv')

__all__ = ['get_historical_data_path', 'sanitize_filename']
"""
Test data utilities and historical data access.

This module provides access to historical market data used for backtesting
and testing purposes.
"""

import os

def get_historical_data_path():
    """Get the path to the historical BTCUSD data file."""
    return os.path.join(os.path.dirname(__file__), 'past-1-years-historical-data-BTCUSD.csv')

__all__ = ['get_historical_data_path']
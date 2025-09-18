"""
Unit tests for Crypto Trading Bot

This package contains comprehensive unit tests for:
- Exchange implementations and compliance
- Strategy implementations and compliance  
- Utility classes and helpers
- Mock data and fixtures
- Historical data and backtesting utilities
"""

from .utils import DataFetchException, StrategyWrapper
from .data import get_historical_data_path

__all__ = ['DataFetchException', 'StrategyWrapper', 'get_historical_data_path']
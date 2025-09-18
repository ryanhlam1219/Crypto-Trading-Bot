"""
Shared pytest configuration and fixtures for Crypto Trading Bot tests.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import project modules
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from Utils.MetricsCollector import MetricsCollector


@pytest.fixture
def mock_metrics_collector():
    """Create a mock MetricsCollector for testing."""
    return Mock(spec=MetricsCollector)


@pytest.fixture
def sample_candlestick_data():
    """Create sample candlestick data for testing."""
    return CandleStickData(
        open_time=1634567890000,    # Mock timestamp
        open_price=50000.0,
        high_price=51000.0,
        low_price=49500.0,
        close_price=50500.0,
        volume=1000.0,
        close_time=1634567950000,
        quote_asset_volume=50500000.0,
        num_trades=100,
        taker_buy_base_asset_volume=600.0,
        taker_buy_quote_asset_volume=30300000.0
    )


@pytest.fixture
def sample_candlestick_list():
    """Create a list of sample candlestick data for testing."""
    return [
        [1634567890000, "50000.0", "51000.0", "49500.0", "50500.0", 
         "1000.0", 1634567950000, "50500000.0", 100, "600.0", "30300000.0"],
        [1634567950000, "50500.0", "50800.0", "50200.0", "50600.0", 
         "800.0", 1634568010000, "40480000.0", 80, "480.0", "24288000.0"],
        [1634568010000, "50600.0", "50900.0", "50400.0", "50700.0", 
         "900.0", 1634568070000, "45630000.0", 90, "540.0", "27378000.0"]
    ]


@pytest.fixture
def mock_api_responses():
    """Standard mock API responses for different endpoints."""
    return {
        'connectivity': {'status': 'OK'},
        'account_status': {
            'status': 'ACTIVE',
            'balances': [
                {'asset': 'USD', 'free': '10000.0', 'locked': '0.0'},
                {'asset': 'BTC', 'free': '1.0', 'locked': '0.0'}
            ]
        },
        'candlestick': [
            [1634567890000, "50000.0", "51000.0", "49500.0", "50500.0", 
             "1000.0", 1634567950000, "50500000.0", 100, "600.0", "30300000.0"]
        ],
        'create_order': {
            'orderId': 123456,
            'status': 'FILLED',
            'symbol': 'BTCUSD',
            'side': 'BUY',
            'type': 'LIMIT',
            'quantity': '1.0',
            'price': '50000.0'
        }
    }


@pytest.fixture
def exchange_init_params():
    """Standard parameters for initializing exchange clients."""
    return {
        'key': 'test_api_key',
        'secret': 'test_api_secret', 
        'currency': 'USD',
        'asset': 'BTC',
        'metrics_collector': Mock(spec=MetricsCollector)
    }


@pytest.fixture
def strategy_init_params(exchange_init_params):
    """Standard parameters for initializing strategy instances."""
    mock_client = Mock()
    mock_client.currency_asset = 'BTCUSD'
    return {
        'client': mock_client,
        'interval': 5,
        'stop_loss_percentage': 2,
        'metrics_collector': exchange_init_params['metrics_collector']
    }


@pytest.fixture
def mock_successful_http_response():
    """Mock a successful HTTP response."""
    response = Mock()
    response.status_code = 200
    response.text = '{"status": "OK"}'
    response.json.return_value = {"status": "OK"}
    return response


@pytest.fixture
def mock_failed_http_response():
    """Mock a failed HTTP response."""
    response = Mock()
    response.status_code = 500
    response.text = '{"error": "Internal Server Error"}'
    response.json.return_value = {"error": "Internal Server Error"}
    return response


# Parametrized fixtures for testing multiple implementations
@pytest.fixture(params=[OrderType.MARKET_ORDER, OrderType.LIMIT_ORDER, OrderType.STOP_LIMIT_ORDER])
def order_type(request):
    """Parametrized order types for testing."""
    return request.param


@pytest.fixture(params=[TradeDirection.BUY, TradeDirection.SELL])
def trade_direction(request):
    """Parametrized trade directions for testing."""
    return request.param


@pytest.fixture(params=[1, 5, 15, 30, 60])
def interval(request):
    """Parametrized intervals for testing."""
    return request.param


# Test data generators
@pytest.fixture
def price_scenarios():
    """Various price scenarios for testing."""
    return {
        'normal': 50000.0,
        'high': 100000.0,
        'low': 1000.0,
        'zero': 0.0,
        'negative': -1000.0,
        'decimal': 50123.456
    }


@pytest.fixture
def grid_test_scenarios():
    """Test scenarios for grid trading strategy."""
    return [
        {'base_price': 50000.0, 'grid_percentage': 0.01, 'num_levels': 3},
        {'base_price': 50000.0, 'grid_percentage': 0.02, 'num_levels': 5},
        {'base_price': 30000.0, 'grid_percentage': 0.005, 'num_levels': 2},
    ]


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup any test artifacts after each test."""
    yield
    # Add any cleanup logic here if needed
    pass
"""
Compliance verification tests for Exchange and Strategy implementations.

Ensures all concrete implementations properly implement their base class contracts.
These tests verify that implementations have required methods and attributes,
preventing runtime errors when new exchanges or strategies are added.
"""

import pytest
from unittest.mock import Mock

# Import implementations to test
from Exchanges.Live.Binance import Binance
from Exchanges.Test.BinanceBacktestClient import BinanceBacktestClient
from Exchanges.Test.KrakenBacktestClient import KrakenBackTestClient
from Exchanges.Test.TestExchange import TestExchange
from Strategies.GridTradingStrategy import GridTradingStrategy


@pytest.mark.parametrize("exchange_class,init_params", [
    (Binance, ("key", "secret", "USD", "BTC", Mock())),
    (BinanceBacktestClient, ("key", "secret", "USD", "BTC", Mock())),
    (KrakenBackTestClient, ("key", "secret", "USD", "BTC", Mock())),
    (TestExchange, ("key", "secret", "USD", "BTC", Mock())),
])
class TestExchangeCompliance:
    """Verify all Exchange implementations comply with base interface."""
    
    def test_has_required_methods(self, exchange_class, init_params):
        """Test that implementation has all required Exchange methods."""
        instance = exchange_class(*init_params)
        
        # Required methods from Exchange base class
        required_methods = [
            'get_connectivity_status',
            'get_account_status', 
            'get_candle_stick_data',
            'create_new_order'
        ]
        
        for method_name in required_methods:
            assert hasattr(instance, method_name), f"{exchange_class.__name__} missing {method_name}"
            assert callable(getattr(instance, method_name)), f"{method_name} not callable"
    
    def test_has_required_attributes(self, exchange_class, init_params):
        """Test that implementation has required attributes."""
        instance = exchange_class(*init_params)
        
        # Required attributes
        required_attrs = ['apiKey', 'apiSecret', 'currency', 'asset', 'currency_asset']
        
        for attr_name in required_attrs:
            assert hasattr(instance, attr_name), f"{exchange_class.__name__} missing {attr_name}"
        
        # Verify attribute values
        assert instance.apiKey == "key"
        assert instance.apiSecret == "secret" 
        assert instance.currency == "USD"
        assert instance.asset == "BTC"
        assert instance.currency_asset == "BTCUSD"


@pytest.mark.parametrize("strategy_class,init_params", [
    (GridTradingStrategy, (Mock(), 1, 5, Mock())),
])
class TestStrategyCompliance:
    """Verify all Strategy implementations comply with base interface."""
    
    def test_has_required_methods(self, strategy_class, init_params):
        """Test that implementation has all required Strategy methods."""
        instance = strategy_class(*init_params)
        
        # Required methods from Strategy base class
        required_methods = [
            'execute_trade',
            'run_strategy',
            'should_enter_trade', 
            'should_exit_trade'
        ]
        
        for method_name in required_methods:
            assert hasattr(instance, method_name), f"{strategy_class.__name__} missing {method_name}"
            assert callable(getattr(instance, method_name)), f"{method_name} not callable"
    
    def test_has_required_attributes(self, strategy_class, init_params):
        """Test that implementation has required attributes."""
        instance = strategy_class(*init_params)
        
        # Required attributes
        required_attrs = ['client', 'interval', 'threshold', 'metrics_collector']
        
        for attr_name in required_attrs:
            assert hasattr(instance, attr_name), f"{strategy_class.__name__} missing {attr_name}"
        
        # Verify client and metrics are set
        assert instance.client is not None
        assert instance.metrics_collector is not None
        assert instance.interval > 0
        assert instance.threshold >= 0


class TestCrossImplementationConsistency:
    """Test consistency across different implementations."""
    
    def test_currency_asset_format_consistency(self):
        """Test all exchanges format currency_asset consistently."""
        exchanges = [
            Binance("key", "secret", "USD", "BTC", Mock()),
            BinanceBacktestClient("key", "secret", "USD", "BTC", Mock()),
            KrakenBackTestClient("key", "secret", "USD", "BTC", Mock()),
            TestExchange("key", "secret", "USD", "BTC", Mock()),
        ]
        
        for exchange in exchanges:
            assert exchange.currency_asset == "BTCUSD"
            assert exchange.currency == "USD" 
            assert exchange.asset == "BTC"
    
    def test_all_exchanges_instantiable(self):
        """Test that all exchange implementations can be instantiated."""
        exchange_configs = [
            (Binance, ("key", "secret", "USD", "BTC", Mock())),
            (BinanceBacktestClient, ("key", "secret", "USD", "BTC", Mock())),
            (KrakenBackTestClient, ("key", "secret", "USD", "BTC", Mock())),
            (TestExchange, ("key", "secret", "USD", "BTC", Mock())),
        ]
        
        for exchange_class, params in exchange_configs:
            # Should not raise exception
            instance = exchange_class(*params)
            assert instance is not None
            assert instance.currency_asset == "BTCUSD"
    
    def test_all_strategies_instantiable(self):
        """Test that all strategy implementations can be instantiated."""
        mock_client = Mock()
        mock_metrics = Mock()
        
        # Test GridTradingStrategy
        strategy = GridTradingStrategy(mock_client, 1, 5, mock_metrics)
        assert strategy is not None
        assert strategy.client == mock_client
        assert strategy.metrics_collector == mock_metrics
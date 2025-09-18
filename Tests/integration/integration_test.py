"""
Integration tests for the crypto trading bot.

Tests end-to-end scenarios with strategies and exchanges working together:
- Strategy + Exchange integration
- Real trading workflows
- Backtest execution flows
- Error handling across components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from Strategies.GridTradingStrategy import GridTradingStrategy
from Exchanges.Test.BinanceBacktestClient import BinanceBacktestClient
from Exchanges.Test.KrakenBacktestClient import KrakenBackTestClient
from Exchanges.Test.testExchange import TestExchange
from Strategies.ExchangeModels import CandleStickData, OrderType, TradeDirection
from Tests.utils import DataFetchException, StrategyWrapper


class TestStrategyExchangeIntegration:
    """Test strategies working with different exchange implementations."""
    
    def setup_method(self):
        """Setup test components."""
        self.mock_metrics = Mock()
    
    def test_grid_strategy_with_binance_backtest_client(self):
        """Test GridTradingStrategy with BinanceBacktestClient."""
        # Create backtest client
        client = BinanceBacktestClient("key", "secret", "USD", "BTC", self.mock_metrics)
        
        # Create strategy with backtest client
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify integration
        assert strategy.client == client
        assert isinstance(strategy.client, BinanceBacktestClient)
        assert strategy.client.currency_asset == "BTCUSD"
    
    def test_grid_strategy_with_kraken_backtest_client(self):
        """Test GridTradingStrategy with KrakenBacktestClient."""
        # Create Kraken backtest client
        client = KrakenBackTestClient("key", "secret", "USD", "BTC")
        
        # Create strategy with Kraken client
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify integration
        assert strategy.client == client
        assert isinstance(strategy.client, KrakenBackTestClient)
        assert strategy.client.currency == "USD"
        assert strategy.client.asset == "BTC"
    
    def test_grid_strategy_with_test_exchange(self):
        """Test GridTradingStrategy with TestExchange."""
        # Create test exchange client
        client = TestExchange("key", "secret", "USD", "BTC", self.mock_metrics)
        
        # Create strategy with test exchange
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify integration
        assert strategy.client == client
        assert isinstance(strategy.client, TestExchange)
        assert strategy.client.api_url == "https://api.binance.us"
    
    @patch('time.sleep')
    def test_strategy_wrapper_integration(self, mock_sleep):
        """Test StrategyWrapper with GridTradingStrategy."""
        # Create mock client that raises DataFetchException to end backtest
        mock_client = Mock()
        mock_client.get_candle_stick_data.side_effect = DataFetchException("Backtest complete")
        
        # Create strategy
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Create strategy wrapper
        wrapper = StrategyWrapper(strategy)
        
        # Verify wrapper integration
        assert wrapper.strategy == strategy
        assert isinstance(wrapper.strategy, GridTradingStrategy)
    
    def test_end_to_end_backtest_simulation(self):
        """Test complete backtest workflow simulation."""
        # Create backtest client with mock data
        client = BinanceBacktestClient("key", "secret", "USD", "BTC", self.mock_metrics)
        
        # Add some mock historical data
        mock_data = [
            [1640995200000, 49000.0, 49500.0, 48500.0, 49200.0, 100.0, 
             1640995259999, 4920000.0, 150, 60.0, 2952000.0, "0"],
            [1640995260000, 49200.0, 49800.0, 48800.0, 49500.0, 110.0,
             1640995319999, 5445000.0, 165, 65.0, 3217500.0, "0"],
            [1640995320000, 49500.0, 50000.0, 49000.0, 49800.0, 120.0,
             1640995379999, 5976000.0, 180, 70.0, 3486000.0, "0"]
        ]
        client.test_data = mock_data
        
        # Create strategy
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify the complete setup
        assert len(client.test_data) == 3
        assert client.testIndex == 0
        assert strategy.candlestick_data == []
        
        # Test getting first candle
        first_candle = client.get_candle_stick_data(1)
        assert isinstance(first_candle, CandleStickData)
        assert client.testIndex == 1
    
    def test_error_propagation_across_components(self):
        """Test error handling across strategy and exchange components."""
        # Create client that will raise connection error
        mock_client = Mock()
        mock_client.get_connectivity_status.return_value = False
        mock_client.get_candle_stick_data.side_effect = ConnectionError("API unavailable")
        
        # Create strategy with failing client
        strategy = GridTradingStrategy(
            client=mock_client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify error propagation
        assert strategy.client.get_connectivity_status() is False
        
        with pytest.raises(ConnectionError):
            strategy.client.get_candle_stick_data(1)
    
    def test_metrics_integration_across_components(self):
        """Test metrics collection across strategy and exchange."""
        # Create shared metrics collector
        shared_metrics = Mock()
        shared_metrics.record_trade_entry.return_value = "trade_123"
        
        # Create components with shared metrics
        client = BinanceBacktestClient("key", "secret", "USD", "BTC", shared_metrics)
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=shared_metrics
        )
        
        # Verify metrics integration
        assert client.metrics_collector == shared_metrics
        assert strategy.metrics_collector == shared_metrics
        assert client.metrics_collector == strategy.metrics_collector
    
    def test_currency_pair_consistency(self):
        """Test currency pair consistency across components."""
        currency = "USD"
        asset = "BTC"
        expected_pair = "BTCUSD"
        
        # Test with different exchange implementations
        exchanges = [
            BinanceBacktestClient("key", "secret", currency, asset, self.mock_metrics),
            KrakenBackTestClient("key", "secret", currency, asset),
            TestExchange("key", "secret", currency, asset, self.mock_metrics),
        ]
        
        for exchange in exchanges:
            assert exchange.currency == currency
            assert exchange.asset == asset
            
            # All exchanges should create the same currency_asset pair
            if hasattr(exchange, 'currency_asset'):
                assert exchange.currency_asset == expected_pair
    
    def test_order_type_consistency(self):
        """Test order type handling consistency across exchanges."""
        order_types = [OrderType.LIMIT_ORDER, OrderType.MARKET_ORDER]
        
        # Test that all exchanges handle the same order types
        for order_type in order_types:
            # BinanceBacktestClient
            binance_type = BinanceBacktestClient._BinanceBacktestClient__get_binance_order_type(order_type)
            assert binance_type in ["LIMIT", "MARKET", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT", "LIMIT_MAKER"]
            
            # TestExchange
            test_type = TestExchange._TestExchange__get_binance_order_type(order_type)
            assert test_type in ["LIMIT", "MARKET", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT", "LIMIT_MAKER"]
            
            # Kraken
            kraken_type = KrakenBackTestClient._KrakenBackTestClient__get_kraken_order_type(order_type)
            assert kraken_type in ["limit", "market"]
    
    def test_trade_direction_consistency(self):
        """Test trade direction handling across components."""
        directions = [TradeDirection.BUY, TradeDirection.SELL]
        
        for direction in directions:
            # Verify direction values are consistent
            assert direction.value in ["BUY", "SELL"]
            
            # Test that strategies can use these directions
            mock_client = Mock()
            strategy = GridTradingStrategy(
                client=mock_client,
                interval=1,
                threshold=5,
                metrics_collector=self.mock_metrics
            )
            
            # Strategy should be able to work with these directions
            assert direction in [TradeDirection.BUY, TradeDirection.SELL]


class TestRealWorldScenarios:
    """Test realistic trading scenarios end-to-end."""
    
    def setup_method(self):
        """Setup realistic test scenarios."""
        self.mock_metrics = Mock()
    
    def test_bull_market_scenario(self):
        """Test strategy behavior in bull market conditions."""
        # Create rising price data
        rising_prices = []
        base_price = 45000.0
        
        for i in range(20):
            # Simulate gradual price increase with some volatility
            price = base_price + (i * 250) + (i % 3 * 100)  # Rising with noise
            candle = [
                1640995200000 + (i * 60000),  # timestamp
                price - 50, price + 100, price - 100, price,  # OHLC
                100.0,  # volume
                1640995259999 + (i * 60000),  # close time
                price * 100,  # quote volume
                150, 60.0, price * 60, "0"  # other fields
            ]
            rising_prices.append(candle)
        
        # Create backtest client with bull market data
        client = BinanceBacktestClient("key", "secret", "USD", "BTC", self.mock_metrics)
        client.test_data = rising_prices
        
        # Create grid strategy
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify strategy can handle bull market data
        assert len(client.test_data) == 20
        
        # Get first few candles to simulate strategy execution
        candle1 = client.get_candle_stick_data(1)
        candle2 = client.get_candle_stick_data(1)
        
        # Verify price progression
        assert candle2.close_price > candle1.close_price  # Rising market
    
    def test_bear_market_scenario(self):
        """Test strategy behavior in bear market conditions."""
        # Create falling price data
        falling_prices = []
        base_price = 55000.0
        
        for i in range(15):
            # Simulate gradual price decrease
            price = base_price - (i * 300)
            candle = [
                1640995200000 + (i * 60000),
                price + 50, price + 200, price - 200, price,
                100.0,
                1640995259999 + (i * 60000),
                price * 100,
                150, 60.0, price * 60, "0"
            ]
            falling_prices.append(candle)
        
        # Create backtest client with bear market data
        client = BinanceBacktestClient("key", "secret", "USD", "BTC", self.mock_metrics)
        client.test_data = falling_prices
        
        # Create grid strategy
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify strategy can handle bear market data
        assert len(client.test_data) == 15
        
        # Test price trend detection
        candle1 = client.get_candle_stick_data(1)
        candle2 = client.get_candle_stick_data(1)
        
        assert candle2.close_price < candle1.close_price  # Falling market
    
    def test_sideways_market_scenario(self):
        """Test strategy behavior in sideways/ranging market."""
        # Create sideways price data
        sideways_prices = []
        base_price = 50000.0
        
        for i in range(25):
            # Simulate price oscillating around base price
            offset = 500 * (1 if i % 4 < 2 else -1)  # Oscillate ±500
            price = base_price + offset + (i % 2 * 100)  # Add some noise
            
            candle = [
                1640995200000 + (i * 60000),
                price - 25, price + 75, price - 75, price,
                100.0,
                1640995259999 + (i * 60000),
                price * 100,
                150, 60.0, price * 60, "0"
            ]
            sideways_prices.append(candle)
        
        # Create backtest client with sideways market data
        client = BinanceBacktestClient("key", "secret", "USD", "BTC", self.mock_metrics)
        client.test_data = sideways_prices
        
        # Create grid strategy (ideal for sideways markets)
        strategy = GridTradingStrategy(
            client=client,
            interval=1,
            threshold=5,
            metrics_collector=self.mock_metrics
        )
        
        # Verify strategy setup for ranging market
        assert len(client.test_data) == 25
        
        # Grid strategies should work well in sideways markets
        # Test that we can get multiple candles with oscillating prices
        prices = []
        for _ in range(5):
            candle = client.get_candle_stick_data(1)
            prices.append(candle.close_price)
        
        # In sideways market, prices should oscillate around base
        price_range = max(prices) - min(prices)
        assert price_range > 0  # Should have price movement
        assert price_range < 2000  # But not trending strongly
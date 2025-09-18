"""
Test fixtures and utilities for strategy testing.
"""

from typing import Dict, Any, List
from unittest.mock import Mock
from datetime import datetime, timedelta


class MockTradeScenarios:
    """Predefined trading scenarios for strategy testing."""
    
    @staticmethod
    def profitable_grid_trade():
        """Scenario where grid trading is profitable."""
        return {
            'initial_price': 50000.0,
            'price_movements': [
                49500.0,  # Trigger buy order
                50000.0,  # Back to initial
                50500.0,  # Trigger sell from buy
                50000.0,  # Back to initial
                49000.0,  # Another buy trigger
                50000.0,  # Back up
            ],
            'expected_trades': 4,
            'expected_profit': True
        }
    
    @staticmethod
    def losing_grid_trade():
        """Scenario where grid trading hits stop losses."""
        return {
            'initial_price': 50000.0,
            'price_movements': [
                49500.0,  # Trigger buy order
                48000.0,  # Hit stop loss
                47000.0,  # Continue down
                46000.0,  # Further down
            ],
            'expected_trades': 2,  # Entry + stop loss exit
            'expected_profit': False
        }
    
    @staticmethod
    def sideways_market():
        """Scenario with sideways price action."""
        return {
            'initial_price': 50000.0,
            'price_movements': [
                50100.0, 49900.0, 50050.0, 49950.0, 50025.0
            ],
            'expected_trades': 0,  # No significant movements
            'expected_profit': None
        }


class MockMetricsCollector:
    """Mock MetricsCollector for testing strategy behavior."""
    
    def __init__(self):
        self.active_trades = []
        self.closed_trades = []
        self.cancelled_trades = []
        self.strategy_signals = []
        self.recorded_entries = []
        self.recorded_exits = []
    
    def record_trade_entry(self, trade_id: str, symbol: str, direction: str, 
                          entry_price: float, quantity: float, stop_loss: float, 
                          profit_target: float, strategy_name: str):
        """Mock trade entry recording."""
        trade = {
            'trade_id': trade_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'profit_target': profit_target,
            'strategy_name': strategy_name,
            'entry_time': datetime.now()
        }
        self.active_trades.append(trade)
        self.recorded_entries.append(trade)
        return trade
    
    def record_trade_exit(self, trade_id: str, exit_price: float, reason: str):
        """Mock trade exit recording."""
        # Find the active trade
        trade = None
        for i, active_trade in enumerate(self.active_trades):
            if active_trade['trade_id'] == trade_id:
                trade = self.active_trades.pop(i)
                break
        
        if not trade:
            return None
        
        # Calculate profit/loss
        if trade['direction'] == 'BUY':
            profit_loss = (exit_price - trade['entry_price']) * trade['quantity']
        else:
            profit_loss = (trade['entry_price'] - exit_price) * trade['quantity']
        
        closed_trade = {
            **trade,
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'reason': reason,
            'profit_loss': profit_loss
        }
        
        self.closed_trades.append(closed_trade)
        self.recorded_exits.append(closed_trade)
        return closed_trade
    
    def get_active_trades_count(self):
        """Get number of active trades."""
        return len(self.active_trades)
    
    def get_total_profit_loss(self):
        """Calculate total profit/loss from closed trades."""
        return sum(trade['profit_loss'] for trade in self.closed_trades)


class StrategyTestHelper:
    """Helper utilities for strategy testing."""
    
    @staticmethod
    def create_mock_exchange_client():
        """Create a mock exchange client with standard behavior."""
        mock_client = Mock()
        mock_client.currency_asset = "BTCUSD"
        mock_client.currency = "USD"
        mock_client.asset = "BTC"
        
        # Mock successful connectivity
        mock_client.get_connectivity_status.return_value = True
        
        # Mock account status
        mock_client.get_account_status.return_value = None
        
        # Mock order creation (successful by default)
        mock_client.create_new_order.return_value = {
            'orderId': 123456,
            'status': 'FILLED'
        }
        
        return mock_client
    
    @staticmethod
    def create_candlestick_sequence(start_price: float, price_movements: List[float]):
        """Create a sequence of candlestick data from price movements."""
        from Strategies.ExchangeModels import CandleStickData
        
        candlesticks = []
        current_time = 1634567890000
        
        for i, close_price in enumerate([start_price] + price_movements):
            open_price = start_price if i == 0 else price_movements[i-1]
            high_price = max(open_price, close_price) * 1.001
            low_price = min(open_price, close_price) * 0.999
            
            candlestick = CandleStickData(
                open_time=current_time,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=1000.0,
                close_time=current_time + 60000,
                quote_asset_volume=close_price * 1000.0,
                num_trades=100,
                taker_buy_base_asset_volume=600.0,
                taker_buy_quote_asset_volume=close_price * 600.0
            )
            
            candlesticks.append(candlestick)
            current_time += 60000
        
        return candlesticks
    
    @staticmethod
    def simulate_strategy_run(strategy, price_sequence: List[float], 
                            initial_candlesticks: int = 10):
        """Simulate a strategy run with given price sequence."""
        results = {
            'trades_executed': 0,
            'final_profit': 0.0,
            'errors': []
        }
        
        try:
            # Simulate initial candlestick collection
            for i in range(initial_candlesticks):
                mock_candlestick = StrategyTestHelper.create_candlestick_sequence(
                    price_sequence[0], [price_sequence[0]]
                )[0]
                strategy.candlestick_data.append(mock_candlestick)
            
            # Simulate price movements
            for price in price_sequence:
                strategy.check_trades(price)
                
                # Update metrics
                if hasattr(strategy, 'metrics_collector') and strategy.metrics_collector:
                    results['trades_executed'] = len(strategy.metrics_collector.recorded_entries)
                    results['final_profit'] = strategy.metrics_collector.get_total_profit_loss()
        
        except Exception as e:
            results['errors'].append(str(e))
        
        return results


# Grid trading specific test data
GRID_TRADING_SCENARIOS = {
    'basic_profitable': {
        'init_params': {
            'grid_percentage': 0.01,  # 1%
            'num_levels': 3,
            'stop_loss_percentage': 2
        },
        'base_price': 50000.0,
        'price_movements': [49500.0, 50500.0, 49000.0, 51000.0],
        'expected_outcome': 'profitable'
    },
    'stop_loss_scenario': {
        'init_params': {
            'grid_percentage': 0.01,
            'num_levels': 2,
            'stop_loss_percentage': 1
        },
        'base_price': 50000.0,
        'price_movements': [49500.0, 48900.0, 48000.0],  # Trigger stop loss
        'expected_outcome': 'loss'
    },
    'high_frequency': {
        'init_params': {
            'grid_percentage': 0.005,  # 0.5%
            'num_levels': 5,
            'stop_loss_percentage': 3
        },
        'base_price': 50000.0,
        'price_movements': [
            49750.0, 50250.0, 49875.0, 50125.0, 49625.0, 50375.0
        ],
        'expected_outcome': 'multiple_trades'
    }
}
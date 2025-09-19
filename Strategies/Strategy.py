from abc import ABC, abstractmethod
import signal
import sys
from typing import TYPE_CHECKING
from Exchanges.exchange import Exchange
from Strategies.ExchangeModels import TradeDirection

if TYPE_CHECKING:
    from Utils.MetricsCollector import MetricsCollector


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Provides common functionality including signal handling for graceful shutdown,
    trade execution interface, and metrics collection integration.
    """
    
    def __init__(self, client: Exchange, interval: int, stop_loss_percentage: int, metrics_collector: "MetricsCollector"):
        self.client = client
        self.interval = interval
        self.current_level = None
        self.current_trade = None
        self.current_direction = TradeDirection.BUY
        self.current_profit_level = None
        self.stop_loss_percentage = stop_loss_percentage
        self.metrics_collector = metrics_collector
        
        # Signal handling for graceful shutdown - common to all strategies
        self.shutdown_requested = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        print("Signal handling initialized - Press Ctrl+C for graceful shutdown")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (Ctrl+C, SIGTERM) gracefully."""
        signal_name = "SIGINT (Ctrl+C)" if signum == signal.SIGINT else f"Signal {signum}"
        print(f"\n{signal_name} received. Initiating graceful shutdown...")
        self.shutdown_requested = True
        self.on_shutdown_signal(signum, frame)

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_requested

    def request_shutdown(self):
        """Programmatically request shutdown."""
        self.shutdown_requested = True

    # Abstract methods that concrete strategies must implement
    @abstractmethod
    def execute_trade(self, price, direction):
        """Execute a trade at the given price and direction."""
        pass

    @abstractmethod
    def close_trade(self, price):
        """Close a trade at the given price."""
        pass

    @abstractmethod
    def check_trades(self, price):
        """Check and manage active trades at the current price."""
        pass
    
    @abstractmethod
    def run_strategy(self, trade_interval):
        """
        Run the main strategy loop.
        
        Implementations should:
        1. Respect self.shutdown_requested flag
        2. Call self.perform_graceful_shutdown() on exit
        3. Handle exceptions appropriately
        """
        pass

    # Default implementations that can be overridden
    def on_shutdown_signal(self, signum, frame):
        """
        Called when a shutdown signal is received.
        
        Override this method to implement strategy-specific shutdown logic.
        Default implementation does nothing.
        """
        pass

    def perform_graceful_shutdown(self):
        """
        Perform graceful shutdown operations.
        
        Override this method to implement strategy-specific cleanup.
        Default implementation provides basic reporting.
        """
        print("\n" + "="*50)
        print("PERFORMING GRACEFUL SHUTDOWN")
        print("="*50)
        
        try:
            # Basic metrics reporting
            if hasattr(self.metrics_collector, 'active_trades'):
                active_trades = getattr(self.metrics_collector, 'active_trades', [])
                if active_trades:
                    print(f"Found {len(active_trades)} active trades during shutdown.")
                    print("Note: Active trades remain open as per strategy design.")
            
            # Basic performance summary
            if hasattr(self.metrics_collector, 'get_performance_summary'):
                print("\nFinal Performance Summary:")
                summary = self.metrics_collector.get_performance_summary()
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            
            print("\nStrategy shutdown completed successfully.")
            
        except Exception as e:
            print(f"Error during graceful shutdown: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*50)

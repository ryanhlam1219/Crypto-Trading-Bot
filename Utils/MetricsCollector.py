"""
Centralized metrics collection system for tracking trading performance,
exchange API metrics, and strategy analytics.
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

class TradeStatus(Enum):
    """Status of a trade."""
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class MetricsCollector:
    """
    Centralized metrics collection for trading bot performance tracking.
    
    Handles:
    - Trade tracking (entry/exit/profit/loss)
    - Exchange API performance metrics
    - Strategy performance analytics
    - Portfolio-level calculations
    """
    
    def __init__(self):
        """Initialize the metrics collector."""
        # Trade tracking
        self.active_trades: List[Dict[str, Any]] = []
        self.closed_trades: List[Dict[str, Any]] = []
        self.cancelled_trades: List[Dict[str, Any]] = []
        
        # Exchange API metrics
        self.api_calls: List[Dict[str, Any]] = []
        self.api_errors: List[Dict[str, Any]] = []
        
        # Strategy metrics
        self.strategy_signals: List[Dict[str, Any]] = []
        
        # Session tracking
        self.session_start_time = datetime.now()
        self.total_trades_executed = 0
        
    def record_trade_entry(self, trade_id: str, symbol: str, direction: str, 
                          entry_price: float, quantity: float, stop_loss: float = None, 
                          profit_target: float = None, strategy_name: str = None) -> Dict[str, Any]:
        """
        Record a new trade entry.
        
        Args:
            trade_id: Unique identifier for the trade
            symbol: Trading symbol (e.g., 'BTCUSD')
            direction: 'BUY' or 'SELL'
            entry_price: Price at which trade was entered
            quantity: Quantity traded
            stop_loss: Stop loss price (optional)
            profit_target: Target profit price (optional)
            strategy_name: Name of strategy that generated the trade
            
        Returns:
            Dict containing the trade record
        """
        trade = {
            'trade_id': trade_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'profit_target': profit_target,
            'strategy_name': strategy_name,
            'entry_time': datetime.now(),
            'status': TradeStatus.ACTIVE.value,
            'exit_price': None,
            'exit_time': None,
            'profit_loss': None,
            'profit_loss_percentage': None
        }
        
        self.active_trades.append(trade)
        self.total_trades_executed += 1
        
        print(f"📈 Trade Entry Recorded: {direction} {quantity} {symbol} at ${entry_price}")
        return trade
    
    def record_trade_exit(self, trade_id: str, exit_price: float, reason: str = "manual") -> Optional[Dict[str, Any]]:
        """
        Record a trade exit and calculate profit/loss.
        
        Args:
            trade_id: Unique identifier for the trade to close
            exit_price: Price at which trade was closed
            reason: Reason for trade closure ('profit_target', 'stop_loss', 'manual')
            
        Returns:
            Dict containing the closed trade record, or None if trade not found
        """
        # Find the active trade
        trade_to_close = None
        for trade in self.active_trades:
            if trade['trade_id'] == trade_id:
                trade_to_close = trade
                break
        
        if not trade_to_close:
            print(f"⚠️ Warning: Trade {trade_id} not found in active trades")
            return None
        
        # Calculate profit/loss
        entry_price = trade_to_close['entry_price']
        quantity = trade_to_close['quantity']
        
        if trade_to_close['direction'] == 'BUY':
            profit_loss = (exit_price - entry_price) * quantity
        else:  # SELL
            profit_loss = (entry_price - exit_price) * quantity
        
        profit_loss_percentage = (profit_loss / (entry_price * quantity)) * 100
        
        # Update trade record
        trade_to_close.update({
            'exit_price': exit_price,
            'exit_time': datetime.now(),
            'profit_loss': profit_loss,
            'profit_loss_percentage': profit_loss_percentage,
            'status': TradeStatus.CLOSED.value,
            'exit_reason': reason
        })
        
        # Move from active to closed
        self.active_trades.remove(trade_to_close)
        self.closed_trades.append(trade_to_close)
        
        print(f"📉 Trade Exit Recorded: {trade_to_close['direction']} {trade_to_close['symbol']} "
              f"closed at ${exit_price}. P&L: ${round(profit_loss, 2)} ({profit_loss_percentage:.2f}%)")
        
        return trade_to_close
    
    def record_api_call(self, endpoint: str, method: str, response_time: float, 
                       status_code: int, success: bool = True, error_message: str = None):
        """
        Record exchange API call metrics.
        
        Args:
            endpoint: API endpoint called
            method: HTTP method (GET, POST, etc.)
            response_time: Response time in seconds
            status_code: HTTP status code
            success: Whether the call was successful
            error_message: Error message if call failed
        """
        api_call = {
            'endpoint': endpoint,
            'method': method,
            'response_time': response_time,
            'status_code': status_code,
            'success': success,
            'error_message': error_message,
            'timestamp': datetime.now()
        }
        
        if success:
            self.api_calls.append(api_call)
        else:
            self.api_errors.append(api_call)
            print(f"🚨 API Error: {method} {endpoint} - {status_code} - {error_message}")
    
    def record_strategy_signal(self, strategy_name: str, signal_type: str, 
                              symbol: str, price: float, confidence: float = None, 
                              metadata: Dict[str, Any] = None):
        """
        Record strategy signal generation.
        
        Args:
            strategy_name: Name of the strategy
            signal_type: Type of signal ('BUY', 'SELL', 'HOLD')
            symbol: Trading symbol
            price: Current price when signal was generated
            confidence: Signal confidence level (0-1)
            metadata: Additional signal metadata
        """
        signal = {
            'strategy_name': strategy_name,
            'signal_type': signal_type,
            'symbol': symbol,
            'price': price,
            'confidence': confidence,
            'metadata': metadata or {},
            'timestamp': datetime.now()
        }
        
        self.strategy_signals.append(signal)
    
    def calculate_total_profit_loss(self) -> float:
        """Calculate total profit/loss from all closed trades."""
        return sum(trade['profit_loss'] for trade in self.closed_trades if trade['profit_loss'] is not None)
    
    def calculate_net_profit_percentage(self) -> float:
        """
        Calculate net profit percentage based on total capital deployed.
        
        Returns:
            Net profit percentage
        """
        if not self.closed_trades:
            return 0.0
        
        total_profit = self.calculate_total_profit_loss()
        total_entry_amount = sum(trade['entry_price'] * trade['quantity'] for trade in self.closed_trades)
        
        if total_entry_amount == 0:
            return 0.0
        
        return (total_profit / total_entry_amount) * 100
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage."""
        if not self.closed_trades:
            return 0.0
        
        winning_trades = len([trade for trade in self.closed_trades if trade['profit_loss'] > 0])
        return (winning_trades / len(self.closed_trades)) * 100
    
    def calculate_average_profit_per_trade(self) -> float:
        """Calculate average profit per trade."""
        if not self.closed_trades:
            return 0.0
        
        return self.calculate_total_profit_loss() / len(self.closed_trades)
    
    def get_api_performance_stats(self) -> Dict[str, Any]:
        """Get API performance statistics."""
        if not self.api_calls:
            return {'avg_response_time': 0, 'success_rate': 0, 'total_calls': 0}
        
        total_calls = len(self.api_calls) + len(self.api_errors)
        success_rate = (len(self.api_calls) / total_calls) * 100
        avg_response_time = sum(call['response_time'] for call in self.api_calls) / len(self.api_calls)
        
        return {
            'avg_response_time': avg_response_time,
            'success_rate': success_rate,
            'total_calls': total_calls,
            'total_errors': len(self.api_errors)
        }
    
    def generate_performance_report(self) -> str:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Formatted string containing performance metrics
        """
        report_lines = [
            "=" * 60,
            "🚀 TRADING BOT PERFORMANCE REPORT",
            "=" * 60,
            f"Session Duration: {datetime.now() - self.session_start_time}",
            f"Total Trades Executed: {self.total_trades_executed}",
            "",
            "📊 TRADING PERFORMANCE:",
            f"  • Active Trades: {len(self.active_trades)}",
            f"  • Closed Trades: {len(self.closed_trades)}",
            f"  • Total P&L: ${self.calculate_total_profit_loss():.2f}",
            f"  • Net Profit %: {self.calculate_net_profit_percentage():.2f}%",
            f"  • Win Rate: {self.calculate_win_rate():.2f}%",
            f"  • Avg Profit/Trade: ${self.calculate_average_profit_per_trade():.2f}",
            ""
        ]
        
        # API Performance
        api_stats = self.get_api_performance_stats()
        report_lines.extend([
            "🌐 API PERFORMANCE:",
            f"  • Total API Calls: {api_stats['total_calls']}",
            f"  • Success Rate: {api_stats['success_rate']:.2f}%",
            f"  • Avg Response Time: {api_stats['avg_response_time']:.3f}s",
            f"  • Total Errors: {api_stats['total_errors']}",
            ""
        ])
        self.closed_trades
        # Recent trades
        if self.closed_trades:
            report_lines.extend([
                "💼 RECENT CLOSED TRADES:",
                "  Trade ID | Symbol | Direction | Entry $ | Exit $ | P&L $ | P&L %"
            ])
            
            for trade in self.closed_trades[-5:]:  # Last 5 trades
                report_lines.append(
                    f"  {trade['trade_id'][:8]} | {trade['symbol']} | {trade['direction']} | "
                    f"${trade['entry_price']:.2f} | ${trade['exit_price']:.2f} | "
                    f"${trade['profit_loss']:.2f} | {trade['profit_loss_percentage']:.2f}%"
                )
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def close_all_active_trades(self, exit_price: float, reason: str = "session_end"):
        """
        Close all active trades (useful for end of session/backtest).
        
        Args:
            exit_price: Price to use for closing all trades
            reason: Reason for closure
        """
        active_trade_ids = [trade['trade_id'] for trade in self.active_trades.copy()]
        
        for trade_id in active_trade_ids:
            self.record_trade_exit(trade_id, exit_price, reason)
        
        print(f"🔒 Closed {len(active_trade_ids)} active trades at session end")
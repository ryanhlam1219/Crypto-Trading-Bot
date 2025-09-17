#!/usr/bin/env python3
"""
Ratio Calculator

Implements the ratio calculation logic from README:
- Calculate T_ratio = T1 - T2 (transaction difference)
- Calculate fee_ratio = fee(T2) - fee(T1) (fee difference) 
- Calculate Ratio = T_ratio / fee_ratio
- Calculate average ratio for each epoch
- Predict fees: T_amt * (ratio_average) = fee_Tamt
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class FeePoint:
    """Single fee data point"""
    transaction_size: float
    fee: float
    timestamp: float
    exchange: str

@dataclass
class RatioPoint:
    """Single ratio calculation result"""
    t_ratio: float          # Transaction size difference (T1 - T2)
    fee_ratio: float        # Fee difference (fee(T2) - fee(T1))
    ratio: float            # T_ratio / fee_ratio
    timestamp: float
    exchange: str
    t1: float              # Larger transaction size
    t2: float              # Smaller transaction size
    fee1: float            # Fee for T1
    fee2: float            # Fee for T2

class RatioCalculator:
    """Calculates fee ratios and predicts fees based on transaction patterns"""
    
    def __init__(self):
        self.ratio_history: Dict[str, List[RatioPoint]] = {}  # exchange -> ratios
        
    def calculate_ratios_for_fee_points(self, fee_points: List[FeePoint], exchange: str) -> List[RatioPoint]:
        """
        Calculate ratios between consecutive fee points within the same time epoch
        
        Following README spec: For T1, T2, T3, T4, T5 calculate:
        T5-T4, T4-T3, T3-T2, T2-T1 and same for fees, then ratio = T_diff / fee_diff
        
        Args:
            fee_points: List of fee data points from same epoch (collection cycle)
            exchange: Exchange name
            
        Returns:
            List of calculated ratio points
        """
        if len(fee_points) < 2:
            logger.warning(f"Need at least 2 fee points to calculate ratios for {exchange}")
            return []
        
        # Sort by transaction size ascending (T1 < T2 < T3 < T4 < T5)
        sorted_points = sorted(fee_points, key=lambda x: x.transaction_size)
        ratios = []
        
        # Calculate consecutive differences: T(n) - T(n-1) for all adjacent pairs
        for i in range(1, len(sorted_points)):
            t_current = sorted_points[i]      # T(n) - larger transaction
            t_previous = sorted_points[i-1]   # T(n-1) - smaller transaction
            
            try:
                # Calculate differences as per README: T(n) - T(n-1)
                t_ratio = t_current.transaction_size - t_previous.transaction_size
                fee_ratio = t_current.fee - t_previous.fee
                
                # Avoid division by zero
                if fee_ratio == 0:
                    logger.warning(f"{exchange}: Zero fee difference between ${t_previous.transaction_size:.0f} and ${t_current.transaction_size:.0f}")
                    continue
                
                ratio = t_ratio / fee_ratio
                
                ratio_point = RatioPoint(
                    t_ratio=t_ratio,
                    fee_ratio=fee_ratio,
                    ratio=ratio,
                    timestamp=max(t_current.timestamp, t_previous.timestamp),  # Use later timestamp
                    exchange=exchange,
                    t1=t_current.transaction_size,   # Larger amount
                    t2=t_previous.transaction_size,  # Smaller amount
                    fee1=t_current.fee,              # Fee for larger amount
                    fee2=t_previous.fee              # Fee for smaller amount
                )
                
                ratios.append(ratio_point)
                
                logger.debug(f"{exchange}: T${t_previous.transaction_size:.0f}→${t_current.transaction_size:.0f} "
                           f"(Δ${t_ratio:.0f}) Fee${t_previous.fee:.4f}→${t_current.fee:.4f} "
                           f"(Δ${fee_ratio:.4f}) Ratio: {ratio:.2f}")
                
            except Exception as e:
                logger.error(f"Error calculating ratio for {exchange}: {e}")
                continue
        
        logger.info(f"{exchange}: Calculated {len(ratios)} consecutive ratios from {len(sorted_points)} fee points")
        return ratios
    
    def calculate_epoch_ratio_average(self, ratios: List[RatioPoint]) -> Tuple[float, int]:
        """
        Calculate average ratio for an epoch (collection of ratios)
        
        Args:
            ratios: List of ratio points
            
        Returns:
            Tuple of (average_ratio, count)
        """
        if not ratios:
            return 0.0, 0
        
        # Filter out extreme outliers (ratios beyond reasonable bounds)
        filtered_ratios = []
        for ratio_point in ratios:
            if -1000 <= ratio_point.ratio <= 1000:  # Reasonable bounds
                filtered_ratios.append(ratio_point.ratio)
        
        if not filtered_ratios:
            logger.warning("All ratios filtered out as outliers")
            return 0.0, 0
        
        # Calculate average
        avg_ratio = statistics.mean(filtered_ratios)
        
        logger.debug(f"Epoch average ratio: {avg_ratio:.4f} from {len(filtered_ratios)} ratios")
        
        return avg_ratio, len(filtered_ratios)
    
    def predict_fee(self, transaction_amount: float, ratio_average: float) -> float:
        """
        Predict fee using: T_amt * (ratio_average) = fee_Tamt
        
        Args:
            transaction_amount: Transaction size in USD
            ratio_average: Average ratio from epoch calculations
            
        Returns:
            Predicted fee amount
        """
        if ratio_average == 0:
            logger.warning("Cannot predict fee with zero ratio average")
            return 0.0
        
        predicted_fee = transaction_amount / ratio_average  # Since ratio = T/fee, fee = T/ratio
        
        logger.debug(f"Predicted fee for ${transaction_amount:.2f}: ${predicted_fee:.4f} (ratio: {ratio_average:.4f})")
        
        return predicted_fee
    
    def store_ratios(self, exchange: str, ratios: List[RatioPoint]):
        """Store calculated ratios for an exchange"""
        if exchange not in self.ratio_history:
            self.ratio_history[exchange] = []
        
        self.ratio_history[exchange].extend(ratios)
        
        # Keep only recent ratios (last 1000 per exchange)
        if len(self.ratio_history[exchange]) > 1000:
            self.ratio_history[exchange] = self.ratio_history[exchange][-1000:]
    
    def get_recent_ratio_average(self, exchange: str, lookback_count: int = 50) -> float:
        """
        Get average ratio from recent calculations for an exchange
        
        Args:
            exchange: Exchange name
            lookback_count: Number of recent ratios to average
            
        Returns:
            Average ratio
        """
        if exchange not in self.ratio_history or not self.ratio_history[exchange]:
            return 0.0
        
        recent_ratios = self.ratio_history[exchange][-lookback_count:]
        avg_ratio, count = self.calculate_epoch_ratio_average(recent_ratios)
        
        logger.info(f"{exchange} recent ratio average: {avg_ratio:.4f} from {count} ratios")
        
        return avg_ratio
    
    def get_all_exchanges_ratio_average(self, lookback_count: int = 50) -> Dict[str, float]:
        """
        Get ratio averages for all exchanges
        
        Args:
            lookback_count: Number of recent ratios to average per exchange
            
        Returns:
            Dict of exchange -> average ratio
        """
        averages = {}
        
        for exchange in self.ratio_history:
            averages[exchange] = self.get_recent_ratio_average(exchange, lookback_count)
        
        return averages
    
    def get_cross_exchange_ratio_average(self, lookback_count: int = 50) -> float:
        """
        Get average ratio across all exchanges
        
        Args:
            lookback_count: Number of recent ratios to average per exchange
            
        Returns:
            Cross-exchange average ratio
        """
        all_recent_ratios = []
        
        for exchange in self.ratio_history:
            if self.ratio_history[exchange]:
                recent_ratios = self.ratio_history[exchange][-lookback_count:]
                all_recent_ratios.extend(recent_ratios)
        
        avg_ratio, count = self.calculate_epoch_ratio_average(all_recent_ratios)
        
        logger.info(f"Cross-exchange ratio average: {avg_ratio:.4f} from {count} ratios across {len(self.ratio_history)} exchanges")
        
        return avg_ratio